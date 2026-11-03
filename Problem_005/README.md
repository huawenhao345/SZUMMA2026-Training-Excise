# Problem_005　校园小巴的高峰运行与调度

原创中文数学建模训练题，非CUMCM、MCM/ICM官方赛题。建议96小时，面向有概率统计、微积分和编程基础的本科生，不要求交通运输专业先修知识。

题目来自用户提供的一条校园交通问题建议及深圳大学粤海、丽湖校区示意图，研究有限座位如何沿环线周转、乘降停站如何改变后续运行，以及信息延迟下的调度取舍。两校区分别建模，不跨校区调车。

**本版供用户审核，暂不创建PR。** 这是有实际问题来源、以明确参考工况开展的建模题。全部数值、简化环线及管理规则为训练设定，尚不能声称已经解决学校当前小巴运营问题；实际应用须经过题目要求的现场核实和试运行。

## 学生材料

- [problem.pdf](problem.pdf)：四页题面，含两套参考环线、运行与信息规则、评价口径及四项任务。
- [problem.tex](problem.tex)：XeLaTeX源文件。
- [data/README.md](data/README.md)：八份机器附件的字段、单位、生成假设及事件约定。

四问依次为对照运行与机制诊断、固定车队的事前安排、延迟信息下的控车与座位预留、交班约束与实际试行计划。重点是车辆、队列和在车目的地之间的动态联系，不能仅把地图转成最短路径，也不能只优化满载率。

## 文件结构

```text
Problem_005/
├── README.md
├── LICENSE.md
├── problem.tex
├── problem.pdf
├── data/
│   ├── README.md
│   ├── stops.csv
│   ├── links.csv
│   ├── vehicles.csv
│   ├── cases.csv
│   ├── passenger_requests.csv
│   ├── link_factors.csv
│   ├── baseline_plan.csv
│   └── rules.json
├── scripts/
│   ├── make_inputs.py
│   ├── check_inputs.py
│   ├── check_plan.py
│   ├── check_action_log.py
│   ├── build_pdf.py
│   └── check_submission.py
└── review/
    ├── research_review.md
    ├── quality_report.md
    ├── editorial_review.md
    └── independent_review.md
```

`review/`保留公开的调研与命题审查，不附完整求解器、优选发车时刻、控制参数或结果轨迹。教师可按发题需要选择分发文件；公开目录不能视为保密区。

## 重现与检查

在本目录运行：

```bash
python scripts/check_inputs.py
python scripts/build_pdf.py
python scripts/check_submission.py
```

辅助脚本仅用Python标准库。PDF另需XeLaTeX、Noto Serif/Sans CJK SC、DejaVu Sans Mono字体，以及Poppler的`pdfinfo`、`pdftotext`。编译执行两遍，辅助文件在临时目录，不写入题目目录。

`make_inputs.py`可逐字节重建八份机器附件，也可在其他种子下生成外部测试样本；用法见数据字典。附事前安排与控制记录检查器，范围是格式、声明与动作的必要条件，不替代完整运行模型或因果性证明。完整回放记录可以用于事后评分，不等于控制器在运行时有权读取未来信息。

## 数据来源与使用边界

原问卷只有一条定性建议，不用于估计需求比例、车队规模或满意度。原文件含身份字段，不随题公开；本目录也不转载原校园地图。题面图为自行绘制的参考连接图。功能区仅参考用户所给示意图，节点和有向环线不是校方确认的现行站表或通行许可。

设计需求样本包含7350条匿名虚拟请求，路段系数有2448条；没有真实乘客行程。生成假设、种子及范围见数据字典。实际使用前应确认两校区的路线、容量、行时、乘降、起讫需求、信息来源与交班制度。历史官方通知的适用时期和本轮阅读范围见 [调研报告](review/research_review.md)，不能把历史班次当作当前数据。

计入所有未完成出行者、限制在线信息并要求双校区验证，是为了使方案能接受实际检验。训练算例的可行性不能代替校内试运行。数值验证与局限见 [质量报告](review/quality_report.md)，授权见 [LICENSE.md](LICENSE.md)。
