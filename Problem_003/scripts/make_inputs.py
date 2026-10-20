#!/usr/bin/env python3
"""重建题设参数附件；不生成运行观测、求解代码或设计方案。"""

import sys

sys.dont_write_bytecode = True

import argparse
import csv
import io
import json
from pathlib import Path


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def csv_bytes(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def build_files():
    parameters = {
        "schema_version": 1,
        "parameter_status": "题设设计参数，非实测数据；用于方案比较，不代表任何实际产品的标定或认证。",
        "mechanical": {
            "wheel_radius_m": 0.16,
            "base_mass_kg": 180,
            "wheel_axle_inertia_kg_m2": 0.20,
            "generator_rotor_inertia_kg_m2": 0.012,
            "gravity_m_s2": 9.81,
            "rolling_resistance_coefficient": 0.012,
            "air_drag_coefficient_kg_m": 0.30,
            "base_mass_scope": "含固定构件及任一备选齿轮箱；不含载荷和散热包增加质量。",
            "wheel_axle_inertia_scope": "所有车轮与轮轴的总转动惯量，不含发电机转子。",
            "gear_ratio_definition": "q = 发电机机械角速度 / 轮轴角速度。",
        },
        "generator": {
            "phase_count": 3,
            "phase_order": ["a", "b", "c"],
            "pole_pairs": 4,
            "phase_flux_peak_wb": 0.24,
            "inductance_matrix_h": [[0.003, -0.001, -0.001], [-0.001, 0.003, -0.001], [-0.001, -0.001, 0.003]],
            "inductance_matrix_definition": "矩阵每项单位均为 H；行、列按 a、b、c 相排序，包含自感和互感。矩阵在题设工况内不随位置、电流或温度变化。",
            "phase_copper_resistance_20c_ohm": 0.24,
            "copper_temp_coefficient_per_k": 0.00393,
            "copper_reference_temp_c": 20,
            "phase_flux_definition": "第 j 相永磁磁链为 psi*cos(theta-2*pi*(j-1)/3)，j=1,2,3 对应 a,b,c；theta=p*q*x/r+theta0。",
            "circuit_connection": "电机绕组 Y 接，三只相同外电阻 Y 接，两个星点互不连接，无中性线；无外部电源及功率电子控制。各相电流正向定义为从该相端口流向发电机星点 Ng。",
            "external_resistor_scope": "Re 是每相外电阻；Re=0 表示直接短接。三相外电阻均不随温度改变。",
        },
        "thermal": {
            "body_w": "全部绕组和规定的电机内部结构组成一个等温体 Tw。",
            "body_r": "三只外电阻及电阻箱规定结构共同组成一个等温体 Tr。",
            "capacity_unit": "J/K",
            "conductance_unit": "W/K",
            "capacity_and_conductance_scope": "每个 C、H 为相应整个热体的总量，不是单相值；不随运动或停歇改变。",
            "heat_input": "三相铜阻的总焦耳热进入 Tw；三相外电阻的总焦耳热进入 Tr；两热体之间不交换热量。",
            "cooling": "各热体分别向环境散热，散热功率为 H*(T-Ta)；摄氏温度之差与开尔文温差数值相同。",
        },
        "pricing": {
            "currency": "CNY",
            "external_box_fixed_cost_cny": 500,
            "external_box_cost_per_ohm_cny": 600,
            "external_box_cost_definition": "Re=0 时增加费用为 0；Re>0 时整套电阻箱增加费用为 500+600*Re 元。",
            "cost_scope": "仅比较题设设计增加费用；不是市场报价。总增加费用为齿轮选型、电阻箱与散热包费用之和。",
            "mass_scope": "基础电阻箱质量已计入基车；它的基础热参数计入 S 包。选型只增加 cooling_options.csv 中的质量。",
        },
        "idealizations": [
            "车轮无滑动，齿轮传动理想。",
            "滚阻为 mu*m*g*cos(beta)，风阻为 c*v^2；均阻碍下坡运动。",
            "忽略铁耗、磁饱和、永磁磁链的温度变化和齿轮损耗。",
            "坡度节点间线性插值角度；题给滚阻是等效近似，不另计坡度曲率力。",
        ],
    }
    routes = []
    for route, points in {
        "A": [(0, 4.5), (10, 4.5), (13, 10), (37, 10), (40, 4.5), (180, 4.5)],
        "B": [(0, 4.5), (100, 4.5), (103, 10), (127, 10), (130, 4.5), (180, 4.5)],
    }.items():
        routes.extend({"route_id": route, "x_m": x, "slope_deg": slope} for x, slope in points)
    gears = [
        {"q": 1, "added_cost_cny": 0},
        {"q": 1.5, "added_cost_cny": 700},
        {"q": 2, "added_cost_cny": 2000},
        {"q": 2.5, "added_cost_cny": 2800},
    ]
    cooling = [
        {"cooling_id": "S", "added_mass_kg": 0, "Cw_J_K": 5000, "Hw_W_K": 1.5, "Cr_J_K": 900, "Hr_W_K": 1.2, "added_cost_cny": 0},
        {"cooling_id": "M", "added_mass_kg": 5, "Cw_J_K": 5000, "Hw_W_K": 3, "Cr_J_K": 1800, "Hr_W_K": 3, "added_cost_cny": 900},
        {"cooling_id": "L", "added_mass_kg": 12, "Cw_J_K": 6500, "Hw_W_K": 5, "Cr_J_K": 3000, "Hr_W_K": 6, "added_cost_cny": 1800},
    ]
    rules = {
        "schema_version": 1,
        "parameter_status": "题设运行条件和设计限制，非实测数据。",
        "route": {"length_m": 180, "ids": ["A", "B"], "slope_interpolation": "按 x_m 对 slope_deg 线性插值；降高为沿线路对 sin(beta) 的积分，不能线性插值高度。"},
        "design": {"q_values": [1, 1.5, 2, 2.5], "Re_ohm_range": [0, 1.2], "cooling_ids": ["S", "M", "L"]},
        "reference_design": {"q": 1, "Re_ohm": 0, "cooling": "S"},
        "task_1": {"fixed_winding_temp_c": 20, "include_air_drag": False, "uniform_slope_deg": [4.5, 10], "payload_kg": [40, 100]},
        "task_2": {"ambient_temp_c": 20, "initial_Tw_c": 20, "initial_Tr_c": 20, "entry_speed_m_s": 0, "theta0_rad": 0, "payload_kg": [40, 100], "run_count_each_case": 1},
        "normal_operation": {
            "ambient_temp_c": 35,
            "initial_Tw_c": 35,
            "initial_Tr_c": 35,
            "payload_kg_range": [40, 100],
            "entry_speed_m_s_range": [0, 0.4],
            "theta0_rad": 0,
            "initial_phase_current_a": [0, 0, 0],
            "run_count_each_case": 10,
            "release_interval_s": 360,
            "return_and_loading_time_s": 45,
            "travel_time_limit_s": 300,
            "payload_and_entry_speed_fixed_within_case": True,
            "routes_tested_separately": True,
            "temperature_inherited_between_runs": True,
            "next_release_phase_current_a": [0, 0, 0],
            "assessment_end_after_last_release_s": 360,
        },
        "arrival_and_wait": {
            "stop_position_m": 180,
            "mechanical_stop": "独立机械装置即时停止车辆并锁住发电机转子；所消耗机械动能不进入 Tw 或 Tr。",
            "electrical_state": "电路仍连接，停靠后的电流自由衰减；其焦耳热仍进入相应热体。",
            "return_drive": "外部牵引回程时与发电机制动系统机械脱开，回程及装卸共 45 s。",
            "waiting_state": "回程和等待时保持相同散热条件，不加外部热；停歇远长于电气时间常数，下一次电流按零初始化。",
        },
        "limits": {"speed_m_s": 3, "winding_temp_c": 90, "resistor_temp_c": 100, "absolute_phase_current_a": 50},
        "fault_operation": {
            "completed_normal_runs_before_fault": 9,
            "prehistory_payload_kg": 100,
            "prehistory_entry_speed_m_s": 0,
            "failed_phase": "a",
            "fault_timing": "第十次放行前 a 相与负载的连接已断开，不模拟带电开断瞬态。",
            "remaining_circuit": "b、c 相连接不变；两个 Y 星点无中线。",
            "payload_kg_range": [0, 100],
            "entry_speed_m_s_range": [0, 0.4],
            "theta0_rad_range": [0, 6.283185307179586],
            "all_initial_conditions_required": True,
            "initial_phase_current_a": [0, 0, 0],
            "initial_temperature": "继承同一线路、该设计在九次指定正常运输后第十次放行前的 Tw、Tr。",
            "travel_time_limit_applies": False,
            "return_time_applies": False,
            "assessed_quantities": ["speed_m_s", "winding_temp_c", "resistor_temp_c", "absolute_phase_current_a"],
            "assessment_interval": "从第十次放行至到达终点停车；不考核该次后的回程。",
        },
    }
    return {
        "parameters.json": json_bytes(parameters),
        "routes.csv": csv_bytes(["route_id", "x_m", "slope_deg"], routes),
        "gear_options.csv": csv_bytes(["q", "added_cost_cny"], gears),
        "cooling_options.csv": csv_bytes(["cooling_id", "added_mass_kg", "Cw_J_K", "Hw_W_K", "Cr_J_K", "Hr_W_K", "added_cost_cny"], cooling),
        "rules.json": json_bytes(rules),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data", help="输出目录（默认本题 data/）")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, content in build_files().items():
        (args.output / name).write_bytes(content)
    print(json.dumps({"status": "PASS", "output_directory": str(args.output), "files": list(build_files())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
