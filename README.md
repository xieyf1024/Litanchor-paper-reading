# LitAnchor 文锚

> Anchor every insight to the source.

LitAnchor 是一个面向研究生的轻量化、证据优先型学术精读 Skill。它从 Zotero 获取用户指定的单篇论文，以论文原文为唯一事实来源，生成带页码和证据映射的中文 Obsidian 笔记。

**当前发布版：v0.5.0 Autonomous Deep Reading。** 这是 Windows 优先的稳定开发者预览 / Early Public Beta。Zotero、PDF 物理页、证据追踪、关键图裁剪、受限 Obsidian 导出和自主全文精读已经形成可审计闭环。ResNet、LOVECLIM 和气候 U-Net 示例继续作为明确标记的人工辅助回归产物，不计入自主评测。

**当前公开测试版：v0.6.0-beta.1 Zero-Config Public Beta。** 该版本把安装、首次配置、诊断和安全生命周期隐藏到 Agent 后面；面向愿意使用本地 Agent、Zotero 与 Obsidian 的早期用户。

v0.5.0 跑通单篇自主深读闭环：冻结无参考答案输入，用 PyMuPDF 建立权威页级工作包，按论文类型执行六遍全文阅读，按本地授权策略调用 MinerU Flash 并融合非权威结构提示，先生成 Evidence/Claim Ledger，再生成 SectionSynthesis、关键视觉分析、独立忠实度/召回审查和 Final 模板笔记。官方六篇评测共覆盖 81 个物理页、182 条 EvidenceUnit、155 条 ClaimRecord 与 15 张关键图，所有确定性质量指标均为 1.0、无 Blocker；三篇额外跨领域论文通过泛化冒烟测试和用户验收；最后一篇完全未见论文也在冻结工作流下通过量化发布门，未触发严重忠实度错误。

本轮数据与发布边界见 [v0.5 final validation](docs/v0.5-final-validation.md)、[cross-paper metrics](evals/cross-paper-metrics.json)、[failure taxonomy](evals/failure-taxonomy.md) 和 [release checklist](docs/release-checklist.md)。人工辅助示例仍见 [examples/v0.4.1](examples/v0.4.1/)。

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
├── examples/v0.4.1/                 # 明确标记为非自主生成的回归示例
├── tests/                           # 契约与本地流水线回归测试
├── requirements.txt                # 当前 PDF 依赖：pypdf + PyMuPDF
├── Paper Template.md                # 项目作者的原始模板
└── 科研文献入门.md                   # 项目作者的原始阅读方法
```

测试论文保存在本地 `Test-PDF/`，已被 `.gitignore` 排除，不随公开仓库分发。

## 适用环境与依赖

当前发布版面向已经具备基础本地环境的用户：

- Windows 10/11 x64；
- 能执行本地 Shell、读写授权目录并下载 GitHub Release 的 Agent，例如 Codex Desktop/CLI；
- Python 3.10 或更高版本 x64，包含 `pip` 和 `venv`；当前 CI 覆盖
  3.10–3.14，更新版本先通过依赖与 doctor 探测；
- Zotero 7 或更高版本桌面端，已允许本机应用通信，目标条目具有本地
  PDF 附件；不设置武断的最高版本；
- Obsidian Desktop 1.x 和一个本地文件系统 Vault；
- 能访问 GitHub、Python 包索引，以及在用户允许时访问 MinerU 的网络环境。

核心 Python 依赖只有 `pypdf>=6.0,<7.0` 与 `PyMuPDF>=1.26,<2.0`。符合条件的 PDF 如需启用 MinerU 结构增强，再安装 `mineru-open-sdk>=0.2.5,<0.3`。完整的必需条件、可选依赖、本地配置和 v0.6 轻量安装目标见 [Installation requirements](docs/INSTALLATION_REQUIREMENTS.md)。

## 当前 v0.5 安装方式

将 `skills/litanchor-paper-reading/` 整个目录复制到 Codex 的 Skills 目录，例如：

```text
%CODEX_HOME%\skills\litanchor-paper-reading
```

然后使用类似请求触发：

```text
使用 LitAnchor 精读 Zotero 中的「论文标题或 citekey」，按 deep 模式准备 Obsidian 笔记。
```

当前版本会先检查可用输入和工具；缺少 Zotero 或写入能力时必须报告缺口，不得假装已经连接。

## v0.6 Agent 安装入口

v0.6 的目标体验只有两个自然语言意图步骤。下面只是示例，不是必须
逐字照说的命令；Agent 应按语义识别安装或单篇精读意图：

```text
帮我安装 Skill：https://github.com/xieyf1024/Litanchor-paper-reading
```

```text
精读《论文标题》，并将笔记保存至 <Obsidian Vault 名称>。
```

本地能力完整的 Agent 会读取 `litanchor-install.json`，校验 Release
包，运行 `install.ps1`，创建隔离环境并安装轻量核心；只有选择允许
MinerU 时才通过 `Repair -IncludeMinerU` 补装可选 SDK。首次配置只允许询问
Vault、Literature Inbox 和 MinerU 授权模式；用户无需手动执行 Python、
`pip`、PowerShell、复制 Skill 或编辑 JSON。

仓库开发态可由 Agent 调用：

```powershell
.\install.ps1 -Action Install
.\litanchor.ps1 doctor
.\litanchor.ps1 setup -Vault "Vault 名称" -Inbox "LitAnchor\00_Inbox" -MinerUConsent always_for_eligible_files -CreateInbox
.\litanchor.ps1 run-plan -Paper "论文标题" -Vault "Vault 名称"
```

这些是 Agent 执行接口，不是普通用户必须输入的安装步骤。`doctor`
返回机器可读的 Python、依赖、Zotero Local API、Vault 路径、UTF-8
写入、空间和 MinerU 状态；安装、修复、升级、回滚和卸载只处理
安装收据确认属于 LitAnchor 的文件。

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

Skill 必须按背景/问题/贡献、数据/方法、结果/图表、讨论/限制等专项遍次读取 `source-bundle.json`，再填充 `evidence.json` 和富结构 `claims.json`。ClaimRecord 是中间知识对象，不是最终的一句式摘要。随后生成预览：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\litanchor_local.py build "runtime\runs\<run-id>"
```

