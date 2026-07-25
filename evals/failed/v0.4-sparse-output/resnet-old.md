---
title: "Deep residual learning for image recognition"
authors: ["Kaiming He"]
year: 2016
journal: null
doi: "10.1109/CVPR.2016.90"
paper_type: []
keywords: []
zotero_key: "he2016DeepResidualLearning"
source_pdf: "item_key:TQ9Q9X2A"
extraction_engine: "pypdf native text + PyMuPDF visual evidence"
review_status: "draft"
tags: [literature-note, deep-reading, litanchor]
created: "2026-07-24T12:00:14+00:00"
---

# Deep residual learning for image recognition

<!--
LitAnchor Final template 1.0
- 只依据论文原文填写事实层。
- 不适用写“**不适用**”；原文没有说明写“**原文未说明**”；无法可靠读取写“**解析失败**”。
- 重要事实必须绑定 Evidence ID 与 PDF 物理页码。
- 以下 litanchor:user 区域由用户编辑，自动更新不得覆盖。
-->

> [!abstract] 一句话摘要
> 论文提出残差学习框架，将深层网络要学习的映射改写为相对输入的残差函数，以缓解网络加深后难以优化的问题，并用 ImageNet、CIFAR-10 与目标检测实验检验这一设计。 〔E-RN-SUM, E-RN-CON1, E-RN-CON2, E-RN-DATA-CF｜PDF p.1, p.2, p.7｜[打开 p.1](zotero://open-pdf/library/items/M8REGQUE?page=1)｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕

## 1. 论文速览

> 本节只提供全文导读，每项控制在 1—3 句话；详细论证放在后续章节。

| 项目 | 内容 |
| --- | --- |
| 论文类型 | 原文未说明 |
| 研究对象 / 数据 / 模型 | ImageNet 实验覆盖 1000 个类别，使用 1.28 million 张训练图像和 50k 张验证图像。 〔E-RN-DATA-IM｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/M8REGQUE?page=4)〕<br>CIFAR-10 实验使用 50k 张训练图像、10k 张测试图像和 10 个类别，主要用于研究极深网络的行为而非刷新最佳结果。 〔E-RN-DATA-CF｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕<br>ImageNet 基线主要使用 3×3 卷积；当特征图尺寸减半时将滤波器数量加倍，以近似保持每层时间复杂度。 〔E-RN-ARCH｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/M8REGQUE?page=3)〕 |
| 核心问题 | 核心研究问题是：仅仅堆叠更多层，是否就能同样容易地学习到更好的网络？ 〔E-RN-Q｜PDF p.1｜[打开 p.1](zotero://open-pdf/library/items/M8REGQUE?page=1)〕 |
| 方法路线 | 残差块先由堆叠的非线性层学习 F(x)=H(x)-x，再把输入 x 通过 shortcut 与 F(x) 相加，得到目标映射 F(x)+x。 〔E-RN-MAP, E-RN-SHORT｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕<br>恒等 shortcut 本身不增加额外参数或主要计算复杂度，因此可以在其他条件相近时公平比较 plain network 与 residual network。 〔E-RN-SHORT｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕<br>ImageNet 基线主要使用 3×3 卷积；当特征图尺寸减半时将滤波器数量加倍，以近似保持每层时间复杂度。 〔E-RN-ARCH｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/M8REGQUE?page=3)〕 |
| 主要发现 | 152-layer ResNet 的单模型 top-5 validation error 为 4.49%，并优于此前列出的 ensemble 结果。 〔E-RN-RES-152｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕<br>六个不同深度模型组成的 ensemble 在 ImageNet test set 上达到 3.57% top-5 error。 〔E-RN-RES-ENS｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕<br>在 CIFAR-10 上，110-layer ResNet 能够收敛，测试误差达到 6.43%，且参数少于文中列举的其他深而窄网络。 〔E-RN-RES-CF, E-RN-RES-CF-B｜PDF p.7, p.8｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕 |
| 核心贡献 | 第一项核心贡献是提出深度残差学习框架，把每组堆叠层的学习目标从直接拟合目标映射改为拟合相对输入的残差。 〔E-RN-CON1, E-RN-MAP｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕<br>第二项贡献是给出直接对照证据：极深残差网络随深度增加仍较容易优化，而仅堆叠层的 plain network 会表现出更高训练误差。 〔E-RN-CON2｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕 |
| 关键限制 | 网络并非越深越好：1202-layer 网络的测试结果差于 110-layer 网络，作者认为这可能是小数据集上的过拟合，并指出 19.4M 参数对该数据集可能过大。 〔E-RN-LIMIT, E-RN-LIMIT-B｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕 |
| 论证主线 | 背景与缺口 → 研究问题 → 方法与证据 → 结果与解释 → 结论与边界 |

