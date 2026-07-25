---
title: "Separation of internal and forced variability of climate using a U‐net"
authors: ["Constantin Bône"]
year: 2024
journal: "Journal of Advances in Modeling Earth Systems"
doi: "10.1029/2023MS003964"
paper_type: ["empirical-research"]
keywords: []
zotero_key: "bone2024SeparationInternalForced"
source_pdf: "item_key:4RNUJQM4"
extraction_engine: "pypdf native text + PyMuPDF visual evidence"
review_status: "reviewed"
generation_mode: "human_assisted_regression"
autonomous_generation: false
tags: [literature-note, deep-reading, litanchor]
created: "2026-07-25T03:50:36+00:00"
---

# Separation of internal and forced variability of climate using a U‐net

<!--
LitAnchor Final template 1.0
- 只依据论文原文填写事实层。
- 论文事实缺失写“**原文未说明**”；论文类型不适用写“**不适用**”。
- deep 模式不生成的学习层写“**本模式未生成（仅 internalize 模式要求）**”。
- 用户个人判断写“**待用户补充**”；无法可靠读取写“**解析失败**”。
- 重要事实必须绑定 Evidence ID 与 PDF 物理页码。
- 以下 litanchor:user 区域由用户编辑，自动更新不得覆盖。
-->

> [!abstract] 一句话摘要
> 论文把气候系统内部变率类比为图像噪声，用 noise-to-noise 训练的 U-Net 从时空地表气温中估计外强迫信号，并用独立的大集合气候模型与观测检验其效果和区域局限。 〔E-UN-Q1, E-UN-M1, E-UN-M2, E-UN-C1｜PDF p.2, p.7, p.17｜[打开 p.2](zotero://open-pdf/library/items/T5VHFPIY?page=2)｜[打开 p.7](zotero://open-pdf/library/items/T5VHFPIY?page=7)｜[打开 p.17](zotero://open-pdf/library/items/T5VHFPIY?page=17)〕

## 1. 论文速览

> 本节只提供全文导读，每项控制在 1—3 句话；详细论证放在后续章节。

| 项目 | 内容 |
| --- | --- |
| 论文类型 | empirical-research |
| 研究对象 / 数据 / 模型 | 训练资料由 47 个 AOGCM 的 801 个成员构成，覆盖 1901–2020 年。 〔E-UN-D1｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/T5VHFPIY?page=4)〕<br>U-Net 由 contracting path 与 expansive path 组成，并以 3-dimensional 卷积替换原本的 2-dimensional 卷积，以便同时处理地表气温的空间和时间维度。 〔E-UN-M3, E-UN-M4｜PDF p.8, p.9｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)｜[打开 p.9](zotero://open-pdf/library/items/T5VHFPIY?page=9)〕 |
| 核心问题 | 论文的核心问题是：如何从地表气温中区分气候系统内部变率与外强迫变率。 〔E-UN-Q1｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/T5VHFPIY?page=2)〕 |
| 方法路线 | 作者采用 noise-to-noise 训练，把不同集合成员视为同一外强迫信号叠加不同内部变率噪声的样本。 〔E-UN-M1, E-UN-M2｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/T5VHFPIY?page=7)〕<br>网络使用具有收缩路径与扩张路径的 U-Net，并把原来的 2-dimensional 卷积改为 3-dimensional 卷积，以同时学习空间和时间特征。 〔E-UN-M3, E-UN-M4｜PDF p.8, p.9｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)｜[打开 p.9](zotero://open-pdf/library/items/T5VHFPIY?page=9)〕<br>U-Net 由 contracting path 与 expansive path 组成，并以 3-dimensional 卷积替换原本的 2-dimensional 卷积，以便同时处理地表气温的空间和时间维度。 〔E-UN-M3, E-UN-M4｜PDF p.8, p.9｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)｜[打开 p.9](zotero://open-pdf/library/items/T5VHFPIY?page=9)〕 |
| 主要发现 | 在两个测试气候模型上，U-Net 与相应集合平均的 RMSE 位于 0.05°C–0.5°C。 〔E-UN-R1｜PDF p.11｜[打开 p.11](zotero://open-pdf/library/items/T5VHFPIY?page=11)〕<br>对全球平均地表气温，U-Net 将内部变率削弱到略多于四倍的程度，效果约等价于 FGOALS-g3 的 17 个成员或 MPI-ESM 的 20 个成员平均。 〔E-UN-R2｜PDF p.13｜[打开 p.13](zotero://open-pdf/library/items/T5VHFPIY?page=13)〕<br>U-Net 对 Nino3.4 外强迫变率的估计呈现稳定变暖趋势。 〔E-UN-R3｜PDF p.16｜[打开 p.16](zotero://open-pdf/library/items/T5VHFPIY?page=16)〕 |
| 核心贡献 | 作者将本文定位为专用神经网络分离内部变率与外强迫变率的开创性应用，但原文以“据作者所知”限定该新颖性判断。 〔E-UN-CONTRIB｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/T5VHFPIY?page=4)〕 |
| 关键限制 | U-Net 在副极地北大西洋估计外强迫变化的能力有限，作者将其与不同模型间该区域温度演变不一致联系起来。 〔E-UN-L1｜PDF p.12｜[打开 p.12](zotero://open-pdf/library/items/T5VHFPIY?page=12)〕<br>该神经网络方法对仪器观测不确定性的敏感性仍未得到检验。 〔E-UN-L2｜PDF p.17｜[打开 p.17](zotero://open-pdf/library/items/T5VHFPIY?page=17)〕 |
| 论证主线 | 背景与缺口 → 研究问题 → 方法与证据 → 结果与解释 → 结论与边界 |

---

## 2. 背景、问题与贡献

### 2.1 研究背景与前人工作

- 地表气温异常可由外部强迫和气候系统内部过程共同驱动，因此检测长期外强迫响应需要把两种变率区分开。 〔E-UN-BG, E-UN-Q1｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/T5VHFPIY?page=2)〕
  - 外强迫包含温室气体、气溶胶、太阳活动、火山喷发和土地利用变化等边界条件影响。
  - 内部变率来自大气、海洋、冰冻圈和陆面的过程及其相互作用。

### 2.2 研究缺口与研究问题

- 论文的核心问题是：如何从地表气温中区分气候系统内部变率与外强迫变率。 〔E-UN-Q1｜PDF p.2｜[打开 p.2](zotero://open-pdf/library/items/T5VHFPIY?page=2)〕
  - 论文把区分对象限定为 surface air temperature 中的两类变率。
  - 输出目标是估计被内部变率遮蔽的外强迫变化。
- 观测记录自 1850 年以来时段较短，难以有把握地区分内部变率；这是该研究试图缓解的主要资料限制。 〔E-UN-G1｜PDF p.3｜[打开 p.3](zotero://open-pdf/library/items/T5VHFPIY?page=3)〕
  - 较短观测时段限制了对低频内部变率的识别。
  - 线性或二次趋势也难以表示火山喷发后的突发降温等时间演变。

### 2.3 贡献与创新

- 作者将本文定位为专用神经网络分离内部变率与外强迫变率的开创性应用，但原文以“据作者所知”限定该新颖性判断。 〔E-UN-CONTRIB｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/T5VHFPIY?page=4)〕
  - 方法利用气候模型中的空间与时间信息学习网络参数。
  - 训练后的网络随后被用于观测资料以估计外强迫信号。

---

## 3. 数据、材料与方法

### 3.1 研究对象、数据或材料

- 训练资料由 47 个 AOGCM 的 801 个成员构成，覆盖 1901–2020 年。 〔E-UN-D1｜PDF p.4｜[打开 p.4](zotero://open-pdf/library/items/T5VHFPIY?page=4)〕
  - 多模型资料同时采样模型差异和强迫差异。
  - 所有模式资料被重网格化到与观测一致的水平网格。

### 3.2 方法与研究设计

- 作者采用 noise-to-noise 训练，把不同集合成员视为同一外强迫信号叠加不同内部变率噪声的样本。 〔E-UN-M1, E-UN-M2｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/T5VHFPIY?page=7)〕
  - 每个气候模式的 forced spatio-temporal anomaly 被视为一个独立对象。
  - 单个集合成员相当于真实外强迫图像叠加内部变率噪声。
  - noise-to-noise 配对使网络无需把单个集合成员当作无噪声真值。
- 网络使用具有收缩路径与扩张路径的 U-Net，并把原来的 2-dimensional 卷积改为 3-dimensional 卷积，以同时学习空间和时间特征。 〔E-UN-M3, E-UN-M4｜PDF p.8, p.9｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)｜[打开 p.9](zotero://open-pdf/library/items/T5VHFPIY?page=9)〕
  - 收缩路径提取多尺度时空特征。
  - 扩张路径恢复输出，并通过跨层连接合并相应尺度信息。

#### 方法流程

1. 作者采用 noise-to-noise 训练，把不同集合成员视为同一外强迫信号叠加不同内部变率噪声的样本。 〔E-UN-M1, E-UN-M2｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/T5VHFPIY?page=7)〕
2. 网络使用具有收缩路径与扩张路径的 U-Net，并把原来的 2-dimensional 卷积改为 3-dimensional 卷积，以同时学习空间和时间特征。 〔E-UN-M3, E-UN-M4｜PDF p.8, p.9｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)｜[打开 p.9](zotero://open-pdf/library/items/T5VHFPIY?page=9)〕

### 3.3 关键模型、算法或技术环节

#### M1. 关键模型 1

- **作用与核心机制**：U-Net 由 contracting path 与 expansive path 组成，并以 3-dimensional 卷积替换原本的 2-dimensional 卷积，以便同时处理地表气温的空间和时间维度。 〔E-UN-M3, E-UN-M4｜PDF p.8, p.9｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)｜[打开 p.9](zotero://open-pdf/library/items/T5VHFPIY?page=9)〕
- contracting path 用于逐步提取特征。
- expansive path 用于恢复输出分辨率，跳跃连接保留跨尺度信息。
- **关键假设 / 条件**：原文未说明

### 3.4 核心公式与评价指标

#### Metric 1：RMSE

- **用途与定义**：论文使用均方根误差（RMSE）比较 U-Net 输出与相应集合平均，测试模型上的 RMSE 范围为 0.05°C–0.5°C。 〔E-UN-R1｜PDF p.11｜[打开 p.11](zotero://open-pdf/library/items/T5VHFPIY?page=11)〕
- **成立条件、单位或适用限制**：FGOALS-g3 与 MPI-ESM 独立测试；单位为 °C。

### 3.5 实验、比较与复现要点

| 实验 / 比较 | 设置、目的与关键结果 | 证据位置 |
| --- | --- | --- |
| 实验 | 训练集采用 noise-to-noise 方法构造输入—目标对，用于学习网络权重与偏置。；训练阶段使用模型成员的成对样本，而不是把集合平均直接作为唯一输入。 | 〔E-UN-M1｜PDF p.7｜[打开 p.7](zotero://open-pdf/library/items/T5VHFPIY?page=7)〕 |
| 实验 | 验证集使用 MIROC6 的 50 成员集合：单个集合成员作为输入，集合平均作为目标输出。 | 〔E-UN-EXP-VALIDATION｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)〕 |
| 实验 | 测试集使用未参与训练的 FGOALS-g3（110 成员）与 MPI-ESM（100 成员）大集合。 | 〔E-UN-EXP-TEST｜PDF p.8｜[打开 p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8)〕 |
| 实验 | 完成测试后，作者将 U-Net 应用于 GISTEMP 地表气温观测，以观测为输入估计外强迫变率。；观测应用位于模型独立测试之后，输出解释为对外强迫变率的估计。 | 〔E-UN-EXP-OBS｜PDF p.14｜[打开 p.14](zotero://open-pdf/library/items/T5VHFPIY?page=14)〕 |

---

## 4. 核心结果与证据

> 每条只记录一个可独立核验的核心结果。推测不写成“结果”，应放入第 6 节。

### R1. 核心结果 1

- **主要发现**：在两个测试气候模型上，U-Net 与相应集合平均的 RMSE 位于 0.05°C–0.5°C。 〔E-UN-R1｜PDF p.11｜[打开 p.11](zotero://open-pdf/library/items/T5VHFPIY?page=11)〕
- **论证与细节**：
  - 误差不是单一值，而是在空间上呈现区域差异。
  - 内部变率强或不同模式外强迫响应不一致的区域误差更大。
- **关键数值、比较或不确定性**：RMSE lower bound 0.05°C（test climate models）；RMSE upper bound 0.5°C（test climate models）
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

### R2. 核心结果 2

- **主要发现**：对全球平均地表气温，U-Net 将内部变率削弱到略多于四倍的程度，效果约等价于 FGOALS-g3 的 17 个成员或 MPI-ESM 的 20 个成员平均。 〔E-UN-R2｜PDF p.13｜[打开 p.13](zotero://open-pdf/library/items/T5VHFPIY?page=13)〕
- **论证与细节**：
  - 该比较把单成员 U-Net 输出与随机子集合的 ensemble mean 误差联系起来。
  - 两个测试模型得到的等效成员数不同，因此结果以范围而非单点表述。
- **关键数值、比较或不确定性**：variability reduction factor four（GSAT）；equivalent ensemble members 17（FGOALS-g3）；equivalent ensemble members 20（MPI-ESM）
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

### R3. 核心结果 3

- **主要发现**：U-Net 对 Nino3.4 外强迫变率的估计呈现稳定变暖趋势。 〔E-UN-R3｜PDF p.16｜[打开 p.16](zotero://open-pdf/library/items/T5VHFPIY?page=16)〕
- **论证与细节**：
  - 该结论只描述 Figure 10 中 Nino3.4 外强迫分量的长期变化，不把跨页残句中的频段信息写入主张。
- **关键数值、比较或不确定性**：原文未说明
- **证据状态**：作者报告
- **成立条件与适用范围**：原文未说明

---

## 5. 重要图表

| 图表编号 | 回答什么问题 | 主要信息 | 支撑结果 | 页码 | 核验状态 |
| --- | --- | --- | --- | --- | --- |
| Figure 3 | 该图完整展示 U-Net 的编码器、解码器、跳跃连接与数据维度，是理解去噪方法的核心流程图。 | Figure 3. Schematic of the U‐Net. The arrows represent the operations within the network. The numbers shows the dimension of the data and the number of filters used. | 核心方法图 | [PDF p.8](zotero://open-pdf/library/items/T5VHFPIY?page=8) | 已查看原 PDF 裁图 |
| Figure 7 | 该图把 U-Net 的误差与不同集合规模均值直接对应，是核心结果和等效集合规模解释的量化依据。 | Figure 7. Spatial average of the RMSE in the 1905–2016 period for the forced variability estimated with the U‐Net outputs obtained from each ensemble member, and the forced variability obtained with ensemble averages subsampling ensemble of size 1 to 40. | 核心结果图 | [PDF p.14](zotero://open-pdf/library/items/T5VHFPIY?page=14) | 已查看原 PDF 裁图 |

### Figure 3

![U-Net Figure 3](assets/unet/figure-3.png)

- **选择理由**：该图完整展示 U-Net 的编码器、解码器、跳跃连接与数据维度，是理解去噪方法的核心流程图。
- **完整图题**：Figure 3. Schematic of the U‐Net. The arrows represent the operations within the network. The numbers shows the dimension of the data and the number of filters used.
- **正文讨论位置**：PDF p.8–9，Section 3.3
- **读图注意事项**：原文未说明
- [在 Zotero 打开原页](zotero://open-pdf/library/items/T5VHFPIY?page=8)

### Figure 7

![U-Net Figure 7](assets/unet/figure-7.png)

- **选择理由**：该图把 U-Net 的误差与不同集合规模均值直接对应，是核心结果和等效集合规模解释的量化依据。
- **完整图题**：Figure 7. Spatial average of the RMSE in the 1905–2016 period for the forced variability estimated with the U‐Net outputs obtained from each ensemble member, and the forced variability obtained with ensemble averages subsampling ensemble of size 1 to 40.
- **正文讨论位置**：PDF p.13–14，Section 4.2
- **读图注意事项**：原文未说明
- [在 Zotero 打开原页](zotero://open-pdf/library/items/T5VHFPIY?page=14)

---

## 6. 讨论、结论与限制

### 6.1 作者如何解释结果

- 作者把单个成员经 U-Net 处理后的误差换算为“等效集合规模”：全球平均效果略高于四倍内部变率削弱，约对应 FGOALS-g3 的 17 个成员或 MPI-ESM 的 20 个成员平均。 〔E-UN-R2｜PDF p.13｜[打开 p.13](zotero://open-pdf/library/items/T5VHFPIY?page=13)〕
  - 等效集合规模用于把神经网络误差转换为传统 ensemble mean 的直观基准。
  - 该换算来自两个独立测试模型，而不是训练集内拟合。

### 6.2 核心结论

- 总体上，单个成员经过 U-Net 后的内部变率削弱超过 4 倍，相当于约 17–20 个成员的集合平均精度。 〔E-UN-C1｜PDF p.17｜[打开 p.17](zotero://open-pdf/library/items/T5VHFPIY?page=17)〕
  - 结论来自 MPI-ESM 和 FGOALS-g3 两个独立大集合测试。
  - 区域结果仍必须与北大西洋等失败区域的限制一起阅读。

### 6.3 局限性与不确定性

- U-Net 在副极地北大西洋估计外强迫变化的能力有限，作者将其与不同模型间该区域温度演变不一致联系起来。 〔E-UN-L1｜PDF p.12｜[打开 p.12](zotero://open-pdf/library/items/T5VHFPIY?page=12)〕
  - 副极地北大西洋在不同模式中具有不一致的地表温度演变。
  - 作者认为这种模式间差异限制了网络辨认各模式特有外强迫变化的能力。
- 该神经网络方法对仪器观测不确定性的敏感性仍未得到检验。 〔E-UN-L2｜PDF p.17｜[打开 p.17](zotero://open-pdf/library/items/T5VHFPIY?page=17)〕
  - 训练资料来自气候模式，而正式应用对象包含仪器观测。
  - 观测数据集和仪器误差变化是否会影响结果，仍需要专门敏感性试验。

---

## 7. 对研究与学习的价值

> [!warning] 以下属于学习启发，不是作者原文结论。

### 7.1 与我的研究的关系

**待用户补充**

<!-- litanchor:user:start -->
- **我的补充**：
<!-- litanchor:user:end -->

### 7.2 125 提炼

#### 1 个可继续发展的思路

**本模式未生成（仅 internalize 模式要求）**

#### 2 个值得模仿的图表

1. **Figure 3**：该图完整展示 U-Net 的编码器、解码器、跳跃连接与数据维度，是理解去噪方法的核心流程图。
2. **Figure 7**：该图把 U-Net 的误差与不同集合规模均值直接对应，是核心结果和等效集合规模解释的量化依据。

#### 5 个值得学习的英文表达

**本模式未生成（仅 internalize 模式要求）**

---

## 8. 术语、原文证据与滚雪球阅读

### 8.1 术语与待解决问题

**本模式未生成（仅 internalize 模式要求）**

### 8.2 关键原文证据与可引用内容

> 只收录支撑核心结论、方法或研究缺口的关键原文；原文必须逐字复制。

| ID | 原文 | 页码 / 章节 | 支撑内容 |
| --- | --- | --- | --- |
| E-UN-Q1 | A methodology is formulated to distinguish between internal and forced variability within the surface air temperature. | PDF p.2 / Abstract | C-UN-Q1 |
| E-UN-G1 | Nevertheless, the availability of instrumental observations is limited to the period since 1850, and the relatively brief duration of these observations presents challenges in effectively and confidently discerning internal variability. | PDF p.3 / Introduction | C-UN-G1 |
| E-UN-M1 | To construct the training data set, we adapt a noise‐to‐noise methodology originally introduced in Lehtinen et al. ( 2018 ). | PDF p.7 / Constitution of the Training, Validation and Test Data Sets | C-UN-M2, C-UN-EXP-TRAIN |
| E-UN-M2 | For our application, we consider the forced spatio‐temporal SAT anomalies from each climate model as distinct objects. These anomalies, inherent to each member, can be assimilated to noisy images, where the internal variability introduces the noise component. | PDF p.7 / Constitution of the Training, Validation and Test Data Sets | C-UN-M2 |
| E-UN-M3 | The U‐Net architecture is characterized by its inclusion of a contracting path and an expansive path, which collectively give rise to its characteristic U shape (refer to Figure 3 ). | PDF p.8 / U-Net | C-UN-M3, C-UN-MODEL |
| E-UN-M4 | a modification is made by replacing the 2‐dimensional convolutional layers with 3‐ dimensional counterparts. | PDF p.9 / U-Net | C-UN-M3, C-UN-MODEL |
| E-UN-R1 | The RMSE values fall within the range of 0.05°C–0.5°C. | PDF p.11 / Filtering of the Test Climate Models | C-UN-R1 |
| E-UN-R2 | The U‐Net effectively diminishes internal variability in GSAT by approximately a factor of slightly more than four, which is analogous to the residual variability observed within subsets containing around 17 members for FGOALS‐g3 and 20 members for MPI‐ESM. | PDF p.13 / Filtering of the Test Climate Models | C-UN-R2 |
| E-UN-R3 | The U‐Net estimates the Nino3.4 forced variability, depicting a steady warming trend. | PDF p.16 / Filtering of the Observations | C-UN-R3 |
| E-UN-L1 | This difference from the ensemble mean highlights the limited capacity of the neural network to accurately predict forced changes within the subpolar North Atlantic, which is a region that exhibits inconsistent surface temperature evolution across models (Swingedouw et al., 2021 ). | PDF p.12 / Filtering of the Test Climate Models | C-UN-L1 |
| E-UN-L2 | The sensibility of this neural network‐based methodology to instrumental uncertainties remains to be established. | PDF p.17 / Conclusion | C-UN-L2 |
| E-UN-C1 | The U‐Net outputs for these two climate models' test data exhibit an error equivalent to an internal variability reduction of a factor of more than 4 (e.g., Figure 7a). This magnitude corresponds to the internal variability one could expect from an ensemble averaging 17 to 20 members. | PDF p.17 / Conclusion | C-UN-C1 |
| E-UN-CONTRIB | To the best of our knowledge, this represents a pioneering application of a dedicated neural network for the purpose of disentangling internal and forced variability. | PDF p.4 / Introduction | C-UN-CONTRIB |
| E-UN-EXP-VALIDATION | To create the validation set, we use the ensemble simulation from the MIROC6 model, which ranks as the third‐largest ensemble in terms of size (with n = 50 members). | PDF p.8 / Constitution of the Training, Validation and Test Data Sets | C-UN-EXP-VALIDATION |
| E-UN-EXP-TEST | To form the test data set, we use the data derived from the FGOALS‐g3 and MPI‐ESM models, using their extensive ensemble sizes of n = 110 and n = 100 respectively. | PDF p.8 / Constitution of the Training, Validation and Test Data Sets | C-UN-EXP-TEST |
| E-UN-EXP-OBS | The U‐Net is now employed to process SAT observations derived from GISTEMP. By utilizing observed data as input, the U‐Net provides an estimate of the forced variability. | PDF p.14 / Filtering of the Observations | C-UN-EXP-OBS |

### 8.3 值得继续追踪的参考文献

**本模式未生成（仅 internalize 模式要求）**

<!-- litanchor:validation template=paper-template-final@1.0; run=20260724T114933Z-4c31db5f17c7; evidence=19; claims=21; status=completed_with_warnings; pdf_sha256=4c31db5f17c7df0e0ae687e4e5ac20e430b0d4b5fedc40ad1ce5550ea45b650a -->
