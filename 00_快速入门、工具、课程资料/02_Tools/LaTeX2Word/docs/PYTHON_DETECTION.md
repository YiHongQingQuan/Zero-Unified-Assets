# 多版本 Python 下的启动器方案（v0.2 设计稿）

> 状态：**v0.1.1 已实现**（见第 13 节落地情况）
> 目标：机器上装了多个 Python、默认那个还低于 3.10 时，`start.cmd` 仍能启动；**全程不需要用户敲命令行**。

## 1. 问题与根因

现状：`start.cmd` 只认 `py -3`，取不到就退到 `python`，然后 `bootstrap.py` 检查版本，不达标直接退出。

本机实测（问题已复现）：

```
> py -0p
 -3.9-64        C:\Users\…\Programs\Python\Python39\python.exe
 -3.12-64       D:\exe\miniconda3\python.exe
> py -3 -c "import sys;print(sys.version)"
3.9.0                      ← 装了 3.12，py -3 仍给 3.9
> python bootstrap.py
[错误] 需要 Python 3.10 以上版本，当前是 3.9.0。   ← 于是工具起不来
```

根因三层：

1. `py -3` 是「py 启动器认为的最新 3.x」，依赖注册顺序，既不是 PATH 上的 `python`，也不是真正最高版本。
2. 「默认 `python`」= PATH 第一个，跟装了哪些版本无关。
3. `bootstrap.py` 只会「不合格就报错」，没有回退去找合格版本。

## 2. 目标 / 非目标

**目标**

- 任意一个 ≥ 3.10 的 CPython（python.org / conda / 绿色版 / Store 版）都能启动。
- 多版本时**弹图形对话框让用户选**，选完记住；随时能在图形界面里改。
- 已经装好的环境不因为「新装了 3.13」而被重建。
- 找不到合格版本时，给出图形化的说明与「浏览文件」「打开下载页」按钮。

**非目标**

- 不自动下载安装 Python（只给入口）。
- 不改依赖策略（仍是 `pip install -r requirements.txt`）。
- 不引入需要编译的第三方组件；不打包 exe。

## 3. 已定决策

| 决策点 | 结论 |
|---|---|
| 选版界面 | **Windows 原生对话框（PowerShell + WinForms）**；PS 被策略禁用时自动退回控制台数字菜单 |
| 首次启动 | **多个才弹窗，单个不打扰**；弹过一次后静默沿用 |
| 事后切换 | **网页设置卡片 + 项目根目录双击入口**，两条路都提供 |
| 控制台窗口 | **保留**（显示版本、安装进度、错误原因），不隐藏不最小化 |
| 旧 `.venv` 不可用 | 自动备份（改名 `.venv.broken-<时间戳>`）并重建 |
| 找不到合格版本 | 图形提示框：已扫描清单 + 浏览文件 + 下载页 + 复制诊断 |
| 探测实现 | **纯批处理**（`py` 启动器逐版本 / PATH / 注册表 / 常见目录）；PowerShell 只负责画界面 |

## 4. 探测优先级

按顺序取第一个「探针通过」的候选：

| 序 | 来源 | 说明 |
|---|---|---|
| 1 | 环境变量 `LATEX2WORD_PYTHON` | 临时/脚本化指定；不合法则警告并继续 |
| 2 | `python.txt` | 用户选择或自动写入；一行绝对路径，`#` 开头为注释 |
| 3 | 现有 `.venv` 的基解释器 | 读 `.venv\pyvenv.cfg` 的 `executable`，通过就直接用 |
| 4 | `py -3.16 … py -3.10` | 逐版本精确探测，绕开 `py -3` |
| 5 | PATH：`python` / `python3` / `python3.14…3.10` | conda 激活、绿色版 |
| 6 | 注册表 `PythonCore\3.*\InstallPath` | HKCU / HKLM / HKLM\WOW6432Node 三处 |
| 7 | 常见目录 | `%LOCALAPPDATA%\Programs\Python\Python3*`、`C:\Python3*`、`%ProgramFiles%\Python3*`、`%USERPROFILE%\miniconda3|anaconda3`、`%LOCALAPPDATA%\miniconda3`、`C:\ProgramData\miniconda3|anaconda3`、`%USERPROFILE%\scoop\apps\python\current` |

