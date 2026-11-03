"""显式定界符 + 隐式识别的行为测试。

这些用例就是「哪些该认、哪些绝不能认」的合同，改规则前先跑它们。
"""

from __future__ import annotations

from app.core.detector import AnalyzeOptions, build_document


def math_nodes(text: str, **kwargs):
    doc, _ = build_document(text, AnalyzeOptions(**kwargs))
    out = []
    for block in doc.blocks:
        for node in block.inlines:
            if node.kind == "math":
                out.append(node)
    return out


def texts(text: str, **kwargs):
    doc, _ = build_document(text, AnalyzeOptions(**kwargs))
    out = []
    for block in doc.blocks:
        for node in block.inlines:
            if node.kind == "text":
                out.append(node.text)
    return "".join(out)


# ------------------------------------------------------------ 显式定界符


def test_inline_dollar():
    nodes = math_nodes(r"由 $a^2+b^2=c^2$ 得")
    assert len(nodes) == 1
    assert nodes[0].origin == "explicit"
    assert nodes[0].display is False
    assert nodes[0].latex == "a^2+b^2=c^2"


def test_display_dollar():
    nodes = math_nodes("$$\nE = mc^2\n$$")
    assert len(nodes) == 1
    assert nodes[0].display is True
    assert nodes[0].latex == "E = mc^2"


def test_bracket_and_paren_delimiters():
    nodes = math_nodes(r"\[ x = 1 \] 与 \( y = 2 \)")
    assert [n.display for n in nodes] == [True, False]
    assert [n.latex for n in nodes] == ["x = 1", "y = 2"]


def test_equation_environment():
    nodes = math_nodes(r"\begin{equation} E = mc^2 \end{equation}")
    assert len(nodes) == 1
    assert nodes[0].display is True
    assert nodes[0].latex.startswith(r"\begin{equation}")


def test_aligned_environment_is_rewritten():
    nodes = math_nodes(r"$$\begin{align} a &= b \\ c &= d \end{align}$$")
    assert len(nodes) == 1
    assert r"\begin{array}" in nodes[0].latex
    assert r"\begin{align}" not in nodes[0].latex


def test_tag_is_extracted():
    nodes = math_nodes(r"$$x = 1 \tag{3}$$")
    assert nodes[0].tag == "3"
    assert "tag" not in nodes[0].latex


# ------------------------------------------------------------ $ 的歧义


def test_currency_is_not_formula():
    nodes = math_nodes("售价 $5 到 $10 之间")
    assert nodes == []
    assert "$5" in texts("售价 $5 到 $10 之间")


def test_escaped_dollar_becomes_text():
    nodes = math_nodes(r"价格 \$99 与 $x$ 不同")
    assert len(nodes) == 1
    assert nodes[0].latex == "x"
    assert "$99" in texts(r"价格 \$99 与 $x$ 不同")


def test_space_after_dollar_is_not_formula():
    assert math_nodes("列出 $ 与 $ 两个符号") == []


# ------------------------------------------------------------ 隐式识别


def test_implicit_superscript():
    nodes = math_nodes("质能方程 E=mc² 说明")
    assert len(nodes) == 1
    assert nodes[0].origin == "implicit"
    assert nodes[0].latex == "E=mc^{2}"
    assert nodes[0].accepted is True


def test_implicit_function_call():
    nodes = math_nodes("设函数 f(x)=x^2+2x+1")
    assert len(nodes) == 1
    assert nodes[0].accepted is True
    assert nodes[0].latex == "f(x)=x^2+2x+1"


def test_implicit_bare_comparison_needs_confirm():
    nodes = math_nodes("当 x>0 时")
    assert len(nodes) == 1
    assert nodes[0].accepted is False
    assert nodes[0].confidence < 0.7


def test_implicit_stops_at_prose_words():
    nodes = math_nodes("the value is x = 2 in this case")
    assert len(nodes) == 1
    assert nodes[0].latex == "x = 2"


def test_implicit_latex_command():
    nodes = math_nodes(r"面积等于 \frac{1}{2} a h")
    assert len(nodes) >= 1
    assert any(r"\frac" in n.latex for n in nodes)


# ------------------------------------------------ 裸参数（\frac1 2 这种写法）


def test_explicit_bare_frac_argument():
    nodes = math_nodes(r"取 $\frac1 2$ 即可")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\frac1 2"
    assert nodes[0].origin == "explicit"


def test_implicit_bare_frac_keeps_denominator():
    """\\frac1 2 里的空格是参数分隔符，不能被当成句子边界。"""
    nodes = math_nodes(r"行内 \frac1 2 不带定界符")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\frac1 2"
    assert nodes[0].accepted is True


def test_implicit_bare_frac_with_space_after_command():
    nodes = math_nodes(r"行内 \frac 1 2 都不带")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\frac 1 2"


def test_implicit_bare_sqrt():
    nodes = math_nodes(r"标准差为 \sqrt 2 倍")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\sqrt 2"
    assert nodes[0].accepted is True


