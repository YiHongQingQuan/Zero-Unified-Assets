"""LaTeX → OMML 转换覆盖率。这份语料就是「常见公式能不能吃下去」的验收线。"""

from __future__ import annotations

import pytest

from app.core.mathconv import M_NS as OMML_NS
from app.core.mathconv import get_engine
from app.core.normalize import normalize

ENGINE = get_engine()
requires_engine = pytest.mark.skipif(not ENGINE.available, reason="本机没有 MML2OMML.XSL")

CORPUS = [
    r"x^2 + y^2 = 1",
    r"E = mc^2",
    r"\frac{a}{b}",
    r"\frac{a+b}{c-d}",
    r"\sqrt{x}",
    r"\sqrt[3]{x+1}",
    r"\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}",
    r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}",
    r"\prod_{k=1}^{n} k = n!",
    r"\lim_{x \to 0} \frac{\sin x}{x} = 1",
    r"\alpha \le \beta \ge \gamma \neq \delta",
    r"\vec{a} \cdot \vec{b} = |\vec{a}||\vec{b}|\cos\theta",
    r"\mathbb{R}^n",
    r"\mathcal{L}(f)",
    r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
    r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}",
    r"\begin{cases} x, & x>0 \\ -x, & x \le 0 \end{cases}",
    r"\begin{aligned} a &= b + c \\ d &= e \end{aligned}",
    r"\begin{aligned} f(x) &= x^2 \\ &= 2x \end{aligned}",
    r"\begin{align} a &= b \\ c &= d \end{align}",
    r"\text{当 } x > 0 \text{ 时}",
    r"\mathrm{d}x",
    r"\left( \frac{a}{b} \right)^2",
    r"\overline{AB}",
    r"\hat{y} = \sum_i w_i x_i + b",
    r"\partial_t u = \nabla^2 u",
    r"e^{i\pi} + 1 = 0",
    r"\begin{matrix} 1 & 2 \\ 3 & 4 \end{matrix}",
    r"a \times b \div c \pm d",
    r"\log_2 n",
    r"\sin^2 x + \cos^2 x = 1",
    r"\overline{x} = \frac{1}{n}\sum_{i=1}^n x_i",
    r"\begin{array}{cc} 1 & 2 \\ 3 & 4 \end{array}",
    r"\underbrace{1+1}_{2}",
    r"\binom{n}{k}",
    r"\iint_S \vec{F}\cdot d\vec{S}",
    r"a_{ij}^{(k)}",
    r"x = 1 \tag{7}",
    r"P(A \mid B) = \frac{P(B \mid A)P(A)}{P(B)}",
    r"\left\{ \begin{matrix} 1 \\ 0 \end{matrix} \right.",
    # 裸参数写法（不带花括号）
    r"\frac1 2",
    r"\frac12",
    r"\frac 1 2",
    r"\frac1x",
    r"\sqrt 2",
    r"\sqrt2",
    r"\sqrt[3] 8",
    r"\binom n k",
]


@requires_engine
@pytest.mark.parametrize("latex", CORPUS)
def test_corpus_converts(latex: str):
    norm = normalize(latex)
    xml = ENGINE.latex_to_omml_xml(norm.latex, display=False)
    assert "oMath" in xml
    assert "<m:t>" in xml or "<m:t " in xml


@requires_engine
def test_display_wraps_once():
    xml = ENGINE.latex_to_omml_xml("a=b", display=True)
    # 一个 m:oMathPara 开标签 + 一个闭标签，不能出现嵌套
    assert xml.count("oMathPara") == 2
    assert xml.count("<m:oMathPara") == 1


@requires_engine
def test_cache_reuses_result():
    a = ENGINE.latex_to_omml_xml("z = 1")
    b = ENGINE.latex_to_omml_xml("z = 1")
    assert a is b


def test_normalize_unchanged_when_plain():
    assert normalize("a+b").latex == "a+b"


def test_normalize_drops_label_and_nonumber():
    norm = normalize(r"x=1 \label{eq:1} \nonumber")
    assert "label" not in norm.latex
    assert "nonumber" not in norm.latex