---

## 2. 背景、问题与贡献

### 2.1 研究背景与前人工作

- 研究背景是网络深度对视觉识别性能很重要，但“更深”只有在网络能够被有效优化时才会转化为更好的表示与精度。 〔E-RN-BG, E-RN-GAP｜PDF p.1｜[打开 p.1](zotero://open-pdf/library/items/M8REGQUE?page=1)〕
- 与同期的 Highway Networks 相比，本文的 shortcut 不使用数据依赖的门控参数，而采用始终开放、无参数的恒等映射。 〔E-RN-PRIOR｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕

### 2.2 研究缺口与研究问题

- 核心研究问题是：仅仅堆叠更多层，是否就能同样容易地学习到更好的网络？ 〔E-RN-Q｜PDF p.1｜[打开 p.1](zotero://open-pdf/library/items/M8REGQUE?page=1)〕
- 作者要解决的不是网络从一开始就无法收敛，而是已经能够收敛的深层网络仍会出现退化：深度继续增加时准确率先饱和、随后迅速下降。 〔E-RN-GAP｜PDF p.1｜[打开 p.1](zotero://open-pdf/library/items/M8REGQUE?page=1)〕
  - 原文将该现象称为 degradation problem。
  - 作者保留了 might 的谨慎语气来描述准确率饱和是否令人意外。
- 作者的关键假设是：相较于直接优化未参照输入的原始映射，优化残差映射可能更容易；这在论文中是待实验支持的假设，而非先验确定事实。 〔E-RN-HYP｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕

### 2.3 贡献与创新

- 第一项核心贡献是提出深度残差学习框架，把每组堆叠层的学习目标从直接拟合目标映射改为拟合相对输入的残差。 〔E-RN-CON1, E-RN-MAP｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕
  - 目标映射记为 H(x)。
  - 堆叠的非线性层学习 F(x)=H(x)-x。
  - 网络输出通过 F(x)+x 恢复原映射。
- 第二项贡献是给出直接对照证据：极深残差网络随深度增加仍较容易优化，而仅堆叠层的 plain network 会表现出更高训练误差。 〔E-RN-CON2｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕
  - 对照对象不是任意两个架构，而是 plain 与 residual counterpart。
  - 比较重点包含优化难度与随深度增加后的精度变化。

---

## 3. 数据、材料与方法

### 3.1 研究对象、数据或材料

- ImageNet 实验覆盖 1000 个类别，使用 1.28 million 张训练图像和 50k 张验证图像。 〔E-RN-DATA-IM｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/M8REGQUE?page=4)〕
- CIFAR-10 实验使用 50k 张训练图像、10k 张测试图像和 10 个类别，主要用于研究极深网络的行为而非刷新最佳结果。 〔E-RN-DATA-CF｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕

### 3.2 方法与研究设计

- 残差块先由堆叠的非线性层学习 F(x)=H(x)-x，再把输入 x 通过 shortcut 与 F(x) 相加，得到目标映射 F(x)+x。 〔E-RN-MAP, E-RN-SHORT｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕
  - H(x) 表示希望拟合的底层映射。
  - F(x) 表示需要学习的残差映射。
  - shortcut 将输入直接送到加法节点。
  - **成立条件与边界**：恒等 shortcut 直接使用时，输入和输出维度需要一致。
- 恒等 shortcut 本身不增加额外参数或主要计算复杂度，因此可以在其他条件相近时公平比较 plain network 与 residual network。 〔E-RN-SHORT｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕
  - shortcut 跳过一个或多个堆叠层。
  - shortcut 输出与堆叠层输出做逐元素相加。

#### 方法流程

1. 残差块先由堆叠的非线性层学习 F(x)=H(x)-x，再把输入 x 通过 shortcut 与 F(x) 相加，得到目标映射 F(x)+x。 〔E-RN-MAP, E-RN-SHORT｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕
2. 恒等 shortcut 本身不增加额外参数或主要计算复杂度，因此可以在其他条件相近时公平比较 plain network 与 residual network。 〔E-RN-SHORT｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕

### 3.3 关键模型、算法或技术环节

#### M1. 关键模型 1

- **作用与核心机制**：ImageNet 基线主要使用 3×3 卷积；当特征图尺寸减半时将滤波器数量加倍，以近似保持每层时间复杂度。 〔E-RN-ARCH｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/M8REGQUE?page=3)〕
- 相同输出特征图尺寸下使用相同数量的滤波器。
- 下采样由带步长的卷积层完成。
- **关键假设 / 条件**：原文未说明

#### M2. 关键模型 2

- **作用与核心机制**：34-layer 基线的计算量为 3.6 billion FLOPs，约为 VGG-19 的 18%，说明本文并非单纯以更高计算量换取更深结构。 〔E-RN-COMPLEX｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/M8REGQUE?page=3)〕
- **关键假设 / 条件**：原文未说明

