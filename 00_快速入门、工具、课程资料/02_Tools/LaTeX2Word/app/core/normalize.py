"""LaTeX 归一化。

只做「让转换器更容易吃下去」的清理，不改变语义：
去定界符、抽 \\tag、删 \\label、统一 \\dfrac/\\tfrac、把 align 系列环境降成 aligned。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TAG_RE = re.compile(r"\\tag\*?\s*\{([^{}]*)\}")
_LABEL_RE = re.compile(r"\\label\s*\{[^{}]*\}")
_NONUMBER_RE = re.compile(r"\\(?:nonumber|notag)\b")

_ENV_ALIAS = {
    "align": "aligned",
    "align*": "aligned",
    "aligned": "aligned",
    "eqnarray": "aligned",
    "eqnarray*": "aligned",
    "split": "split",
    "gather": "gathered",
    "gather*": "gathered",
    "gathered": "gathered",
    "multline": "gathered",
    "multline*": "gathered",
    "array": "array",
    "matrix": "matrix",
    "pmatrix": "pmatrix",
    "bmatrix": "bmatrix",
    "Bmatrix": "Bmatrix",
    "vmatrix": "vmatrix",
    "Vmatrix": "Vmatrix",
    "cases": "cases",
    "alignedat": "aligned",
}

_FRAC_ALIAS = {"dfrac": "frac", "tfrac": "frac", "cfrac": "frac"}

# latex2mathml 不认 align 系列环境，统一降级成 array（列对齐由 & 数量推出）
_ALIGN_ENVS = (
    "aligned", "align", "align*", "alignedat", "eqnarray", "eqnarray*",
    "split", "flalign", "flalign*", "gather", "gather*", "gathered",
    "multline", "multline*",
)
_ALIGN_RE = re.compile(
    r"\\begin\{(" + "|".join(re.escape(e) for e in _ALIGN_ENVS) + r")\}(.*?)\\end\{\1\}",
    re.S,
)
_CENTERED_ENVS = {"gather", "gather*", "gathered", "multline", "multline*"}


def _rewrite_align(m: re.Match[str]) -> str:
    env, body = m.group(1), m.group(2)
    rows = re.split(r"\\\\", body)
    ncols = max(1, max(r.count("&") + 1 for r in rows))
    if env in _CENTERED_ENVS:
        spec = "c" * ncols
    else:
        spec = "".join("rl"[i % 2] for i in range(ncols))
    return "\\begin{array}{" + spec + "}" + body + "\\end{array}"


@dataclass
class Normalized:
    latex: str = ""
    tag: str | None = None
    warnings: list[str] = field(default_factory=list)


def strip_delimiters(text: str) -> str:
    s = text.strip()
    for left, right in (("$$", "$$"), ("\\[", "\\]"), ("\\(", "\\)"), ("$", "$")):
        if s.startswith(left) and s.endswith(right) and len(s) >= len(left) + len(right):
            return s[len(left): len(s) - len(right)].strip()
    return s


def unescape_dollars(text: str) -> str:
    """正文里的 \\$ 还原成 $。"""
    return text.replace("\\$", "$")


def normalize(latex: str) -> Normalized:
    out = Normalized()
    s = strip_delimiters(latex)

    tag = _TAG_RE.search(s)
    if tag:
        out.tag = tag.group(1).strip()
        s = _TAG_RE.sub(" ", s)

    s = _LABEL_RE.sub(" ", s)
    s = _NONUMBER_RE.sub(" ", s)
    s = re.sub(r"\\displaystyle\b", " ", s)
    s = re.sub(r"\\(dfrac|tfrac|cfrac)\b", r"\\frac", s)
    # latex2mathml 对单字符 \mathrm{d} 会丢掉正体变体，换成 \text 更稳
    s = re.sub(r"\\mathrm\s*\{\s*([^{}\\ ])\s*\}", r"\\text{\1}", s)
    s = s.replace("~", " ")

    # align 系列 → array（latex2mathml 只认 array/matrix）
    s = _ALIGN_RE.sub(_rewrite_align, s)

    # 环境降级：align -> aligned（latex2mathml 不认 align）
    def _env(m: re.Match[str]) -> str:
        name = m.group(1).strip()
        target = _ENV_ALIAS.get(name)
        if target is None:
            out.warnings.append(f"未知环境 {name}，原样透传")
            return m.group(0)
        return "\\begin{" + target + "}"

    s = re.sub(r"\\begin\{([^{}]*)\}", _env, s)

    # 换行统一：\\\\ 保留（表格/多行），单独换行变空格
    s = re.sub(r"[ \t]*\r?\n[ \t]*", " ", s)
    s = re.sub(r"[ \t]{2,}", " ", s).strip()

    # 没有环境却残留的 & 对齐符会让转换器报错，直接去掉
    if "&" in s and "\\begin{" not in s:
        s = s.replace("&", " ")
        out.warnings.append("去掉了不在环境中的 & 对齐符")

    out.latex = s
    return out


def latex_preview(latex: str, limit: int = 60) -> str:
    s = " ".join(latex.split())
    return s if len(s) <= limit else s[: limit - 1] + "…"
