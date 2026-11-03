"""隐式公式识别：没有 $ 包裹，靠信号打分 + 边界收敛。

三步：
  1. 分词，找「种子」（LaTeX 命令、^/_、关系符、Unicode 数学符号）
  2. 从种子向两侧生长，遇到汉字、句读、两个相邻的英文词就停（这一条最关键，
     否则 "the value is x = 2" 会把整句吃进公式）
  3. 打分分级：高置信直接接受，中置信默认待确认，低置信丢弃
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.unicode_math import SUBSCRIPTS, SUPERSCRIPTS, has_math_char

# ------------------------------------------------------------------ 分词

TOKEN_RE = re.compile(
    r"(?P<cmd>\\[A-Za-z]+)"
    r"|(?P<word>[A-Za-z]+)"
    r"|(?P<num>\d+(?:\.\d+)?)"
    r"|(?P<space>[ \t]+)"
    r"|(?P<newline>\n)"
    r"|(?P<cjk>[\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])"
    r"|(?P<sym>[\u0370-\u03ff\u2070-\u209f\u1d00-\u1dbf\u2100-\u214f\u2190-\u21ff\u2200-\u27ff\u00b1-\u00f7\u2c7c])"
    r"|(?P<op>[\^_]|<=|>=|!=|[-+*/=<>(){}\[\],;:!|'~])"
    r"|(?P<other>.)"
)

_MATH_OPS = set("+-*/=<>^_()[]{},;:!|'~")
_EDGE_DROP = set("+-*/=<>^_,;:|'~")
_RELATION_CHARS = set("=<>")

SENSITIVITY = {
    # 名称: (自动接受阈值, 待确认阈值)
    "conservative": (7.0, 4.5),
    "standard": (6.0, 3.0),
    "aggressive": (5.0, 2.0),
}


@dataclass
class Tok:
    type: str
    text: str
    start: int
    end: int


@dataclass
class Candidate:
    start: int
    end: int
    text: str
    score: float
    tier: str  # auto | confirm
    reasons: list[str] = field(default_factory=list)


def tokenize(text: str) -> list[Tok]:
    return [Tok(m.lastgroup or "other", m.group(0), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]


def _is_alnum(tok: Tok) -> bool:
    return tok.type in ("word", "num")


def _token_ok(tok: Tok) -> bool:
    if tok.type in ("cmd", "word", "num", "sym"):
        return True
    if tok.type == "op":
        return tok.text in _MATH_OPS
    return False


def _space_ok(left: Tok | None, right: Tok | None) -> bool:
    """空格只有当它不在「两个英文词之间」时才允许留在公式里。"""
    if left is None or right is None:
        return False
    return not (_is_alnum(left) and _is_alnum(right))


# 这些命令吃「裸参数」：\frac1 2、\binom n k 在 TeX 里是合法的
_BARE_ARG_CMDS = {"frac", "dfrac", "tfrac", "cfrac", "binom", "dbinom", "tbinom",
                  "overset", "underset", "stackrel", "sqrt"}


def _space_ok_at(tokens: list[Tok], j: int) -> bool:
    """tokens[j] 是空格，判断它能否留在候选公式里。

    除了常规规则，额外允许「命令的裸参数之间」的空格，
    否则 \\frac1 2 只会认到 \\frac1，分母那个 2 被丢掉。
    """
    if j <= 0 or j + 1 >= len(tokens):
        return False
    left, right = tokens[j - 1], tokens[j + 1]
    if not (_is_alnum(left) and _is_alnum(right)):
        return True
    k = j - 2
    while k >= 0 and tokens[k].type == "space":
        k -= 1
    return k >= 0 and tokens[k].type == "cmd" and tokens[k].text.lstrip("\\") in _BARE_ARG_CMDS


def _is_seed(tok: Tok) -> bool:
    if tok.type == "cmd":
        return True
    if tok.type == "sym":
        return True
    if tok.type == "op" and tok.text in ("^", "_", "=", "<", ">", "+"):
        return True
    return False


def _extend(tokens: list[Tok], idx: int) -> tuple[int, int]:
    l = idx
    r = idx

    while l > 0:
        j = l - 1
        tok = tokens[j]
        if tok.type == "space":
            if len(tok.text) > 1 or not _space_ok_at(tokens, j):
                break
        elif not _token_ok(tok):
            break
        l = j

    while r < len(tokens) - 1:
        j = r + 1
        tok = tokens[j]
        if tok.type == "space":
            if len(tok.text) > 1 or not _space_ok_at(tokens, j):
                break
        elif not _token_ok(tok):
            break
        r = j

    # 修剪两端的空格与散落运算符
    while l <= r and tokens[l].type == "space":
        l += 1
    while r >= l and tokens[r].type == "space":
        r -= 1
    while l <= r and tokens[l].type == "op" and tokens[l].text in _EDGE_DROP:
        l += 1
    while r >= l and tokens[r].type == "op" and tokens[r].text in _EDGE_DROP:
        r -= 1
    return l, r


_FUNC_RE = re.compile(
    r"\b(sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan|sinh|cosh|tanh"
    r"|log|lg|ln|exp|lim|max|min|sup|inf|det|dim|ker|gcd|mod|arg|deg)\b"
)
_SUP_RE = re.compile(r"[A-Za-z0-9)\]}]\s*[\^_]")
_REL_RE = re.compile(
    r"(?<![<>=!])=(?!=)|(?<![<>=])[<>](?![<>=])|<=|>=|!=|\\le|\\ge|\\leq|\\geq"
    r"|\\approx|\\neq|\\ne|\\equiv|\\sim|\\propto|\\to|\\rightarrow|\\ll|\\gg"
    r"|[≤≥≈≠≡∝→≪≫∈∉⊂⊃⊆⊇∣∥⊥]"
)
_MIX_RE = re.compile(r"\d\s*[+\-*/]\s*\d|\d[A-Za-z]|[A-Za-z]\d|[A-Za-z]\s*/\s*[A-Za-z\d]")
_CALL_RE = re.compile(r"[A-Za-z]\s*\([^()]*\)\s*$|[A-Za-z]\s*\([^()]*\)")
_URL_RE = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|cn|org|net|edu|io|gov)\b", re.I)
# 命令后面直接跟参数，说明是真在用 LaTeX（区别于正文里的反斜杠）
_CMD_ARG_RE = re.compile(r"\\[A-Za-z]+(\[[^\]]*\])?\s*[\d{(\[a-zA-Z\\]")
# Windows 路径 / UNC 路径里的反斜杠不是 LaTeX
_PATH_RE = re.compile(r"[A-Za-z]:\\|\\\\[A-Za-z0-9_.-]+\\")
# 整段屏蔽区：网址、邮箱里的等号不是公式
_MASK_RES = [
    re.compile(r"https?://[^\s<>\"'）】]+", re.I),
    re.compile(r"\bwww\.[^\s<>\"'）】]+", re.I),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
]
_DATE_RE = re.compile(r"\d{4}\s*[-/年]\s*\d{1,2}\s*[-/月]\s*\d{1,2}|\d{4}\s*年")
_VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)+|\bv\d+\.\d+", re.I)
_RANGE_RE = re.compile(r"^\s*\d+(?:\.\d+)?\s*[-–—~至]\s*\d+(?:\.\d+)?\s*$")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def score(text: str) -> tuple[float, list[str]]:
    s = 0.0
    reasons: list[str] = []

    if "\\" in text:
        s += 5
        reasons.append("含 LaTeX 命令")
    if _CMD_ARG_RE.search(text):
        s += 2
        reasons.append("命令带参数")
    if _SUP_RE.search(text):
        s += 3
        reasons.append("含上下标")
    if _REL_RE.search(text):
        s += 3
        reasons.append("含关系符")
    if has_math_char(text):
        s += 2
        reasons.append("含数学符号")
    if any(ch in SUPERSCRIPTS or ch in SUBSCRIPTS for ch in text):
        s += 3
        reasons.append("含 Unicode 上下标")
    if _FUNC_RE.search(text):
        s += 3
        reasons.append("含数学函数")
    if _MIX_RE.search(text):
        s += 2
        reasons.append("数字与运算符混排")
    if _CALL_RE.search(text):
        s += 2
        reasons.append("函数调用形态")

    # 负向
    if _URL_RE.search(text):
        s -= 8
        reasons.append("像网址")
    if _PATH_RE.search(text):
        s -= 10
        reasons.append("像文件路径")
    if _DATE_RE.search(text):
        s -= 8
        reasons.append("像日期")
    if _VERSION_RE.search(text):
        s -= 6
        reasons.append("像版本号")
    if _RANGE_RE.match(text):
        s -= 6
        reasons.append("像数值区间")
    if _CJK_RE.search(text):
        s -= 6
        reasons.append("混入汉字")
    if len(text) > 120:
        s -= 3
        reasons.append("过长")
    if text.count("(") != text.count(")") or text.count("[") != text.count("]"):
        s -= 2
        reasons.append("括号不配对")
    if text.endswith(".") and len(text.split()) > 2:
        s -= 2
        reasons.append("像句子结尾")

    return s, reasons


def _syntax_ok(text: str) -> bool:
    if not text.strip():
        return False
    depth = 0
    for ch in text:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False
    if depth != 0:
        return False
    if text.count("(") != text.count(")"):
        return False
    if re.search(r"[\^_]\s*$", text):
        return False
    if not re.search(r"[A-Za-z0-9\u0370-\u03ff\u2070-\u209f]", text):
        return False
    return True


def _masked_ranges(segment: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in _MASK_RES:
        for m in pattern.finditer(segment):
            spans.append((m.start(), m.end()))
    return spans


def find_candidates(segment: str, sensitivity: str = "standard") -> list[Candidate]:
    """在一个「没有任何显式公式」的文本片段里找隐式公式候选。"""
    if not segment.strip():
        return []

    masked = _masked_ranges(segment)

    auto_thr, confirm_thr = SENSITIVITY.get(sensitivity, SENSITIVITY["standard"])
    tokens = tokenize(segment)
    if not tokens:
        return []

    ranges: list[tuple[int, int]] = []
    for idx, tok in enumerate(tokens):
        if not _is_seed(tok):
            continue
        if any(l <= idx <= r for l, r in ranges):
            continue
        l, r = _extend(tokens, idx)
        if l > r:
            continue
        # 和已有区间重叠/相接则合并
        merged = False
        for k, (pl, pr) in enumerate(ranges):
            if l <= pr + 1 and r >= pl - 1:
                ranges[k] = (min(l, pl), max(r, pr))
                merged = True
                break
        if not merged:
            ranges.append((l, r))

    results: list[Candidate] = []
    for l, r in sorted(ranges):
        start = tokens[l].start
        end = tokens[r].end
        raw = segment[start:end]
        if not _syntax_ok(raw):
            continue
        sc, reasons = score(raw)
        if sc >= auto_thr:
            tier = "auto"
        elif sc >= confirm_thr:
            tier = "confirm"
        else:
            continue
        results.append(Candidate(start, end, raw, sc, tier, reasons))

    results = [c for c in results if not _overlaps_masked(c, masked)]
    return _drop_overlaps(results)


def _overlaps_masked(cand: Candidate, masked: list[tuple[int, int]]) -> bool:
    return any(cand.start < b and cand.end > a for a, b in masked)


def _drop_overlaps(items: list[Candidate]) -> list[Candidate]:
    """区间若相互重叠，保留得分高的那个。"""
    out: list[Candidate] = []
    for cand in sorted(items, key=lambda c: (-c.score, c.start)):
        if any(not (cand.end <= o.start or cand.start >= o.end) for o in out):
            continue
        out.append(cand)
    return sorted(out, key=lambda c: c.start)
