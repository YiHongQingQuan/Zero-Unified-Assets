# Zero-Unified-Assets

> 按赛项归档的技术资产仓库 —— 代码、脚本与踩坑记录，留给下一届。

## 这是什么

一个按「赛项 / 课程」分目录归档的仓库。每个子目录是一个独立项目，各自带一份 README，
说明它做了什么、依赖什么、怎么跑起来、有哪些已知问题。

仓库本身**不是**某个项目的工程目录，而是多届、多赛项的集合，所以没有统一的构建方式 ——
先进到具体项目目录，再看它的 README。

## 目录结构

```
Zero-Unified-Assets/
├── 00_课程资料/                      课程作业与学习资料
├── 01_CCCC/                          CCCC 赛项
│   └── 2025_Unity_ExhibitionHall/       2025 · Unity 航天文化馆 AI 虚拟展馆
├── 02_GPLT/                          GPLT 赛项（待补充）
├── 03_MathematicalModeling/          数学建模（待补充）
├── 04_Astar/                         A* 算法相关（待补充）
├── LICENSE                           MIT，适用于全仓库
├── .gitignore                        Unity 工程与密钥的通用忽略规则
└── .gitattributes                    换行符与二进制文件的统一约定
```

目录命名约定：`NN_赛项简称/YYYY_项目名/`。`NN` 用于控制排序，年份前缀用于区分届次。

空的预留目录里放了 `.gitkeep`，否则 git 不会保存空文件夹。

## 现有项目

| 目录 | 赛项 | 年份 | 技术栈 | 内容 |
| --- | --- | --- | --- | --- |
| [01_CCCC/2025_Unity_ExhibitionHall](01_CCCC/2025_Unity_ExhibitionHall/README.md) | CCCC | 2025 | Unity · C# · DeepSeek API · 百度语音 | 航天文化馆 AI 虚拟展馆：语音问答、空间站拆解、拼图、自由漫游 |

## 怎么用

1. 按上表进入感兴趣的项目目录；
2. 读该目录的 `README.md` —— 「快速开始」写环境与导入方式，「脚本索引」列出每个脚本的职责与要绑定的方法；
3. 手上已有旧版场景、想把脚本升级到最新版的，读同目录的 `MIGRATION.md`。

## 新增一个项目

1. 建目录 `NN_赛项简称/YYYY_项目名/`；
2. 里面至少放一份 `README.md`：做了什么 / 环境要求 / 如何运行 / 已知问题；
3. 只提交源码与文档，构建产物交给 `.gitignore`；
4. 密钥、账号、个人信息一律不进仓库（见下一节）。

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
