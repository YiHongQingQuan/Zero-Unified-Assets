"""文档中间表示（IR）。

这一层刻意与「文本」「docx」两种外部形态解耦：
    text  --(segmenter/detector)-->  Document  --(docx_writer)-->  .docx
    .docx --(docx_reader, 预留)---->  Document  --(未来: docx_writer)-->  .docx

新增格式只加在 IO 两端，不动中间的识别与排版逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass
class TextRun:
    """普通文字片段。"""

    text: str = ""
    bold: bool = False
    italic: bool = False
    code: bool = False
    kind: str = field(default="text", init=False)


@dataclass
class MathNode:
    """一个公式。

    latex       归一化之后的 LaTeX（送给转换器的那份）
    raw         用户在原文里实际写的形态（失败时原样回显用）
    origin      explicit（带 $） / implicit（识别出来的）
    confidence  0~1；显式公式恒为 1.0
    accepted    是否最终写入 docx（前端可逐个切换）
    """

    id: str = ""
    latex: str = ""
    raw: str = ""
    display: bool = False
    origin: str = "explicit"
    confidence: float = 1.0
    accepted: bool = True
    warnings: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)  # 为什么判为公式（隐式识别给出）
    error: Optional[str] = None
    # 预留：编号与 \tag，本版不生成编号
    number: Optional[int] = None
    tag: Optional[str] = None
    kind: str = field(default="math", init=False)


Inline = Union[TextRun, MathNode]


@dataclass
class Block:
    """段落级单元。kind: paragraph | heading | list_item | quote | code | display_math"""

    kind: str = "paragraph"
    inlines: list[Inline] = field(default_factory=list)
    level: Optional[int] = None
    ordered: Optional[bool] = None
    rows: list[list[str]] = field(default_factory=list)  # kind == "table" 时使用


@dataclass
class Document:
    blocks: list[Block] = field(default_factory=list)
    source: str = "text"  # text（本期） | docx（预留）
    meta: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------- 序列化


def inline_to_dict(node: Inline) -> dict[str, Any]:
    if isinstance(node, MathNode):
        return {
            "kind": "math",
            "id": node.id,
            "latex": node.latex,
            "raw": node.raw,
            "display": node.display,
            "origin": node.origin,
            "confidence": round(float(node.confidence), 3),
            "accepted": bool(node.accepted),
            "warnings": list(node.warnings),
            "reasons": list(node.reasons),
            "error": node.error,
        }
    return {
        "kind": "text",
        "text": node.text,
        "bold": node.bold,
        "italic": node.italic,
        "code": node.code,
    }


def block_to_dict(block: Block) -> dict[str, Any]:
    return {
        "kind": block.kind,
        "level": block.level,
        "ordered": block.ordered,
        "rows": [list(r) for r in block.rows],
        "inlines": [inline_to_dict(n) for n in block.inlines],
    }


def document_to_dict(doc: Document) -> dict[str, Any]:
    return {
        "source": doc.source,
        "meta": dict(doc.meta),
        "blocks": [block_to_dict(b) for b in doc.blocks],
    }


def inline_from_dict(data: dict[str, Any]) -> Inline:
    if data.get("kind") == "math":
        return MathNode(
            id=str(data.get("id") or ""),
            latex=str(data.get("latex") or ""),
            raw=str(data.get("raw") or data.get("latex") or ""),
            display=bool(data.get("display")),
            origin=str(data.get("origin") or "explicit"),
            confidence=float(data.get("confidence") or 1.0),
            accepted=bool(data.get("accepted", True)),
            warnings=list(data.get("warnings") or []),
            reasons=list(data.get("reasons") or []),
            error=data.get("error"),
        )
    return TextRun(
        text=str(data.get("text") or ""),
        bold=bool(data.get("bold")),
        italic=bool(data.get("italic")),
        code=bool(data.get("code")),
    )


def document_from_dict(data: dict[str, Any]) -> Document:
    blocks = []
    for raw_block in data.get("blocks") or []:
        blocks.append(
            Block(
                kind=str(raw_block.get("kind") or "paragraph"),
                inlines=[inline_from_dict(n) for n in raw_block.get("inlines") or []],
                level=raw_block.get("level"),
                ordered=raw_block.get("ordered"),
                rows=[list(r) for r in raw_block.get("rows") or []],
            )
        )
    return Document(
        blocks=blocks,
        source=str(data.get("source") or "text"),
        meta=dict(data.get("meta") or {}),
    )


def iter_math(doc: Document):
    """遍历文档里所有公式节点（含被忽略的），产出 (block 序号, MathNode)。"""
    for bi, block in enumerate(doc.blocks):
        for node in block.inlines:
            if isinstance(node, MathNode):
                yield bi, node


def plain_text(doc: Document) -> str:
    """粗还原：用于文件名与调试。"""
    chunks: list[str] = []
    for block in doc.blocks:
        parts = []
        for node in block.inlines:
            if isinstance(node, MathNode):
                parts.append(f"${node.latex}$")
            else:
                parts.append(node.text)
        chunks.append("".join(parts))
    return "\n".join(chunks)
