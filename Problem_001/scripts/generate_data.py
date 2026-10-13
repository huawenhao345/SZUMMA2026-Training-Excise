#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Rebuild the complete synthetic public attachment set (Python standard library).

No network transport solver, parameter estimator or flushing optimizer is included.
All seeds, synthetic laboratory mechanisms and operating assumptions are public.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import random

SEED = 20261013
SCHEMA_VERSION = '1.0'
# Explicit synthetic high-reactivity water, not a rate measured by an agency.
BOTTLE_A20_H_1 = .0208
BOTTLE_B20_L_MG_H = .0048
BOTTLE_A_FACTOR_PER_5C = 1.35
BOTTLE_B_FACTOR_PER_5C = 1.25
PIPES = [
    ('P0','S','J',900,.150,'PE',8.0,.0008,.0025),
    ('P1','J','T1',650,.100,'ductile_iron',5.2,.0015,.0060),
    ('P2','J','T2',800,.100,'ductile_iron',4.8,.0015,.0060),
    ('P3','T1','U1',700,.063,'PE',3.0,.0008,.0025),
    ('P4','T1','U2',1050,.063,'PE',3.0,.0008,.0025),
    ('P5','T1','U3',1350,.063,'ductile_iron',3.0,.0015,.0060),
    ('P6','T2','U4',550,.063,'PE',3.0,.0008,.0025),
    ('P7','T2','U5',950,.063,'PE',3.0,.0008,.0025),
    ('P8','T2','U6',1450,.063,'ductile_iron',3.0,.0015,.0060),
]
USERS = [('U1','T1',.56,0), ('U2','T1',.62,1), ('U3','T1',.67,-1),
         ('U4','T2',.48,0), ('U5','T2',.58,-1), ('U6','T2',.61,1)]
TANKS = [('T1',18.0,.40,.75,[.7,2.4,.42]),
         ('T2',14.0,.70,.78,[.6,2.0,.36])]
DAILY_SHAPE = [.34,.30,.28,.27,.30,.42,.72,1.45,1.65,1.20,1.02,.98,
               1.12,1.0,.94,.98,1.15,1.38,1.55,1.42,1.12,.86,.61,.44]
BOTTLE_TIMES = [0,6,12,24,36,48,60,72,96]
TRACER_TIMES = [0,1,2,4,6,8,12,16,24,32,48,64,96,128,160,200]


def fnum(value: float, digits: int = 6) -> str:
    return f'{value:.{digits}f}'


def write_csv(directory: Path, filename: str, fields: list[str], rows: list[list]) -> None:
    with (directory / filename).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(fields)
        writer.writerows(rows)


def rules() -> dict:
    return {
        'schema_version': SCHEMA_VERSION, 'synthetic': True,
        'generation_seed': SEED,
        'time_step_h': 1, 'historical_start_time_h': -72,
        'decision_start_time_h': 0, 'decision_end_time_h_exclusive': 168,
        'initial_chlorine_mg_L': .75, 'initial_water_age_h': 12,
        'initial_water_age_distribution': 'point_mass_at_12_h_everywhere',
        'initial_water_temperature_C': 24,
        'source_capacity_m3_h': 8,
        'flush_start_hour': 6, 'flush_end_hour_exclusive': 22,
        'max_simultaneous_flush_ports': 2,
        'weekly_flush_budgets_m3': [60,120,180],
        'nominal_service_chlorine_target_mg_L': .20,
        'wall_rate_temperature_factor_per_5C': 1.35,
        'wall_rate_reference_temperature_C': 20,
        'capacity_demand_factor': 1.25,
        'uncertainty_demand_factor_min': .75,
        'uncertainty_demand_factor_max': 1.25,
        'uncertainty_source_chlorine_offset_min_mg_L': -.05,
        'uncertainty_source_chlorine_offset_max_mg_L': .05,
        'uncertainty_water_temperature_offset_min_C': -2,
        'uncertainty_water_temperature_offset_max_C': 2,
        'source_chlorine_physical_bounds_mg_L': [.55,.95],
        'water_temperature_physical_bounds_C': [18,32],
        'historical_flush_m3_h': 0,
        'water_temperature_applies_to': 'all_pipes_and_tanks_at_this_time',
        'tank_volume_policy': 'constant; outlet_total_equals_inlet_total',
        'flush_action_policy': 'each_hour_constant_rate_at_user_terminal; continuous_rate',
        'flush_water_quality_policy': 'advects_water_only; wall_decay_rates_unchanged',
        'capacity_policy': 'all_downstream_demand_and_flush; verify_with_1.25_times_nominal_demand',
        'uncertainty_information_policy': 'hour_t_actual_demand_not_known_when_setting_hour_t_action; current_source_and_water_temperature_known; past_actual_demand_available',
        'clock_policy': 'hour_of_day=time_h_mod_24; interval=[time_h,time_h+1)',
        'bottle_detection_limit_mg_L': .005,
        'chlorine_measurement_resolution_mg_L': .0001,
        'tracer_measurement_resolution': .0001,
        'tracer_measurement_std': .007,
        'laboratory_role_policy': 'calibration_rows_only_for_fitting; validation_rows_for_external_validation',
        'license': 'CC0-1.0 (synthetic attachments and documentation)',
    }


