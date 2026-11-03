# LaTeX2Word 设计方案（v1 设计稿）

> 状态：**v0.1 已按本稿落地**（M0–M4 完成，M5 部分完成）· 本文件保留设计意图，实现细节以代码为准
> 目标目录：`D:\DeepSeek Harness\LaTeX2Word`

## 0. v0.1 落地情况

| 里程碑 | 状态 | 说明 |
|---|---|---|
| M0 骨架 + IR + 引擎自检 | ✅ | `app/core/ir.py`、`/api/health` 返回 XSL 路径与可用性 |
| M1 显式定界符全链路 | ✅ | 40 条公式语料 40/40 转换成功（`tests/test_convert.py`） |
| M2 隐式识别 | ✅ | 打分 + 边界收敛 + Unicode 映射；正反例用例见 `tests/test_detector.py` |
| M3 复核交互 | ✅ | 预览高亮/编号、清单双向联动、三档灵敏度、全部接受/忽略、只看待确认 |
| M4 排版与边界 | ✅ | 矩阵、align、`\text{}`、行距缩进、设置面板全部可配 |
| M5 质量报告 / README | 🟡 | 转换失败在预览与清单中标记；导出返回跳过数量；README 完成；exe 打包未做 |

实现与设计的两处偏差（都是有意的）：
1. **多加了「解析 Markdown」开关**，把表格/标题/列表/代码块纳入，未重构架构。
2. **公式预检放在 `/api/analyze` 阶段**：识别时就把转换失败的公式标出来，导出前即可见，而不是导出时才发现。

## 1. 需求与范围

| 编号 | 需求 | v1 是否覆盖 | 说明 |
|---|---|---|---|
| R1 | 粘贴含 LaTeX 的文本 → 生成 docx，且文档中公式已是渲染结果 | ✅ 覆盖 | 渲染为 **Word 原生公式（OMML）**，Word 内可继续编辑 |
| R2 | 识别隐式公式（无 `$` 包裹） | ✅ 覆盖 | 规则引擎打分 + 人工选择性复核 |
| R3 | 同时支持带 `$` 与不带 `$` 的公式 | ✅ 覆盖 | 显式定界符优先，隐式识别只在未覆盖文本上做 |
| R4 | 为将来「导入 Word 文档」预留 | ✅ 预留 | 引入文档中间表示（IR）+ 双向 IO 目录，本期只留接口 |
| R5 | 疑问提问 | — | 见第 10 节 |

已确认的决策（共 8 项，详见下表）：

| 项 | 决策 |
|---|---|
| 软件形态 | **本地网页应用**：`start.cmd` 启动，浏览器打开 `127.0.0.1:PORT`，左粘贴右预览，一键导出 docx |
| 隐式公式 | **自动识别 + 选择性人工复核**：候选项在预览里高亮/编号，可单独接受或忽略，也可一键全接受/全忽略，不必逐条确认 |
| 渲染内核 | **OMML 原生公式**：LaTeX → MathML → OMML，注入 docx 成为 Word 原生可编辑公式 |
| 输入结构 | 默认按**纯段落**解析，另给「解析 Markdown 结构」开关（`#` 标题、`-` 列表、`>` 引用、表格） |
| 公式编号 | **v1 不做自动编号**；IR 保留 `number`/`tag` 字段，后续再加 |
| 排版 | **全部可配置**（字体/字号/行距/缩进/页边距/纸张），默认取中文学术常规 |
| 批量 | **v1 只做单篇**，一次一个粘贴区、一次一个 docx |
| 失败兜底 | **保留原文 + 高亮 + 报告定位**；不出图片、不静默丢内容 |

## 2. 可行性验证（已实测，非纸面结论）

本轮已在当前机器上把最关键的一段链路跑通：

```
latex2mathml（纯 Python）→ MathML → MML2OMML.XSL（Office 自带，lxml 执行 XSLT）→ m:oMath → 注入 python-docx
```

实测结果：

1. `x^2 + \frac{a}{b} = \sqrt{\beta}` 正确转出带 `m:sSup / m:f / m:rad` 的 OMML。
2. 生成的 `test.docx` 用 Word 打开后 `OMaths.Count == 2`，正文文本被读成 `𝐸=𝑚𝑐2`（数学斜体字形），说明 **Word 把注入内容识别为真正的公式对象，而不是文本**。

环境事实：

- Office：`Microsoft Office LTSC 专业增强版 2024`，`C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL` 存在（194 KB）。**同目录还有 `OMML2MML.XSL`**，这正是将来 R4 反向解析要用的东西。
- 运行时可用的 Python 3.12.14 已带 `python-docx 1.2.0` 与 `lxml`；系统另有 Python 3.9。
- 机器上没有 pandoc / TeX / LibreOffice；PyPI 可访问（依赖可在线安装，也可预置离线包）。
- 公式字体将由 Word 默认的 Cambria Math 承载，无需额外装字体。