产物保存在被 Git 忽略的 `runtime/`。所有 `deep`/`internalize` 输出必须使用 `assets/Paper Template - Final.md`。`build` 会阻断错误或未验证页码、无法在原页找到的引文、必需内容组缺失、内容召回或章节深度不足、未完成关键视觉筛选、未通过裁剪来源门禁、数值/单位不一致、Final 模板缺节、语义校验失败和文件覆盖。页码未知时不会回退成 `p.1`。

v0.5 使用 `autonomous_deep_reading.py start` 建立六遍阅读包，并按本地授权策略自动执行符合条件的 MinerU 路由；随后由 Skill 生成逐页语义审阅回执，并用 `autonomous_semantic.py` 物化 Evidence/Claim 账本。`finalize` 只有在页面回执、SectionSynthesis、视觉分析和独立双审查均通过后才生成 Final 模板候选。用户确认视觉和链接后，再执行 `accept-visual-review` 与受限导出。完整顺序见 [autonomous deep-reading reference](skills/litanchor-paper-reading/references/autonomous-deep-reading.md)。

从原 PDF 裁剪一张已核对的关键图：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\pdf_figures.py "paper.pdf" `
  --page 3 --label "Figure 1" --output "runtime\figures\figure-1.png"
```

该命令只接受一基物理页码，默认拒绝覆盖，并为 PNG 生成包含原 PDF 哈希、页码、图题、裁剪框、边缘检查和输出哈希的 JSON 清单。自动定位失败时应先查看原页，再显式给出 `--bbox`；不得猜测裁剪范围。每篇 `deep` 笔记必须完成一次视觉筛选，默认只嵌入 1–3 张不可替代的流程图、结构图、结果图或机制示意图；没有合适对象时记录原因，不为凑数插图。

可选的 MinerU Flash 结构增强安装在独立依赖文件中：

```powershell
.\.venv\Scripts\pip install -r requirements-mineru.txt
```

先在本地设置授权策略：

```powershell
.\.venv\Scripts\python skills\litanchor-paper-reading\scripts\autonomous_deep_reading.py `
  set-mineru-consent --mode always_for_eligible_files
```

支持 `always_for_eligible_files`、`ask_each_time` 和 `never`。配置只保存在用户本机，不进入 Git。`start` 会依据该策略自动调用无需 Token 的 Flash/Quick Parse 接口，并强制检查单文件不超过 10 MiB、20 页；长论文只对选定的复杂页建立保留原物理页码的合规子集。输出只用于标题层级、阅读顺序、图题和复杂结构候选；`exact`、`fuzzy`、`unmatched` 对齐结果都不能绕过 PyMuPDF 原页核验。

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

## 当前运行范围

v0.5.0 的稳定路径是：本机 Zotero Local API 或用户提供的单篇 PDF，经 PyMuPDF 权威页级解析、按授权自动执行的 MinerU 结构增强、六遍精读、双审查和 Final 模板编排后，写入用户明确授权的 Obsidian Vault 子目录。Zotero 保持只读，已有笔记默认不覆盖。

v0.6 已完成 Agent 辅助安装、环境诊断、MinerU 融合实证、Windows CI、
冻结留出评测和可发布安装包，现以 `v0.6.0-beta.1` 开放公开测试。
结果见 [v0.6 validation](evals/reports/v0.6-public-beta-validation.md)、
[MinerU component A/B](evals/reports/v0.6-mineru-ab.md) 和
[v0.6 roadmap](docs/ROADMAP_V0.6.md)。产品、流程、数据、评测和集成规格分别见
[PRODUCT](docs/PRODUCT.md)、[WORKFLOW](docs/WORKFLOW.md)、
[DATA_SCHEMA](docs/DATA_SCHEMA.md)、[EVALUATION](docs/EVALUATION.md) 和
[INTEGRATIONS](docs/INTEGRATIONS.md)。

## License

[GNU Affero General Public License v3.0 only](LICENSE)。选择 AGPL-3.0-only 是为了在开源分发中与 PyMuPDF 的 AGPL 许可路径保持清晰兼容。若未来改为闭源或不愿遵守 AGPL，应重新评估并向 Artifex 获取适当许可。第三方依赖、许可证和借鉴边界见 [THIRD_PARTY.md](THIRD_PARTY.md)，显著告知见 [NOTICE.md](NOTICE.md)。
