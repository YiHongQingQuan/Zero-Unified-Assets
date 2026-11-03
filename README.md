# Zero-Unified-Assets

> 按赛项归档的技术资产仓库

## 关于 Zero-Unified-Assets

一个按「赛项 / 课程」分目录归档的仓库。每个子目录是一个独立项目，各自带一份 README，
说明它做了什么、依赖什么、怎么跑起来、有哪些已知问题。

仓库本身**不是**某个项目的工程目录，而是多届、多赛项的集合，所以没有统一的构建方式 ——
先进到具体项目目录，再看它的 README。

## 目录结构

```
Zero-Unified-Assets/
├── 00_快速入门、工具、课程资料/      入门指引、自研工具、课程资料
│   ├── 01_Getting-Started/             环境搭建与常用命令
│   ├── 02_Tools/LaTeX2Word/            LaTeX 公式转 Word 的本地工具
│   └── 03_Courses/                     课程习题与专题训练
├── 01_CCCC/                          计算机设计大赛
│   └── 2025_Unity_ExhibitionHall/       2025 · Unity 航天文化馆 AI 虚拟展馆
├── 02_GPLT/                          团体程序设计天梯赛
├── 03_MathematicalModeling/          数学建模
├── 04_Astar/                         百度之星
├── LICENSE                           MIT，适用于全仓库
├── .gitignore                        各项目通用的忽略规则（Unity / Python / 密钥）
└── .gitattributes                    换行符与二进制文件的统一约定
```

目录命名约定：`NN_大类/YYYY_项目名/`。`NN` 用于控制排序，年份前缀用于区分届次。
`00_` 留给跨赛项的通用内容（入门指引、工具、课程资料），`01_` 之后按赛事编号。

空的预留目录里放了 `.gitkeep`，否则 git 不会保存空文件夹。

## 现有项目

| 目录 | 类别 | 年份 | 技术栈 | 内容 |
| --- | --- | --- | --- | --- |
| [00_快速入门、工具、课程资料/02_Tools/LaTeX2Word](00_快速入门、工具、课程资料/02_Tools/LaTeX2Word/README.md) | 自研工具 | — | Python · FastAPI · KaTeX | 把 LaTeX 公式批量转成 Word 文档的本地工具，带浏览器界面 |
| [00_快速入门、工具、课程资料/03_Courses](00_快速入门、工具、课程资料/03_Courses) | 课程资料 | — | — | 高等数学、复变函数与积分变换的专题训练与解析 |
| [01_CCCC/2025_Unity_ExhibitionHall](01_CCCC/2025_Unity_ExhibitionHall/README.md) | 计算机设计大赛 | 2025 | Unity · C# · DeepSeek API · 百度语音 | 航天文化馆 AI 虚拟展馆：语音问答、空间站拆解、拼图、自由漫游 |

## 怎么用

**第一次来，先看 `00_快速入门、工具、课程资料`** —— 里面是环境搭建、常用命令和课题资料，与具体赛项无关。

然后按上表进入感兴趣的项目目录，读它自己的 `README.md`：

- 「快速开始」写环境与导入方式
- 「脚本索引」列出每个文件的职责与要绑定的方法
- 手上已有旧版场景、想升级脚本的，读同目录的 `MIGRATION.md`

## 新增一个项目

1. 建目录 `NN_大类/YYYY_项目名/`；
2. 里面至少放一份 `README.md`：做了什么 / 环境要求 / 如何运行 / 已知问题；
3. 只提交源码与文档，构建产物交给 `.gitignore`；
4. 密钥、账号、个人信息一律不进仓库（见下一节）。

### 关于自研工具

`00_快速入门、工具、课程资料/02_Tools/` 下的工具是独立的小项目，各自带 `.gitignore`。

**Python 项目千万不要提交虚拟环境**：`.venv/` 里通常有几千个文件、几十 MB，
提交后仓库会瞬间膨胀且无法通过删除文件瘦身（历史里永久保留）。
根 `.gitignore` 已统一排除 `.venv/`、`__pycache__/`、`*.pyc`、`.pytest_cache/`，
项目内再放一份 `.gitignore` 兜底更稳妥。

## 密钥与隐私

仓库是公开的，只放代码。API Key 统一放在项目内的 `Assets/StreamingAssets/api-config.json`，
由 `.gitignore` 排除，仓库里只保留 `api-config.example.json` 模板。

提交前自查：

```bash
git grep -n -i -E 'apiKey|client_secret|sk-[a-zA-Z0-9]{16,}|"secret"' -- . ':!*example*'
```

结果为空再提交。误传过的密钥请到服务商后台**吊销并重新生成**，删文件是救不回 git 历史的。

## 许可证

[MIT](LICENSE)
