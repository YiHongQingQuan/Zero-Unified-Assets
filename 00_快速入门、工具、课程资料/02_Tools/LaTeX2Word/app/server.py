"""本地 Web 服务：粘贴 → 识别 → 预览 → 导出 docx。

只监听 127.0.0.1，不需要账号、不落盘（导出文件直接回给浏览器）。
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.core import ir
from app.core.detector import AnalyzeOptions, build_document
from app.core.docx_writer import ExportOptions, write_docx
from app.core.mathconv import get_engine

APP_NAME = "LaTeX2Word"
APP_VERSION = "0.1.7"

ROOT = Path(__file__).resolve().parent.parent
PYTHON_TXT = ROOT / "python.txt"
VENV_DIR = ROOT / ".venv"

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptionsIn(BaseModel):
    sensitivity: str = "standard"
    markdown: bool = False
    line_mode: bool = True
    # 排版
    cn_font: str = "宋体"
    en_font: str = "Times New Roman"
    font_size: float = 12.0
    line_spacing: float = 1.5
    first_line_indent: float = 2.0
    margin_cm: float = 2.54
    paper: str = "A4"
    # 上下限位置：below（一律下方，默认）/ auto（LaTeX 惯例）/ side（一律右侧）
    limits_mode: str = "below"
    # 大型运算符尺寸：auto（高内容时固定，默认）/ fixed（一律固定）/ native（跟随内容）
    nary_mode: str = "auto"


class AnalyzeIn(BaseModel):
    text: str = ""
    options: OptionsIn = Field(default_factory=OptionsIn)


class ExportIn(BaseModel):
    document: dict = Field(default_factory=dict)
    options: OptionsIn = Field(default_factory=OptionsIn)
    filename: Optional[str] = None


def _export_options(o: OptionsIn) -> ExportOptions:
    return ExportOptions(
        cn_font=o.cn_font,
        en_font=o.en_font,
        font_size=float(o.font_size),
        line_spacing=float(o.line_spacing),
        first_line_indent=float(o.first_line_indent),
        margin_cm=float(o.margin_cm),
        paper=o.paper,
        limits_mode=o.limits_mode,
        nary_mode=o.nary_mode,
    )


@app.get("/api/health")
def health() -> dict:
    engine = get_engine()
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "engine": engine.status(),
        "python": sys.version.split()[0],
    }


# ---------------------------------------------------------------- 运行环境


def _read_python_txt() -> Optional[str]:
    if not PYTHON_TXT.exists():
        return None
    for line in PYTHON_TXT.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return None


def _read_pyvenv() -> dict:
    cfg = VENV_DIR / "pyvenv.cfg"
    values: dict = {}
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                values[key.strip().lower()] = value.strip()
    return values


@app.get("/api/environment")
def environment() -> dict:
    base = _read_pyvenv()
    return {
        "python": {
            "version": platform.python_version(),
            "bits": 64 if sys.maxsize > 2**32 else 32,
            "executable": sys.executable,
        },
        "base": {
            "executable": base.get("executable") or base.get("home"),
            "version": base.get("version"),
        },
        "venv": {
            "path": str(VENV_DIR),
            "exists": (VENV_DIR / "pyvenv.cfg").exists(),
        },
        "config": {
            "file": str(PYTHON_TXT),
            "value": _read_python_txt(),
        },
    }


@app.post("/api/environment/select")
def environment_select() -> dict:
    script = ROOT / "scripts" / "find-python.cmd"
    if not script.exists():
        raise HTTPException(status_code=500, detail="找不到 scripts/find-python.cmd")
    before = _read_python_txt()
    try:
        proc = subprocess.run(["cmd", "/c", str(script), "--choose"], cwd=str(ROOT))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"无法启动选择器：{exc}") from exc
    after = _read_python_txt()
    changed = bool(after) and after != before
    return {
        "ok": proc.returncode == 0,
        "cancelled": proc.returncode != 0,
        "chosen": after,
        "changed": changed,
        "restart_required": changed,
    }


@app.post("/api/environment/restart")
def environment_restart() -> dict:
    start_cmd = ROOT / "start.cmd"
    if not start_cmd.exists():
        raise HTTPException(status_code=500, detail="找不到 start.cmd")
    # 等 2 秒让端口释放，再在新窗口里重新启动；随后本进程自行退出
    subprocess.Popen(
        ["cmd", "/c", f'timeout /t 2 >nul & start "" "{start_cmd}"'],
        cwd=str(ROOT),
        creationflags=0x00000010,  # CREATE_NEW_CONSOLE
    )
    threading.Timer(0.8, lambda: os._exit(0)).start()
    return {"ok": True}


@app.post("/api/analyze")
def analyze(payload: AnalyzeIn) -> dict:
    options = payload.options
    doc, stats = build_document(
        payload.text,
        AnalyzeOptions(
            sensitivity=options.sensitivity,
            markdown=options.markdown,
            line_mode=options.line_mode,
        ),
    )

    # 预检：提前把转换失败的公式标出来，前端就能在预览里提示
    engine = get_engine()
    failed = 0
    if engine.available:
        for _, node in ir.iter_math(doc):
            if not node.accepted:
                continue
            try:
                engine.latex_to_omml_xml(node.latex, node.display, options.limits_mode, options.nary_mode)
            except Exception as exc:  # noqa: BLE001 - 失败原因要透传给用户
                node.error = str(exc)
                failed += 1
    else:
        for _, node in ir.iter_math(doc):
            node.error = engine.error

    data = ir.document_to_dict(doc)
    data["stats"] = {**stats.as_dict(), "failed": failed}
    data["engine"] = engine.status()
    return data


@app.post("/api/export")
def export(payload: ExportIn) -> StreamingResponse:
    engine = get_engine()
    if not engine.available:
        raise HTTPException(status_code=503, detail=engine.error or "转换引擎不可用")

    try:
        doc = ir.document_from_dict(payload.document)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"文档数据无法解析：{exc}") from exc

    result = write_docx(doc, _export_options(payload.options), engine)
    name = _filename(payload.filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}",
        "X-Rendered": str(result.rendered),
        "X-Skipped": str(result.skipped),
        "X-Issues": str(len(result.issues)),
        "Access-Control-Expose-Headers": "X-Rendered, X-Skipped, X-Issues",
    }
    return StreamingResponse(
        iter([result.data]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


def _filename(raw: str | None) -> str:
    name = (raw or "").strip() or "output.docx"
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "")
    if not name.lower().endswith(".docx"):
        name += ".docx"
    return name[:120]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


def pick_port(preferred: int = 8765, tries: int = 40) -> int:
    for offset in range(tries):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("找不到可用端口")


def main() -> None:
    import uvicorn

    host = "127.0.0.1"
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else pick_port()
    url = f"http://{host}:{port}/"

    print("=" * 56, flush=True)
    print(f"  {APP_NAME} v{APP_VERSION}", flush=True)
    print(f"  地址：{url}", flush=True)
    engine = get_engine()
    print(f"  公式引擎：{'就绪' if engine.available else '不可用 - ' + str(engine.error)}", flush=True)
    print("  关闭本窗口即可停止服务", flush=True)
    print("=" * 56, flush=True)

    threading.Thread(
        target=lambda: (time.sleep(1.2), webbrowser.open(url)), daemon=True
    ).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
