"""【v0.1 预留】docx → IR。

本期不实现，但把接口和实现路径固定下来，避免以后改架构：
    1. python-docx 读出段落与 m:oMath 节点
    2. 用 Office 自带的 OMML2MML.XSL 把 OMML 转回 MathML
    3. MathML → LaTeX（自建小转换器或复用第三方）
    4. 填进 Document / Block / MathNode，交给同一个 docx_writer 重新排版

反向链路的关键文件 OMML2MML.XSL 与 MML2OMML.XSL 同目录，安装 Office 即存在。
"""

from __future__ import annotations

from pathlib import Path

from app.core.ir import Document

_XSL_NAME = "OMML2MML.XSL"


def read_docx(path: str | Path) -> Document:  # pragma: no cover - 预留接口
    """读取 docx 并返回 IR。

    Raises:
        NotImplementedError: v0.1 尚未实现。
    """
    raise NotImplementedError(
        "导入 Word 文档功能尚未实现（计划 v0.2）。"
        "预留的链路：python-docx 读段落 → OMML2MML.XSL 转 MathML → MathML 转 LaTeX → 复用 Document IR。"
    )


def reverse_supported() -> bool:
    """反向转换所需的环境是否就绪（Office 的 OMML2MML.XSL 是否存在）。"""
    from app.core.mathconv import locate_xsl

    mml2omml = locate_xsl()
    if mml2omml is None:
        return False
    return (mml2omml.parent / _XSL_NAME).is_file()