def test_normalize_frac_aliases():
    assert normalize(r"\dfrac{1}{2}").latex == r"\frac{1}{2}"


def test_normalize_align_to_array():
    out = normalize(r"\begin{align} a &= b \\ c &= d \end{align}").latex
    assert out == r"\begin{array}{rl} a &= b \\ c &= d \end{array}"


def test_normalize_single_char_mathrm_becomes_text():
    assert normalize(r"\mathrm{d}x").latex == r"\text{d}x"
    # 多字符的 \mathrm 保持原样（latex2mathml 自己能处理）
    assert normalize(r"\mathrm{abc}").latex == r"\mathrm{abc}"


@requires_engine
def test_function_names_are_upright():
    xml = ENGINE.latex_to_omml_xml(r"\max_{\alpha}", display=False)
    assert 'm:sty m:val="p"' in xml
    xml_sin = ENGINE.latex_to_omml_xml(r"\sin x", display=False)
    assert 'm:sty m:val="p"' in xml_sin
    # 普通变量不应被标成正体
    xml_var = ENGINE.latex_to_omml_xml(r"a=b", display=False)
    assert "m:sty" not in xml_var


# ------------------------------------------------ 极限的下沿标（limLow）


@requires_engine
def test_display_lim_puts_limit_below():
    xml = ENGINE.latex_to_omml_xml(r"\lim_{n\to\infty} S_n = \frac{1}{2}", display=True)
    assert "<m:limLow>" in xml
    assert "<m:lim>" in xml


@requires_engine
def test_inline_lim_default_is_below():
    """默认策略是 below：行内也把下沿标排到下方。"""
    xml = ENGINE.latex_to_omml_xml(r"\lim_{n\to\infty} S_n", display=False)
    assert "<m:limLow>" in xml


@requires_engine
def test_auto_mode_keeps_inline_limits_on_the_side():
    xml = ENGINE.latex_to_omml_xml(r"\lim_{n\to\infty} S_n", display=False, limits="auto")
    assert "<m:limLow>" not in xml
    assert "<m:sSub>" in xml


@requires_engine
def test_side_mode_puts_display_limits_on_the_side():
    xml = ENGINE.latex_to_omml_xml(r"\lim_{n\to\infty} S_n", display=True, limits="side")
    assert "<m:limLow>" not in xml
    assert "<m:sSub>" in xml


@requires_engine
def test_display_max_puts_limit_below():
    assert "<m:limLow>" in ENGINE.latex_to_omml_xml(r"\max_{x\in A} f(x) = 1", display=True)


@requires_engine
def test_auto_mode_max_inline_keeps_side():
    xml = ENGINE.latex_to_omml_xml(r"\max_{x\in A} f(x)", display=False, limits="auto")
    assert "<m:limLow>" not in xml


@requires_engine
def test_sum_follows_mode():
    below = ENGINE.latex_to_omml_xml(r"\sum_{i=1}^{n} i", display=False, limits="below")
    assert 'm:limLoc m:val="undOvr"' in below
    auto = ENGINE.latex_to_omml_xml(r"\sum_{i=1}^{n} i", display=False, limits="auto")
    assert 'm:limLoc m:val="subSup"' in auto
    side = ENGINE.latex_to_omml_xml(r"\sum_{i=1}^{n} i", display=True, limits="side")
    assert 'm:limLoc m:val="subSup"' in side


@requires_engine
def test_integral_never_moves_below():
    """积分上下限按惯例始终在右侧，不受策略影响。"""
    for mode in ("below", "auto", "side"):
        for display in (False, True):
            xml = ENGINE.latex_to_omml_xml(r"\int_0^1 f(x)\,dx", display=display, limits=mode)
            assert 'm:limLoc m:val="subSup"' in xml
            assert "<m:limLow>" not in xml


@requires_engine
def test_plain_subscript_untouched():
    """S_n 这种普通下标不能变成下沿标。"""
    xml = ENGINE.latex_to_omml_xml(r"S_n + a_i", display=True)
    assert "<m:limLow>" not in xml
    assert "<m:sSub>" in xml


