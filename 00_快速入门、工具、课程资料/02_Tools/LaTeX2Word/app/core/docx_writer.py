"""IR → .docx。

页面、字体、行距、缩进都可以配；公式直接以 OMML 注入段落，
失败时保留原文并在报告里留下定位信息。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from docx import Document as DocxDocument
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from app.core.ir import Block, Document, MathNode, TextRun
from app.core.mathconv import ConversionError, OmmlEngine, get_engine

PAPER_SIZES = {
    "A4": (21.0, 29.7),
    "Letter": (21.59, 27.94),
    "A5": (14.8, 21.0),
    "B5": (17.6, 25.0),
}

_HEADING_SIZES = {1: 16, 2: 14, 3: 13, 4: 12, 5: 12, 6: 12}


@dataclass
class ExportOptions:
    cn_font: str = "宋体"
    en_font: str = "Times New Roman"
    font_size: float = 12.0          # pt，12pt = 小四
    line_spacing: float = 1.5
    first_line_indent: float = 2.0   # 字符数
    margin_cm: float = 2.54
    paper: str = "A4"
    math_font: str = "Cambria Math"
    # 上下限位置：below（一律下方，默认）/ auto（跟随 LaTeX 惯例）/ side（一律右侧）
    limits_mode: str = "below"
    # 大型运算符尺寸：auto（高内容时固定，默认）/ fixed（一律固定）/ native（跟随内容）
    nary_mode: str = "auto"


@dataclass
class Issue:
    block: int
    formula: str
    message: str


@dataclass
class WriteResult:
    data: bytes
    issues: list[Issue] = field(default_factory=list)
    rendered: int = 0
    skipped: int = 0


class DocxWriter:
    def __init__(self, options: ExportOptions, engine: OmmlEngine | None = None) -> None:
        self.options = options
        self.engine = engine or get_engine()
        self.result = WriteResult(data=b"")
        self.doc = DocxDocument()
        self._prepare_page()
        self._prepare_styles()

    # ------------------------------------------------------------ 基础设置
    def _prepare_page(self) -> None:
        section = self.doc.sections[0]
        w, h = PAPER_SIZES.get(self.options.paper, PAPER_SIZES["A4"])
        section.page_width = Cm(w)
        section.page_height = Cm(h)
        m = Cm(self.options.margin_cm)
        section.top_margin = m
        section.bottom_margin = m
        section.left_margin = m
        section.right_margin = m

    def _prepare_styles(self) -> None:
        opt = self.options
        normal = self.doc.styles["Normal"]
        normal.font.name = opt.en_font
        normal.font.size = Pt(opt.font_size)
        rpr = normal.element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:ascii"), opt.en_font)
        rfonts.set(qn("w:hAnsi"), opt.en_font)
        rfonts.set(qn("w:eastAsia"), opt.cn_font)
        rfonts.set(qn("w:cs"), opt.en_font)

        pf = normal.paragraph_format
        pf.line_spacing = opt.line_spacing
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.first_line_indent = Pt(opt.font_size * opt.first_line_indent)

    # ------------------------------------------------------------ 主流程
    def write(self, doc: Document) -> WriteResult:
        self.result.data = b""
        self.result.issues = []
        self.result.rendered = 0
        self.result.skipped = 0

        for bi, block in enumerate(doc.blocks):
            self._write_block(block, bi)

        import io

        buf = io.BytesIO()
        self.doc.save(buf)
        self.result.data = buf.getvalue()
        return self.result

    def _write_block(self, block: Block, bi: int) -> None:
        if block.kind == "table":
            self._write_table(block)
            return
        if block.kind == "display_math":
            self._write_display_math(block, bi)
            return
        if block.kind == "code":
            self._write_code(block)
            return
        if block.kind == "heading":
            self._write_heading(block)
            return
        if block.kind == "list_item":
            self._write_list_item(block, bi)
            return
        if block.kind == "quote":
            p = self.doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(self.options.font_size * 2)
            p.paragraph_format.first_line_indent = Pt(0)
            self._fill_inline(p, block, bi)
            return

        p = self.doc.add_paragraph()
        self._fill_inline(p, block, bi)

    # ------------------------------------------------------------ 各类块
    def _write_heading(self, block: Block) -> None:
        level = block.level or 1
        p = self.doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(self.options.font_size * 0.6)
        p.paragraph_format.space_after = Pt(self.options.font_size * 0.3)
        for node in block.inlines:
            if isinstance(node, TextRun):
                run = p.add_run(node.text)
                run.bold = True
                run.font.size = Pt(_HEADING_SIZES.get(level, 12))

    def _write_list_item(self, block: Block, bi: int) -> None:
        p = self.doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.left_indent = Pt(self.options.font_size * 2)
        marker = "1. " if block.ordered else "• "
        p.add_run(marker)
        self._fill_inline(p, block, bi)

    def _write_code(self, block: Block) -> None:
        p = self.doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(0)
        for node in block.inlines:
            if isinstance(node, TextRun):
                run = p.add_run(node.text)
                run.font.name = "Consolas"
                run.font.size = Pt(self.options.font_size - 1.5)

    def _write_display_math(self, block: Block, bi: int) -> None:
        node = next((n for n in block.inlines if isinstance(n, MathNode)), None)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(self.options.font_size * 0.5)
        p.paragraph_format.space_after = Pt(self.options.font_size * 0.5)
        if node is None:
            return
        if not node.accepted:
            p.add_run(node.raw or node.latex)
            self.result.skipped += 1
            return
        try:
            el = self.engine.omml_element(node.latex, display=True, limits=self.options.limits_mode, nary=self.options.nary_mode)
        except ConversionError as exc:
            self._fallback(p, node, bi, exc)
            return
        p._p.append(el)
        self.result.rendered += 1

    def _write_table(self, block: Block) -> None:
        rows = block.rows or []
        if not rows:
            return
        cols = max(len(r) for r in rows)
        table = self.doc.add_table(rows=len(rows), cols=cols)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for ri, row in enumerate(rows):
            for ci in range(cols):
                cell = table.cell(ri, ci)
                text = row[ci] if ci < len(row) else ""
                para = cell.paragraphs[0]
                para.paragraph_format.first_line_indent = Pt(0)
                run = para.add_run(text)
                if ri == 0:
                    run.bold = True
                run.font.size = Pt(self.options.font_size - 1)

    # ------------------------------------------------------------ 行内
    def _fill_inline(self, p, block: Block, bi: int) -> None:
        for node in block.inlines:
            if isinstance(node, TextRun):
                self._add_text(p, node)
                continue
            if not node.accepted:
                p.add_run(node.raw or node.latex)
                self.result.skipped += 1
                continue
            try:
                el = self.engine.omml_element(node.latex, display=False, limits=self.options.limits_mode, nary=self.options.nary_mode)
            except ConversionError as exc:
                self._fallback(p, node, bi, exc)
                continue
            p._p.append(el)
            self.result.rendered += 1

    def _add_text(self, p, node: TextRun) -> None:
        if not node.text:
            return
        parts = node.text.split("\n")
        for i, part in enumerate(parts):
            if i:
                p.add_run().add_break()
            if not part:
                continue
            run = p.add_run(part)
            if node.bold:
                run.bold = True
            if node.italic:
                run.italic = True
            if node.code:
                run.font.name = "Consolas"

    def _fallback(self, p, node: MathNode, bi: int, exc: Exception) -> None:
        p.add_run("⟦" + (node.raw or node.latex) + "⟧")
        self.result.skipped += 1
        self.result.issues.append(
            Issue(block=bi, formula=node.latex, message=str(exc))
        )
        node.error = str(exc)


def write_docx(doc: Document, options: ExportOptions | None = None,
               engine: OmmlEngine | None = None) -> WriteResult:
    writer = DocxWriter(options or ExportOptions(), engine)
    return writer.write(doc)
