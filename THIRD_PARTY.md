# Third-party references

本项目不复制、修改或打包下列设计参考项目的代码。运行依赖由用户环境按对应 requirements 文件安装，仓库不重新分发其源码。下表记录截至 2026-08-01 的项目判断；版本、许可证和服务政策在真正升级或引入前必须重新核实。本文件不是法律意见。

## Runtime dependency

| 项目 | 版本范围 | 许可证 | 用途 |
|---|---|---|---|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | `>=1.26`；开发环境核验版本 `1.28.0` | GNU AGPL v3 或 Artifex 商业许可的双重许可 | 本地 PDF 预检、物理页文本/坐标、页面渲染、关键图裁剪、页面子集与最终证据核验 |
| [MinerU Open SDK](https://github.com/opendatalab/MinerU-Ecosystem) | 可选依赖 `>=0.2.5`；开发环境核验版本 `0.2.5` | Apache-2.0（官方生态仓库） | 按本地持久授权自动调用无需 Token 的 Flash/Quick Parse 云端接口，辅助恢复标题、阅读顺序和图题 |
| [PyYAML](https://github.com/yaml/pyyaml) | 开发依赖 `>=6.0` | MIT | 在 CI 和发布审计中验证 Skill YAML；不进入默认运行环境 |

三类依赖文件有意分开：`requirements.txt` 只含核心本地依赖，`requirements-mineru.txt` 只在用户启用 MinerU 时安装，`requirements-dev.txt` 仅供测试与发布验证。所有依赖采用最低版本、不设置人为最高版本；CI、`doctor` 与升级流程负责发现新版本兼容性问题。

开发环境中 PyMuPDF `COPYING` 文件的首行许可声明已人工核对。LitAnchor 当前以 `AGPL-3.0-only` 发布，并把 PyMuPDF 作为未修改的 Python 依赖使用。不能或不愿遵守 AGPL 的使用者应自行评估 Artifex 商业许可。

## Design references

| 项目 | 当前许可证判断 | 仅借鉴的设计思路 | 当前使用方式 |
|---|---|---|---|
| [Zotero Analytical Workflow Skills](https://github.com/cheneternity/Zotero-Analytical-Workflow-Skills) | 仓库页面未发现明确许可证；按未授权代码处理 | 获取、分析、写入分层；原始语料先缓存；公式乱码阻断 | 只借鉴抽象思路，不复制代码或模板 |
| [Obsidian Zotero Integration](https://github.com/obsidian-community/obsidian-zotero-integration) | GPL-3.0 | citekey、Frontmatter、Zotero 跳转链接与模板兼容 | 不作为依赖，不复制代码 |
| [Zotero Bridge](https://github.com/vanakat/zotero-bridge) | MIT | Zotero 7 Local API 抽象、标准化元数据对象 | 只作为后续适配器研究资料 |
| [Zotero MCP](https://github.com/54yyyu/zotero-mcp) | MIT | 搜索、元数据、全文、批注、citekey 和只读访问 | 仅作为调研对照；LitAnchor 采用 Zotero Local API，不提供此适配器 |
| [paper-notes](https://github.com/ZinSheng/paper-notes) | MIT | evidence-first、解析失败阻断、运行产物分离、用户编辑优先 | 只借鉴工作流原则，不复制实现 |
| [llm-for-zotero](https://github.com/yilewang/llm-for-zotero) | AGPL-3.0 | 原始文本与结构化文本双通道；结构工具定位、原 PDF 提供最终视觉证据 | 只借鉴架构并独立实现，不复制代码 |
| [nature-paper-card](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-paper-card) | Apache-2.0 | 简洁的双语 Skill 展示、论文类型路由、来源标签和结构定位降级 | 只借鉴公开设计模式；LitAnchor 保留独立实现、Schema 与可靠性边界 |
| [MinerU](https://github.com/opendatalab/MinerU) | 仓库与云端 SDK/服务应分别复核 | 复杂版面、OCR、公式、表格和图题的可选结构增强层 | v0.6 已验证整篇与保留页码子集路由；仅在同意后上传，并重新对齐原 PDF |

MinerU 免费 Agent/Flash 接口的可用性、文件限制、限流和表格/公式能力由外部服务控制，不属于 LitAnchor 的稳定承诺。当前适配器强制执行 10 MiB、20 页限制，不读取 Token，并保存请求、响应、隐私回执与对齐产物。MinerU 输出不能直接成为正式证据；正式页码、引文和视觉对象必须回到原 PDF 核验。

## Project-authored source material

可安装 Skill 中的公开内容契约 `assets/Paper Template.md`、内部渲染资产
`assets/Paper Template - Runtime.md` 与
`references/reading-method.md` 由项目作者整理并遵循本仓库
AGPL-3.0-only 许可。`reading-method.md` 是可选学习方法，不构成外部权威
或论文事实来源。
