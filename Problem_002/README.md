# Problem_002：苹果园的授粉安排

**原创中文数学建模模拟题，审核稿。** 本题不是CUMCM、MCM/ICM或HiMCM官方赛题。面向有数学、统计与编程基础的本科生，建议三人组队、96小时；72小时训练可以采用较简洁的过程模型和有限方案比较。

合作社希望比较增加访花量与改植授粉树。遗传相容、花期重合、空间位置和此前携带的花粉共同影响初期坐果，改植又会减少主栽树位。四问依次研究试验支持的模型、原布局表现、有限预算的安排和花期前固定方案的可靠性。

本轮按用户要求先供审核，**尚未创建PR**。题面与附件完成数值检查后保存在独立审核分支；用户审核通过或提出修改后，再修订并创建PR。

## 使用与文件

发给参赛队的是 [problem.pdf](problem.pdf)、完整 `data/` 和生成说明。题面正文一页，附件与参考资料一页；必要的数据口径见 [data/README.md](data/README.md)。

```text
Problem_002/
├── README.md
├── LICENSE.md
├── problem.tex
├── problem.pdf
├── data/
│   ├── README.md
│   ├── orchard.csv
│   ├── cultivar_genotypes.csv
│   ├── cultivar_planning.csv
│   ├── bloom_profiles.csv
│   ├── visitation.csv
│   ├── movement_trials.csv
│   ├── carryover_trials.csv
│   ├── fruit_set_trials.csv
│   ├── scenarios.csv
│   └── rules.json
├── scripts/
│   ├── generate_data.py
│   ├── check_data.py
│   ├── check_plan.py
│   ├── build_pdf.py
│   └── check_submission.py
└── review/
    ├── research_review.md
    ├── quality_report.md
    └── editorial_review.md
```

CSV共2197行，其中5条品种S型为WSU公开事实，2192条为模拟记录；果园、经营参数和试验都不能称为真实现场数据。公开生成器只构造输入与独立试验，不计算整园坐果或选择配置。留出按完整访花者或批次划分；造数机制公开，不构成盲测。比赛无需再下载外部数据。

`review/` 给教师和审核者阅读，记录参考资料、真实问题、修订和非答案性验证证据。没有完整参考解答、最佳配置、主栽预测果数或可复制的基准求解步骤。临时数值原型未上传，也没有假定仓库某目录保密。

## 复现与编译

数据及方案检查使用Python 3.10以上标准库。进入本题目录：

```bash
python3 scripts/check_data.py
python3 scripts/check_submission.py
```

第一条核查字段、单位、分组、情景守恒及10个机器附件的确定性重生成，第二条增加PDF与交付检查。主动重建数值附件：

```bash
python3 scripts/generate_data.py --output-dir data
```

数据字典是手写说明，不会被造数器覆盖。随机种子与构造常量集中在程序中。

重新生成PDF：

```bash
python3 scripts/build_pdf.py
```

需要XeLaTeX、Noto Serif/Sans CJK SC与DejaVu Sans Mono字体、常用TeX Live包（含`fontspec`、`fancyhdr`、`booktabs`、`hyperref`、`xurl`等）。脚本编译两遍，辅助文件放在临时目录，检查溢出、缺字和字体替代。完整交付检查另需要Poppler的`pdfinfo`、`pdftotext`。

方案可用全144树位的CSV表示，字段为 `tree_id,cultivar_id`，不改植的树位保持原品种。检查不会估算坐果：

```bash
python3 scripts/check_plan.py your_plan.csv --bees 1 --budget 6000
```

租蜂数单独给出，预算只接受6000或10000。程序检查树位、改植品种、每行上限、主栽保留数量、增蜂数和总费用。

## 审核与许可

[质量报告](review/quality_report.md)包含数据与可解性证据、88/100内部自审评分和保留局限；它不是外部人类评审认证。[文字检查](review/editorial_review.md)记录本次行文调整，最终以用户审核意见为准。

题面、README和审查文字为CC BY 4.0；原创合成数值、数据说明及自行编排为CC0 1.0；程序MIT。遗传型事实标注原来源，原网页、原表和第三方图文不在这些授权范围，详见 [LICENSE.md](LICENSE.md)。