同一路径多来源命中时按路径去重（大小写不敏感）；列表保留「来源」列。

## 5. 探测协议

统一探针，**只认标准输出里的标记行**：

```
<候选> -c "import sys;print('L2WOK', sys.version_info[0], sys.version_info[1], sys.version_info[2], 64 if sys.maxsize>2**32 else 32, sys.executable)"
```

- 判定：首行以 `L2WOK` 开头，且 `major>3` 或 `major==3 and minor>=10`。
- 额外校验 `import venv, ensurepip`：精简版/嵌入式没有 venv，跳过并注明原因。
- 用 `sys.executable` 作为规范路径（把 `py -3.12` 解析成真实 exe）。
- 输出重定向到临时文件再 `for /f` 解析，**不依赖控制台编码**（路径可能含中文，如本机 `C:\Users\泓\…`）。
- 微软商店的 `WindowsApps\python.exe` 是别名桩：探针没有标记行，自动排除，无需特判。

## 6. 交互设计

### 6.1 启动判定

```
找到合格解释器？
├─ 0 个  → 弹「找不到」对话框（6.3）→ 退出码 2
├─ 1 个  → 直接用（若还没有 .venv 或 .venv 不符，bootstrap 自动建）
└─ N 个  → 已经记住过选择（python.txt 有效）→ 直接用，静默
           否则 → 弹「选择」对话框（6.2）
```

无论哪条路径，控制台都打印一行实际使用的解释器：

```
使用 Python 3.12.7 (64 位)  D:\exe\miniconda3\python.exe
```

### 6.2 选择对话框

```
┌─ 选择 LaTeX2Word 使用的 Python ─────────────────────────┐
│ 检测到 2 个可用的 Python 3.10+ 解释器：                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ● 3.12.7  64 位  D:\exe\miniconda3\python.exe       │ │
│ │     来源：py 启动器                                  │ │
│ │ ○ 3.11.9  64 位  C:\…\Python311\python.exe          │ │
│ │     来源：PATH                                      │ │
│ └─────────────────────────────────────────────────────┘ │
│ ☑ 记住这次选择（以后不再询问）                          │
│                                                          │
│ [ 浏览其他 python.exe… ]   [ 重新检测 ]                  │
│                                  [ 使用这个 ]  [ 取消 ]  │
└──────────────────────────────────────────────────────────┘
```

规则：

- 排序：版本降序，同版本 64 位优先；默认选中第 1 个；回车 = 使用选中项，Esc = 取消。
- 「浏览…」打开 `OpenFileDialog`（默认定位到 `%LOCALAPPDATA%\Programs\Python`），选完**当场跑探针验证**：不合格弹「这个 exe 不是可用的 Python 3.10+」，不关闭对话框。
- 「重新检测」重新调用 `scripts\find-python.cmd --list-only` 刷新列表（不递归调用整个启动流程）。
- 取消 = 不写配置、退出码 2，控制台给出「已取消，可再次双击 start.cmd」。
- 勾选「记住」才写 `python.txt`；不勾选则下次仍然询问。
- 只有一个版本时不弹这个对话框。

### 6.3 找不到时的对话框

```
┌─ 没有找到 Python 3.10 或更高版本 ───────────────────────┐
│ 扫描到的解释器：                                         │
│   3.9.0  C:\Users\me\…\Python39\python.exe              │
│   （其余来源：py 启动器、PATH、注册表、常见目录 —— 均无）│
│                                                          │
│ 你需要 Python 3.10 或更高版本才能运行本工具。            │
│                                                          │
│ [ 浏览 python.exe… ] [ 打开下载页 ] [ 复制诊断信息 ]     │
│                                          [ 退出 ]        │
└──────────────────────────────────────────────────────────┘
```

「复制诊断信息」把扫描清单放到剪贴板，方便贴给他人求助。

