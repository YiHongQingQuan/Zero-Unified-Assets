"""控制台版 Python 选择器（PowerShell 不可用时的兜底）。

用法：python menu.py <候选清单> <结果文件>

候选清单每行：path|version|bits|source
结果文件两行：选中的路径 / remember=1|0
"""

from __future__ import annotations

import sys
from pathlib import Path

SOURCE_LABEL = {
    "env": "环境变量",
    "cfg": "配置文件",
    "venv": "现有环境",
    "py": "py 启动器",
    "path": "PATH",
    "registry": "注册表",
    "dirs": "常见目录",
    "browse": "手动选择",
    "chosen": "已选择",
}


def parse(text: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        path, ver, bits = parts[0], parts[1], parts[2]
        src = parts[3] if len(parts) > 3 else ""
        rows.append((path, ver, bits, src))
    return rows


def sort_key(row: tuple[str, str, str, str]) -> tuple:
    ver, bits = row[1], row[2]
    nums = []
    for piece in ver.split("."):
        try:
            nums.append(int(piece))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2], 1 if bits == "64" else 0)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: menu.py <list-file> <out-file>")
        return 2

    list_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    rows = parse(list_path.read_text(encoding="utf-8", errors="replace")) if list_path.exists() else []
    rows = sorted(rows, key=sort_key, reverse=True)

    if not rows:
        print("没有找到可用的 Python 3.10+ 解释器。")
        return 1

    print()
    print("=" * 66)
    print(f" 找到 {len(rows)} 个可用的 Python 3.10+ 解释器，用哪个？")
    print("-" * 66)
    for i, (path, ver, bits, src) in enumerate(rows, start=1):
        label = SOURCE_LABEL.get(src, src)
        print(f"  [{i}] {ver:<10} {bits} 位  {label:<8} {path}")
    print("-" * 66)
    print(f" 直接回车 = 1（{rows[0][1]}），输入编号后回车；输入 q 取消：")
    sys.stdout.write(" > ")
    sys.stdout.flush()

    choice = sys.stdin.readline().strip()
    if choice.lower() in ("q", "quit", "exit"):
        print("已取消。")
        return 1

    index = 0
    if choice.isdigit():
        index = int(choice) - 1
    if index < 0 or index >= len(rows):
        index = 0

    path, ver, bits, _ = rows[index]
    remember = "1"
    answer = input_text(" 记住这次选择？[Y/n] > ")
    if answer.strip().lower() in ("n", "no"):
        remember = "0"

    out_path.write_text(path + "\n" + "remember=" + remember + "\n", encoding="utf-8")
    print(f" 已选择 Python {ver}（{bits} 位）：{path}")
    return 0


def input_text(prompt: str) -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        return sys.stdin.readline()
    except KeyboardInterrupt:
        return ""


if __name__ == "__main__":
    sys.exit(main())