## 3. 总体架构

```
┌──────────────── 浏览器（前端，无构建步骤：原生 HTML/CSS/ES Module + KaTeX）────────────────┐
│  粘贴区        │  预览区（KaTeX 近似预览 / 成稿预览）      │  公式清单（可勾选）           │
└───────────────┬──────────────────────────────────────────────────────────────────────────┘
                │ JSON over HTTP（本机回环）
┌───────────────▼──────────────── 后端 Python（FastAPI + uvicorn）──────────────────────────┐
│  api/                                                                                      │
│   ├── /api/health      引擎自检（Office XSL 是否可用、版本号）                              │
│   ├── /api/analyze     text + options → 段落/公式节点 + 候选 + 统计（不落盘）               │
│   └── /api/export      resolved IR + options → .docx 字节流                                 │
│  core/        ── 纯函数，与 Web 无关，可单独测试 ──                                         │
│   ├── ir.py            文档中间表示（段落 / 行内 / 公式节点）                                │
│   ├── segmenter.py     文本 → 块（段落、标题、列表项…）                                      │
│   ├── detector/        公式识别                                                │
│   │   ├── explicit.py   $$ \[ \] \( \) $ \begin{equation} 等显式定界                      │
│   │   ├── implicit.py   无定界符候选发现 + 打分 + 边界收敛                                  │
│   │   └── unicode_math.py  Unicode 数学符号 ↔ LaTeX（α ∫ ∑ ² √ ≤ …）                       │
│   ├── normalize.py     LaTeX 清洗：\text{}、\left\right、\,、\tag、\\ 换行 …                 │
│   ├── mathconv.py      LaTeX → MathML → OMML（Office XSL；缺失时回落 pandoc）                │
│   ├── docx_writer.py   IR → docx（python-docx + OMML 注入）                                 │
│   ├── docx_reader.py   【预留】docx → IR，本期仅接口与 NotImplemented                        │
│   └── report.py        转换质量报告（成功/降级/失败清单）                                    │
│  web/         静态资源（index.html / app.js / style.css / vendor/katex/）                   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

要点：**前端只做预览与交互，不做权威渲染**。KaTeX 预览是"近似效果"，最终以 python-docx 写出的 docx 为准；这样避免前后端两套渲染器互相打架。

## 4. 处理流水线

```
原始文本
  → ① 分块（按空行/换行；打开「解析 Markdown 结构」开关时再解析 # 标题 / - 列表 / > 引用 / 表格）
  → ② 显式公式抽取（带定界符，最高优先级，占据的区间打标记）
  → ③ 隐式候选发现（仅在②未覆盖的文本上做：种子 → 打分 → 边界收敛 → 语法体检）
  → ④ 归一化（Unicode→LaTeX、去噪、环境规范化）
  → ⑤ 逐条 LaTeX → MathML → OMML（带缓存，同一公式只转一次）
  → ⑥ docx 组装（样式、字体、行距、编号、公式居中）
  → ⑦ 质量报告（失败项、降级项、置信度分布）