### 6.4 事后切换（两条图形入口）

**A. 网页设置卡片**

「⚙ 排版」面板旁新增「运行环境」区：

```
运行环境
  Python     3.12.7 (64 位)
  位置       D:\exe\miniconda3\python.exe
  虚拟环境   .venv（3.12.14）            [ 切换 Python… ]
```

点「切换 Python…」→ `POST /api/environment/select` → 服务端用同样方式拉起选择对话框 → 写入 `python.txt` → 提示「需要重启以生效」并提供「立即重启」按钮：服务端 spawn 一个新的 `start.cmd` 后自行退出（新进程接管端口，被占用则自动顺延）。

新增接口：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/environment` | 返回当前解释器路径、版本、位数、venv 版本、是否需要重建 |
| POST | `/api/environment/select` | 拉起选择对话框；返回 `{changed, chosen, restart_required}` |
| POST | `/api/environment/restart` | 重启服务（spawn 新进程后退出） |

**B. 项目根目录入口**

`选择 Python.cmd`（内容全 ASCII，文件名中文便于发现）：双击 → 对话框 → 写 `python.txt` → 调用 `bootstrap.py --prepare`（只同步 venv 与依赖，不启动服务）→ 提示「下次启动生效」。

### 6.5 兜底：控制台数字菜单

PowerShell 不存在、执行策略被 GPO 锁死、或脚本被拦截（退出码 2）时，自动退回：

```
找到 2 个可用的 Python：
  [1] 3.12.7  64 位  D:\exe\miniconda3\python.exe
  [2] 3.11.9  64 位  C:\…\Python311\python.exe
直接回车 = 1，输入编号后回车：
```

非交互环境（管道输入）取默认值，不阻塞。

### 6.6 批处理与 PowerShell 的契约

| 项 | 约定 |
|---|---|
| 启动命令 | `powershell -NoProfile -STA -ExecutionPolicy Bypass -File "scripts\picker.ps1" -List <临时文件> -Out <临时文件> -Mode select|missing` |
| 列表文件 | UTF-8，每行 `路径|版本|位数|来源`；Windows 文件名禁止 `|`，可安全当分隔符 |
| 回写文件 | UTF-8，两行：`选择的路径`、`remember=1|0` |
| 退出码 | `0` 已选择 / `1` 用户取消 / `2` PowerShell 不可用（批处理据此决定是否走控制台菜单） |
| 编码 | 批处理首行 `chcp 65001`；PS 用 `Get-Content -Encoding UTF8` / `Set-Content -Encoding UTF8`；临时文件放 `%TEMP%` |
| 窗口 | 对话框 `TopMost` 并 `Activate()`，确保压住控制台窗口 |

## 7. 选择与记忆

- 自动选择 / 对话框选择成功后写入 `python.txt`（UTF-8）：

```
# 由 LaTeX2Word 设置于 2026-10-23 17:10；删掉本文件或运行「选择 Python」即可重选
D:\exe\miniconda3\python.exe
```

- 读取时跳过 `#` 开头与空行。
- 启动时校验：探针不过 → 打警告、忽略内容、重新走探测流程（不擅自删除文件，只在控制台提示）。
- 环境变量 `LATEX2WORD_PYTHON` 优先级最高，临时覆盖，不写盘。

## 8. `.venv` 生命周期

`bootstrap.py` 负责（Python 判断比批处理可靠）：

| 状态 | 判定 | 处理 |
|---|---|---|
| 健康 | `.venv\Scripts\python.exe` 可运行，`pyvenv.cfg` 版本 ≥ 3.10，且 `executable` 与本次选中的基解释器一致 | 直接用 |
| 版本不符 | `pyvenv.cfg` 的 `version` < 3.10 | 备份重建 |
| 已损坏 | venv 内 python 跑不起来（基解释器被卸载/移动） | 备份重建 |

重建 = 改名 `.venv.broken-20261023-170245`（不删数据）→ `python -m venv .venv` → 装依赖。改名失败（文件被占用）打印「请关闭正在使用 .venv 的窗口后重试」。

