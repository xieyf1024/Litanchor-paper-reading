# Product definition

## Summary

LitAnchor（文锚）是一个面向研究生的轻量化、证据优先型学术精读 Skill。用户指定一篇 Zotero 文献或提供单篇 PDF 后，LitAnchor 只依据该论文原文，按固定流程生成可追溯的中文 Obsidian Markdown 笔记。

## Product promise

LitAnchor 不承诺替代阅读全文，也不判断论文结论在学界是否正确。它承诺让正式笔记中的重要事实能够回到原文，并在无法可靠处理时明确失败。

质量优先级固定为：

```text
忠实性 > 可追溯性 > 关键信息完整性 > 结构清晰度 > 阅读效率 > 表达流畅度
```

## Target users and jobs

- 阅读英文论文的研究生新生与跨专业科研学习者。
- 使用 Zotero 管理文献、使用 Obsidian 沉淀知识的研究人员。
- 核心任务：指定一篇论文，获得结构清晰、证据可回溯、可安全存档的中文笔记。

## Modes

| 模式 | 目的 | 必须覆盖 |
|---|---|---|
| `skim` | 判断论文主题、方法与是否值得精读 | 骨架、问题、方法概览、主要结果与结论 |
| `deep` | 默认的研究生级精读 | 背景、空白、数据、方法、指标、关键公式与图表、结果、讨论、局限性、结论 |
| `internalize` | 在 `deep` 结果上支持学习迁移 | 125 学习法、写作表达、可追踪参考文献、待研究问题；所有启发与原文事实分层 |

## Scope

### v0.1：本轮交付

- 可安装 Skill 指令与 UI 元数据。
- 可靠性、工作流、集成、阅读方法和受控进化参考。
- Obsidian 笔记、校验报告、失败报告模板。
- SourceBundle、EvidenceUnit、ClaimRecord、NotePackage、FeedbackEvent JSON Schema。
- 产品文档、测试语料清单和无外部依赖的契约测试。

v0.1 是设计与测试骨架，不宣称已经跑通 Zotero、PDF 解析或 Obsidian 自动写入。

### MVP：后续最小运行闭环

```text
单篇手动 PDF
→ 页面级预检与提取
→ 证据单元
→ 主张账本
→ 中文 Markdown
→ 确定性与语义校验
→ 用户预览
→ 测试 Inbox 安全写入
```

在该闭环稳定后，再加入 Zotero 只读访问与页面跳转链接。

### Later

- Zotero 标题、citekey、DOI 和 Item Key 搜索。
- Zotero 原生批注、附件 Key 与 Local API/MCP 接入。
- 扫描件 OCR、复杂表格、公式识别与可选 MinerU 后备层。
- 多论文比较、文献矩阵和 Agent 调度。

## Non-goals

- 不默认部署数据库、向量库、嵌入模型或长期后台服务。
- 不进行全文逐段翻译、开放式网络补全或论文外知识混写。
- 不自动判断论文真假或综合质量。
- 不在首版开发 Obsidian 插件、批量处理或知识图谱。
- 不修改 Zotero 条目，不覆盖既有 Obsidian 笔记。
- 不在运行中自动改写或发布正式 Skill。

## Release gates for a runnable version

- 核心事实证据覆盖率 100%，严重不受支持主张为 0。
- 页码准确率至少 99%，核心数值错误为 0。
- 阻断级解析失败检测率 100%。
- 正式导出的 YAML/Markdown 通过率 100%。
- 用户编辑区域保留，重名文件默认阻断。