```

### 4.1 显式公式定界符

| 形式 | 类型 | 备注 |
|---|---|---|
| `$$…$$` | 独立公式 | 允许跨行 |
| `\[ … \]`、`\( … \)` | 独立 / 行内 | |
| `\begin{equation}` `align` `gather` `eqnarray` `multline` `cases` `matrix` 等 | 独立公式 | 按环境名决定是否居中、是否拆行 |
| `$…$` | 行内公式 | 需防误判，见下 |

`$` 的歧义处理（货币 vs 公式）：满足任一即判为公式 —— 内容命中数学信号（`\`、`^`、`_`、`=`、希腊字母等）；或内容不含空白、不含纯数字金额形态；或紧邻字符是中文/标点而非数字。典型反例 `售价 $5 到 $10` 必须保持原样。

### 4.2 隐式公式识别（R2 的核心）

**打分信号**（正向）：

| 信号 | 权重 |
|---|---|
| 出现 LaTeX 命令（`\frac \sqrt \sum \int \alpha \cdot`…） | +5 |
| `^` / `_` 且前后是数学原子（字母/数字/右括号） | +3 |
| 关系符（`= \le \ge \approx \neq \equiv \propto \sim`）两侧为数学原子 | +3 |
| Unicode 数学符号（`α β ∫ ∑ √ ≈ ≤ ≥ ± × ÷ ∈ ∀ ∃ ∞ → ∂ ∇ °`） | +2 |
| Unicode 上下标写法（`x²`、`x₁`） | +3 |
| 函数调用形态（`f(x)`、`sin x`、`lim_{x→0}`、`log_2`、`\max`） | +3 |
| 数字与运算符混排（`a/b`、`3x`、`2n+1`、`1.5×10^-3`） | +2 |

**负向信号**：汉字与中文标点占比高、句末标点、URL/路径、日期、版本号（`v1.2`）、区间（`1-3`）、百分比、行内代码反引号、长度 > 120 字符。

**分级与阈值**：`score ≥ 6` 高置信（默认接受，无需点）、`3 ≤ score < 6` 中置信（默认待确认，需点一次）、`score < 3` 忽略。

**边界收敛（比打分更容易翻车的地方）**：以命中 token 为种子向两侧扩张，遇句读/空白+汉字/`，；：、`停；再修剪首尾标点；括号不配对则向内收缩；最后做语法体检（`^`/`_` 必须有操作数、`\cmd` 必须有参数），不合法就退到最近合法子区间。宁可少认，不可把半句话吃进公式。

**Unicode → LaTeX**：`α→\alpha`、`²→^2`、`₁→_1`、`√x→\sqrt{x}`、`×→\times`、`≤→\le`、`∑_{i=1}^{n}→\sum_{i=1}^{n}`、`∫→\int` 等，映射表独立成模块，便于加词条。

### 4.3 归一化常见坑

`\text{中文}`、`\mathrm / \mathbf / \mathbb`、`\left( \right)`、`\, \quad \qquad`、`\tag{1}`、`\\` 行内换行、`&` 对齐点、`\label`、宏定义 `\newcommand`（v1 不做展开，遇到则原样透传给 latex2mathml，失败则报告）。

### 4.4 降级策略

用户选的是纯 OMML 路线（不出图片）。因此某条公式转换失败时：**该条保留为带标记的原文**（如 `⟦公式转换失败: …⟧` 或保留原 LaTeX 并高亮），同时在质量报告里列出失败原因与行号，绝不静默丢内容。是否需要在失败时改用图片兜底，留作待确认项。

## 5. 文档中间表示（IR）—— 同时服务于 R4

```python
@dataclass
class Document:
    blocks: list[Block]
    options: ExportOptions
    source: str = "text"          # text | docx  ← R4 预留

@dataclass
class Block:
    kind: str                     # paragraph | heading | list_item | display_math | table(预留)
    inlines: list[Inline]
    level: int | None = None

# Inline = TextRun | MathNode
@dataclass
class TextRun:
    text: str; bold: bool = False; italic: bool = False; code: bool = False

@dataclass
class MathNode:
    latex: str
    display: bool
    origin: str                   # explicit | implicit
    confidence: float             # 显式公式恒为 1.0
    accepted: bool = True
    omml: str | None = None       # 转换结果缓存
    warnings: list[str]
    number: int | None = None     # 预留：公式编号（v1 不填）
    tag: str | None = None        # 预留：\tag{...} 原值
```

R4 预留的三个具体钩子：
1. `core/docx_reader.py` 定义 `read_docx(path) -> Document`，本期 `raise NotImplementedError`，README 写明实现路径。
2. 反向转换链已验证可行：`OMML → OMML2MML.XSL → MathML → (MathML→LaTeX)`，XSL 文件就在 Office 目录里，不需要重造。
3. 目录按 `core/io/` 归拢，新增格式不动其它模块；UI 上「打开 Word 文件」按钮位置先占位隐藏。

## 6. 交互设计

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LaTeX2Word   灵敏度[保守│标准│激进]  ☐解析Markdown  ⚙设置     [导出 Word]     │
├───────────────────────────────────┬──────────────────────────────────────────┤
│ ① 粘贴区                          │ ② 预览                                   │
│ 把含公式的文本贴到这里…            │ [原文视图 | 成稿视图]                     │
│                                   │ 质能方程 E=mc² 表明 …（KaTeX 渲染）       │
│ 支持 .txt 拖入                    │ 高亮 = 已识别公式，点编号可定位           │
├───────────────────────────────────┴──────────────────────────────────────────┤
│ ③ 公式清单（可折叠）： # │ 来源 │ 类型 │ 置信度 │ LaTeX │ [接受/忽略]          │
│    全部接受 · 全部忽略 · 只看待确认(3)                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

- 「⚙设置」面板承载全部排版参数：中文字体（默认宋体）、西文字体（默认 Times New Roman）、字号（默认小四 12pt）、行距（默认 1.5 倍）、首行缩进（默认 2 字符）、页边距与纸张（默认 A4 常规），设置项随导出一起提交，并可保存到本地（localStorage）供下次沿用。
- 每个候选都有稳定编号，预览高亮与清单双向联动。
- 三档灵敏度只改阈值，不改规则集：保守(高≥7/中≥5)、标准(6/3)、激进(5/2)。
- 导出前列出"待确认 N 条"提醒，允许直接导出（按当前状态）。
- 验收口径：公式清单里任意一条改状态，成稿预览立即变化。

## 7. 接口草案

| 方法 | 路径 | 入参 | 出参 |
|---|---|---|---|
| GET | `/api/health` | — | `{ok, engine, xsl_path, versions}` 引擎自检 |
| POST | `/api/analyze` | `{text, options}` | `{blocks, candidates, stats}` |
| POST | `/api/export` | `{document, options}` | `docx` 二进制（`Content-Disposition` 带文件名） |

无持久化、无账号、全程本机回环，端口默认 8765（被占用则自增）。

## 8. 目录与依赖

```
LaTeX2Word/
  docs/DESIGN.md          本文件
  docs/DETECTION_RULES.md 隐式识别规则表（实现时同步维护）
  app/…                   见第 3 节
  app/web/vendor/katex/   本地内置 KaTeX（离线可用，不引 CDN）
  samples/                样例输入（含隐式公式、矩阵、中文混排的坑点样本）
  tests/                  pytest：规则单测 + 端到端 docx 断言 + 公式语料回归
  requirements.txt
  start.cmd               建 .venv（用随附 Python 3.12）→ 装依赖 → 起服务 → 开浏览器
  README.md
