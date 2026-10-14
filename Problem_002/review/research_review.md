# 第二题调研与选题记录

核查日期：2026-10-14（北京时间）。本记录为命题材料，不含参考解答。

## 阅读范围

上一题已筛查CUMCM与COMAP近十年的官方目录，并阅读代表性题面、2018国赛A官方展示论文及若干公开评阅摘要。本轮沿用这部分记录，重新打开 [CUMCM历年赛题](https://www.mcm.edu.cn/html_cn/block/8579f5fce999cdc896f78bca5d4f8237.html)和 [COMAP官方矩阵](https://contest.comap.com/undergraduate/contests/matrix/index.html)，重点核查新选题近邻和题面行文。不是重新精读每年全部A—F，也没有把目录访问当作全文阅读。

本轮直接读取了2025 ICM E与2022 HiMCM A的官方PDF，及2021 MCM A官方资源页。部分2021/2023官方PDF地址本轮无法访问；2018 A401官方展示论文的再次打开超时，采用上一轮已读记录并明确这一限制。COMAP优秀论文和讲评仍有会员限制，没有获取或声称获取这些全文。国赛年度下载为压缩包，目录核查不等于压缩包内所有题面阅读。

## 从赛题到问题与文字

| 样本及阅读范围 | 命题结构上的参考 | 文字处理上的参考 |
|---|---|---|
| 2018 CUMCM A，高温作业专用服装；上一轮阅读官方展示A401全文 | 从机理、试验进入设计，复杂度由约束与验证支撑 | 先交代对象和测量条件，再设问；不在题面替学生写模型结构 |
| 2021 CUMCM B，乙醇偶合制备C4烯烃；上一轮公开评述摘要 | 试验关系与后续工艺决策相连 | 用具体对象和问题动词，避免算法目录式要求 |
| 2023 CUMCM C，蔬菜定价补货；上一轮公开评阅摘要 | 区分统计规律与决策后的系统变化 | 定义必要经营量，不用长段审查要求代替设问 |
| 2021 MCM A，Fungi；本轮官方背景页 | 科学背景可以给必要机制，保留模型构造和环境外推 | 背景、研究要求和附件分工清楚；科学资料不直接变成指定解法 |
| 2025 ICM E，Making Room for Agriculture；本轮题面全文 | 环境变化和人类行动在同一系统内发生影响 | 多问服务同一对象，但正文无需逐项冠以教学环节名称 |
| 2022 HiMCM A，The Need for Bees；本轮题面全文 | 必须查到主题近邻，才能判断研究对象是否重复 | 以简短背景引入实际问题，数量与术语明确 |

本题没有套用上一题的“预测—排放—传感器反馈”。这里的状态是花粉来源与访花过程，决策在花期前作出，重点是遗传相容、时间重合、空间访问与非线性坐果；最后一问比较事先固定的安排。

## 候选比较

| 候选 | 数学潜力与数据基础 | 主要疑点 | 取舍 |
|---|---|---|---|
| 地下水恢复后的地面沉降 | USGS解释弹性与不可逆压密、延迟排水；有压密数据目录和近期研究 | 厚层参数、长期初态与同地点水位配套尚未验证；完整地质抽象需要更多工作 | 本次暂不选 |
| 退役电池分选与组装 | 异质性、筛选误差与串并联约束有现实意义 | 与成熟电池评估及新近分组研究相近，易降为已有流程的简化复现 | 本次不选 |
| 苹果园授粉安排 | 遗传相容事实有推广机构依据；开花、访花与带粉可设置独立试验 | 不是新的授粉机制；需防止变成按花期的静态匹配或只估蜂数 | 选择，并加入原树位损失、花期错开、剂量异质性和有限预算 |

选择不是因为背景“新”，而是这组条件能够在本科生可承受的数据和计算规模内形成相连的数学问题。先完成基本预测和合法方案试算，再写题面；未以选题主观评分直接定稿。

## 科学依据及近邻

[WSU推广资料](https://treefruit.wsu.edu/article/cross-compatibility-of-apple-cultivars-and-pollinizers/)说明苹果的配子体自交不亲和与S型，并列出品种遗传型。本题只摘取5条有来源的事实另行编排，开花曲线和实验数值另行构造，未把它们称为WSU实测。

[Hung等，2023](https://doi.org/10.1002/eap.2917)研究了不同访花者的带粉延续、移动与果园空间背景。实际成功访问了出版商摘要及方法部分，确认该机制和果园布局研究并非首次提出；后续打开部分页面返回403，未导入其原始数据或附录程序。该文比较蜂类与既定布局、使用授粉效率指标；本题固定访花者类型，研究不同花期、遗传半相容、非线性初期坐果和现有树位的有限改植。既没有改写其模拟流程，也没有将科学机制称为原创。

2022 HiMCM A要求蜂群人口变化、人口因素敏感性和支持20英亩土地需要的蜂群数量。虽然主题都涉及授粉，本题不研究蜂群出生死亡或按面积估蜂数，而是给定访花机会、研究有效供粉与树位安排。2025 ICM E主要研究森林转农田后的食物网、农药与物种恢复，本题不设置食物网或生态演替。

另以“数学建模竞赛＋苹果园＋授粉”“MCM＋orchard＋pollination”“ICM＋pollen＋layout”等组合筛查，未找到可核查的同结构CUMCM/MCM/ICM题面。结论限于已查目录、代表全文和本轮检索，不保证全球没有类似模拟题。仓库第一题为低用水管网，两题的对象、实验、状态和决策不同。

## 可核查资料

- [CUMCM官方目录](https://www.mcm.edu.cn/html_cn/block/8579f5fce999cdc896f78bca5d4f8237.html)、[COMAP官方矩阵](https://contest.comap.com/undergraduate/contests/matrix/index.html)。
- [2025 ICM E官方PDF](https://www.contest.comap.com/undergraduate/contests/mcm/contests/2025/problems/2025_ICM_Problem_E.pdf)。
- [2022 HiMCM A官方PDF](https://www.contest.comap.com/highschool/contests/himcm/2022_Problems/2022_HiMCM_Problem_A.pdf)。
- [2021 MCM A官方资源页](https://www.comap.org/membership/member-resources/item/fungi)，本轮读取背景与会员条件。
- [2018 A401官方展示PDF](https://dxs.moe.gov.cn/zx/2018/1101/1541041099335.pdf)，上一轮全文已读，本轮再次访问超时。
- [2023 C官方期刊评阅摘要](https://cjournal.hep.com.cn/2095-3070/CN/1179753514924154977)，DOI：10.19943/j.2095-3070.jmmia.2024.02.04；完整阅读范围见上一题调研报告。
- WSU Tree Fruit：上述S型资料，2019，2024-02-13复核；[Apple Pollination](https://treefruit.wsu.edu/web-article/apple-pollination/)，本轮读取正文。
- Hung, K.-L. J., Fan, S. L., Strang, C. G., Park, M. G., Thomson, J. D. 2023. *Pollen carryover, pollinator movement, and spatial context impact the delivery of pollination services in apple orchards*. Ecological Applications, 33(8):e2917. DOI：[10.1002/eap.2917](https://doi.org/10.1002/eap.2917)；[PubMed记录](https://pubmed.ncbi.nlm.nih.gov/37661589/)。
- [USGS，Groundwater sustainability and land subsidence in California’s Central Valley，2024](https://www.usgs.gov/publications/groundwater-sustainability-and-land-subsidence-californias-central-valley)，仅用于候选机制与数据检索。
- [USGS压密数据目录](https://data.usgs.gov/datacatalog/data/USGS%3A61d74604d34ed79294005087)，只核查可用数据条目，未取得并验证配套数值。
- [电池二次使用适用性评估机构记录](https://research-hub.nlr.gov/en/publications/procedure-for-assessing-the-suitability-of-battery-second-life-ap/)，用于候选检索，未引用其实验结果。

没有转载官方题面、优秀论文、图片或第三方实验表。
