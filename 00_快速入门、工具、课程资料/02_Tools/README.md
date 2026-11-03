# 自研工具

> 为解决具体问题写的小工具，每个都是独立项目，各自带 README。

这些工具不依赖任何赛项，谁都能拿来用。

## 工具列表

| 工具 | 解决什么问题 | 技术栈 |
| --- | --- | --- |
| [LaTeX2Word](LaTeX2Word/README.md) | 把带 LaTeX 公式的文本转成 Word 原生公式（OMML），公式在 Word 里还能继续编辑 | Python · FastAPI · KaTeX |

## 新增一个工具

1. 在本目录下建独立子目录，用工具名命名（如 `LaTeX2Word`）；
2. 目录内必须有 `README.md`，写清楚：**解决什么问题 / 环境要求 / 如何运行**；
3. 带上自己的 `.gitignore`，**不要提交虚拟环境**：
   - Python：`.venv/`、`__pycache__/`、`*.pyc`、`.pytest_cache/`
   - Node：`node_modules/`
   - 构建产物：`out/`、`dist/`、`build/`
4. 依赖清单单独成文件（`requirements.txt`、`package.json`），别把环境一起打包；
5. 在上面那张表里加一行。

> 根目录的 `.gitignore` 已经统一排除 `.venv/`、`__pycache__/`、`*.pyc` 等，
> 但项目内再放一份更稳妥——别人单独拷走这个目录时也能生效。
