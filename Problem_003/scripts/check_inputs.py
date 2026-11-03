#!/usr/bin/env python3
"""检查参数附件结构、内部一致性与逐字节可复现性；不计算车辆运行。"""

import sys

sys.dont_write_bytecode = True

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from make_inputs import build_files


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite_number(value, label, minimum=None, strict=False):
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), f"{label} 必须为有限数值")
    if minimum is not None:
        require(value > minimum if strict else value >= minimum, f"{label} 超出允许范围")
    return float(value)


def read_csv(path, fields):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == fields, f"{path.name} 字段或字段顺序错误")
        rows = list(reader)
    require(all(None not in row and all(value is not None for value in row.values()) for row in rows), f"{path.name} 行列数错误")
    return rows


def check_spd(matrix):
    require(isinstance(matrix, list) and len(matrix) == 3 and all(isinstance(row, list) and len(row) == 3 for row in matrix), "电感矩阵必须为 3×3")
    for i in range(3):
        for j in range(3):
            finite_number(matrix[i][j], f"L[{i},{j}] (H)")
            require(abs(matrix[i][j] - matrix[j][i]) <= 1e-14, "电感矩阵必须对称")
    chol = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(i + 1):
            pivot = matrix[i][j] - sum(chol[i][k] * chol[j][k] for k in range(j))
            if i == j:
                require(pivot > 0, "电感矩阵不是正定矩阵")
                chol[i][j] = math.sqrt(pivot)
            else:
                chol[i][j] = pivot / chol[j][j]


def route_drop(points):
    total = 0.0
    for (x0, deg0), (x1, deg1) in zip(points, points[1:]):
        beta0, beta1 = math.radians(deg0), math.radians(deg1)
        if beta0 == beta1:
            total += (x1 - x0) * math.sin(beta0)
        else:
            total += (x1 - x0) * (math.cos(beta0) - math.cos(beta1)) / (beta1 - beta0)
    return total


