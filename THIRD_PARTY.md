# Third-party references

除下方单列的 `pypdf` 外，本项目当前没有复制、修改或打包设计参考项目的代码，也没有把它们声明为运行时依赖。下表记录截至 2026-07-22 的判断；真正引入其他依赖前必须重新核实许可证和版本。

## Runtime dependency

| 项目 | 版本范围 | 许可证 | 用途 |
|---|---|---|---|
| [pypdf](https://github.com/py-pdf/pypdf) | `>=6.0,<7.0` | BSD-3-Clause | 单篇本地 PDF 的有效性检查、物理页文本提取与元数据读取 |

`pypdf` 由用户环境按 `requirements.txt` 安装；本仓库不复制或打包其源码。

## Design references

| 项目 | 当前许可证判断 | 仅借鉴的设计思路 | 当前使用方式 |
|---|---|---|---|
| [Zotero Analytical Workflow Skills](https://github.com/cheneternity/Zotero-Analytical-Workflow-Skills) | 仓库页面未发现明确许可证；按未授权代码处理 | 获取、分析、写入分层；原始语料先缓存；公式乱码阻断 | 只借鉴抽象思路，不复制代码或模板 |
| [Obsidian Zotero Integration](https://github.com/obsidian-community/obsidian-zotero-integration) | GPL-3.0 | citekey、Frontmatter、Zotero 跳转链接与模板兼容 | 不作为依赖，不复制代码 |
| [Zotero Bridge](https://github.com/vanakat/zotero-bridge) | MIT | Zotero 7 Local API 抽象、标准化元数据对象 | 只作为后续适配器研究资料 |
| [Zotero MCP](https://github.com/54yyyu/zotero-mcp) | MIT | 搜索、元数据、全文、批注、citekey 和只读访问 | 后续可选集成；本版本未安装、未打包 |
| [paper-notes](https://github.com/ZinSheng/paper-notes) | MIT | evidence-first、解析失败阻断、运行产物分离、用户编辑优先 | 只借鉴工作流原则，不复制实现 |
| [MinerU](https://github.com/opendatalab/MinerU) | MinerU Open Source License，基于 Apache-2.0 且含附加条件 | 复杂 PDF、OCR、公式和表格解析的可选后备层 | 本版本不安装、不依赖；引入前重新审查条款 |

## Project-authored source material

- `Paper Template.md`：项目作者提供的原始文献精读模板。
- `科研文献入门.md`：项目作者提供的原始阅读方法笔记。

可安装 Skill 中的 `assets/paper-note.md` 与 `references/reading-method.md` 是对以上材料的精简整理，并遵循本仓库 MIT License。