### 3.4 核心公式与评价指标

#### Eq. 1：名称原文未说明

- **用途与定义**：维度一致时，残差块的核心表达式为 y=F(x,{Wi})+x（式 1）。 〔E-RN-EQ1｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/M8REGQUE?page=3)〕
- **成立条件、单位或适用限制**：x 与 F(x,{Wi}) 的维度必须相同。

#### Eq. 2：名称原文未说明

- **用途与定义**：维度不一致时，可由投影 shortcut 使用 Ws 匹配维度，表达式为 y=F(x,{Wi})+Wsx（式 2）。 〔E-RN-EQ2｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/M8REGQUE?page=3)〕
- **成立条件、单位或适用限制**：仅在输入和输出通道等维度不能直接相加时需要匹配。

### 3.5 实验、比较与复现要点

| 实验 / 比较 | 设置、目的与关键结果 | 证据位置 |
| --- | --- | --- |
| 实验 | ImageNet 训练从头开始，使用 SGD、mini-batch 256、初始学习率 0.1；误差平台期将学习率除以 10，weight decay 为 0.0001、momentum 为 0.9，并且不使用 dropout。；训练采用 SGD。；学习率按误差平台触发衰减。；实验明确未使用 dropout。 | 〔E-RN-IMPL｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/M8REGQUE?page=4)〕 |

---

## 4. 核心结果与证据

> 每条只记录一个可独立核验的核心结果。推测不写成“结果”，应放入第 6 节。

### R1. 核心结果 1

- **主要发现**：152-layer ResNet 的单模型 top-5 validation error 为 4.49%，并优于此前列出的 ensemble 结果。 〔E-RN-RES-152｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕
- **论证与细节**：
  - 该结果来自单模型而非六模型集成。
  - 比较对象是表中此前的 ensemble results。
- **关键数值、比较或不确定性**：model depth 152-layer（single model）；top-5 validation error 4.49%%（ImageNet）
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

### R2. 核心结果 2

- **主要发现**：六个不同深度模型组成的 ensemble 在 ImageNet test set 上达到 3.57% top-5 error。 〔E-RN-RES-ENS｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)〕
- **论证与细节**：
  - ensemble 由六个不同深度的模型组成。
  - 提交时其中只有两个是 152-layer 模型。
- **关键数值、比较或不确定性**：top-5 test error 3.57%%（ImageNet ensemble）
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

### R3. 核心结果 3

