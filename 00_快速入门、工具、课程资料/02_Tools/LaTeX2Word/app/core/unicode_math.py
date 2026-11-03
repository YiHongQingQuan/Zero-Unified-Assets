"""Unicode 数学符号与 LaTeX 之间的映射。

用户从网页、PDF、聊天窗口里粘过来的公式，常常是 Unicode 形态：
    "x² + y² = z²"、"√(a+b)"、"∑"、"α ≤ β"
识别出候选区间后，先把这些字符换成 LaTeX，再交给 latex2mathml。
"""

from __future__ import annotations

import re

# 希腊字母
GREEK: dict[str, str] = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "varepsilon",
    "ϵ": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta", "ϑ": "vartheta",
    "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi",
    "π": "pi", "ϖ": "varpi", "ρ": "rho", "ϱ": "varrho", "σ": "sigma",
    "ς": "varsigma", "τ": "tau", "υ": "upsilon", "φ": "varphi", "ϕ": "phi",
    "χ": "chi", "ψ": "psi", "ω": "omega",
    "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta", "Λ": "Lambda", "Ξ": "Xi",
    "Π": "Pi", "Σ": "Sigma", "Υ": "Upsilon", "Φ": "Phi", "Ψ": "Psi",
    "Ω": "Omega",
}

# 运算符 / 关系 / 其它符号
SYMBOLS: dict[str, str] = {
    "×": "times", "÷": "div", "±": "pm", "∓": "mp", "·": "cdot", "⋅": "cdot",
    "∙": "bullet", "∘": "circ", "∗": "ast", "÷": "div",
    "≤": "le", "≥": "ge", "≦": "leq", "≧": "geq", "≠": "neq", "≈": "approx",
    "≡": "equiv", "∼": "sim", "≅": "cong", "∝": "propto", "≪": "ll", "≫": "gg",
    "≺": "prec", "≻": "succ", "⊥": "perp", "∥": "parallel", "∣": "mid",
    "∈": "in", "∉": "notin", "∋": "ni", "⊂": "subset", "⊃": "supset",
    "⊆": "subseteq", "⊇": "supseteq", "∪": "cup", "∩": "cap", "∖": "setminus",
    "∅": "emptyset", "∀": "forall", "∃": "exists", "∄": "nexists", "¬": "neg",
    "∧": "wedge", "∨": "vee", "⊕": "oplus", "⊗": "otimes", "⊙": "odot",
    "→": "to", "←": "leftarrow", "↔": "leftrightarrow", "⇒": "Rightarrow",
    "⇐": "Leftarrow", "⇔": "Leftrightarrow", "↦": "mapsto", "↑": "uparrow",
    "↓": "downarrow", "↗": "nearrow", "↘": "searrow",
    "∞": "infty", "∂": "partial", "∇": "nabla", "ℏ": "hbar", "ℓ": "ell",
    "°": "degree", "′": "prime", "″": "dprime", "‴": "prime",
    "∑": "sum", "∏": "prod", "∫": "int", "∬": "iint", "∭": "iiint",
    "∮": "oint", "⋃": "bigcup", "⋂": "bigcap", "⋁": "bigvee", "⋀": "bigwedge",
    "…": "ldots", "⋯": "cdots", "⋮": "vdots", "⋱": "ddots",
    "∎": "blacksquare", "□": "square", "△": "triangle", "∠": "angle",
    "⟨": "langle", "⟩": "rangle", "⌊": "lfloor", "⌋": "rfloor",
    "⌈": "lceil", "⌉": "rceil", "‖": "Vert", "ℜ": "Re", "ℑ": "Im",
    "ℵ": "aleph", "≮": "nless", "≯": "ngtr",
    # 中文论文里常见的黑板体
    "ℝ": "mathbb{R}", "ℂ": "mathbb{C}", "ℕ": "mathbb{N}",
    "ℚ": "mathbb{Q}", "ℤ": "mathbb{Z}", "ℙ": "mathbb{P}",
    "ℰ": "mathcal{E}", "ℱ": "mathcal{F}", "ℒ": "mathcal{L}",
}

SUPERSCRIPTS: dict[str, str] = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")",
    "ⁿ": "n", "ⁱ": "i", "ᵃ": "a", "ᵇ": "b", "ᵈ": "d", "ᵉ": "e",
    "ᵍ": "g", "ᵐ": "m", "ᵖ": "p", "ᵗ": "t", "ᵛ": "v", "ˣ": "x", "ʸ": "y",
    "ᵀ": "T", "ᴴ": "H", "ᴷ": "K", "ᴺ": "N", "ᵂ": "W", "ᶜ": "c", "ᵏ": "k",
    "ᶠ": "f", "ˡ": "l", "ʳ": "r", "ˢ": "s", "ᶻ": "z",
}

