#!/usr/bin/env python3
"""仅检查选型格式、允许范围以及费用和质量；不判断运行安全或设计可行性。"""

import sys

sys.dont_write_bytecode = True

import argparse
import csv
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), f"{label} 必须为有限数值")
    return float(value)


def read_options(path, id_field):
    with path.open(encoding="utf-8", newline="") as stream:
        return {row[id_field]: row for row in csv.DictReader(stream)}


def check_design(design, directory):
    require(isinstance(design, dict), "设计文件必须为 JSON 对象")
    require(set(design) == {"q", "Re_ohm", "cooling"}, "设计文件必须且只能包含 q、Re_ohm、cooling 三个字段")
    parameters = json.loads((directory / "parameters.json").read_text(encoding="utf-8"))
    rules = json.loads((directory / "rules.json").read_text(encoding="utf-8"))
    q, re_ohm = number(design["q"], "q"), number(design["Re_ohm"], "Re_ohm")
    require(q in rules["design"]["q_values"], "q 不是允许的齿轮比")
    require(rules["design"]["Re_ohm_range"][0] <= re_ohm <= rules["design"]["Re_ohm_range"][1], "Re_ohm 超出允许范围")
    cooling_id = design["cooling"]
    require(isinstance(cooling_id, str) and cooling_id in rules["design"]["cooling_ids"], "cooling 不是允许的散热包编号")
    gears = read_options(directory / "gear_options.csv", "q")
    gear = next(row for row in gears.values() if float(row["q"]) == q)
    cooling = read_options(directory / "cooling_options.csv", "cooling_id")[cooling_id]
    gear_cost = float(gear["added_cost_cny"])
    cooling_cost = float(cooling["added_cost_cny"])
    pricing = parameters["pricing"]
    box_cost = 0.0 if re_ohm == 0 else pricing["external_box_fixed_cost_cny"] + pricing["external_box_cost_per_ohm_cny"] * re_ohm
    added_mass = float(cooling["added_mass_kg"])
    return {
        "status": "PASS",
        "check_scope": "选型格式、允许范围、费用和质量；运行安全与设计可行性尚未检查。",
        "design": design,
        "added_cost_cny": {"gear": gear_cost, "external_box": box_cost, "cooling": cooling_cost, "total": gear_cost + box_cost + cooling_cost},
        "cooling_added_mass_kg": added_mass,
        "vehicle_mass_without_payload_kg": parameters["mechanical"]["base_mass_kg"] + added_mass,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path, help='JSON 文件，字段为 q、Re_ohm、cooling')
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    try:
        result = check_design(json.loads(args.design.read_text(encoding="utf-8")), args.data_dir)
    except (ValueError, KeyError, TypeError, OSError, StopIteration, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
