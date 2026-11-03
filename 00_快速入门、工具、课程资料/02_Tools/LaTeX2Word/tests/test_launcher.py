"""选择器 / 引导脚本的纯逻辑测试（不涉及 GUI）。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


menu = _load("l2w_menu", "scripts/menu.py")
bootstrap = _load("l2w_bootstrap", "bootstrap.py")


# ---------------------------------------------------------------- 候选清单解析


def test_parse_keeps_full_path_with_spaces():
    rows = menu.parse("C:\\Program Files\\Python\\python.exe|3.12.7|64|dirs\n")
    assert rows == [("C:\\Program Files\\Python\\python.exe", "3.12.7", "64", "dirs")]


def test_parse_allows_missing_source():
    rows = menu.parse("C:\\py\\python.exe|3.11.9|64")
    assert rows[0][3] == ""


def test_parse_skips_blank_and_short_lines():
    rows = menu.parse("\nC:\\a\\python.exe\n\n")
    assert rows == []


def test_sort_prefers_higher_version_then_64bit():
    rows = [
        ("a", "3.9.0", "64", "path"),
        ("b", "3.12.7", "64", "py"),
        ("c", "3.10.11", "32", "dirs"),
        ("d", "3.10.11", "64", "registry"),
    ]
    ordered = sorted(rows, key=menu.sort_key, reverse=True)
    assert [r[1] + "/" + r[2] for r in ordered] == [
        "3.12.7/64",
        "3.10.11/64",
        "3.10.11/32",
        "3.9.0/64",
    ]


# ---------------------------------------------------------------- .venv 校验


def _fake_venv(tmp_path: Path, version: str, executable: str) -> Path:
    venv = tmp_path / ".venv"
    (venv / "Scripts").mkdir(parents=True)
    (venv / "Scripts" / "python.exe").write_bytes(b"")
    cfg = venv / "pyvenv.cfg"
    cfg.write_text(f"version = {version}\nexecutable = {executable}\n", encoding="utf-8")
    return venv


def test_venv_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "VENV", tmp_path / "nope")
    monkeypatch.setattr(bootstrap, "VENV_PY", tmp_path / "nope" / "Scripts" / "python.exe")
    monkeypatch.setattr(bootstrap, "PYVENV_CFG", tmp_path / "nope" / "pyvenv.cfg")
    assert bootstrap.venv_problem() == "missing"


def test_venv_built_with_old_python(tmp_path, monkeypatch):
    venv = _fake_venv(tmp_path, "3.9.0", "C:\\Python39\\python.exe")
    monkeypatch.setattr(bootstrap, "VENV", venv)
    monkeypatch.setattr(bootstrap, "VENV_PY", venv / "Scripts" / "python.exe")
    monkeypatch.setattr(bootstrap, "PYVENV_CFG", venv / "pyvenv.cfg")
    problem = bootstrap.venv_problem()
    assert problem is not None and problem.startswith("built-with-")


def test_venv_built_with_other_interpreter(tmp_path, monkeypatch):
    venv = _fake_venv(tmp_path, "3.12.7", "C:\\Somewhere\\Else\\python.exe")
    monkeypatch.setattr(bootstrap, "VENV", venv)
    monkeypatch.setattr(bootstrap, "VENV_PY", venv / "Scripts" / "python.exe")
    monkeypatch.setattr(bootstrap, "PYVENV_CFG", venv / "pyvenv.cfg")
    assert bootstrap.venv_problem() == "built-with-other-python"