依赖缺失（import 探针失败）只重装依赖，不重建环境。

新增 `--prepare` 模式：只做 venv 同步与依赖安装，不启动服务（供 `选择 Python.cmd` 调用）。

## 9. 风险与边界

| 项 | 处理 |
|---|---|
| PowerShell 被 GPO/AppLocker 禁用 | 退出码 2 → 控制台菜单；探测逻辑本身不依赖 PS |
| 路径含中文（本机 `C:\Users\泓\…`） | 全程 UTF-8 文件互传 + `chcp 65001`；单列测试用例 |
| 商店 Python 桩 | 无标记行，自动排除 |
| 嵌入式/精简 Python | `import venv, ensurepip` 失败 → 跳过并注明 |
| 32 位 | 允许，同版本 64 位优先 |
| 预发布版（3.14.0rc1） | 允许但排正式版之后；仅预发布时提示可能缺轮子 |
| `python.txt` 指向已卸载路径 | 探针失败 → 警告 + 回落扫描 |
| 对话框抢不到焦点 | `TopMost = true`，显示后 `Activate()` |
| 网页切换后重启失败 | 提示「请手动双击 start.cmd」；配置已写入，不影响下次启动 |
| 端口被旧进程占用 | 复用现有「端口顺延」逻辑，控制台打印实际地址 |

## 10. 改动清单

| 文件 | 改动 |
|---|---|
| `start.cmd` | 变薄：chcp / cd / 处理 `--select`、`--python` / 调 `scripts\find-python.cmd` / 调 bootstrap / 出错 pause |
| `scripts\find-python.cmd` | **新增**：候选枚举、探针、去重、排序、判定「几个」，读 `python.txt`，写临时列表，决定弹窗还是直接过 |
| `scripts\picker.ps1` | **新增**：WinForms 选择框与「找不到」框，浏览/重检/复制诊断，回写结果 |
| `选择 Python.cmd` | **新增**：双击入口（ASCII 内容），选完跑 `bootstrap.py --prepare` |
| `bootstrap.py` | 增加 venv 校验与备份重建、`--prepare` 模式 |
| `app/server.py` | 新增 `/api/environment`、`/api/environment/select`、`/api/environment/restart` |
| `app/web/*` | 设置面板新增「运行环境」卡片与「切换 Python」按钮 |
| `python.txt` | 运行时生成，加入 `.gitignore` |
| `README.md` | 补多版本行为、图形入口、`python.txt` 说明 |

## 11. 验收矩阵

| # | 场景 | 构造方式 | 期望 |
|---|---|---|---|
| 1 | 默认 `python` 是 3.9，另有 3.12 | 本机现状 | 弹出选择框（或已记住则直接用 3.12），服务启动 |
| 2 | 只有一个合格版本 | 临时屏蔽其他候选 | 不弹窗，直接启动 |
| 3 | 多个合格版本，未记住 | 清空 `python.txt` | 弹窗，默认选中最高版本 |
| 4 | 勾选「记住」后再次启动 | 连续两次 | 第二次不弹窗，控制台打印所用版本 |
| 5 | 不勾「记住」 | 取消勾选 | 每次启动都弹 |
| 6 | 「浏览…」选一个无效 exe | 选记事本 | 对话框提示不合格，不关闭 |
| 7 | 「浏览…」选合格的 3.11 | 手选 3.11 | 立即采用并写配置 |
| 8 | 「重新检测」 | 点按钮 | 列表刷新，不重启整个流程 |
| 9 | 完全没有合格版本 | shim：假 `py` 返回 103 + 仅留 3.9 的 PATH | 「找不到」对话框，列出 3.9，退出码 2 |
| 10 | PowerShell 不可用 | 用包装脚本模拟退出码 2 | 自动退回控制台数字菜单，仍能启动 |
| 11 | 中文路径读写 | 含「泓」的路径 | 配置读写不乱码 |
| 12 | `.venv` 由 3.9 创建 | 改 `pyvenv.cfg` 的 version | 备份为 `.venv.broken-*` 并重建 |
| 13 | `.venv` 基解释器已删除 | 改 `pyvenv.cfg` 的 home | 同上 |
| 14 | 网页「切换 Python」 | 启动后点按钮 | 弹窗选择 → 写配置 → 重启后生效 |
| 15 | `选择 Python.cmd` | 双击 | 弹窗 → 写配置 → `--prepare` 同步环境 |
| 16 | `--select` 开关 | 运行 | 强制重选并覆盖 |
| 17 | 非交互环境 | `echo. | start.cmd` | 走默认值，不卡死 |

