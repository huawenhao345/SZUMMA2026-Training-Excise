#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check declarations, declared action bounds and a necessary causal-prefix test."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import json
from pathlib import Path
from check_inputs import need, read_csv
from make_inputs import HEADERS

ACTION_FIELDS = ['case_id', 'event_index', 'time_s', 'bus_id', 'stop_id', 'ready_s',
                 'reserve_seats', 'extra_hold_s', 'handover', 'delayed_cutoff_s']
DECLARATION_FIELDS = {'schema_version', 'task', 'information_delay_s', 'controller_name',
                      'instant_fields', 'delayed_fields', 'planning_cases', 'uses_case_id',
                      'uses_future_truth', 'uses_waiting_individual_od_or_deadline',
                      'logs_all_arrival_decisions'}


def check(log, declaration, directory):
    directory = Path(directory)
    rules = json.loads((directory / 'rules.json').read_text(encoding='utf-8'))
    declaration = json.loads(Path(declaration).read_text(encoding='utf-8'))
    need(isinstance(declaration, dict) and set(declaration) == DECLARATION_FIELDS, '声明字段缺失或多余')
    need(type(declaration['schema_version']) is int and declaration['schema_version'] == 1
         and type(declaration['task']) is int and declaration['task'] in (3, 4), '声明版本或任务不符')
    delay = declaration['information_delay_s']
    need(isinstance(delay, int) and not isinstance(delay, bool) and delay in (0, 60, 120), '信息延迟须为0/60/120整数秒')
    need(isinstance(declaration['controller_name'], str) and bool(declaration['controller_name'].strip()), '缺少控制器名称')
    for key in ('instant_fields', 'delayed_fields'):
        values = declaration[key]
        need(isinstance(values, list) and all(isinstance(v, str) for v in values)
             and len(values) == len(set(values))
             and set(values) <= set(rules['information'][key]), '使用未知或重复的信息字段: ' + key)
    for key in ('uses_case_id', 'uses_future_truth', 'uses_waiting_individual_od_or_deadline'):
        need(declaration[key] is False, '声明使用禁止信息: ' + key)
    need(declaration['logs_all_arrival_decisions'] is True, '须声明记录所有到站决策')
    cases = {r['case_id']: r for r in read_csv(directory / 'cases.csv', HEADERS['cases.csv'])}
    training = declaration['planning_cases']
    need(isinstance(training, list) and all(isinstance(v, str) for v in training)
         and len(training) == len(set(training))
         and all(v in cases and cases[v]['role'] == 'planning' for v in training), '规划样本声明不符')
    vehicles = {r['bus_id']: r for r in read_csv(directory / 'vehicles.csv', HEADERS['vehicles.csv'])}
    counts = {}
    for row in read_csv(directory / 'stops.csv', HEADERS['stops.csv']):
        counts[row['campus_id']] = counts.get(row['campus_id'], 0) + 1
    rows = read_csv(Path(log), ACTION_FIELDS)
    need(bool(rows), '日志为空')
    groups = {case: [] for case, r in cases.items() if r['role'] == 'validation'}
    handovers = {case: set() for case in groups}
    indices = {case: set() for case in groups}
    for row in rows:
        case, bus = row['case_id'], row['bus_id']
        need(case in groups and bus in vehicles, '日志仅接受N/R/E验证样本和已知车辆')
        campus = cases[case]['campus_id']
        need(vehicles[bus]['campus_id'] == campus, '日志跨校区用车')
        index, time, stop, ready, reserve, hold, handover, cutoff = (int(row[k]) for k in
            ('event_index', 'time_s', 'stop_id', 'ready_s', 'reserve_seats', 'extra_hold_s', 'handover', 'delayed_cutoff_s'))
        need(index >= 0 and index not in indices[case], '决策事件序号重复或为负')
        indices[case].add(index)
        need(0 <= time <= 7200 and time <= ready and 0 <= stop < counts[campus], '日志时刻或站点无效')
        need(0 <= reserve <= 4 and 0 <= hold <= 90 and (stop in (0, 4) or hold == 0), '声明的预留/控车动作超界')
        need(cutoff <= time - delay, '声明的全网历史读取截止超前')
        need(handover in (0, 1), 'handover须为0或1')
        if declaration['task'] == 3:
            need(handover == 0, '第三问不启用交班')
        if handover:
            v = vehicles[bus]
            need(stop == 0 and int(v['handover_start_s']) <= ready <= int(v['handover_end_s']) - 120,
                 '声明的交班站点或ready时刻超界')
            need(bus not in handovers[case], '同车重复交班')
            handovers[case].add(bus)
        groups[case].append((index, time, bus, stop, ready, reserve, hold, handover, cutoff))
    need(all(groups.values()), '须提交两校区全部六个N/R/E日志')
    for case, actions in groups.items():
        need(actions == sorted(actions, key=lambda a: (a[1], a[2])) and
             [a[0] for a in actions] == sorted(a[0] for a in actions), '各工况须按time_s、bus_id排列并递增事件序号')
        if declaration['task'] == 4:
            campus = cases[case]['campus_id']
            need(handovers[case] == {b for b, v in vehicles.items() if v['campus_id'] == campus},
                 '第四问声明日志未给出每辆车的一次交班')
    for campus in counts:
        prefixes = [[a for a in groups[f'{campus}_{suffix}'] if a[1] < 1800] for suffix in ('N', 'R', 'E')]
        need(bool(prefixes[0]) and prefixes[0] == prefixes[1] == prefixes[2], '1800秒前共同前缀决策不一致或为空')
    return {'status': 'PASS', 'action_rows': len(rows), 'validation_cases': len(groups),
            'task': declaration['task'], 'information_delay_s': delay,
            'scope': '仅声明、动作边界及1800秒前共同前缀的必要检查；未核对真实车辆事件、日志完整性、容量、性能或代码是否偷读未来；不构成因果性全证明。'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--declaration', required=True, type=Path)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    args = parser.parse_args()
    try:
        result = check(args.log, args.declaration, args.data_dir)
    except (ValueError, KeyError, TypeError, OSError, csv.Error) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
