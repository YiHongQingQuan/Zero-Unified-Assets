"""导出的 docx 必须是「真公式」，而不是一堆文本。"""

from __future__ import annotations

import io
import zipfile

import pytest
from docx import Document as DocxDocument

from app.core.detector import AnalyzeOptions, build_document
from app.core.docx_writer import ExportOptions, write_docx
from app.core.mathconv import get_engine

ENGINE = get_engine()
requires_engine = pytest.mark.skipif(not ENGINE.available, reason="本机没有 MML2OMML.XSL")

SAMPLE = """# 论文片段

质能方程 E=mc² 说明质量与能量等价，其中 $\\alpha \\le \\beta$。

$$
\\int_0^\\infty e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2}
$$

分段函数：
\\begin{equation}
f(x) = \\begin{cases} x, & x>0 \\\\ -x, & x\\le 0 \\end{cases}
\\end{equation}

矩阵 $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$ 混排在文字里。
"""


def _build(text: str = SAMPLE, accept_all: bool = True):
    doc, stats = build_document(text, AnalyzeOptions(markdown=True))
    for block in doc.blocks:
        for node in block.inlines:
            if node.kind == "math":
                node.accepted = accept_all
    return doc, stats


def _document_xml(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.read("word/document.xml").decode("utf-8")


@requires_engine
def test_omml_is_embedded():
    doc, _ = _build()
    result = write_docx(doc, ExportOptions())
    xml = _document_xml(result.data)
    assert xml.count("<m:oMath>") >= 5
    assert "<m:oMathPara>" in xml
    assert result.rendered >= 5
    assert result.skipped == 0


@requires_engine
def test_docx_reopens_with_python_docx():
    doc, _ = _build()
    result = write_docx(doc, ExportOptions())
    reopened = DocxDocument(io.BytesIO(result.data))
    assert len(reopened.paragraphs) >= 5
    assert reopened.sections[0].page_width is not None


@requires_engine
def test_rejected_formula_keeps_raw_text():
    doc, _ = _build(accept_all=False)
    result = write_docx(doc, ExportOptions())
    xml = _document_xml(result.data)
    assert result.rendered == 0
    assert "E=mc²" in xml or "E=mc" in xml


@requires_engine
def test_broken_formula_falls_back_with_issue():
    doc, _ = build_document(r"$$\frac{$$", AnalyzeOptions())
    node = [n for b in doc.blocks for n in b.inlines if n.kind == "math"][0]
    node.accepted = True
    result = write_docx(doc, ExportOptions())
    # 要么渲染成功，要么降级并留报告，不能静默丢弃
    assert result.rendered == 1 or result.issues


def test_page_options_applied():
    doc, _ = _build()
    result = write_docx(doc, ExportOptions(font_size=14, margin_cm=3.0, paper="A5"))
    reopened = DocxDocument(io.BytesIO(result.data))
    section = reopened.sections[0]
    assert round(section.page_width.cm, 1) == 14.8
    assert round(section.top_margin.cm, 1) == 3.0


@requires_engine
def test_table_written():
    text = "| 符号 | 含义 |\n| --- | --- |\n| x | 自变量 |"
    doc, _ = build_document(text, AnalyzeOptions(markdown=True))
    result = write_docx(doc, ExportOptions())
    reopened = DocxDocument(io.BytesIO(result.data))
    assert len(reopened.tables) == 1
    assert reopened.tables[0].cell(1, 0).text == "x"
