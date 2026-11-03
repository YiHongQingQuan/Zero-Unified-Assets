"""启动引导。

职责：
  1. 校验 .venv 是否由本次选中的解释器创建、是否可用；不可用就备份重建
  2. 缺失依赖就安装
  3. 用 .venv 里的解释器重新执行自己，再启动服务

中文输出放在这里（而不是 start.cmd），因为 cmd.exe 用系统码页解析批处理，
非 ASCII 字符会变成乱码命令；Python 输出到 65001 控制台没有这个问题。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PYVENV_CFG = VENV / "pyvenv.cfg"
REQUIREMENTS = ROOT / "requirements.txt"
IMPORTS = "import fastapi, uvicorn, docx, lxml, latex2mathml"
MIN_VERSION = (3, 10)


def log(message: str = "") -> None:
    print(message, flush=True)


def _in_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == VENV.resolve()
    except OSError:
        return False


def _bits() -> str:
    return "64" if sys.maxsize > 2**32 else "32"


def _norm(path: str) -> str:
    p = str(path).strip().strip('"')
    try:
        return os.path.normcase(os.path.abspath(p))
    except OSError:
        return p.lower()


# ---------------------------------------------------------------- venv


def _read_cfg() -> dict[str, str]:
    values: dict[str, str] = {}
    if not PYVENV_CFG.exists():
        return values
    for line in PYVENV_CFG.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip().lower()] = value.strip()
    return values


def _venv_runs() -> bool:
    if not VENV_PY.exists():
        return False
    try:
        probe = subprocess.run(
            [str(VENV_PY), "-c", "import sys"],
            capture_output=True,
            timeout=30,
        )
        return probe.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def venv_problem() -> str | None:
    """返回不能复用 .venv 的原因；None 表示可以复用。"""
    if not VENV.exists():
        return "missing"
    if not VENV_PY.exists():
        return "missing-interpreter"

    cfg = _read_cfg()
    version = cfg.get("version", "")
    if version:
        try:
            major, minor = (int(x) for x in version.split(".")[:2])
        except ValueError:
            major, minor = 0, 0
        if (major, minor) < MIN_VERSION:
            return f"built-with-{version}"

    recorded = cfg.get("executable") or cfg.get("home", "")
    if recorded and _norm(recorded) != _norm(sys.executable):
        return "built-with-other-python"

    if not _venv_runs():
        return "broken"
    return None


def rebuild_venv(reason: str) -> bool:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f".venv.broken-{stamp}"
    log(f"[提示] 现有 .venv 不可用（{reason}），将备份为 {backup.name} 并用当前解释器重建。")
    try:
        VENV.rename(backup)
    except OSError as exc:
        log(f"[错误] 无法移动 .venv：{exc}")
        log("       请关闭正在使用 .venv 的窗口（编辑器 / 终端 / 服务）后重试。")
        return False

    log("[1/3] 正在创建虚拟环境…")
    result = subprocess.run([sys.executable, "-m", "venv", str(VENV)])
    if result.returncode != 0 or not VENV_PY.exists():
        log("[错误] 创建虚拟环境失败。")
        return False
    return True


# ---------------------------------------------------------------- deps


def deps_ready() -> bool:
    try:
        probe = subprocess.run([str(VENV_PY), "-c", IMPORTS], capture_output=True)
        return probe.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def ensure_deps() -> bool:
    if deps_ready():
        return True
    log("[2/3] 正在安装依赖（首次需要联网，约 1-2 分钟）…")
    result = subprocess.run(
        [
            str(VENV_PY), "-m", "pip", "install",
            "--no-input", "--disable-pip-version-check",
            "-r", str(REQUIREMENTS),
        ]
    )
    if result.returncode != 0 or not deps_ready():
        log("[错误] 依赖安装失败，请检查网络后重试。")
        return False
    return True


# ---------------------------------------------------------------- main


def run_server(args: list[str]) -> int:
    sys.argv = [str(ROOT / "app" / "server.py"), *args]
    os.chdir(ROOT)
    from app.server import main as server_main

    server_main()
    return 0


def prepare() -> int:
    """只同步环境，不启动服务（供「选择 Python.cmd」调用）。"""
    problem = venv_problem()
    if problem is None:
        log("[1/3] 复用现有虚拟环境，无需重建。")
    elif not rebuild_venv(problem):
        return 1
    if not ensure_deps():
        return 1
    log("[3/3] 环境就绪，下次启动即使用新解释器。")
    return 0


def main() -> int:
    args = list(sys.argv[1:])

    if sys.version_info < MIN_VERSION:
        log(f"[错误] 需要 Python 3.10 以上版本，当前是 {sys.version.split()[0]}。")
        log("       请安装新版 Python：https://www.python.org/downloads/")
        return 1

    if _in_venv():
        if not ensure_deps():
            return 1
        return run_server(args)

    if "--prepare" in args:
        return prepare()

    log(f"使用 Python {sys.version.split()[0]} ({_bits()} 位)  {sys.executable}")

    problem = venv_problem()
    if problem is not None and not rebuild_venv(problem):
        return 1

    if not ensure_deps():
        return 1

    log("[3/3] 启动服务…")
    result = subprocess.run([str(VENV_PY), "-X", "utf8", str(Path(__file__).resolve()), *args])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
