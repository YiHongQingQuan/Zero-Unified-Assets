"""LaTeX → MathML → OMML。

LaTeX 转 MathML 使用纯 Python 的 latex2mathml；
MathML 转 OMML 使用 Office 自带的 MML2OMML.XSL（微软官方转换表），
这样产出的公式是 Word 原生可编辑公式，不需要装 TeX。
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from lxml import etree

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_M = "{%s}" % M_NS

_XSL_NAME = "MML2OMML.XSL"

# 这些函数名在 Word 里必须直立（正体），否则会被当成变量斜体
_FUNC_NAMES = {
    "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "coth", "log", "lg", "ln", "exp", "lim",
    "max", "min", "sup", "inf", "det", "dim", "ker", "hom", "gcd",
    "Pr", "arg", "deg", "mod",
}

# 这些函数在独立公式里把下标排到正下方（\\max_{x} / \\lim_{n\\to\\infty}）。
# 注意不含 \\sin \\log 这类——它们在 LaTeX 里本来就不带下沿标。
_LIMIT_FUNCS = {
    "lim", "limsup", "liminf", "max", "min", "sup", "inf",
    "det", "gcd", "Pr", "arg", "argmax", "argmin", "dim", "ker", "hom",
}

# 上下限位置策略：
#   below - 一律排正下方（默认；行内也排下方）
#   auto  - 跟随 LaTeX 惯例：独立公式排下方，行内公式排右侧
#   side  - 一律排右侧
LIMIT_MODES = ("below", "auto", "side")

# 大型运算符（∑ ∏ 等）尺寸策略：
#   auto   - 操作数里有分式/根式等「高」内容时改用固定尺寸，否则保留 Word 原生 n 元运算符
#   fixed  - 一律固定尺寸（不随内容放大）
#   native - 保留 Word 原生行为（运算符跟着内容长高）
NARY_MODES = ("auto", "fixed", "native")

# 会被 Word 当作「高内容」、从而把 ∑ 撑大的结构
_TALL_TAGS = {"f", "rad", "nary", "eqArr", "m", "groupChr", "limLow", "limUpp", "box"}

# 积分符号的上下限按惯例永远在右侧，不受上述策略影响
_NARY_INTEGRALS = {"∫", "∬", "∭", "∮", "∯", "∰"}

_CANDIDATE_DIRS = [
    r"C:\Program Files\Microsoft Office\root\Office16",
    r"C:\Program Files\Microsoft Office\root\Office15",
    r"C:\Program Files (x86)\Microsoft Office\root\Office16",
    r"C:\Program Files (x86)\Microsoft Office\root\Office15",
    r"C:\Program Files\Microsoft Office\Office16",
    r"C:\Program Files\Microsoft Office\Office15",
    r"C:\Program Files (x86)\Microsoft Office\Office16",
]


class EngineUnavailable(RuntimeError):
    """找不到 MML2OMML.XSL。"""


class ConversionError(RuntimeError):
    """单条公式转换失败。"""


def _registry_office_dirs() -> list[str]:
    dirs: list[str] = []
    try:
        import winreg  # type: ignore
    except Exception:
        return dirs
    keys = [
        (r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration", "InstallPath"),
        (r"SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration", "InstallPath"),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE", None),
    ]
    for sub, value in keys:
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root, sub) as key:
                    if value:
                        raw, _ = winreg.QueryValueEx(key, value)
                        dirs.append(str(raw))
                    else:
                        raw, _ = winreg.QueryValueEx(key, "")
                        dirs.append(str(Path(str(raw)).parent))
            except Exception:
                continue
    return dirs


def locate_xsl() -> Path | None:
    """按优先级找 MML2OMML.XSL。"""
    env = os.environ.get("LATEX2WORD_XSL")
    if env and Path(env).is_file():
        return Path(env)

    local = Path(__file__).resolve().parent.parent / "resources" / _XSL_NAME
    if local.is_file():
        return local

    for d in _CANDIDATE_DIRS:
        p = Path(d) / _XSL_NAME
        if p.is_file():
            return p

    for base in _registry_office_dirs():
        p = Path(base)
        if p.is_file() and p.name.lower() == _XSL_NAME.lower():
            return p
        cand = p / _XSL_NAME
        if cand.is_file():
            return cand
        try:
            for sub in p.glob("**/" + _XSL_NAME):
                return sub
        except Exception:
            continue
    return None


class OmmlEngine:
    """带缓存的转换器。线程内复用同一个实例即可。"""

    def __init__(self) -> None:
        self._path: Path | None = None
        self._transform = None
        self._cache: dict[tuple[str, bool], str] = {}
        self._error: str | None = None
        self._init()

    def _init(self) -> None:
        path = locate_xsl()
        if path is None:
            self._error = (
                "未找到 MML2OMML.XSL。请确认已安装 Microsoft Office，"
                f"或把该文件放到 {Path(__file__).resolve().parent.parent / 'resources'} 目录下，"
                "也可用环境变量 LATEX2WORD_XSL 指定路径。"
            )
            return
        try:
            doc = etree.parse(str(path))
            self._transform = etree.XSLT(doc)
            self._path = path
        except Exception as exc:  # pragma: no cover - 取决于本机环境
            self._error = f"加载 MML2OMML.XSL 失败：{exc}"

    # ------------------------------------------------------------ 状态
    @property
    def available(self) -> bool:
        return self._transform is not None

    @property
    def xsl_path(self) -> str | None:
        return str(self._path) if self._path else None

    @property
    def error(self) -> str | None:
        return self._error

    def status(self) -> dict:
        return {
            "available": self.available,
            "xsl_path": self.xsl_path,
            "error": self._error,
        }

    # ------------------------------------------------------------ 转换
    def latex_to_omml_xml(
        self,
        latex: str,
        display: bool = False,
        limits: str = "below",
        nary: str = "auto",
    ) -> str:
        limits = limits if limits in LIMIT_MODES else "below"
        nary = nary if nary in NARY_MODES else "auto"
        key = (latex, display, limits, nary)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        if not self.available:
            raise EngineUnavailable(self._error or "转换引擎不可用")
        if not latex.strip():
            raise ConversionError("空公式")

        try:
            from latex2mathml.converter import convert as latex_to_mathml
        except Exception as exc:  # pragma: no cover
            raise EngineUnavailable(f"latex2mathml 不可用：{exc}") from exc

        try:
            mml = latex_to_mathml(latex, display="block" if display else "inline")
        except Exception as exc:
            raise ConversionError(_short(str(exc))) from exc

        try:
            mml_root = etree.fromstring(mml.encode("utf-8"))
        except Exception as exc:
            raise ConversionError(f"MathML 解析失败：{_short(str(exc))}") from exc

        # 上下限位置在 MathML 层改（msub↔munder 等），再交给微软的 XSL。
        # 不要在 OMML 上手工拼 m:limLow——m:lim 里塞 m:sub 是非法结构，
        # Word 会把它当成空参数，显示成一个虚线空框。
        _normalize_bars(mml_root)
        _rewrite_limits(mml_root, display, limits)

        try:
            result = self._transform(mml_root)
        except Exception as exc:
            raise ConversionError(f"MathML→OMML 失败：{_short(str(exc))}") from exc

        root = result.getroot()
        if root is None:
            raise ConversionError("转换结果为空")

        _upright_functions(root)
        _apply_nary_mode(root, nary)

        # display 模式下 XSL 已经给出 m:oMathPara，别再包一层
        if display and etree.QName(root).localname == "oMath":
            root = _wrap_display(root)
        xml = etree.tostring(root, encoding="unicode")
        self._cache[key] = xml
        return xml

    def omml_element(
        self, latex: str, display: bool = False, limits: str = "below", nary: str = "auto"
    ):
        xml = self.latex_to_omml_xml(latex, display, limits, nary)
        return etree.fromstring(xml.encode("utf-8"))


def _upright_functions(root) -> None:
    """把 \\max \\sin 这类函数名标成正体。

    latex2mathml 有时给出 <mo>max</mo>，XSL 转出来是普通斜体 run，Word 里就歪了；
    这里按文本内容补一个 <m:sty m:val="p"/>。
    """
    for run in root.iter(_M + "r"):
        rpr = run.find(_M + "rPr")
        if rpr is not None and rpr.find(_M + "sty") is not None:
            continue
        text = "".join(t.text or "" for t in run.findall(_M + "t")).strip()
        if text not in _FUNC_NAMES:
            continue
        if rpr is None:
            rpr = etree.Element(_M + "rPr")
            run.insert(0, rpr)
        sty = etree.SubElement(rpr, _M + "sty")
        sty.set(_M + "val", "p")


MATHML_NS = "http://www.w3.org/1998/Math/MathML"
_MM = "{%s}" % MATHML_NS

# n 元运算符：它们的上下限位置受「上下限位置」设置影响（积分除外）
_NARY_CHARS = set("∑∏∐⋃⋂⋁⋀⨁⨂⨀⨄⨆")

# 绝对值/范数的竖线
_BAR_CHARS = {"|", "‖"}


def _normalize_bars(mml_root) -> None:
    """裸竖线不要交给 XSL 当分隔符配对。

    MML2OMML 会把 mrow 里第一个 `|` 和接下来那个 `|` 组成一个 m:d
    （dPr 里 begChr/endChr 都是 `|`），于是 |a|+|b| 的第二组竖线被吞进同一个
    括号组里，Word 里就出现「一根横跨整条公式的大竖线 + 里面两根小竖线」。
    把非 fence 的竖线降级成 <mi>，XSL 就只输出普通 run，高度与其他字符一致——
    这也正是 LaTeX 里裸 `|` 不自动伸缩的语义（要伸缩得写 \\left| … \\right|）。
    """
    for mo in list(mml_root.iter(_MM + "mo")):
        text = (mo.text or "").strip()
        if text not in _BAR_CHARS:
            continue
        if mo.get("fence") == "true" or mo.get("stretchy") == "true":
            continue
        mo.tag = _MM + "mi"


def _mo_text(node) -> str:
    if len(node) == 0:
        return ""
    base = node[0]
    if etree.QName(base).localname != "mo":
        return ""
    return (base.text or "").strip()


def _rewrite_limits(mml_root, display: bool, limits: str) -> None:
    """在 MathML 层把上下限改成「下方」或「右侧」的写法。

    LaTeX 里 \\lim_{x} 与 \\sum_{i}^{n} 的上下限位置由「是不是 display」决定，
    而用户可以在设置里强制指定。这里改 msub/msubsup ↔ munder/munderover，
    交给微软的 XSL 生成合法的 OMML（m:limLow / m:nary）。

    积分符号不参与：按排版惯例它们的上下限始终在右侧。
    """
    if limits == "auto" and not display:
        return

    if limits == "side":
        for node in list(mml_root.iter(_MM + "munder")):
            text = _mo_text(node)
            if text in _LIMIT_FUNCS or text in _NARY_CHARS:
                node.tag = _MM + "msub"
        for node in list(mml_root.iter(_MM + "munderover")):
            if _mo_text(node) in _NARY_CHARS:
                node.tag = _MM + "msubsup"
        for node in list(mml_root.iter(_MM + "mover")):
            if _mo_text(node) in _NARY_CHARS:
                node.tag = _MM + "msup"
        return

    # below（lim 类函数恒排下方；独立公式在 auto 模式下也走这里）
    for node in list(mml_root.iter(_MM + "msub")):
        text = _mo_text(node)
        if text in _LIMIT_FUNCS or text in _NARY_CHARS:
            node.tag = _MM + "munder"
    for node in list(mml_root.iter(_MM + "msubsup")):
        if _mo_text(node) in _NARY_CHARS:
            node.tag = _MM + "munderover"
    for node in list(mml_root.iter(_MM + "msup")):
        if _mo_text(node) in _NARY_CHARS:
            node.tag = _MM + "mover"


def _apply_nary_mode(root, mode: str) -> None:
    """处理 Word 把 ∑ 撑到与操作数同高的问题。

    微软 XSL 固定输出 <m:nary> + <m:grow m:val="1"/>，含义是「运算符伸长到
    内容高度」。操作数里有个高个儿分式时，∑ 会被拉到四五倍字号；而 LaTeX 的
    大型运算符是固定尺寸。这里按设置把它换成 limLow/limUpp 堆叠的固定尺寸写法。

    只处理上下限在上下的（limLoc=undOvr）；积分等上下限在右侧的保持原生。
    """
    if mode == "native":
        return
    for nary in list(root.iter(_M + "nary")):
        pr = nary.find(_M + "naryPr")
        if pr is None:
            continue
        loc = pr.find(_M + "limLoc")
        if loc is None or (loc.get(_M + "val") or "subSup") != "undOvr":
            continue
        body = nary.find(_M + "e")
        if mode == "auto":
            if body is None or not _looks_tall(body):
                continue
        _stack_operator(nary)


def _looks_tall(element) -> bool:
    for el in element.iter():
        if etree.QName(el).localname in _TALL_TAGS:
            return True
    return False


def _stack_operator(nary) -> None:
    """把 m:nary 换成「固定尺寸运算符 + 上下限堆叠」，操作数移到它后面。"""
    pr = nary.find(_M + "naryPr")
    chr_el = pr.find(_M + "chr") if pr is not None else None
    char = (chr_el.get(_M + "val") if chr_el is not None else "∑") or "∑"
    sub = nary.find(_M + "sub")
    sup = nary.find(_M + "sup")
    body = nary.find(_M + "e")

    run = etree.Element(_M + "r")
    rpr = etree.SubElement(run, _M + "rPr")
    etree.SubElement(rpr, _M + "sty").set(_M + "val", "p")
    etree.SubElement(run, _M + "t").text = char
    node = run

    if sup is not None and len(sup):
        upper = etree.Element(_M + "limUpp")
        etree.SubElement(upper, _M + "e").append(node)
        lim = etree.SubElement(upper, _M + "lim")
        for child in list(sup):
            lim.append(child)
        node = upper

    if sub is not None and len(sub):
        lower = etree.Element(_M + "limLow")
        etree.SubElement(lower, _M + "e").append(node)
        lim = etree.SubElement(lower, _M + "lim")
        for child in list(sub):
            lim.append(child)
        node = lower

    parent = nary.getparent()
    if parent is None:
        return
    index = parent.index(nary)
    parent.insert(index, node)
    parent.remove(nary)

    # 操作数移到运算符后面（LaTeX 语义就是「运算符作用于后面的表达式」）
    if body is not None:
        for offset, child in enumerate(list(body)):
            body.remove(child)
            parent.insert(index + 1 + offset, child)


def _wrap_display(omml) -> "etree._Element":
    """把 m:oMath 包进居中的 m:oMathPara。"""
    para = etree.Element("{%s}oMathPara" % M_NS, nsmap={"m": M_NS})
    pr = etree.SubElement(para, "{%s}oMathParaPr" % M_NS)
    jc = etree.SubElement(pr, "{%s}jc" % M_NS)
    jc.set("{%s}val" % M_NS, "center")
    para.append(omml)
    return para


def _short(msg: str, limit: int = 160) -> str:
    msg = re.sub(r"\s+", " ", msg).strip()
    return msg if len(msg) <= limit else msg[: limit - 1] + "…"


_engine: OmmlEngine | None = None


def get_engine() -> OmmlEngine:
    global _engine
    if _engine is None:
        _engine = OmmlEngine()
    return _engine


@lru_cache(maxsize=1)
def engine_status() -> dict:
    return get_engine().status()
