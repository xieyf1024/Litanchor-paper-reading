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

### v0.4：当前交付

- 保留 v0.3 的 Zotero Local API、页码链接和受限 Obsidian 导出闭环。
- 将 PyMuPDF 加入本地 PDF 证据层，用原 PDF 渲染和裁剪关键图像，并为图像保存来源清单。
- 笔记属性只显示第一作者；完整作者列表继续保存在 SourceBundle。
- Zotero 标题查询可用去标点前缀重试，但最终仍要求规范化标题完全一致。
- 三篇现有精读笔记被定位为“AI 辅助参考标准”，用于形成标注规范；未经独立人工复核不得称为金标准。
- MinerU 与 PyMuPDF 采用协作设计：MinerU 未来只做经同意的结构增强，PyMuPDF 和原 PDF 负责最终页码、引文与视觉证据。
- 不安装 Zotero MCP、Obsidian 插件、OCR 模型或后台服务。

语义证据提取与忠实度审查仍由调用 Skill 的模型完成；脚本只验证结构化声明，不能替代人工金标准。

### v0.3：已完成本地集成闭环

- 保留 v0.2 的手动 PDF、证据账本、主张账本、校验与预览能力。
- 使用 Zotero Local API v3，按标题、DOI、citekey 或 Item Key 唯一解析单篇论文。
- 仅通过回环地址和 `GET` 读取元数据、PDF 附件 Key 与本地附件路径。
- 在正文生成经验证的 `zotero://open-pdf/...?...page=` 物理页链接。
- 仅向显式授权测试根目录下的 Inbox 写入，不覆盖笔记或侧车。
- 导出前验证 Markdown SHA-256、校验状态、路径包含关系、警告接受与碰撞。
- 不新增 Python 运行依赖、MCP 服务、Obsidian 插件或后台进程。

### v0.2：已完成本地最小闭环

- v0.1 的可安装 Skill、UI 元数据、模板、Schema、文档与评测骨架。
- 单篇手动 PDF 的有效性检查、物理页提取、文件哈希和原生文本覆盖率判断。
- 私有运行目录中的 SourceBundle、Evidence/Claim 账本和运行记录。
- 页码、引文回溯、Evidence ID、数值、单位与基础结构的确定性校验。
- 仅从已校验账本生成、不覆盖既有文件的 Markdown 预览。
- 合成空白/损坏 PDF 的负向回归测试和一篇真实论文的纵向冒烟测试。

### v0.1：已完成基础

- 可安装 Skill 指令与 UI 元数据。
- 可靠性、工作流、集成、阅读方法和受控进化参考。
- Obsidian 笔记、校验报告、失败报告模板。
- SourceBundle、EvidenceUnit、ClaimRecord、NotePackage、FeedbackEvent JSON Schema。
- 产品文档、测试语料清单和无外部依赖的契约测试。

v0.1 是设计与测试骨架，不宣称已经跑通 Zotero、PDF 解析或 Obsidian 自动写入。

### MVP：当前剩余验证

```text
单篇手动 PDF 或 Zotero Local API（已完成）
→ 页面级预检与提取（已完成）
→ 证据单元与主张账本（已完成结构化运行路径）
→ 中文 Markdown 与确定性校验（已完成）
→ 测试 Inbox 安全写入（已完成集成冒烟测试）
→ 多论文金标准与完整语义评测（待完成）
```

v0.4 证明了工程闭环、原 PDF 关键图像导出和六篇 Zotero 语料解析，但尚未达到 PRODUCT/EVALUATION 中面向发布的多论文人工金标准门槛。

### Later

- Zotero 原生批注读取增强；Zotero MCP 不纳入项目运行路线。
- Zotero→Obsidian 反向链接；只有明确开启 Zotero 写权限后才考虑，且不属于轻量 MVP。
- 扫描件 OCR、复杂表格、公式识别与需明确同意的 MinerU 结构增强层；不采用 MinerU 付费精准解析 API。
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