@requires_engine
def test_unknown_limits_mode_falls_back_to_below():
    xml = ENGINE.latex_to_omml_xml(r"\lim_{n} a_n", display=False, limits="whatever")
    assert "<m:limLow>" in xml


# ------------------------------------------------ 下沿标必须是合法结构


def _lim_low_arg(xml: str):
    from lxml import etree

    tag = "{%s}" % OMML_NS
    root = etree.fromstring(xml.encode())
    low = next(root.iter(tag + "limLow"))
    return low.find(tag + "lim")


@requires_engine
@pytest.mark.parametrize(
    "latex",
    [r"\lim_{k\to\infty} a_k", r"\max_{x\in A} f(x)", r"\min_{i} a_i", r"\sup_{n} x_n"],
)
def test_lim_low_argument_is_schema_valid(latex: str):
    """m:lim 里必须是数学内容本身。

    早先的实现在 m:lim 里塞了一个 <m:sub>，Word 2024 能容忍并在保存时自动修正，
    但部分版本的 Word/WPS 会把它当成空参数，渲染成一个虚线空框（用户实测）。
    """
    tag = "{%s}" % OMML_NS
    xml = ENGINE.latex_to_omml_xml(latex, display=True)
    lim = _lim_low_arg(xml)
    assert lim is not None
    assert lim.find(tag + "sub") is None
    text = "".join(t.text or "" for t in lim.iter(tag + "t")).strip()
    assert text, "下沿标内容不能为空"


@requires_engine
def test_lim_low_argument_keeps_whole_subscript():
    tag = "{%s}" % OMML_NS
    xml = ENGINE.latex_to_omml_xml(r"\lim_{k\to\infty} a_k", display=True)
    lim = _lim_low_arg(xml)
    text = "".join(t.text or "" for t in lim.iter(tag + "t"))
    assert text.replace(" ", "") == "k→∞"


# ------------------------------------------------ 绝对值竖线


def _omml_text(xml: str) -> str:
    from lxml import etree

    tag = "{%s}" % OMML_NS
    root = etree.fromstring(xml.encode())
    return "".join(t.text or "" for t in root.iter(tag + "t"))


@requires_engine
def test_plain_bars_are_not_paired_as_delimiters():
    """裸 | 不能被 XSL 配成一对括号，否则整条公式会被一根大竖线包住。"""
    xml = ENGINE.latex_to_omml_xml(r"|x_{n+1}-2| \le \frac{1}{2}|x_n-2|", display=True)
    assert 'begChr m:val="|"' not in xml
    assert "<m:d>" not in xml


@requires_engine
def test_plain_bars_keep_all_four_marks():
    xml = ENGINE.latex_to_omml_xml(r"|a|+|b|", display=True)
    assert _omml_text(xml).count("|") == 4


@requires_engine
def test_left_right_bars_stay_stretchy():
    """\\left| … \\right| 是真正的括号结构，要保留 m:d。"""
    xml = ENGINE.latex_to_omml_xml(r"\left|x-2\right|", display=True)
    assert 'begChr m:val="|"' in xml
    assert "<m:d>" in xml


@requires_engine
def test_norm_bars_are_not_paired():
    xml = ENGINE.latex_to_omml_xml(r"\|x\|", display=True)
    assert "<m:d>" not in xml
    assert _omml_text(xml).count("‖") == 2


@requires_engine
def test_lvert_rvert_not_paired():
    xml = ENGINE.latex_to_omml_xml(r"\lvert x \rvert \le 1", display=True)
    assert "<m:d>" not in xml


# ------------------------------------------------ 大型运算符尺寸


TALL_SUM = r"\sum_{k=1}^{n} \frac{1}{k}"
SHORT_SUM = r"\sum_{i=1}^{n} i"


@requires_engine
def test_nary_auto_makes_tall_sum_fixed_size():
    """操作数里有分式时，∑ 不再随内容放大。"""
    xml = ENGINE.latex_to_omml_xml(TALL_SUM, display=True, nary="auto")
    assert "<m:nary>" not in xml
    assert "<m:limLow>" in xml
    assert "<m:limUpp>" in xml


