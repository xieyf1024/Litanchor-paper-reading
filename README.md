# LitAnchor 文锚

> Anchor every insight to the source.

[![Release](https://img.shields.io/github/v/release/xieyf1024/Litanchor-paper-reading?include_prereleases&label=release)](https://github.com/xieyf1024/Litanchor-paper-reading/releases)
[![Windows CI](https://github.com/xieyf1024/Litanchor-paper-reading/actions/workflows/ci.yml/badge.svg)](https://github.com/xieyf1024/Litanchor-paper-reading/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB?logo=python&logoColor=white)](docs/INSTALLATION_REQUIREMENTS.md)
[![License](https://img.shields.io/github/license/xieyf1024/Litanchor-paper-reading)](LICENSE)

[English](README_EN.md) · [安装要求](docs/INSTALLATION_REQUIREMENTS.md) · [工作流](docs/WORKFLOW.md) · [评测](docs/EVALUATION.md) · [路线图](docs/ROADMAP.md)

LitAnchor 是一个面向研究生和科研工作者的轻量化、证据优先型学术精读 Skill。它从 Zotero 获取指定的单篇论文，只依据论文原文生成中文 Obsidian 笔记，并将重要主张锚定到 PDF 物理页、原文证据和 Zotero 跳转链接。

当前候选版本：**v0.6.0-beta.2 Zero-Config Public Beta**。它面向 Windows 上具备本地 Shell、文件和网络权限的 Agent；还不是支持所有 PDF 和所有聊天客户端的无人审核产品。

## 两步使用

用户不需要逐字照抄下面的话。Agent 应按语义识别安装和精读意图。

```text
帮我安装这个 Skill：https://github.com/xieyf1024/Litanchor-paper-reading
```

```text
精读《论文标题》，把笔记保存到我的 Research Vault。
```

首次安装最多确认三项本机配置：Obsidian Vault、Literature Inbox，以及是否允许符合条件的 PDF 使用 MinerU。之后由 Agent 负责隔离环境、依赖、Zotero 定位、全文精读、质量校验和受限导出。

## 它与普通 AI 摘要有什么不同

| 普通摘要常见行为 | LitAnchor |
|---|---|
| 从全文生成一段流畅概括 | 先构建 Evidence → Claim → SectionSynthesis，再编排笔记 |
| 只检查已经写出的内容 | 分别检查忠实度和关键内容召回 |
| 页码未知时仍给出定位 | 未验证页码不得成为正式证据 |
| 容易忽略公式、指标和图表 | 单独处理方法、公式、实验和关键视觉对象 |
| 直接覆盖目标文件 | 只写授权目录，默认拒绝覆盖 |
| 把模型知识混入论文结论 | 论文事实只来自用户提供的原文 |

## 工作流

```mermaid
flowchart TB
    subgraph grounding["来源与页面基线"]
        direction LR
        source["Zotero 或本地 PDF"] --> pages["PyMuPDF 物理页基线"]
        pages -.-> mineru["MinerU 结构提示"]
    end

    subgraph reading["结构化全文精读"]
        direction LR
        profile["论文类型与章节地图"] --> passes["六遍专项阅读"] --> evidence["Evidence 证据账本"]
    end

    subgraph synthesis["证据约束的综合"]
        direction LR
        claims["Claim 主张账本"] --> sections["Section Synthesis 章节综合"] --> visuals["关键图表分析"]
    end

    subgraph delivery["质量门与交付"]
        direction LR
        review["忠实度与召回审查"] --> compose["Final 模板编排"] --> obsidian["授权的 Obsidian Inbox"]
    end

    pages --> profile
    mineru -.-> profile
    evidence --> claims
    visuals --> review

    classDef sourceLayer fill:#E8F1FF,stroke:#2563EB,stroke-width:2px,color:#172554
    classDef assistLayer fill:#F3E8FF,stroke:#9333EA,stroke-width:2px,color:#3B0764
    classDef knowledgeLayer fill:#FFF7E6,stroke:#D97706,stroke-width:2px,color:#451A03
    classDef qualityLayer fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B
    class source,pages sourceLayer
    class mineru assistLayer
    class profile,passes,evidence,claims,sections,visuals knowledgeLayer
    class review,compose,obsidian qualityLayer
```

PyMuPDF 始终负责物理页码、原文引文、坐标和图片来源。MinerU 负责改善章节层级、阅读顺序、图题及复杂结构候选；它的内容只有重新对齐原始 PDF 页面后才能进入正式证据。

## 核心保证

- 只依据用户提供的论文原文；原文没有说明时明确标记。
- 不把讨论、解释、假设或推测升级成确定事实。
- 事实性主张绑定 Evidence ID 和经过验证的 PDF 物理页。
- 保留数值、单位、变量、范围和适用条件。
- 解析失败和质量阻断必须显式报告。
- Zotero 默认只读；Obsidian 仅写入用户授权目录。
- 用户笔记默认不覆盖，外部上传必须服从本地 MinerU 授权策略。

## 环境要求

- Windows 10/11 x64；
- Python 3.10 或更高版本，当前 CI 覆盖 3.10–3.14；
- Zotero 7 或更高版本，已启用本机应用通信并具有本地 PDF 附件；
- Obsidian Desktop 和本地文件系统 Vault；
- 能执行本地命令、读写授权目录并下载依赖的 Agent。

Python 和 Zotero 只设最低版本，不设武断的最高版本；未覆盖的新版本由 `doctor` 进行能力探测并给出警告。完整说明见[安装要求](docs/INSTALLATION_REQUIREMENTS.md)。

## Agent 与开发接口

普通用户优先使用上面的自然语言入口。Agent 或贡献者可以调用：

```powershell
.\install.ps1 -Action Install
.\litanchor.ps1 doctor
.\litanchor.ps1 doctor -SupportBundle
.\litanchor.ps1 setup -Vault "Vault 名称" -Inbox "LitAnchor\00_Inbox" -MinerUConsent ask_each_time -CreateInbox
.\litanchor.ps1 run-plan -Paper "论文标题" -Vault "Vault 名称"
```

这些是 Agent 执行接口，不是要求普通用户手动完成的步骤。安装器只管理安装收据确认属于 LitAnchor 的文件，并支持修复、升级、回滚和确认式卸载。

公开反馈分为安装/生命周期、运行/PDF 和笔记质量三类。需要共享诊断时优先使用 `doctor -SupportBundle` 生成的脱敏 ZIP，并在上传前人工复核；不要附带论文、完整笔记、Zotero 数据或本机路径。

## 输出内容

`deep` 模式默认覆盖：

- 论文问题、背景、研究空白和贡献；
- 数据、材料、预处理、方法和模型；
- 公式、评价指标、关键参数与实验设计；
- 核心结果、作者解释、限制和适用边界；
- 1–3 个关键视觉对象及其原 PDF 来源；
- 精简证据标记、Zotero 页码链接和审查状态。

完整原文证据保存在侧车文件中，Markdown 正文只展示必要定位和少量折叠证据，避免把笔记变成全文摘抄。

## 当前评测状态

v0.6.0-beta.2 候选版在 beta.1 的 Windows Python 3.10–3.14 CI、冻结留出评测、病理 PDF/失败路径、MinerU 融合对比、隐私审计和 Release 构建基础上，增加公开反馈、脱敏支持包、生命周期恢复、语义意图回归与依赖收敛。评测论文只用于学习可复用的失败类型与工作流规则，不得把论文答案写入可分发 Skill。

- [v0.6 Public Beta 验证](evals/reports/v0.6-public-beta-validation.md)
- [MinerU 组件 A/B](evals/reports/v0.6-mineru-ab.md)
- [v0.6 评测指标](evals/v0.6-public-beta-metrics.json)
- [防测试集泄漏审计](docs/anti-leak-audit.md)

## 当前边界

- 一次处理一篇论文，不做批量综述或知识图谱。
- 以原生文本 PDF 为稳定路径；扫描件和异常版式可能降级或阻断。
- MinerU 是需要网络和用户授权的可选增强，不是正式证据来源。
- 不写回 Zotero，不提供双向同步，也不自动覆盖已有 Obsidian 笔记。
- 用户仍应复核关键图、引用定位和将要长期保存的最终笔记。

## 仓库结构

```text
.
├── .github/                         # CI、依赖更新与 Issue 模板
├── skills/litanchor-paper-reading/  # 可安装 Skill 及运行资源
├── docs/                            # 产品、工作流、架构与公开路线图
├── evals/                           # v0.6 评测清单、量表与公开报告
├── tests/                           # 自动化回归测试
├── tools/                           # 构建、验证、评测与发布审计
├── install.ps1                      # Windows 安装生命周期入口
├── litanchor.ps1                    # doctor、setup 与 run-plan
└── litanchor-install.json           # 机器可读安装契约
```

可安装 Skill 只包含运行所需的 `SKILL.md`、脚本、Schema、参考规则和模板。项目历史由 Git Tag、Release 和 [CHANGELOG](CHANGELOG.md) 保存，不在当前主分支重复堆放旧预览与开发记录。

## 文档与贡献

从[文档导航](docs/README.md)选择产品、工作流、Schema、集成、评测或隐私说明。提交问题或改进前请阅读[贡献指南](CONTRIBUTING.md)。

请勿提交论文 PDF、私人 Zotero 数据、Obsidian Vault、API 密钥、个人批注或运行时 Evidence/Claim 文件。

## License

[GNU Affero General Public License v3.0 only](LICENSE)。PyMuPDF 的许可路径、MinerU 外部服务边界和设计参考项目见 [THIRD_PARTY.md](THIRD_PARTY.md) 与 [NOTICE.md](NOTICE.md)。
