# Problem_004　轻型屋盖的积水与排水

这是一道原创数学建模训练题，并非 CUMCM、MCM/ICM 官方赛题。面向具有微积分、常微分方程、线性代数和编程基础的本科生，建议比赛时间 **96 小时**，也可用于 72 小时训练。

平屋盖变形后，积水荷载、湿润范围、排水口高程和分区交换都会改变。本题用一根等效梁承载两区积水，研究静水约束、有限进水过程、永久改造和单向临时顶撑。附件是规定的物理参数与进水工况，不含观测样本，不需要拟合监测数据。

四问依次研究：给定水量与给定水位下的平衡和稳定性；变形与分区排水的相互影响；两档预算下的永久改造；排水口堵塞后的临时顶撑。题面解释结构力学术语，并给出通用梁弯曲关系、支座条件和平面与纵剖面示意，不要求已修读结构力学课程。水荷载与变形的耦合、水量、稳定性及接触模型由参赛者建立。

本版为**审核稿**。按本轮要求，先提供题面、附件和审查记录供审阅，审核通过后再创建 PR。

## 文件

```text
Problem_004/
├── README.md
├── LICENSE.md
├── problem.tex
├── problem.pdf
├── data/
│   ├── README.md
│   ├── parameters.json
│   ├── rules.json
│   ├── inflows.csv
│   └── stiffening_options.csv
├── scripts/
│   ├── make_inputs.py
│   ├── check_inputs.py
│   ├── check_design.py
│   ├── build_pdf.py
│   └── check_submission.py
└── review/
    ├── research_review.md
    ├── quality_report.md
    └── editorial_review.md
```

学生使用 [正式题面 PDF](problem.pdf) 和 [附件说明](data/README.md)。`review/` 是公开的命题审查材料，未附参考解答、推荐组件组合或计算结果曲线；教师可在发题时将此目录留作命题记录。目录公开与否不构成保密措施。

## 使用与检查

在本目录执行以下命令。Python 脚本只使用标准库；编译和 PDF 检查另需 XeLaTeX、Noto Serif/Sans CJK SC、DejaVu Sans Mono 及 Poppler 的 `pdfinfo`、`pdftotext`。

```bash
python scripts/check_inputs.py
python scripts/build_pdf.py
python scripts/check_submission.py
```

`check_inputs.py` 检查几何、时轴、单位字段、三工况总进水曲线和附件逐字节重生成。需要重建机器可读附件时执行：

```bash
python scripts/make_inputs.py
```

`check_design.py` 可核对自拟方案的组件、费用与预算，不计算力学或排水结果：

```bash
python scripts/check_design.py /path/to/design.json --budget 7500
```

方案文件须含 `stiffening`（`B`、`S` 或 `T`）、`left_x_m`、`right_x_m`、`left_area_m2`、`right_area_m2` 五个字段，不接受其他字段。位置、面积按题面选择；`--budget` 取 `1500` 或 `7500`。通过此检查不代表满足挠度、弯矩、残余水量或顶撑要求。

## 参数性质与适用范围

本题没有引用实测结构、产品规格或工程报价。全部数值是为训练设计的参数和工况，按确定性程序重建；参考文献用于核查积水与变形反馈的物理背景。几何、边界、荷载、单位及简化条件见题面和 [数据字典](data/README.md)，来源与阅读边界见 [调研记录](review/research_review.md)。

本题采用准静态、小挠度线弹性等效梁和分区水平水面，不能直接用于实际屋盖设计或应急支撑施工。命题试算、局限及修订记录见 [质量报告](review/quality_report.md)。文字、数值附件、代码及第三方资料的授权分别见 [LICENSE.md](LICENSE.md)。
