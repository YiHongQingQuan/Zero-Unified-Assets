"""识别编排：显式扫描 → 分块 → 段内隐式识别 → 生成 IR。"""

from __future__ import annotations

from dataclasses import dataclass

from app.core import segmenter
from app.core.detector import explicit, implicit
from app.core.ir import Block, Document, MathNode, TextRun
from app.core.normalize import normalize
from app.core.segmenter import SegmentOptions
from app.core.unicode_math import to_latex


@dataclass
class AnalyzeOptions:
    sensitivity: str = "standard"
    markdown: bool = False
    line_mode: bool = True


@dataclass
class Stats:
    formulas: int = 0
    explicit: int = 0
    implicit_auto: int = 0
    implicit_confirm: int = 0
    pending: int = 0

    def as_dict(self) -> dict:
        return {
            "formulas": self.formulas,
            "explicit": self.explicit,
            "implicit_auto": self.implicit_auto,
            "implicit_confirm": self.implicit_confirm,
            "pending": self.pending,
        }


def build_document(text: str, options: AnalyzeOptions) -> tuple[Document, Stats]:
    seg_opts = SegmentOptions(markdown=options.markdown, line_mode=options.line_mode)

    code_ranges = segmenter.scan_code_fences(text) if options.markdown else []
    spans = [s for s in explicit.scan(text) if not _in_any(s.start, s.end, code_ranges)]

    blocks = segmenter.build_block_ranges(
        text, seg_opts, protected=[(s.start, s.end) for s in spans]
    )

    doc = Document(blocks=[], source="text")
    stats = Stats()

    for bi, br in enumerate(blocks):
        if br.kind == "code":
            doc.blocks.append(
                Block(kind="code", inlines=[TextRun(text=text[br.start: br.end])])
            )
            continue
        if br.kind == "table":
            doc.blocks.append(Block(kind="table", rows=[list(r) for r in br.rows]))
            continue

        inlines, count = _build_inlines(text, br.start, br.end, spans, options, stats, bi, 0)
        kind = br.kind
        # 整段只有一个公式时按独立公式排版：居中对齐、lim/∑ 的上下限展开。
        # 只有「识别出来的」隐式公式才自动升级；用户写了 $x$ 就是行内意图，不动。
        if kind == "paragraph" and len(inlines) == 1 and isinstance(inlines[0], MathNode):
            node = inlines[0]
            if node.display or node.origin == "implicit":
                node.display = True
                kind = "display_math"
        doc.blocks.append(Block(kind=kind, inlines=inlines, level=br.level, ordered=br.ordered))

    doc.meta["stats"] = stats.as_dict()
    doc.meta["blocks"] = len(doc.blocks)
    return doc, stats


def _in_any(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start < b and end > a for a, b in ranges)


def _build_inlines(
    text: str,
    start: int,
    end: int,
    spans: list[explicit.Span],
    options: AnalyzeOptions,
    stats: Stats,
    bi: int,
    counter: int,
) -> tuple[list, int]:
    inlines: list = []
    pos = start

    for span in spans:
        if span.start < start or span.end > end:
            continue
        if span.start > pos:
            counter = _emit_gap(text, pos, span.start, inlines, options, stats, bi, counter)
        inlines.append(_make_explicit(span, bi, counter))
        counter += 1
        stats.formulas += 1
        stats.explicit += 1
        pos = span.end

    if pos < end:
        counter = _emit_gap(text, pos, end, inlines, options, stats, bi, counter)

    if not inlines:
        inlines.append(TextRun(text=""))
    return inlines, counter


def _emit_gap(
    text: str,
    start: int,
    end: int,
    inlines: list,
    options: AnalyzeOptions,
    stats: Stats,
    bi: int,
    counter: int,
) -> int:
    gap = text[start:end]
    if not gap:
        return counter
    if not gap.strip():
        inlines.append(TextRun(text=gap))
        return counter

    cands = implicit.find_candidates(gap, options.sensitivity)
    pos = 0
    for cand in cands:
        if cand.start > pos:
            inlines.append(TextRun(text=_clean_text(gap[pos: cand.start])))
        inlines.append(_make_implicit(cand, bi, counter, stats))
        counter += 1
        pos = cand.end
    if pos < len(gap):
        inlines.append(TextRun(text=_clean_text(gap[pos:])))
    return counter


def _clean_text(s: str) -> str:
    return s.replace("\\$", "$")


def _make_explicit(span: explicit.Span, bi: int, counter: int) -> MathNode:
    norm = normalize(span.latex)
    return MathNode(
        id=f"b{bi}m{counter}",
        latex=norm.latex,
        raw=span.latex.strip(),
        display=span.display,
        origin="explicit",
        confidence=1.0,
        accepted=True,
        warnings=list(norm.warnings),
        tag=norm.tag,
    )


def _make_implicit(cand: implicit.Candidate, bi: int, counter: int, stats: Stats) -> MathNode:
    norm = normalize(to_latex(cand.text))
    accepted = cand.tier == "auto"
    if accepted:
        stats.implicit_auto += 1
    else:
        stats.implicit_confirm += 1
        stats.pending += 1
    stats.formulas += 1
    reasons = list(dict.fromkeys(cand.reasons))
    return MathNode(
        id=f"b{bi}m{counter}",
        latex=norm.latex,
        raw=cand.text,
        display=False,
        origin="implicit",
        confidence=0.9 if accepted else 0.55,
        accepted=accepted,
        warnings=list(norm.warnings),
        reasons=reasons,
    )
