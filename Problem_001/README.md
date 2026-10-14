# Problem_001：低用水片区的余氯保障与有限排放

这是一道独立设计的**原创中文数学建模模拟题**，不是全国大学生数学建模竞赛或 MCM/ICM 官方赛题。面向有数学、统计和编程基础的本科生，建议三人组队、**96 小时**完成；72 小时训练可保留第四问的基础方案，不要求证明全局最优。

题目围绕持续保压的低用水片区：设施规模不变，用水减少使输运与混合的历史影响更突出；有限排放既消耗水资源，也改变共享上游的更新过程。四项任务依次研究可检验模型、无排放质量与简化指标、预算下的运行方案，以及有限监测的反馈价值。数学挑战来自机制、证据和跨时段决策，不限定算法。

## 文件与使用

```text
Problem_001/
├── README.md
├── LICENSE.md
├── problem.tex
├── problem.pdf
├── data/
│   ├── README.md
│   ├── network_nodes.csv
│   ├── pipes.csv
│   ├── tanks.csv
│   ├── users.csv
│   ├── forcing.csv
│   ├── demands.csv
│   ├── bottle_tests.csv
│   ├── tank_tracer.csv
│   └── operating_rules.json
├── scripts/
│   ├── generate_data.py
│   ├── check_data.py
│   ├── build_pdf.py
│   └── check_submission.py
└── review/
    ├── research_review.md
    ├── independent_review.md
    └── quality_report.md
```

将 [problem.pdf](problem.pdf)、全部 `data/` 附件及生成说明发给参赛队即可开赛。[data/README.md](data/README.md) 是数据字典。生成机制公开，实验留出标签用于方法比较，不是保密盲测。比赛不依赖外网下载；第三方资料只作为背景参考，不是附件实测来源。

全部附件为明确标识的合成训练数据：9 根管道、2 座恒水位在线水箱、6 个用户末端，包含 3 日正常用水输入和 7 日决策输入，以及独立瓶试和水箱示踪。公开生成程序没有全网水质求解器、用户端水质真值或预设最优策略。用水质量目标仅为本题服务目标。

`review/` 是非答案性的命题审查材料。教师应先阅读 [质量报告](review/quality_report.md)，了解数据适用边界、已发现并修订的问题和实际检查结果；它不包含完整参考解答、基准策略、评分数值答案或可复制的求解步骤。本公开仓库中的任何目录都不是保密位置。

## 复现与检查

生成及检查程序只需要 Python **3.10 或以上**，无需第三方 Python 包。在本题目录运行：

```bash
python3 scripts/check_data.py
python3 scripts/check_submission.py
```

检查程序在临时目录重生成附件并比较逐文件 SHA-256，不改现有数据。若要主动重新生成附件：

```bash
python3 scripts/generate_data.py --output-dir data
```

排版采用 XeLaTeX、A4 纸及 Noto Serif/Sans CJK SC 字体；需要 TeX Live 的 `fontspec`、`amsmath`、`tikz`、`xurl`、`hyperref` 等常用包。没有要求安装专用供水软件。重新编译：

```bash
python3 scripts/build_pdf.py
```

编译两遍，辅助文件留在临时目录，成功后只更新 `problem.pdf`；脚本检查缺字和公式/文本溢出。`check_submission.py` 还需要 Poppler 的 `pdfinfo` 与 `pdftotext`，用来确认 PDF 页数和中文文本抽取；数值附件检查不依赖 Poppler。

私下试算采用了基础科学计算工具，验证了每问的可行路径、守恒和数值精度。详细求解程序和策略结果仅在本次临时工作区用于命题验证，未上传公开仓库，也未声称它是保密参考答案存档。公开代码只负责造数、编译和交付检查。

## 许可与引用

原创题面及审查文档采用 CC BY 4.0；合成数据及数据字典采用 CC0 1.0；`scripts/` 代码采用 MIT，完整说明见 [LICENSE.md](LICENSE.md)。引用的第三方网页、论文、官方赛题和软件遵守各自许可，不在本仓库转载。

建议引用：`SZUMMA2026-Training-Excise, Problem_001：低用水片区的余氯保障与有限排放，原创模拟题，2026。`
