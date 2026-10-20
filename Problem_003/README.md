# Problem_003：山地货运轨道车的无源限速

**原创中文数学建模模拟题，已通过用户审核。** 本题不是 CUMCM、MCM/ICM 或其他竞赛的官方题目。面向有数学、物理和编程基础的本科生，建议三人组队、96 小时；72 小时训练可限制候选设计和故障边界的搜索规模。

本题研究车轮驱动永磁发电机、固定电阻负载构成的无源限速装置。核心是从感应、受力与能量关系建立机电热模型，分析稳定限速、有限陡坡响应、重复运行积热和断相后的工作范围。没有运行样本、回归或预测算法任务，也不要求收集现场数据。电路、磁链、互感与启停条件已给出，不要求学习电机控制或有限元软件。

四问相连：恒温均匀坡道上的限速机制 → 首趟有限线路运行 → 十趟连续运输的装置选择 → 九趟运行后放行前断相的下行范围。第四问改变接线结构；不能只把载荷换成另一个数。题目允许得到应停运的结论，不预设降载一定有效。

## 使用

发给参赛队的是 [problem.pdf](problem.pdf)、完整 `data/` 及附件整理说明。PDF 共三页：背景与系统、四问、参数和附件。附件为题设设计值，不是产品实测数据或采购报价。

```text
Problem_003/
├── README.md
├── LICENSE.md
├── problem.tex
├── problem.pdf
├── data/
│   ├── README.md
│   ├── parameters.json
│   ├── routes.csv
│   ├── gear_options.csv
│   ├── cooling_options.csv
│   └── rules.json
├── scripts/
│   ├── make_inputs.py
│   ├── check_inputs.py
│   ├── check_design.py
│   ├── build_pdf.py
│   └── check_submission.py
└── review/
    ├── research_review.md
    ├── quality_report.md
    ├── independent_review.md
    └── editorial_review.md
```

`review/` 给教师和审核者阅读，不宜与题面混为一份学生任务书。公开审查材料不含完整状态方程推导、推荐选型数值、运行轨迹、故障载荷边界或完整参考求解器。命题试算程序仅在本次临时工作区使用，没有假定公开仓库的任何目录保密。

## 复现与检查

进入本题目录，用 Python 3.10 以上标准库核查附件和交付：

```sh
python3 scripts/check_inputs.py
python3 scripts/check_submission.py
```

主动重建五个机器附件：

```sh
python3 scripts/make_inputs.py --output data
```

生成器没有随机观测或隐藏运行输出，只按题设整理参数、线路和规则。数据字典是手写说明，不会被覆盖。自己准备选型 JSON，字段为 `q`、`Re_ohm`、`cooling` 后可运行：

```sh
python3 scripts/check_design.py design.json
```

这个工具只核查组件范围、费用和质量。是否满足车速、温度、电流与运输时间要求，须由参赛队自己的模型判断。

重新编译题面：

```sh
python3 scripts/build_pdf.py
```

需要 XeLaTeX、Noto Serif/Sans CJK SC 和 DejaVu Sans Mono 字体，以及常用 TeX Live 包。脚本两遍编译，将辅助文件放在临时目录并检查溢出、缺字和字体替代。完整 PDF 检查需要 Poppler 的 `pdfinfo`、`pdftotext`。

## 审核与许可

题目于2026-10-20通过用户审核，并获授权创建 PR。完整成果通过独立分支提交，变更范围仅为 `Problem_003/`。验证证据、评分及边界见 [质量报告](review/quality_report.md)；[独立审查](review/independent_review.md)由另一 AI 协作代理完成，不是外部人类评审认证。

题面与说明采用 CC BY 4.0；原创设计参数与编排采用 CC0 1.0；代码采用 MIT。引用文献、官方题面、第三方文档及图文不属于这些授权范围，详见 [LICENSE.md](LICENSE.md)。
