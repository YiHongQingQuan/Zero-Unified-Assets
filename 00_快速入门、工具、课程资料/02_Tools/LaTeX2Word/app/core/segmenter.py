"""把原始文本切成段落 / 标题 / 列表 / 引用 / 代码块 / 表格。

切分必须绕开「已经确定的公式区间」，否则一个跨行的 $$…$$ 会被拆成两半。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^\s*(\d{1,3})[.)]\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_FENCE_RE = re.compile(r"^\s*(```+|~~~+)(.*)$")
_TABLE_SEP_RE = re.compile(r"^:?-{2,}:?$")


@dataclass
class BlockRange:
    kind: str
    start: int
    end: int
    level: int | None = None
    ordered: bool | None = None
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class SegmentOptions:
    markdown: bool = False
    line_mode: bool = True  # True: 每个换行单独成段；False: 仅空行分段


def _line_spans(text: str) -> list[tuple[int, int]]:
    lines: list[tuple[int, int]] = []
    i = 0
    n = len(text)
    while i <= n:
        j = text.find("\n", i)
        if j < 0:
            lines.append((i, n))
            break
        lines.append((i, j))
        i = j + 1
    return lines


def _covered(pos: int, protected: list[tuple[int, int]]) -> bool:
    return any(a < pos < b for a, b in protected)


def scan_code_fences(text: str) -> list[tuple[int, int]]:
    """找出 markdown 代码块（含围栏行）的区间，用于豁免公式识别。"""
    lines = _line_spans(text)
    out: list[tuple[int, int]] = []
    idx = 0
    while idx < len(lines):
        ls, le = lines[idx]
        m = _FENCE_RE.match(text[ls:le])
        if not m:
            idx += 1
            continue
        fence = m.group(1)[:3]
        close = len(lines) - 1
        for k in range(idx + 1, len(lines)):
            if text[lines[k][0]: lines[k][1]].strip().startswith(fence):
                close = k
                break
        out.append((ls, lines[close][1]))
        idx = close + 1
    return out


def build_block_ranges(
    text: str,
    options: SegmentOptions,
    protected: list[tuple[int, int]] | None = None,
) -> list[BlockRange]:
    protected = protected or []
    lines = _line_spans(text)
    consumed: set[int] = set()
    blocks: list[BlockRange] = []

    # 1) Markdown 代码块（优先，内部不做任何识别）
    if options.markdown:
        idx = 0
        while idx < len(lines):
            ls, le = lines[idx]
            m = _FENCE_RE.match(text[ls:le])
            if not m:
                idx += 1
                continue
            fence = m.group(1)
            close = idx
            for k in range(idx + 1, len(lines)):
                if lines[k] and text[lines[k][0]: lines[k][1]].strip().startswith(fence[:3]):
                    close = k
                    break
            body_start = lines[idx][1] + 1 if lines[idx][1] < len(text) else len(text)
            body_end = lines[close][0] if close > idx else body_start
            blocks.append(BlockRange("code", min(body_start, len(text)), max(body_end, body_start)))
            for k in range(idx, close + 1):
                consumed.add(k)
            idx = close + 1

    # 2) Markdown 表格
    if options.markdown:
        idx = 0
        while idx < len(lines):
            if idx in consumed:
                idx += 1
                continue
            ls, le = lines[idx]
            body = text[ls:le].strip()
            if not (body.startswith("|") and body.endswith("|") and len(body) > 1):
                idx += 1
                continue
            group = [idx]
            k = idx + 1
            while k < len(lines) and k not in consumed:
                s2 = text[lines[k][0]: lines[k][1]].strip()
                if s2.startswith("|") and s2.endswith("|"):
                    group.append(k)
                    k += 1
                else:
                    break
            if len(group) >= 2:
                rows: list[list[str]] = []
                for gi in group:
                    consumed.add(gi)
                    cell_text = text[lines[gi][0]: lines[gi][1]].strip()
                    cells = [c.strip() for c in cell_text.strip("|").split("|")]
                    if all(_TABLE_SEP_RE.match(c) for c in cells if c):
                        continue
                    rows.append(cells)
                if rows:
                    blocks.append(
                        BlockRange("table", lines[group[0]][0], lines[group[-1]][1], rows=rows)
                    )
            idx = max(k, idx + 1)

    # 3) 普通段落
    cur: BlockRange | None = None
    for idx, (ls, le) in enumerate(lines):
        if idx in consumed:
            if cur:
                blocks.append(cur)
                cur = None
            continue
        line = text[ls:le]
        if not line.strip():
            if cur:
                blocks.append(cur)
                cur = None
            continue

        if cur is None:
            cur = BlockRange("paragraph", ls, le)
        else:
            # 行首是否落在受保护区间内（跨行公式）——是则不能断开
            if options.line_mode and not _covered(ls, protected):
                blocks.append(cur)
                cur = BlockRange("paragraph", ls, le)
            else:
                cur.end = le
                continue

        # 段内分类（仅 Markdown 模式）
        if options.markdown:
            _classify(text[ls:le], cur, ls)

    if cur:
        blocks.append(cur)

    # 4) 修剪首尾空白
    trimmed: list[BlockRange] = []
    for b in sorted(blocks, key=lambda x: x.start):
        if b.kind in ("code", "table"):
            trimmed.append(b)
            continue
        s, e = b.start, b.end
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if e > s:
            b.start, b.end = s, e
            trimmed.append(b)
    return trimmed


def _classify(line: str, block: BlockRange, line_start: int) -> None:
    m = _HEADING_RE.match(line)
    if m:
        block.kind = "heading"
        block.level = min(len(m.group(1)), 6)
        block.start = line_start + m.start(2)
        return
    m = _UL_RE.match(line)
    if m:
        block.kind = "list_item"
        block.ordered = False
        block.start = line_start + m.start(1)
        return
    m = _OL_RE.match(line)
    if m:
        block.kind = "list_item"
        block.ordered = True
        block.start = line_start + m.start(2)
        return
    m = _QUOTE_RE.match(line)
    if m:
        block.kind = "quote"
        block.start = line_start + m.start(1)
