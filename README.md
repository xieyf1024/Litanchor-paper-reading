# LitAnchor 文锚

> Anchor every insight to the source.

LitAnchor 是一个面向研究生的轻量化、证据优先型学术精读 Skill。它计划从 Zotero 获取用户指定的单篇论文，以论文原文为唯一事实来源，生成带页码和证据映射的中文 Obsidian 笔记。

**当前状态：v0.1 设计与测试骨架。** 本版本提供可安装的 Skill 指令、笔记模板、JSON Schema、产品文档和评测框架；尚未实现或安装 Zotero 适配器、PDF 解析器、Obsidian 自动写入器及 MinerU。

## 核心约束

- 只依据用户提供的论文原文；原文没有说明时明确写“原文未说明”。
- 不把讨论、解释、假设或推测升级为确定事实。
- 所有事实性主张必须绑定原文页码与 Evidence ID。
- 准确保留数值、单位、变量、范围和适用条件。
- 解析失败必须显式报告；阻断级校验失败时禁止正式导出。
- Zotero 默认只读；Obsidian 仅写入用户明确授权的目录，且默认禁止覆盖。

## 仓库结构

```text
.
├── skills/litanchor-paper-reading/  # 可安装 Skill
├── docs/                            # 产品、流程、数据与集成规格
├── evals/                           # 本地 PDF 评测清单与标注规范
├── tests/                           # 无外部依赖的骨架契约测试
├── Paper Template.md                # 项目作者的原始模板
└── 科研文献入门.md                   # 项目作者的原始阅读方法
```

测试论文保存在本地 `Test-PDF/`，已被 `.gitignore` 排除，不随公开仓库分发。

## 安装 Skill

将 `skills/litanchor-paper-reading/` 整个目录复制到 Codex 的 Skills 目录，例如：

```text
%CODEX_HOME%\skills\litanchor-paper-reading
```

然后使用类似请求触发：

```text
使用 LitAnchor 精读 Zotero 中的「论文标题或 citekey」，按 deep 模式准备 Obsidian 笔记。
```

当前版本会先检查可用输入和工具；缺少 Zotero/PDF/写入能力时必须报告缺口，不得假装闭环已经完成。

## 第一阶段边界

本轮不安装软件、不访问真实 Zotero 库、不写入测试或正式 Obsidian Vault、不批量处理论文、不启用 OCR 或 MinerU，也不自动修改正式 Skill。下一阶段的目标是先跑通手动 PDF 到可追溯 Markdown 的最小闭环，再接入只读 Zotero 和受限 Obsidian Inbox。

详细规格见 [docs/PRODUCT.md](docs/PRODUCT.md)、[docs/WORKFLOW.md](docs/WORKFLOW.md)、[docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md)、[docs/EVALUATION.md](docs/EVALUATION.md) 和 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

## License

[MIT](LICENSE)。参考项目、许可证和借鉴边界见 [THIRD_PARTY.md](THIRD_PARTY.md)。