README = r'''# 合成附件与数据字典

本目录全部数值是为原创训练题设计的**合成数据**，不来自实际水厂、现场监测或第三方数据集。地点、用户与设施均为虚构，不能据此推断真实供水系统的安全性。设定用于研究低需求下的余氯输运和有限排放；浓度目标 0.20 mg/L 是本题管理目标，不宣称为某地区法律限值。

全部附件由 `../scripts/generate_data.py` 以 Python 标准库确定性生成；随机种子为 20261013（瓶试和示踪分别使用该种子与该种子加一）。使用 `python3 scripts/generate_data.py` 在题目根目录重建；`python3 scripts/check_data.py` 执行结构、范围、守恒、容量及重生成检查。所有CSV采用UTF-8、逗号分隔、点号小数和LF换行。无需下载其他数据。合成附件和本说明以 CC0-1.0 发布；生成与检查代码许可见文件头及题目README。

## 时钟、量与控制口径

时间单位为小时；流量为 m³/h；浓度为 mg/L；容积为 m³；温度为 °C。`time_h=-72,...,-1` 是3日正常需求历史，`0,...,167` 是7日低需求决策期；`time_h=0` 表示第1日00:00，`hour_of_day=time_h % 24`，`day_index=floor(time_h/24)`（历史为 -3,-2,-1）。CSV第 t 行的输入在区间 [t,t+1) 恒定。初态为 t=-72 时全管道与水箱余氯 0.75 mg/L，水龄分布在每处均为 12h 的点质量；这是明确的训练假定，不是现场测得。该时刻输入温度为24°C、源余氯为0.75mg/L。

`water_temperature_C` 为该小时**全网络统一的水温工况**，不只是入口水温；本题不求解传热。网络一直保持充满、保压，无流向反转。水箱恒水位，其总进流量等于总出流量。各用户的正常用水量为 `demands.csv` 中流量；末端冲洗是额外排放，并计入沿途全部管段、水箱出入流量与源流量。管道流量上限是设施已认证的允许值，只约束总下游流量，本题无需由粗糙度推算压力损失。

每口每小时固定额外排放速率 0≤u≤2.2 m³/h，任一小时正排放口至多2个；仅每日6≤hour_of_day<22允许排放。周预算60/120/180m³分别评价，不互相累加。历史无冲洗。所有容量在**当小时名义需求的1.25倍加已选择排放**下检查，不允许事先获知该小时需求扰动再设定该小时动作。关闭所有冲洗的正常历史和低需求期都满足该容量要求。冲洗只换水，不改变本题管壁衰减率。

## 文件与字段

- `network_nodes.csv`：`node_id`唯一节点ID；`node_type`为source/junction/tank/user；`label`是中文展示名。共S、J、T1/T2、U1..U6十个节点。
- `pipes.csv`：`pipe_id,from_node,to_node`定义有向管段；`length_m,diameter_m`是内长、内径；`volume_m3=πD²L/4`（保留6位小数）；`material`为PE或ductile_iron；`flow_limit_m3_h`是认证总流量上限；`wall_rate20_min_h_1,wall_rate20_max_h_1`是20°C时整个管段对余氯的**有效附加一阶衰减率**区间，单位h⁻¹。它已经包含表面积/体积效应，不能再乘4/D。两端不是估计结果或真实答案；缺少独立管壁实验，选手应自行讨论该区间。温度换算统一乘1.35^((Tw−20)/5)。水箱壁衰减在本题忽略。
- `tanks.csv`：`tank_id,working_volume_m3`给定恒定工作容积；`level_policy=constant`。不公开网络运行期间任何箱内或用户余氯真值。
- `users.csv`：`user_id,tank_id`定义服务关系；`normal_mean_reference_m3_h`是构造需求曲线时的参考均值（不是每周观测均值）；`flush_max_m3_h`是该口额外排放上限。
- `forcing.csv`：`time_h,day_index,hour_of_day,stage,source_chlorine_mg_L,water_temperature_C`，共240行，无缺测。stage为normal_history或low_demand。源浓度为两周期的平滑组合，水温含昼夜变化和决策期缓慢升温；CSV为具体输入，生成公式不是反演对象。
- `demands.csv`：`time_h,user_id,nominal_demand_m3_h`，共1440行。正常曲线由归一化24小时形状、用户错峰和小幅每日变化形成；低需求阶段整体为该正常曲线的0.36倍。本题不要求预测名义曲线；曲线是可用计划输入。
- `bottle_tests.csv`：`batch_id,replicate_id,water_temperature_C,nominal_initial_chlorine_mg_L,sample_time_h,measured_chlorine_mg_L,role`。3温度×2初浓度×3独立平行瓶×9时点，共162行，无缺测。每组温度和初浓度下第1、2瓶是calibration，第3瓶是validation；同一瓶各时点连续观测，不能把同瓶时点当独立实验重复。瓶试不含管壁反应。浓度均高于0.005mg/L检出限；固定报告分辨率0.0001mg/L。
- `tank_tracer.csv`：`experiment_id,tank_id,role,flow_m3_h,sample_time_h,inlet_step_value,measured_outlet_fraction,measurement_status`。每箱2个标定流量和1个留出低流量，共6试验×16时点=96行。入口示踪在t=0从0阶跃至1、初始箱内为0，`inlet_step_value=1`是阶跃后的入口值；试验全程恒流、恒容积，不含任何化学衰减。出口是归一化保守示踪浓度。标定试验中各有一个缺测值，单元格为空且status=missing；其余status=observed。缺测不是零。t=0出口设置为0；后续加入量测误差，故不要求每条观测曲线严格单调；范围截断至[0,1]。validation表示第三个低流工况，拟合不得使用；末端未必达到1，尾部可延续到200h以后。
- `operating_rules.json`：机器可读控制、初态、管理目标和扰动界。温度±2°C、源浓度±0.05mg/L、需求系数[0.75,1.25]是鲁棒性评估界，非概率分布；物理裁剪界为温度[18,32]、浓度[0.55,0.95]。本题不提供唯一场景概率。

## 合成机制与合理性边界

生成器只建立外部输入、独立瓶试和孤立水箱示踪；**不包含网络输运求解器、网络余氯真值、最佳冲洗方案或评分答案**。

瓶试合成以一阶损耗与浓度相关损耗并存的独立瓶机制为基础，随温度升高反应加快；设定为明确的高反应性合成水质，速率不是某权威机构的实测结果。独立瓶对反应速率、初始剂量存在小幅随机变动，再加入0.002mg/L量级的加性量测噪声。具体公式、常量、温度修正及扰动分布集中写在公开生成器中，便于完整复现和检查；这些构造假定不强制指定网络反应模型。数据允许评价较简洁的有效一阶近似和更复杂形式，拟合与验证应分瓶进行。

示踪合成采用两条并行混合通道，以不均匀流量分配产生较快响应和慢尾部；两通道体积之和等于已知工作容积，流量之和等于给定实验流量，各通道分别满足保守示踪物质量守恒。具体比例和响应计算集中写在公开生成器中。T1标定试验q=0.7、2.4m³/h，留出q=0.42；T2标定试验q=0.6、2.0，留出q=0.36。观测叠加标准差0.007的独立噪声（并截断至[0,1]），由此存在小量非单调。低流时较慢尾部在200h以后仍可延续；不能把截断观测直接视为响应完全结束。如何把孤立试验推广到时变网络及模型复杂度的取舍，仍由参赛者判断。

`validation` 标签用于规范模型建立与方法比较。由于合成构造机制及完整生成器已经公开，这不是保密盲测，也不能宣称是独立现场验证。参赛队应声明是否参考了生成机制，并把对新运行条件的推断边界与方法验证区分清楚。同一瓶连续时点不能视为独立重复，独立瓶之间亦共享批次条件。

公开生成机制不提供隐藏的唯一网络答案。全部网络参数、扰动界和初态均为明确训练设定；真实供水系统可能具有不同水力、混合、反应与监测条件。必要的机制简化应在论文中说明。检查脚本核查生成设计中的守恒关系，不用生成参数替代参赛论文的模型验证。
'''


