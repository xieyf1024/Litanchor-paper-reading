# LitAnchor 文锚

> Anchor every insight to the source.

LitAnchor 是一个面向研究生的轻量化、证据优先型学术精读 Skill。它计划从 Zotero 获取用户指定的单篇论文，以论文原文为唯一事实来源，生成带页码和证据映射的中文 Obsidian 笔记。

**当前状态：v0.4 PDF 证据与关键图像阶段。** 本版本保留 Zotero Local API 只读接入和受限 Obsidian 导出，增加 PyMuPDF 原 PDF 图像裁剪、图像来源清单、首作者笔记属性、复杂标点标题回退查询，以及 AI 辅助参考标准与人工金标准的明确分层。MinerU 被设计为需要用户同意的可选结构增强层，本阶段没有上传论文，也不安装 Zotero MCP、Obsidian 插件或 OCR 模型。

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
├── tests/                           # 契约与本地流水线回归测试
├── requirements.txt                # 当前 PDF 依赖：pypdf + PyMuPDF
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

当前版本会先检查可用输入和工具；缺少 Zotero 或写入能力时必须报告缺口，不得假装已经连接。

## 手动 PDF 最小闭环

建议在本项目的 D 盘目录中创建隔离环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

预检并提取一篇论文：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\litanchor_local.py prepare "Test-PDF\paper.pdf" --output-root "runtime\runs" --mode deep
```

Skill 依据生成的 `source-bundle.json` 填充该运行目录中的 `evidence.json` 和 `claims.json`。随后生成预览：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\litanchor_local.py build "runtime\runs\<run-id>"
```

产物保存在被 Git 忽略的 `runtime/`。`build` 会阻断错误页码、无法在原页找到的引文、数值/单位不一致、语义校验失败和文件覆盖。

从原 PDF 裁剪一张已核对的关键图：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\pdf_figures.py "paper.pdf" `
  --page 3 --label "Figure 1" --output "runtime\figures\figure-1.png"
```

该命令只接受一基物理页码，默认拒绝覆盖，并为 PNG 生成包含原 PDF 哈希、页码、图题、裁剪框和输出哈希的 JSON 清单。自动定位失败时应先查看原页，再显式给出 `--bbox`；不得猜测裁剪范围。

## Zotero Local API 与测试 Inbox

Zotero 桌面端开启 Local API 后，可以先检查连接，再按一个精确选择器准备论文：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\zotero_local.py check
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\zotero_local.py prepare --title "Exact paper title" --output-root "runtime\runs" --mode deep
```

适配器仅访问回环地址、仅发送 `GET`，并要求唯一书目匹配与唯一 PDF 附件。完成证据/主张账本并执行 `build` 后，使用显式授权参数导出：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\export_obsidian.py "runtime\runs\<run-id>" `
  --allowed-root "D:\path\to\LitAnchor-Test" `
  --inbox "D:\path\to\LitAnchor-Test\00_Inbox" `
  --confirm-export
```

警告状态还必须显式添加 `--allow-warnings`。导出前会验证 Markdown 哈希、Inbox 路径包含关系、侧车文件和目标碰撞；现有文件不会被覆盖。

## 当前阶段边界

当前实现只支持本机 Zotero Local API 与用户明确授权的测试目录。它不修改 Zotero，不写正式 Vault 的其他位置，不提供 Zotero→Obsidian 反向链接或双向同步，不批量处理论文，也不启用 OCR 或 Zotero MCP。PyMuPDF 提供权威页码、原文定位和原 PDF 图像；MinerU 只作为未来可选的结构增强通道，其输出必须重新对齐原 PDF，且调用云端服务前必须取得用户对该文档的明确同意。

详细规格见 [docs/PRODUCT.md](docs/PRODUCT.md)、[docs/WORKFLOW.md](docs/WORKFLOW.md)、[docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md)、[docs/EVALUATION.md](docs/EVALUATION.md) 和 [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md)。

## License

[GNU Affero General Public License v3.0 only](LICENSE)。选择 AGPL-3.0-only 是为了在开源分发中与 PyMuPDF 的 AGPL 许可路径保持清晰兼容。若未来改为闭源或不愿遵守 AGPL，应重新评估并向 Artifex 获取适当许可。第三方依赖、许可证和借鉴边界见 [THIRD_PARTY.md](THIRD_PARTY.md)，显著告知见 [NOTICE.md](NOTICE.md)。