## 12. 工作量

| 部分 | 估计 |
|---|---|
| `find-python.cmd`（枚举/探针/判定） | 约 160 行 |
| `picker.ps1`（两个对话框） | 约 180 行 |
| `bootstrap.py`（校验/重建/`--prepare`） | 约 70 行 |
| 服务端接口 + 网页卡片 | 约 80 行 |
| 文档与手工验证 | 半天 |

## 13. v0.1.1 落地情况

已实现（与本文的差异都记在下面）：

| 能力 | 状态 | 实测 |
|---|---|---|
| 7 级候选枚举 + 探针（含 venv/ensurepip 校验） | ✅ | 本机正确识别出 conda 3.12.7，并拒绝 3.9 |
| 去重、版本排序 | ✅ | 同一路径来自 `py` 与注册表时只保留一条 |
| WinForms 选择框 / 找不到提示框 | ✅ | 两个对话框均已渲染截图确认（中文、排序、来源标签正常） |
| 记住选择 → `python.txt` | ✅ | 自动与手动两条路径都写入 |
| 控制台兜底菜单 | ✅ | `PS_DISABLED=1` 时正常出菜单并回写结果 |
| `.venv` 校验 + 备份重建 + `--prepare` | ✅ | 把 `pyvenv.cfg` 改成 3.9 后自动备份重建并重装依赖 |
| `--select` / `--python` / `LATEX2WORD_PYTHON` | ✅ | `--python` 与 `--select` 均验证通过 |
| 网页「运行环境」卡片 + 切换/重启接口 | ✅ 接口与卡片已验证，点击切换需人工确认（headless 无法点击） |  |
| 中文路径 | ✅ | 用 `C:\Users\泓\…` 验证了配置读写、警告输出、菜单显示 |

实现中踩到并已修复的坑（后续维护请勿回退）：

1. **`.cmd` 必须是 CRLF 换行**。LF-only 时 `call :label` 会报 "cannot find the batch label"，`>>` 写文件也会随机失败。
2. **`%~dp0` 必须在 `shift` 之前存进变量**。`shift` 会改写 `%0`，之后再取 `%~dp0` 得到的是别的东西（这曾导致 `ROOT` 指向上一层目录）。
3. **`requirements.txt` 必须保持 ASCII**。pip 用系统码页解码 requirements 文件，UTF-8 中文注释会直接报 `UnicodeDecodeError`。
4. **`py` 的版本参数要带横线**：`py -3.12`；`py 3.12` 会被当成“运行名为 3.12 的脚本”。
5. **注册表的 `InstallPath` 是子键的默认值**，不是同名值，得 `reg query <key>\InstallPath /ve`。
6. **`chcp 65001` 要写进 `find-python.cmd` 自己**，因为它可能被直接调用，不依赖 start.cmd 先设好。
7. **venv 快路径改为直接探 `.venv\Scripts\python.exe`**，不再解析 `pyvenv.cfg`——后者在中文路径下会读成乱码。
8. **`.ps1` 必须 UTF-8 带 BOM**，否则 PowerShell 5.1 按 ANSI 读，中文全变乱码。

未做/后续可加：

- 网页里点击「切换 Python…」的完整链路（接口已通，缺少自动化点击验证）。
- 多显示器 / 高 DPI 下的对话框截图（`-Capture` 只是开发自测用，实际显示由系统缩放处理）。
- `python.txt` 被手动改坏时只警告不自动修复（保留用户文件）。