def build(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_csv(directory, 'network_nodes.csv', ['node_id','node_type','label'],
              [['S','source','供水入口'], ['J','junction','分流点'],
               ['T1','tank','在线水箱1'], ['T2','tank','在线水箱2']]
              + [[u[0],'user',f'用户末端{u[0][1:]}'] for u in USERS])
    write_csv(directory, 'pipes.csv', ['pipe_id','from_node','to_node','length_m','diameter_m',
              'volume_m3','material','flow_limit_m3_h','wall_rate20_min_h_1','wall_rate20_max_h_1'],
              [[p[0],p[1],p[2],p[3],fnum(p[4]),fnum(math.pi*p[4]**2*p[3]/4),
                p[5],fnum(p[6]),fnum(p[7]),fnum(p[8])] for p in PIPES])
    write_csv(directory, 'tanks.csv', ['tank_id','working_volume_m3','level_policy'],
              [[t[0],fnum(t[1]),'constant'] for t in TANKS])
    write_csv(directory, 'users.csv', ['user_id','tank_id','normal_mean_reference_m3_h','flush_max_m3_h'],
              [[u[0],u[1],fnum(u[2]),fnum(2.2)] for u in USERS])
    forcing = []
    demands = []
    mean_shape = sum(DAILY_SHAPE)/24
    for time_h in range(-72,168):
        hour = time_h % 24
        day = time_h // 24
        stage = 'normal_history' if time_h < 0 else 'low_demand'
        source = .75 + .025*math.sin(2*math.pi*hour/24) + .015*math.sin(2*math.pi*(time_h+72)/96)
        temp = 24 + 1.7*math.sin(2*math.pi*hour/24) + (3*time_h/167 if time_h >= 0 else 0)
        forcing.append([time_h,day,hour,stage,fnum(source),fnum(temp)])
        for user, tank, base, shift in USERS:
            shape = DAILY_SHAPE[(hour+shift)%24] / mean_shape
            day_factor = 1+.035*math.sin(2*math.pi*(day+3)/7+.3*int(user[1:]))
            demand = base*shape*day_factor*(1 if time_h < 0 else .36)
            demands.append([time_h,user,fnum(demand)])
    write_csv(directory, 'forcing.csv', ['time_h','day_index','hour_of_day','stage',
              'source_chlorine_mg_L','water_temperature_C'], forcing)
    write_csv(directory, 'demands.csv', ['time_h','user_id','nominal_demand_m3_h'], demands)
    rng = random.Random(SEED)
    bottles = []
    for temperature in [20,25,30]:
        for nominal_initial in [.4,.85]:
            for rep in [1,2,3]:
                a = BOTTLE_A20_H_1*BOTTLE_A_FACTOR_PER_5C**((temperature-20)/5)*(1+rng.uniform(-.035,.035))
                b = BOTTLE_B20_L_MG_H*BOTTLE_B_FACTOR_PER_5C**((temperature-20)/5)*(1+rng.uniform(-.08,.08))
                initial = nominal_initial*(1+rng.uniform(-.008,.008))
                role = 'validation' if rep == 3 else 'calibration'
                for time_h in BOTTLE_TIMES:
                    decay = math.exp(-a*time_h)
                    latent = initial*decay/(1+b*initial/a*(1-decay))
                    observed = max(0,latent+rng.gauss(0,.002))
                    batch = f'B{temperature}_{round(nominal_initial*100):02d}'
                    bottles.append([batch,rep,temperature,fnum(nominal_initial,2),time_h,
                                    fnum(observed,4),role])
    write_csv(directory, 'bottle_tests.csv', ['batch_id','replicate_id','water_temperature_C',
              'nominal_initial_chlorine_mg_L','sample_time_h','measured_chlorine_mg_L','role'], bottles)
    rng = random.Random(SEED+1)
    tracer = []
    for tank, volume, fraction_volume, fraction_flow, flows in TANKS:
        for experiment, flow in enumerate(flows,1):
            role = 'validation' if experiment == 3 else 'calibration'
            for time_h in TRACER_TIMES:
                fraction = (fraction_flow*(1-math.exp(-fraction_flow*flow*time_h/(fraction_volume*volume)))
                            +(1-fraction_flow)*(1-math.exp(-(1-fraction_flow)*flow*time_h/((1-fraction_volume)*volume))))
                observed = 0 if time_h == 0 else min(1,max(0,fraction+rng.gauss(0,.007)))
                missing = (experiment == 1 and time_h == 16) or (experiment == 2 and time_h == 32)
                tracer.append([f'{tank}_E{experiment}',tank,role,fnum(flow),time_h,1,
                               '' if missing else fnum(observed,4),'missing' if missing else 'observed'])
    write_csv(directory, 'tank_tracer.csv', ['experiment_id','tank_id','role','flow_m3_h',
              'sample_time_h','inlet_step_value','measured_outlet_fraction','measurement_status'], tracer)
    (directory/'operating_rules.json').write_text(json.dumps(rules(), ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    (directory/'README.md').write_text(README,encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1]/'data')
    args = parser.parse_args()
    build(args.output_dir)
    print(f'Generated synthetic attachments in {args.output_dir}')


if __name__ == '__main__':
    main()
