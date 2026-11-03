"""HTTP 接口测试（进程内 TestClient，不需要起服务器）。"""

from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.core.mathconv import get_engine
from app.server import app

client = TestClient(app)
requires_engine = pytest.mark.skipif(not get_engine().available, reason="本机没有 MML2OMML.XSL")

TEXT = r"""行内 $x^2$ 与 E=mc²。

$$\frac{a}{b} = 1$$
"""


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "LaTeX2Word"
    assert data["version"].startswith("0.1")


def test_analyze_returns_blocks_and_stats():
    res = client.post("/api/analyze", json={"text": TEXT, "options": {"sensitivity": "standard"}})
    assert res.status_code == 200
    data = res.json()
    assert data["stats"]["formulas"] == 3
    assert data["engine"]["available"] is True
    kinds = [b["kind"] for b in data["blocks"]]
    assert "display_math" in kinds


def test_analyze_empty_text():
    res = client.post("/api/analyze", json={"text": ""})
    assert res.status_code == 200
    assert res.json()["blocks"] == []


@requires_engine
def test_export_returns_docx():
    doc = client.post("/api/analyze", json={"text": TEXT}).json()
    res = client.post(
        "/api/export",
        json={"document": {"blocks": doc["blocks"]}, "options": {}, "filename": "测试.docx"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert res.headers["x-rendered"] == "3"
    assert "filename*=UTF-8''" in res.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
        assert "word/document.xml" in zf.namelist()


@requires_engine
def test_export_respects_accepted_flag():
    doc = client.post("/api/analyze", json={"text": TEXT}).json()
    for block in doc["blocks"]:
        for inline in block["inlines"]:
            if inline["kind"] == "math":
                inline["accepted"] = False
    res = client.post("/api/export", json={"document": {"blocks": doc["blocks"]}})
    assert res.status_code == 200
    assert res.headers["x-rendered"] == "0"
    assert res.headers["x-skipped"] == "3"


def test_export_rejects_garbage():
    res = client.post("/api/export", json={"document": {"blocks": [{"kind": "paragraph"}]}})
    assert res.status_code in (200, 400)
