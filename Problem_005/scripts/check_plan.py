#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check one fixed pre-operation plan; do not judge transport performance."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import json
from pathlib import Path
from check_inputs import need, read_csv
from make_inputs import HEADERS


def check(plan, directory):
    directory = Path(directory)
    vehicles = {r['bus_id']: r for r in read_csv(directory / 'vehicles.csv', HEADERS['vehicles.csv'])}
    rows = read_csv(Path(plan), HEADERS['baseline_plan.csv'])
    need(len(rows) == len(vehicles) and len({r['bus_id'] for r in rows}) == len(rows),
         '每辆车须且只能出现一次，两校区全部车辆均须给出')
    need({r['bus_id'] for r in rows} == set(vehicles), '车辆缺失或未知')
    for row in rows:
        need(row['campus_id'] == vehicles[row['bus_id']]['campus_id'], '不可跨校区调车')
        first, hold = int(row['first_service_s']), int(row['base_hold_s'])
        need(0 <= first <= 600 and 0 <= hold <= 60, '首次服务或固定回场等候超界')
    return {'status': 'PASS', 'vehicles': len(rows),
            'scope': '仅核对车辆归属、完整性、整数时刻和动作范围；未检验客流、乘降、容量、交班或服务表现。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    args = parser.parse_args()
    try:
        result = check(args.plan, args.data_dir)
    except (ValueError, KeyError, TypeError, OSError, csv.Error) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
