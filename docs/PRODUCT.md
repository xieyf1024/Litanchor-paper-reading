# Product definition

## Summary

LitAnchor（文锚）是一个面向研究生的轻量化、证据优先型学术精读
Skill。用户指定一篇 Zotero 文献或提供单篇 PDF 后，LitAnchor 只依据
该论文原文，生成可追溯的中文 Obsidian Markdown 笔记。

Current version: `v0.6.0-beta.3 Note Experience & Paper Template v1.0 Freeze`
Public status: Windows-first beta for local-capable Agents

## Product promise

LitAnchor 不承诺替代阅读全文，也不判断论文结论在学界是否正确。它承诺：

- 正式笔记中的重要事实可以回到原文物理页；
- 方法、指标、关键图表、结果、解释和限制经过独立覆盖；
- 数值、单位、条件、范围和作者语气不会被静默增强；
- 无法可靠处理时明确失败；
- Zotero 保持只读，Obsidian 只写入授权目录且默认不覆盖。

质量优先级固定为：

```text
忠实性 > 可追溯性 > 关键信息完整性 > 结构清晰度 > 阅读效率 > 表达流畅度
```

## Target users and baseline

Core users:

- 阅读英文论文的研究生与跨专业科研学习者；
- 使用 Zotero 管理文献、使用 Obsidian 沉淀知识的研究人员；
- 能使用具有本地执行能力的 Agent 完成安装和精读的人。

Supported baseline:

- Windows 10/11 x64；
- Python 3.10 或更高版本（当前 CI 覆盖 3.10–3.14）；
- Zotero 7 或更高版本 Desktop 与本地 PDF 附件；
- Obsidian Desktop 和本地 Vault；
- 能执行本地 Shell、访问 GitHub 并写入授权目录的 Agent。

完整条件见 `INSTALLATION_REQUIREMENTS.md`。

## Modes

| 模式 | 目的 | 必须覆盖 |
|---|---|---|
| `skim` | 快速判断论文讲什么、是否值得继续读 | 只生成模板第 1 节：一句话摘要、类型、结构、问题、方法骨架、主要结果、结论边界和必要定位 |
| `deep` | 默认的研究生级精读 | 生成模板第 1–6 节；内部保留 Evidence/Claim，正文覆盖方法/公式/参数、实验证据链、结果、直接嵌入的关键图表、作者解释、结论边界和作者局限 |
| `internalize` | 在 `deep` 结果上形成可检验的研究行动 | 生成完整第 1–8 节：deep 全部内容；研究联系、可证伪假设、相对原文增量、验证方案、至少两个失败条件、新颖性核查状态、术语/表达/追踪文献；所有启发与原文事实分层 |

## Autonomous deep-reading baseline

The published stable path includes:

1. exact single-paper resolution from Zotero Local API or a user-provided PDF;
2. PyMuPDF-authoritative physical-page extraction and original-PDF crops;
3. consent-aware automatic MinerU structure enhancement for eligible whole
   papers or page-preserving subsets;
4. paper-type-aware six-pass full-text reading;
5. EvidenceUnit, ClaimRecord and SectionSynthesis materialization;
6. complete figure inventory and zero to three selected method/result visuals;
7. independent fidelity and recall review;
8. `Paper Template v1.0` composition through the private Runtime template;
9. deterministic page, quote, number, symbol, depth, Markdown and collision
   gates;
10. hash-verified, path-contained and non-overwriting Obsidian export.

The v0.5.0 baseline was extended through v0.6.0-beta.3 with Agent-assisted install,
doctor, setup, upgrade, rollback and uninstall; Windows Python 3.10–3.14 CI;
frozen holdout evaluation; pathological PDF/failure fixtures; MinerU component
A/B evidence; deterministic Release artifacts; public issue routing; redacted
support bundles; interrupted-lifecycle recovery; and the frozen Paper Template
v1.0 reader contract with mode-specific output, compact page locators, explicit
provenance, conclusion boundaries and structured experiment chains.

Release evidence:

- six official autonomous evaluation papers;
- three extended non-autonomous renderer/quality regressions;
- three cross-domain generalization cases;
- one final source-closed unseen smoke test;
- the repository test suite plus Skill, compilation, privacy and anti-leak checks.

These papers are evaluation artifacts. Their titles, conclusions, values and
paper-specific fixes do not enter the distributable Skill.

## v1 product experience

The target public workflow contains two user requests:

```text
帮我安装 Skill：https://github.com/xieyf1024/Litanchor-paper-reading
```

```text
精读《论文标题》，并将笔记保存至 <Obsidian Vault 名称>。
```

The Agent handles the LitAnchor virtual environment, dependencies, Skill
installation, diagnostics, paper resolution, autonomous reading and contained
export. The user is interrupted only for first-run choices, ambiguous sources,
collisions, external-upload consent or reliability blockers.

v0.6 implements and validates this Agent-assisted setup and public-beta
hardening path. See `ROADMAP.md` for the remaining stable-release gates.

## Permanent product boundaries

- Formal paper facts come only from the supplied paper.
- External learning or user reflection stays visibly separate from paper
  claims.
- Unverified pages, quotations or visual crops cannot become formal evidence.
- A blocker prevents formal export.
- Existing notes, Zotero records and user-owned files are never silently
  replaced or modified.
- Evaluation papers can teach general failure classes and workflow rules, not
  their answers.

## Release gates

- core factual claim evidence coverage 100%;
- severe unsupported claims 0;
- physical-page accuracy at least 99%;
- core numeric errors 0 and numeric fidelity at least 99.5%;
- blocker detection 100%;
- Final-template, YAML and Markdown validity 100%;
- required method/result/discussion/limitation coverage for the detected paper
  type;
- installation, export and rollback stay inside LitAnchor-owned or
  user-authorized paths.