def test_implicit_bare_sqrt_no_space():
    nodes = math_nodes(r"标准差为 \sqrt2 倍")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\sqrt2"


def test_bare_frac_stops_at_chinese():
    nodes = math_nodes(r"比例 \frac1 2 的结果如下")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\frac1 2"


def test_windows_path_is_not_formula():
    assert math_nodes(r"路径 C:\Users\name\file.txt 不是公式") == []


def test_implicit_greek_and_relation():
    nodes = math_nodes("设 α ≤ β 时成立")
    assert len(nodes) == 1
    assert nodes[0].latex == r"\alpha \le \beta"


def test_version_number_is_not_formula():
    assert math_nodes("当前版本 v1.2.3 已发布") == []


def test_date_is_not_formula():
    assert math_nodes("截至 2024-03-01 完成") == []


def test_url_is_not_formula():
    assert math_nodes("详见 https://example.com/a?x=1") == []


def test_range_is_not_formula():
    assert math_nodes("第 3-5 章") == []


def test_cjk_never_inside_implicit_formula():
    nodes = math_nodes("质量 m=5 kg 的物体")
    for node in nodes:
        assert not any("\u4e00" <= ch <= "\u9fff" for ch in node.latex)


def test_sensitivity_aggressive_catches_more():
    text = "令 α 为该系数"
    assert math_nodes(text, sensitivity="standard") == []
    nodes = math_nodes(text, sensitivity="aggressive")
    assert len(nodes) == 1


# ------------------------------------------------------------ 分块与结构


def test_paragraph_split_by_line():
    doc, _ = build_document("第一行\n第二行", AnalyzeOptions(line_mode=True))
    assert len(doc.blocks) == 2


def test_paragraph_merge_without_line_mode():
    doc, _ = build_document("第一行\n第二行", AnalyzeOptions(line_mode=False))
    assert len(doc.blocks) == 1


def test_display_math_kept_whole():
    doc, _ = build_document("前文\n$$\na=b\n$$\n后文", AnalyzeOptions())
    kinds = [b.kind for b in doc.blocks]
    assert "display_math" in kinds
    assert len(doc.blocks) == 3


def test_markdown_heading_and_list():
    doc, _ = build_document("# 标题\n- 项目", AnalyzeOptions(markdown=True))
    assert doc.blocks[0].kind == "heading"
    assert doc.blocks[0].level == 1
    assert doc.blocks[1].kind == "list_item"
    assert doc.blocks[1].ordered is False


def test_markdown_table():
    doc, _ = build_document("| a | b |\n| --- | --- |\n| 1 | 2 |", AnalyzeOptions(markdown=True))
    table = [b for b in doc.blocks if b.kind == "table"][0]
    assert table.rows[0] == ["a", "b"]
    assert table.rows[1] == ["1", "2"]


def test_code_fence_skips_detection():
    text = "```\n$x$ 不应被识别\n```"
    doc, _ = build_document(text, AnalyzeOptions(markdown=True))
    assert doc.blocks[0].kind == "code"
    assert math_nodes(text, markdown=True) == []


def test_unescaped_percent_and_dollar_in_text_survive():
    nodes = math_nodes(r"增长 5% 时 $a$ 变化")
    assert len(nodes) == 1
    assert "5%" in texts(r"增长 5% 时 $a$ 变化")


# ------------------------------------------------------------ 独立公式判定


def test_lone_implicit_formula_becomes_display():
    """整段只有一个识别出来的公式时，按独立公式排版（极限才能排到下面）。"""
    doc, _ = build_document(r"lim_{n\to\infty} S_n=\frac{1}{2}", AnalyzeOptions())
    assert doc.blocks[0].kind == "display_math"
    node = doc.blocks[0].inlines[0]
    assert node.display is True
    assert node.latex.startswith(r"\lim")


def test_lone_explicit_inline_formula_stays_inline():
    """用户明确写了 $...$，就按行内处理，不擅自居中。"""
    doc, _ = build_document(r"$\lim_{n\to\infty} S_n$", AnalyzeOptions())
    assert doc.blocks[0].kind == "paragraph"
    assert doc.blocks[0].inlines[0].display is False


def test_formula_inside_sentence_stays_inline():
    doc, _ = build_document(r"设 $\lim_{n\to\infty} S_n$ 收敛", AnalyzeOptions())
    assert doc.blocks[0].kind == "paragraph"
    assert doc.blocks[0].inlines[1].display is False


def test_bare_function_name_gets_backslash():
    nodes = math_nodes(r"lim_{n\to\infty} S_n")
    assert len(nodes) == 1
    assert nodes[0].latex.startswith(r"\lim")


def test_function_words_are_prefixed():
    from app.core.unicode_math import to_latex

    assert to_latex("lim_{n→∞}") == r"\lim_{n\to\infty}"
    assert to_latex("sin x") == r"\sin x"
    assert to_latex(r"\sin x") == r"\sin x"  # 已经有反斜杠，不重复加
    assert to_latex("limit") == "limit"  # 不是函数名，不动
    assert to_latex("max_{x∈A}") == r"\max_{x\in A}"