SUBSCRIPTS: dict[str, str] = {
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "₊": "+", "₋": "-", "₌": "=", "₍": "(", "₎": ")",
    "ₐ": "a", "ₑ": "e", "ₕ": "h", "ᵢ": "i", "ⱼ": "j", "ₖ": "k",
    "ₗ": "l", "ₘ": "m", "ₙ": "n", "ₒ": "o", "ₚ": "p", "ᵣ": "r",
    "ₛ": "s", "ₜ": "t", "ᵤ": "u", "ᵥ": "v", "ₓ": "x",
    "ᵢ": "i", "ⱼ": "j", "ᵣ": "r",
}

# 识别阶段用来判定的字符集合
MATH_CHARS = set(GREEK) | set(SYMBOLS) | set(SUPERSCRIPTS) | set(SUBSCRIPTS)

_ASCII_MATH = set("+-*/=<>^_()[]{}\\|,'.!:%$&")
_ASCII_DIGITS = set("0123456789")

# ∈{0,1} 这类写法里的花括号是要显示出来的
_SET_BRACE_RE = re.compile(r"([∈∉⊂⊃⊆⊇∪∩])\s*\{([^{}]*)\}")

# 隐式识别出来的公式里，用户通常直接写 lim / max / sin，需要补反斜杠
_FUNC_WORDS = (
    "limsup", "liminf", "lim", "max", "min", "sup", "inf", "det", "gcd",
    "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "sin", "cos",
    "tan", "cot", "sec", "csc", "log", "lg", "ln", "exp", "arg", "deg",
    "dim", "ker", "hom", "Pr",
)
_FUNC_WORD_RE = re.compile(
    r"(?<![\\A-Za-z])(" + "|".join(_FUNC_WORDS) + r")(?![A-Za-z])"
)


def is_math_char(ch: str) -> bool:
    return ch in MATH_CHARS


def has_math_char(text: str) -> bool:
    return any(ch in MATH_CHARS for ch in text)


def _needs_space_after(cmd: str) -> bool:
    """\\alpha 紧跟 ASCII 字母时必须补空格，否则会被吃成 \\alphax。"""
    return True


def to_latex(text: str) -> str:
    """把一段 Unicode 形态的公式文本转成 LaTeX。"""
    # 集合写法：∈{0,1} 里的花括号是「字面花括号」，不能被当成 LaTeX 分组
    text = _SET_BRACE_RE.sub(lambda m: m.group(1) + r"\{ " + m.group(2) + r" \}", text)
    # 裸函数名补上反斜杠：lim_{n→∞} -> \lim_{n→∞}
    # 否则 latex2mathml 会把 lim 拆成 l·i·m 三个变量，既变斜体也排不出下沿标
    text = _FUNC_WORD_RE.sub(r"\\\1", text)

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        # 上标游程：x²³ -> x^{23}
        if ch in SUPERSCRIPTS:
            group = []
            while i < n and text[i] in SUPERSCRIPTS:
                group.append(SUPERSCRIPTS[text[i]])
                i += 1
            out.append("^{" + "".join(group) + "}")
            continue

        # 下标游程：a₁₂ -> a_{12}
        if ch in SUBSCRIPTS:
            group = []
            while i < n and text[i] in SUBSCRIPTS:
                group.append(SUBSCRIPTS[text[i]])
                i += 1
            out.append("_{" + "".join(group) + "}")
            continue

        # 根号：√x / √(a+b) / √2
        if ch == "√":
            i += 1
            body, i = _read_atom(text, i)
            out.append("\\sqrt{" + to_latex(body) + "}")
            continue

        cmd = GREEK.get(ch) or SYMBOLS.get(ch)
        if cmd:
            out.append("\\" + cmd)
            nxt = text[i + 1] if i + 1 < n else ""
            # 命令后紧跟 ASCII 字母/数字时必须断开
            if nxt and (nxt.isascii() and (nxt.isalnum() or nxt in "\\")):
                out.append(" ")
            i += 1
            continue

        out.append(ch)
        i += 1
    return "".join(out)


def _read_atom(text: str, i: int) -> tuple[str, int]:
    """从 i 起读一个「原子」：括号组、花括号组、单个字符。"""
    n = len(text)
    if i >= n:
        return "", i
    if text[i] == "(":
        depth = 0
        j = i
        while j < n:
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    return text[i + 1:j], j + 1
            j += 1
        return text[i + 1:], n
    if text[i] == "{":
        depth = 0
        j = i
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    return text[i + 1:j], j + 1
            j += 1
        return text[i + 1:], n
    # 连续数字整体作为一个原子
    if text[i].isdigit():
        j = i
        while j < n and (text[j].isdigit() or text[j] == "."):
            j += 1
        return text[i:j], j
    return text[i], i + 1


def looks_prose(text: str) -> bool:
    """汉字占比过高时，基本可以确定不是公式。"""
    if not text:
        return True
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    stripped = [ch for ch in text if not ch.isspace()]
    if not stripped:
        return True
    return cjk / len(stripped) > 0.3