def check_inputs(directory):
    parameters = json.loads((directory / "parameters.json").read_text(encoding="utf-8"))
    rules = json.loads((directory / "rules.json").read_text(encoding="utf-8"))
    require(parameters.get("schema_version") == 1 and rules.get("schema_version") == 1, "未知附件版本")
    require("非实测" in parameters["parameter_status"] and "非实测" in rules["parameter_status"], "缺少设计参数声明")
    mechanical = parameters["mechanical"]
    for field in ("wheel_radius_m", "base_mass_kg", "wheel_axle_inertia_kg_m2", "generator_rotor_inertia_kg_m2", "gravity_m_s2"):
        finite_number(mechanical[field], field, 0, strict=True)
    for field in ("rolling_resistance_coefficient", "air_drag_coefficient_kg_m"):
        finite_number(mechanical[field], field, 0)
    require(mechanical["rolling_resistance_coefficient"] < 1, "滚阻系数超出题设近似的合理范围")
    generator = parameters["generator"]
    require(generator["phase_count"] == 3 and generator["phase_order"] == ["a", "b", "c"], "相数或相序错误")
    require(isinstance(generator["pole_pairs"], int) and generator["pole_pairs"] > 0, "极对数错误")
    for field in ("phase_flux_peak_wb", "phase_copper_resistance_20c_ohm", "copper_temp_coefficient_per_k"):
        finite_number(generator[field], field, 0, strict=True)
    check_spd(generator["inductance_matrix_h"])
    require("H" in generator["inductance_matrix_definition"] and "a、b、c" in generator["inductance_matrix_definition"], "电感矩阵单位或相序定义缺失")
    require(parameters["thermal"]["capacity_unit"] == "J/K" and parameters["thermal"]["conductance_unit"] == "W/K", "热参数单位错误")
    require(parameters["pricing"]["currency"] == "CNY", "费用单位错误")

    route_rows = read_csv(directory / "routes.csv", ["route_id", "x_m", "slope_deg"])
    routes = {route: [] for route in rules["route"]["ids"]}
    for row in route_rows:
        require(row["route_id"] in routes, "未知线路")
        x, slope = float(row["x_m"]), float(row["slope_deg"])
        finite_number(x, "x_m", 0)
        finite_number(slope, "slope_deg", 0, strict=True)
        require(slope < 90, "坡度必须小于 90 度")
        routes[row["route_id"]].append((x, slope))
    for route, points in routes.items():
        require(len(points) >= 2 and points[0][0] == 0 and points[-1][0] == rules["route"]["length_m"], f"线路 {route} 端点不完整")
        require(all(right[0] > left[0] for left, right in zip(points, points[1:])), f"线路 {route} 节点未严格递增")
    drops = {route: route_drop(points) for route, points in routes.items()}
    require(max(drops.values()) - min(drops.values()) < 1e-11, "两线路的总降高不相同")
    require(routes["A"] != routes["B"], "两线路不应完全相同")

    gears = read_csv(directory / "gear_options.csv", ["q", "added_cost_cny"])
    q_values = [float(row["q"]) for row in gears]
    require(q_values == rules["design"]["q_values"] and len(set(q_values)) == len(q_values), "齿轮选项与规则不一致或重复")
    for row in gears:
        finite_number(float(row["q"]), "q", 0, strict=True)
        finite_number(float(row["added_cost_cny"]), "齿轮费用", 0)
    cooling = read_csv(directory / "cooling_options.csv", ["cooling_id", "added_mass_kg", "Cw_J_K", "Hw_W_K", "Cr_J_K", "Hr_W_K", "added_cost_cny"])
    require([row["cooling_id"] for row in cooling] == rules["design"]["cooling_ids"], "散热选项与规则不一致或重复")
    for row in cooling:
        for field in ("added_mass_kg", "added_cost_cny"):
            finite_number(float(row[field]), field, 0)
        for field in ("Cw_J_K", "Hw_W_K", "Cr_J_K", "Hr_W_K"):
            finite_number(float(row[field]), field, 0, strict=True)

    normal = rules["normal_operation"]
    require(normal["run_count_each_case"] == 10, "正常运输次数错误")
    require(normal["travel_time_limit_s"] + normal["return_and_loading_time_s"] < normal["release_interval_s"], "运行、回程与发车间隔互相冲突")
    require(normal["payload_kg_range"] == [40, 100] and normal["entry_speed_m_s_range"] == [0, 0.4], "正常工况范围错误")
    require(normal["payload_and_entry_speed_fixed_within_case"] is True and normal["routes_tested_separately"] is True and normal["temperature_inherited_between_runs"] is True, "正常试验继承或独立性规则缺失")
    require(normal["initial_phase_current_a"] == [0, 0, 0] and normal["next_release_phase_current_a"] == [0, 0, 0], "放行电流规则错误")
    require(normal["assessment_end_after_last_release_s"] == normal["release_interval_s"], "末次评估终点错误")
    fault = rules["fault_operation"]
    require(fault["all_initial_conditions_required"] is True, "故障载荷允许标准必须覆盖所有初始条件")
    require(fault["completed_normal_runs_before_fault"] == normal["run_count_each_case"] - 1 and fault["prehistory_payload_kg"] == 100 and fault["prehistory_entry_speed_m_s"] == 0, "故障前史错误")
    require(fault["payload_kg_range"] == [0, 100] and fault["entry_speed_m_s_range"] == normal["entry_speed_m_s_range"], "故障运行范围错误")
    require(fault["theta0_rad_range"][0] == 0 and abs(fault["theta0_rad_range"][1] - 2 * math.pi) < 1e-14, "故障初相位范围错误")
    require(fault["failed_phase"] == "a" and fault["travel_time_limit_applies"] is False and fault["return_time_applies"] is False, "故障电路或免考规则错误")
    require(set(fault["assessed_quantities"]) == set(rules["limits"]), "故障考核量与限值不一致")
    for field, value in rules["limits"].items():
        finite_number(value, field, 0, strict=True)
    re_range = rules["design"]["Re_ohm_range"]
    require(re_range == [0, 1.2], "外电阻范围错误")
    copper_resistance = generator["phase_copper_resistance_20c_ohm"] * (1 + generator["copper_temp_coefficient_per_k"] * (rules["limits"]["winding_temp_c"] - generator["copper_reference_temp_c"]))
    require(copper_resistance > 0, "允许温度上界的铜阻非正")

    hashes = {}
    for name, expected in build_files().items():
        actual = (directory / name).read_bytes()
        require(actual == expected, f"{name} 与确定性重生成结果不一致")
        hashes[name] = hashlib.sha256(actual).hexdigest()
    return {"status": "PASS", "machine_file_count": len(hashes), "csv_row_counts": {"routes": len(route_rows), "gear_options": len(gears), "cooling_options": len(cooling)}, "inductance_matrix": "symmetric_positive_definite", "equal_route_drop": True, "time_schedule_consistent": True, "byte_reproducible": True, "sha256": hashes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    try:
        result = check_inputs(args.data_dir)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
