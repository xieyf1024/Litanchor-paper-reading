# Documentation

本目录保存当前版本的公共产品与工程契约。旧版本实现细节由 Git Tag、GitHub Release 和根目录 `CHANGELOG.md` 保存，不在当前文档树重复维护。

## Start here

| 文档 | 回答的问题 |
|---|---|
| [PRODUCT.md](PRODUCT.md) | LitAnchor 为谁解决什么问题，当前支持边界是什么？ |
| [INSTALLATION_REQUIREMENTS.md](INSTALLATION_REQUIREMENTS.md) | 安装需要哪些本机能力，版本兼容策略是什么？ |
| [WORKFLOW.md](WORKFLOW.md) | Zotero 到 Obsidian 的端到端流程如何运行？ |
| [INTEGRATIONS.md](INTEGRATIONS.md) | Zotero、PyMuPDF、MinerU 和 Obsidian 如何分工？ |
| [DATA_SCHEMA.md](DATA_SCHEMA.md) | Evidence、Claim、Review 和 NotePackage 如何表示？ |
| [EVALUATION.md](EVALUATION.md) | 如何验证忠实度、召回、页码和失败检测？ |
| [ROADMAP.md](ROADMAP.md) | Public Beta 如何走向稳定公开发行？ |
| [v0.6-stabilization-checklist.md](v0.6-stabilization-checklist.md) | beta.1 到 beta.2 的历史稳定化记录 |

## Release and trust

| 文档 | 用途 |
|---|---|
| [RELEASE_NOTES_v0.6.0-beta.1.md](RELEASE_NOTES_v0.6.0-beta.1.md) | 上一个 Public Beta 的历史能力、限制和升级说明 |
| [RELEASE_NOTES_v0.6.0-beta.2.md](RELEASE_NOTES_v0.6.0-beta.2.md) | 上一 Public Beta 的稳定化、兼容策略与发布边界 |
| [RELEASE_NOTES_v0.6.0-beta.3.md](RELEASE_NOTES_v0.6.0-beta.3.md) | 当前 Note Experience 与 Paper Template v1.0 冻结内容及发布边界 |
| [release-checklist.md](release-checklist.md) | 发布门与完成记录 |
| [anti-leak-audit.md](anti-leak-audit.md) | 测试论文答案、私有运行数据和 Skill 的隔离检查 |
| [v0.5-final-validation.md](v0.5-final-validation.md) | 首个自主全文精读稳定基线的历史验证 |

旧版本 Release Notes 作为已发布版本的审计记录保留，但不再作为当前操作说明。开发或测试时以当前代码、`README.md` 和上表中的现行契约为准。
