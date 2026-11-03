"""显式定界符扫描：$$…$$、\\[…\\]、\\(…\\)、$…$、\\begin{env}…\\end{env}。

返回的区间是相对「整段原文」的绝对偏移，方便后面跨段落引用。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 这些环境默认按独立公式（居中、单独成段）处理
DISPLAY_ENVS = {
    "equation", "equation*", "align", "align*", "aligned", "gather", "gather*",
    "multline", "multline*", "eqnarray", "eqnarray*", "split", "cases",
    "displaymath", "math", "array", "matrix", "pmatrix", "bmatrix", "Bmatrix",
    "vmatrix", "Vmatrix", "alignat", "alignat*", "flalign", "flalign*",
}

_BEGIN_RE = re.compile(r"\\begin\s*\{([^{}]+)\}")


@dataclass
class Span:
    start: int
    end: int  # 不含
    latex: str
    display: bool
    origin: str = "explicit"

    def __len__(self) -> int:
        return self.end - self.start


def _escaped(text: str, i: int) -> bool:
    """判断 text[i] 前面是否有奇数个反斜杠。"""
    n = 0
    j = i - 1
    while j >= 0 and text[j] == "\\":
        n += 1
        j -= 1
    return n % 2 == 1


def _find(text: str, start: int, needle: str) -> int:
    """找未转义的 needle。"""
    i = start
    while True:
        j = text.find(needle, i)
        if j < 0:
            return -1
        if needle == "\\]" and _escaped(text, j):
            i = j + 1
            continue
        if needle == "$$" and _escaped(text, j):
            i = j + 2
            continue
        return j


def _find_dollar(text: str, start: int) -> int:
    """找下一个未转义、且不是 $$ 的单个 $。"""
    i = start
    while i < len(text):
        j = text.find("$", i)
        if j < 0:
            return -1
        if text.startswith("$$", j):
            i = j + 2
            continue
        if _escaped(text, j):
            i = j + 1
            continue
        return j
    return -1


_CURRENCY_RE = re.compile(r"^[\d.,\s]+$")


def looks_like_formula_dollar(content: str) -> bool:
    """判断 $…$ 里的内容是真的公式还是金额。"""
    if not content:
        return False
    if content[0].isspace() or content[-1].isspace():
        # $ 后紧跟空格通常不是行内公式（Pandoc 同规则）
        return False
    body = content.strip()
    if not body:
        return False
    # 纯数字/千分位 -> 金额
    if _CURRENCY_RE.match(body):
        return False
    return True


def scan(text: str) -> list[Span]:
    spans: list[Span] = []
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]

        if ch == "\\":
            if text.startswith("\\[", i):
                close = _find(text, i + 2, "\\]")
                if close > 0:
                    spans.append(Span(i, close + 2, text[i + 2: close], True))
                    i = close + 2
                    continue
                i += 2
                continue
            if text.startswith("\\(", i):
                close = _find(text, i + 2, "\\)")
                if close > 0:
                    spans.append(Span(i, close + 2, text[i + 2: close], False))
                    i = close + 2
                    continue
                i += 2
                continue
            m = _BEGIN_RE.match(text, i)
            if m:
                env = m.group(1).strip()
                end_tag = "\\end{" + env + "}"
                close = _find_env_end(text, m.end(), env)
                if close > 0:
                    body_start = m.start()
                    spans.append(
                        Span(i, close + len(end_tag), text[body_start: close + len(end_tag)],
                             env in DISPLAY_ENVS)
                    )
                    i = close + len(end_tag)
                    continue
                i = m.end()
                continue
            # 其它命令（含 \$）整体跳过
            i += 2 if i + 1 < n else 1
            continue

        if ch == "$":
            if text.startswith("$$", i):
                close = _find(text, i + 2, "$$")
                if close > 0:
                    spans.append(Span(i, close + 2, text[i + 2: close], True))
                    i = close + 2
                    continue
                i += 2
                continue
            close = _find_dollar(text, i + 1)
            if close > 0:
                content = text[i + 1: close]
                if looks_like_formula_dollar(content):
                    spans.append(Span(i, close + 1, content, False))
                    i = close + 1
                    continue
            i += 1
            continue

        i += 1

    return spans


def _find_env_end(text: str, start: int, env: str) -> int:
    """找匹配的 \\end{env}，允许同名环境嵌套。"""
    open_re = re.compile(r"\\begin\s*\{" + re.escape(env) + r"\}")
    close_re = re.compile(r"\\end\s*\{" + re.escape(env) + r"\}")
    depth = 1
    pos = start
    while pos < len(text):
        m_open = open_re.search(text, pos)
        m_close = close_re.search(text, pos)
        if not m_close:
            return -1
        if m_open and m_open.start() < m_close.start():
            depth += 1
            pos = m_open.end()
            continue
        depth -= 1
        if depth == 0:
            return m_close.start()
        pos = m_close.end()
    return -1