@requires_engine
def test_nary_auto_keeps_short_sum_native():
    """短求和不折腾，保留 Word 原生 n 元运算符。"""
    xml = ENGINE.latex_to_omml_xml(SHORT_SUM, display=True, nary="auto")
    assert "<m:nary>" in xml
    assert "<m:limLow>" not in xml


@requires_engine
def test_nary_fixed_always_stacks():
    xml = ENGINE.latex_to_omml_xml(SHORT_SUM, display=True, nary="fixed")
    assert "<m:nary>" not in xml
    assert "<m:limLow>" in xml


@requires_engine
def test_nary_native_keeps_word_behavior():
    xml = ENGINE.latex_to_omml_xml(TALL_SUM, display=True, nary="native")
    assert "<m:nary>" in xml
    assert 'm:grow m:val="1"' in xml


@requires_engine
def test_integral_is_never_stacked():
    """积分的上下限本来就在右侧，不参与固定尺寸改造。"""
    xml = ENGINE.latex_to_omml_xml(r"\int_0^1 \frac{1}{x}\,dx", display=True, nary="fixed")
    assert "<m:nary>" in xml
    assert "<m:limLow>" not in xml


@requires_engine
def test_stacked_operator_keeps_both_limits():
    import re

    from lxml import etree

    tag = "{%s}" % OMML_NS
    xml = ENGINE.latex_to_omml_xml(TALL_SUM, display=True, nary="fixed")
    root = etree.fromstring(xml.encode())
    low = next(root.iter(tag + "limLow"))
    low_text = "".join(t.text or "" for t in low.find(tag + "lim").iter(tag + "t"))
    upp = next(root.iter(tag + "limUpp"))
    upp_text = "".join(t.text or "" for t in upp.find(tag + "lim").iter(tag + "t"))
    assert re.sub(r"\s", "", low_text) == "k=1"
    assert re.sub(r"\s", "", upp_text) == "n"
    # 运算符本体还在
    assert _omml_text(xml).count("∑") == 1


@requires_engine
def test_stacked_operator_keeps_operand():
    xml = ENGINE.latex_to_omml_xml(TALL_SUM, display=True, nary="fixed")
    from lxml import etree

    tag = "{%s}" % OMML_NS
    root = etree.fromstring(xml.encode())
    assert list(root.iter(tag + "f")), "操作数（分式）不能被丢掉"


M_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def _omml_parts(latex: str) -> list[tuple[str, str]]:
    from lxml import etree

    xml = ENGINE.latex_to_omml_xml(latex, display=False)
    root = etree.fromstring(xml.encode())
    out = []
    for f in root.iter(M_NS + "f"):
        num = "".join(t.text or "" for t in f.find(M_NS + "num").iter(M_NS + "t"))
        den = "".join(t.text or "" for t in f.find(M_NS + "den").iter(M_NS + "t"))
        out.append((num, den))
    return out


@requires_engine
@pytest.mark.parametrize(
    "latex,expected",
    [
        (r"\frac1 2", ("1", "2")),
        (r"\frac12", ("1", "2")),
        (r"\frac 1 2", ("1", "2")),
        (r"\frac1x", ("1", "x")),
        (r"\binom n k", ("n", "k")),
    ],
)
def test_bare_arguments_bind_correctly(latex: str, expected: tuple[str, str]):
    """裸参数必须按 TeX 语义各取一个 token，不能把 12 当成一个参数。"""
    assert _omml_parts(latex) == [expected]


@requires_engine
def test_bare_arguments_sqrt():
    from lxml import etree

    for latex, deg, body in [(r"\sqrt 2", "", "2"), (r"\sqrt[3] 8", "3", "8")]:
        root = etree.fromstring(ENGINE.latex_to_omml_xml(latex, display=False).encode())
        rad = next(root.iter(M_NS + "rad"))
        got_deg = "".join(t.text or "" for t in rad.find(M_NS + "deg").iter(M_NS + "t"))
        got_body = "".join(t.text or "" for t in rad.find(M_NS + "e").iter(M_NS + "t"))
        assert (got_deg, got_body) == (deg, body)
