#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check prescribed inputs and exact reproduction, not transport performance."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from make_inputs import build_files, HEADERS, CAMPUS


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path, fields):
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        need(reader.fieldnames == fields, '字段或顺序不符: ' + path.name)
        rows = list(reader)
    need(all(None not in row and None not in row.values() for row in rows), 'CSV行列不符: ' + path.name)
    return rows


def check(directory, seed_offset=0):
    directory = Path(directory)
    tables = {name: read_csv(directory / name, fields) for name, fields in HEADERS.items()}
    rules = json.loads((directory / 'rules.json').read_text(encoding='utf-8'))
    need(rules['schema_version'] == 1 and '训练设定' in rules['status'], '缺少版本或输入性质声明')
    need(rules['time']['horizon_s'] == 7200 and rules['time']['arrival_end_s_exclusive'] == 5400,
         '观察时间或到站截止不符')
    need(rules['service']['freeze_queue_at_arrival'] is True, '未冻结到站时的候选队列')
    need(rules['random_generation']['seed_offset'] == seed_offset, 'seed_offset与检查参数不符')
    stop_sets = {}
    for campus, c in CAMPUS.items():
        stops = [row for row in tables['stops.csv'] if row['campus_id'] == campus]
        n = len(c['names'])
        stop_sets[campus] = set(range(n))
        need(len(stops) == n and {int(x['stop_id']) for x in stops} == stop_sets[campus], '站点缺失或重复')
        need(all(int(x['control_allowed']) == int(int(x['stop_id']) in (0, 4)) for x in stops), '控车站点错误')
        links = [row for row in tables['links.csv'] if row['campus_id'] == campus]
        need(len(links) == n and {int(x['from_stop']) for x in links} == stop_sets[campus], '路段缺失或重复')
        need(all(int(x['to_stop']) == (int(x['from_stop']) + 1) % n and int(x['base_travel_s']) > 0
                 for x in links), '不是规定的正行时单向环线')
    need(len(tables['stops.csv']) == 17 and len(tables['links.csv']) == 17, '未知校区或额外路段')
    vehicles = {}
    for row in tables['vehicles.csv']:
        campus, bus = row['campus_id'], row['bus_id']
        need(campus in CAMPUS and bus not in vehicles, '车辆归属错误或重复')
        need(int(row['seats']) == 14, '座位数错误')
        need(all(math.isfinite(float(row[k])) and float(row[k]) > 0
                 for k in ('driver_factor_before', 'driver_factor_after')), '司机系数无效')
        need(0 <= int(row['handover_start_s']) < int(row['handover_end_s']) - 120 <= 7200, '交班窗口无效')
        vehicles[bus] = row
    need(set(vehicles) == {f'{campus}{i+1}' for campus, c in CAMPUS.items() for i in range(c['buses'])},
         '车队缺失或含多余车辆')
    plans = tables['baseline_plan.csv']
    need(len(plans) == len(vehicles) and {row['bus_id'] for row in plans} == set(vehicles), '对照方案车辆不完整')
    for row in plans:
        bus = row['bus_id']
        need(row['campus_id'] == vehicles[bus]['campus_id'], '对照方案跨校区调车')
        need(int(row['first_service_s']) == 120 * (int(bus[1:]) - 1) and int(row['base_hold_s']) == 0,
             '对照方案不符')
    cases = {row['case_id']: row for row in tables['cases.csv']}
    expected_cases = {f'{campus}_{suffix}' for campus in CAMPUS for suffix in ('P1', 'P2', 'P3', 'N', 'R', 'E')}
    need(len(cases) == len(tables['cases.csv']) == 12 and set(cases) == expected_cases, '工况缺失、未知或重复')
    for case, row in cases.items():
        campus, suffix = case.split('_')
        need(row['campus_id'] == campus, '工况校区错误')
        need(row['role'] == ('planning' if suffix.startswith('P') else 'validation'), '工况用途错误')
        need(row['scenario'] == {'R': 'rain', 'E': 'event'}.get(suffix, 'normal'), '工况类型错误')
    requests = {case: [] for case in cases}
    pairs = set()
    for row in tables['passenger_requests.csv']:
        case, request = row['case_id'], row['request_id']
        need(case in cases and (case, request) not in pairs, '未知工况或请求标识重复')
        pairs.add((case, request))
        campus = cases[case]['campus_id']
        arrival, origin, destination, deadline = (int(row[k]) for k in
                                                 ('arrival_s', 'origin_stop', 'destination_stop', 'deadline_s'))
        need(0 <= arrival < 5400 and arrival < deadline < 7200, '到站或完成下车期限无效')
        need(origin in stop_sets[campus] and destination in stop_sets[campus] and origin != destination, 'OD无效')
        c, n = CAMPUS[campus], len(stop_sets[campus])
        hops = (destination - origin) % n
        od_base = sum(c['links'][(origin + i) % n] for i in range(hops))
        need(deadline - arrival - (24 * od_base + 24) // 25 - 10 * (hops + 1) - 5
             in (240, 360, 480, 600), '期限的松弛时间不在规定集合')
        requests[case].append((request, arrival, origin, destination, deadline))
    need(all(rows for rows in requests.values()), '存在空请求工况')
    factors = {case: {} for case in cases}
    for row in tables['link_factors.csv']:
        case = row['case_id']
        need(case in cases, '路段系数属于未知工况')
        campus = cases[case]['campus_id']
        t0, t1, i, j = (int(row[k]) for k in ('block_start_s', 'block_end_s', 'from_stop', 'to_stop'))
        value = float(row['factor'])
        need(t0 in range(0, 7200, 300) and t1 == t0 + 300 and i in stop_sets[campus]
             and j == (i + 1) % len(stop_sets[campus]), '路段系数时轴或边错误')
        need(math.isfinite(value) and value > 0 and (t0, i) not in factors[case], '路段系数无效或重复')
        factors[case][t0, i] = value
    for case in cases:
        campus = cases[case]['campus_id']
        need(set(factors[case]) == {(t, i) for t in range(0, 7200, 300) for i in stop_sets[campus]},
             '路段系数未覆盖全部边和时段')
    for campus, c in CAMPUS.items():
        normal, rain, event = [f'{campus}_{suffix}' for suffix in ('N', 'R', 'E')]
        need(requests[normal] == requests[rain], 'R不得改变正常请求')
        regular_event = [r for r in requests[event] if r[0].startswith('R')]
        extra = [r for r in requests[event] if r[0].startswith('X')]
        need(regular_event == requests[normal] and len(extra) == c['extra'], 'E的常规或追加请求不符')
        need(all(2100 <= r[1] < 2400 and r[2] == c['event_origin']
                 and (r[3] - r[2]) % len(c['names']) in (2, 3) for r in extra), '活动追加请求不符')
        for case in (rain, event):
            need([r for r in requests[case] if r[1] < 1800] == [r for r in requests[normal] if r[1] < 1800],
                 'N/R/E请求共同前缀不一致')
        need(factors[event] == factors[normal], 'E不得改变路段系数')
        for key, value in factors[normal].items():
            multiplier = 1.25 if key[0] >= 1800 else 1.0
            need(abs(factors[rain][key] - value * multiplier) < 5.1e-7, 'R路段系数变化不符')
    hashes = {}
    for name, content in build_files(seed_offset).items():
        need((directory / name).read_bytes() == content, '确定性重生成不一致: ' + name)
        hashes[name] = hashlib.sha256(content).hexdigest()
    return {'status': 'PASS', 'machine_files': 8, 'stops': len(tables['stops.csv']),
            'vehicles': len(vehicles), 'cases': len(cases), 'requests': len(pairs),
            'link_factor_rows': len(tables['link_factors.csv']), 'seed_offset': seed_offset,
            'common_prefix_before_1800s': 'PASS', 'byte_reproducible': True, 'sha256': hashes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    parser.add_argument('--seed-offset', type=int, default=0)
    args = parser.parse_args()
    try:
        result = check(args.data_dir, args.seed_offset)
    except (ValueError, KeyError, TypeError, OSError, csv.Error) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