```

依赖：`fastapi`、`uvicorn`、`python-docx`、`lxml`、`latex2mathml`；可选 `pypandoc-binary`（Office 缺失时的备用转换通道）。全部为纯 Python 或 wheel，无需编译器。

## 9. 里程碑

| 阶段 | 内容 | 判定标准 |
|---|---|---|
| M0 | 骨架 + IR + 引擎自检 + 冒烟 docx | `/api/health` 绿，能导出一个含 1 条 OMML 的 docx |
| M1 | 显式定界符全链路 | 50 条公式语料显式转换成功率 ≥ 95% |
| M2 | 隐式识别（打分+边界收敛+Unicode 映射） | 自建 20 段中文学术样张，召回 ≥ 90%，误报 ≤ 5% |
| M3 | 复核交互（高亮/清单/三档/一键操作） | 任意候选可单独接受或忽略，导出结果与勾选一致 |
| M4 | 排版与边界（矩阵、align、`\text{中文}`、行距缩进、设置面板） | 五个真实样例文档肉眼验收 |
| M5 | 质量报告、README、可选打包 exe | 新机器按 README 一次跑通 |

## 10. 决策落地与仍需确认的细节

已拍板（第 1 节决策表）：网页应用形态、OMML 原生公式、自动识别 + 选择性复核、Markdown 结构开关、v1 不做编号、排版全可配、单篇转换、失败保留原文。

实现时按以下默认值走，除非你另有指示（这些属于"我说了算也不影响架构"的量级，可开工后随时改）：

1. 端口 `8765`（占用自增）；`start.cmd` 用随附 Python 3.12 建 `.venv`，双击即用，无需管理员权限。
2. 灵敏度默认「标准」档；高置信自动接受、中置信待确认、低置信忽略。
3. 排版默认值：中文宋体 12pt / 西文 Times New Roman / 行距 1.5 / 首行缩进 2 字符 / A4 常规页边距；全部可在设置面板改。
4. 导出文件名默认取粘贴内容首行截断，或固定 `output.docx` 后由浏览器另存。
5. 公式转换失败时保留原文并加高亮，质量报告按段落号定位（不降级为图片）。

## 11. 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| latex2mathml 对部分 LaTeX 支持不全 | 少数公式失败 | 先跑语料摸清覆盖边界；对高频缺口做预处理；必要时接 pandoc 兜底 |
| 隐式识别误报（把普通文字吃成公式） | 文档出错，比漏认更难受 | 阈值偏保守 + 边界收敛 + 逐条可撤销 + 默认中置信需确认 |
| `$` 金额歧义 | 财务类文本刷错 | 上下文规则 + 语料回归用例锁定 |
| 目标机器没有 Office（XSL 缺失） | 无法生成 OMML | 启动即自检并给出明确提示；提供 pandoc 备用通道 |
| 中英混排 + 公式的行距不齐 | 观感差 | 段落行距用"多倍行距 + 固定网格关闭"，专项调参 |
| KaTeX 预览与 Word 渲染有细微差异 | 用户预期落差 | UI 明确标注"近似预览"，最终以 docx 为准 |