- **主要发现**：在 CIFAR-10 上，110-layer ResNet 能够收敛，测试误差达到 6.43%，且参数少于文中列举的其他深而窄网络。 〔E-RN-RES-CF, E-RN-RES-CF-B｜PDF p.7, p.8｜[打开 p.7](zotero://open-pdf/library/items/M8REGQUE?page=7)｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕
- **论证与细节**：
  - 论文强调这里关注极深网络的行为而非专门追逐 state of the art。
  - 结果与 FitNet、Highway 等深而窄网络进行参数和误差比较。
- **关键数值、比较或不确定性**：model depth 110-layer（CIFAR-10）；test error 6.43%%（CIFAR-10）
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

### R4. 核心结果 4

- **主要发现**：在 COCO 目标检测中，用 ResNet 表示替代基线表示后，COCO 标准 mAP 指标增加 6.0%，相对改进为 28%。 〔E-RN-DETECT, E-RN-DETECT-B｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕
- **论证与细节**：
  - 检测实现保持不变，作者把增益归因于 learned representations。
  - 该实验用于检验残差表示能否迁移到分类以外的识别任务。
- **关键数值、比较或不确定性**：mAP increase 6.0%%（COCO mAP@[.5,.95]）；relative improvement 28%%（COCO）
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

---

## 5. 重要图表

| 图表编号 | 回答什么问题 | 主要信息 | 支撑结果 | 页码 | 核验状态 |
| --- | --- | --- | --- | --- | --- |
| Figure 2 | 该图直接呈现输入 x、残差分支 F(x) 与恒等 shortcut 的相加关系，是理解论文核心方法不可替代的示意图。 | Figure 2. Residual learning: a building block. | 核心方法/结果 | [PDF p.2](zotero://open-pdf/library/items/M8REGQUE?page=2) | 已查看原 PDF 裁图 |

### Figure 2

![[LitAnchor-Test/_assets/deep-residual-learning/figure-2.png]]

- **选择理由**：该图直接呈现输入 x、残差分支 F(x) 与恒等 shortcut 的相加关系，是理解论文核心方法不可替代的示意图。
- **完整图题**：Figure 2. Residual learning: a building block.
- **正文讨论位置**：PDF p.2 Introduction 与 PDF p.3 Section 3.2
- **读图注意事项**：原文未说明
- [在 Zotero 打开原页](zotero://open-pdf/library/items/M8REGQUE?page=2)

---

## 6. 讨论、结论与限制

### 6.1 作者如何解释结果

- 作者的关键假设是：相较于直接优化未参照输入的原始映射，优化残差映射可能更容易；这在论文中是待实验支持的假设，而非先验确定事实。 〔E-RN-HYP｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)〕
- 作者把残差网络较小的层响应解释为对其动机的支持：残差函数可能通常比非残差函数更接近零；原文使用 might，因此这里不能写成已被证明的普遍事实。 〔E-RN-INTERP｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕
  - 分析对象是 BN 后、非线性之前的层响应。
  - 该结果属于作者对机制的解释，不等同于单独的因果验证。

### 6.2 核心结论

- 作者据多任务结果认为残差学习原则具有通用性，并预期它还可用于其他视觉与非视觉问题；“可用于其他问题”在原文中仍是预期，而不是本文已覆盖的实验事实。 〔E-RN-CONCL, E-RN-DETECT｜PDF p.2, p.8｜[打开 p.2](zotero://open-pdf/library/items/M8REGQUE?page=2)｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕
  - 论文已用分类和目标检测结果展示跨任务迁移。
  - 对其他视觉与非视觉问题的适用性属于作者 expectation。

### 6.3 局限性与不确定性

- 网络并非越深越好：1202-layer 网络的测试结果差于 110-layer 网络，作者认为这可能是小数据集上的过拟合，并指出 19.4M 参数对该数据集可能过大。 〔E-RN-LIMIT, E-RN-LIMIT-B｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕
  - 两种深度的训练误差相近，但测试表现不同。
  - 过拟合是作者的解释，原文使用 argue 和 may。
  - 实验没有使用 maxout 或 dropout 等更强正则化。
- 作者提出未来可研究把极深残差网络与更强正则化结合，这被表述为可能改善结果的后续方向。 〔E-RN-FUTURE｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/M8REGQUE?page=8)〕

---

## 7. 对研究与学习的价值

> [!warning] 以下属于学习启发，不是作者原文结论。

### 7.1 与我的研究的关系

当前未生成；请结合个人研究主题在受保护区域补充。

<!-- litanchor:user:start -->
- **我的补充**：
<!-- litanchor:user:end -->

### 7.2 125 提炼

#### 1 个可继续发展的思路

**原文未说明**

#### 2 个值得模仿的图表

1. **Figure 2**：该图直接呈现输入 x、残差分支 F(x) 与恒等 shortcut 的相加关系，是理解论文核心方法不可替代的示意图。

#### 5 个值得学习的英文表达

**原文未说明**

---

## 8. 术语、原文证据与滚雪球阅读

### 8.1 术语与待解决问题

**原文未说明**

### 8.2 关键原文证据与可引用内容

> 只收录支撑核心结论、方法或研究缺口的关键原文；原文必须逐字复制。

| ID | 原文 | 页码 / 章节 | 支撑内容 |
| --- | --- | --- | --- |
| E-RN-Q | Driven by the significance of depth, a question arises: Is learning better networks as easy as stacking more layers? | PDF p.1 / Introduction | C-RN-Q |
| E-RN-GAP | When deeper networks are able to start converging, a degradation problem has been exposed: with the network depth increasing, accuracy gets saturated (which might be unsurprising) and then degrades rapidly. | PDF p.1 / Introduction | C-RN-GAP |
| E-RN-CON1 | In this paper, we address the degradation problem by introducing a deep residual learning framework. | PDF p.2 / Introduction | C-RN-CON1 |
| E-RN-CON2 | Our extremely deep residual nets are easy to optimize | PDF p.2 / Introduction | C-RN-CON2 |
| E-RN-MAP | Formally, denoting the desired underlying mapping as H(x), we let the stacked nonlinear layers fit another mapping of F(x): = H(x) − x. The original mapping is recast into F(x)+ x. | PDF p.2 / Introduction | C-RN-CON1, C-RN-METHOD-MAP |
| E-RN-SHORT | Identity shortcut connections add neither extra parameter nor computational complexity. | PDF p.2 / Introduction | C-RN-METHOD-MAP, C-RN-METHOD-SHORT |
| E-RN-ARCH | The convolutional layers mostly have 3 ×3 filters and follow two simple design rules: (i) for the same output feature map size, the layers have the same number of filters; and (ii) if the feature map size is halved, the number of filters is doubled so as to preserve the time complexity per layer. | PDF p.3 / Network Architectures | C-RN-MODEL-ARCH |
| E-RN-COMPLEX | Our 34-layer baseline has 3.6 billion FLOPs (multiply-adds), which is only 18% of VGG-19 (19.6 billion FLOPs). | PDF p.3 / Network Architectures | C-RN-MODEL-COST |
| E-RN-IMPL | We use SGD with a mini-batch size of 256. The learning rate starts from 0.1 and is divided by 10 when the error plateaus, and the models are trained for up to 60 × 104 iterations. We use a weight decay of 0.0001 and a momentum of 0.9. We do not use dropout | PDF p.4 / Implementation | C-RN-EXP |
| E-RN-RES-152 | Our 152-layer ResNet has a single-model top-5 validation error of 4.49%. This single-model result outperforms all previous ensemble results | PDF p.7 / ImageNet Classification | C-RN-RES-152 |
| E-RN-RES-ENS | We combine six models of different depth to form an ensemble (only with two 152-layer ones at the time of submitting). This leads to 3.57% top-5 error on the test set | PDF p.7 / ImageNet Classification | C-RN-RES-ENS |
| E-RN-RES-CF | This 110-layer network converges well | PDF p.7 / CIFAR-10 and Analysis | C-RN-RES-CF |
| E-RN-RES-CF-B | yet is among the state-of-the-art results (6.43%, Table 6). | PDF p.8 / CIFAR-10 and Analysis | C-RN-RES-CF |
| E-RN-LIMIT | The testing result of this 1202-layer network is worse than that of our 110-layer network | PDF p.8 / Exploring Over 1000 Layers | C-RN-LIMIT |
| E-RN-LIMIT-B | We argue that this is because of overfitting. The 1202-layer network may be unnecessarily large (19.4M) for this small dataset. | PDF p.8 / Exploring Over 1000 Layers | C-RN-LIMIT |
| E-RN-DETECT | we obtain a 6.0% increase in | PDF p.8 / Object Detection on PASCAL and MS COCO | C-RN-RES-DET, C-RN-CONCL |

### 8.3 值得继续追踪的参考文献

**原文未说明**

<!-- litanchor:validation template=paper-template-final@1.0; run=20260724T114926Z-51b5de45eb0b; evidence=29; claims=26; status=completed_with_warnings; pdf_sha256=51b5de45eb0b558b19c3affe49503cff50cb170a32de602983d6e2ec286942a7 -->
