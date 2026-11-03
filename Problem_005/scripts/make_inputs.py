#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Recreate prescribed training inputs. This program contains no transport solver."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import io
import json
import math
import random
from pathlib import Path

CAMPUS = {
    'Y': {
        'names': ['南部宿舍片区', '西南出入口片区', '西侧教学片区', '北侧教学科研片区',
                  '北部体育片区', '东北教学片区', '东侧生活片区', '中部公共服务片区'],
        'links': [90, 105, 85, 110, 100, 95, 95, 100], 'buses': 5, 'rate': 7.2,
        'weights': [.32, .14, .17, .05, .06, .05, .08, .13], 'rotate': 4,
        'event_origin': 6, 'extra': 90, 'seed': 101,
    },
    'L': {
        'names': ['西北宿舍片区', '西侧教学片区', '西侧体育片区', '西南生活片区',
                  '南部教学片区', '东南出入口片区', '东部学院片区', '东北教学片区', '北部公共教学片区'],
        'links': [85, 80, 100, 105, 90, 110, 95, 90, 85], 'buses': 4, 'rate': 5.4,
        'weights': [.33, .11, .06, .08, .12, .05, .08, .09, .08], 'rotate': 5,
        'event_origin': 7, 'extra': 70, 'seed': 201,
    },
}
PROFILE = [.7, 1.1, 1.8, 1.6, 1.2, .6, .7, 1.2, 1.8, 1.5, .9, .5, .7, 1.2, 1.7, 1.2, .5, .3]
BEFORE = [1.00, 1.06, .96, 1.10, 1.02]
AFTER = [1.08, .98, 1.04, .95, 1.00]
HEADERS = {
    'stops.csv': ['campus_id', 'stop_id', 'stop_name', 'control_allowed'],
    'links.csv': ['campus_id', 'from_stop', 'to_stop', 'base_travel_s'],
    'vehicles.csv': ['campus_id', 'bus_id', 'seats', 'driver_factor_before', 'driver_factor_after',
                     'handover_start_s', 'handover_end_s'],
    'cases.csv': ['case_id', 'campus_id', 'role', 'scenario', 'paired_normal_case_id',
                  'event_start_s', 'event_extra_passengers', 'event_origin_stop'],
    'passenger_requests.csv': ['case_id', 'request_id', 'arrival_s', 'origin_stop', 'destination_stop', 'deadline_s'],
    'link_factors.csv': ['case_id', 'block_start_s', 'block_end_s', 'from_stop', 'to_stop', 'factor'],
    'baseline_plan.csv': ['campus_id', 'bus_id', 'first_service_s', 'base_hold_s'],
}


def poisson(rng, mean):
    threshold = math.exp(-mean)
    value, product = 0, 1.0
    while product > threshold:
        value += 1
        product *= rng.random()
    return value - 1


def deadline(c, arrival, origin, hops, rng):
    n = len(c['links'])
    route_time = sum(c['links'][(origin + k) % n] for k in range(hops))
    slack = rng.choices([240, 360, 480, 600], weights=[.1, .3, .4, .2])[0]
    return arrival + (24 * route_time + 24) // 25 + 10 * (hops + 1) + 5 + slack


def requests(c, seed):
    rng = random.Random(seed)
    arrivals = []
    for block, multiplier in enumerate(PROFILE):
        count = poisson(rng, c['rate'] * 5 * multiplier)
        arrivals.extend(block * 300 + rng.randrange(300) for _ in range(count))
    result = []
    n = len(c['links'])
    for index, arrival in enumerate(sorted(arrivals), 1):
        shift = c['rotate'] if 1800 <= arrival < 3600 else 0
        origin_base = rng.choices(range(n), weights=c['weights'])[0]
        origin = (origin_base + shift) % n
        if origin_base in (0, 1):
            hops = rng.choices([4, 5, 2], weights=[.55, .25, .20])[0]
        else:
            hops = rng.choices([1, 2, 3], weights=[.4, .4, .2])[0]
        result.append((f'R{index:06d}', arrival, origin, (origin + hops) % n,
                       deadline(c, arrival, origin, hops, rng)))
    return result


def factors(c, seed):
    rng = random.Random(seed)
    n = len(c['links'])
    return [(t, t + 300, i, (i + 1) % n, round(rng.uniform(.95, 1.08), 6))
            for t in range(0, 7200, 300) for i in range(n)]


def extra_requests(c, seed):
    rng = random.Random(seed)
    n, origin = len(c['links']), c['event_origin']
    rows = []
    arrivals = sorted(rng.randrange(2100, 2400) for _ in range(c['extra']))
    for index, arrival in enumerate(arrivals, 1):
        hops = rng.choice([2, 3])
        rows.append((f'X{index:06d}', arrival, origin, (origin + hops) % n,
                     deadline(c, arrival, origin, hops, rng)))
    return rows


def build_files(seed_offset=0):
    if not isinstance(seed_offset, int) or isinstance(seed_offset, bool) or seed_offset < 0:
        raise ValueError('seed_offset须为非负整数')
    data = {name: [] for name in HEADERS}
    seeds = {}
    for campus, c in CAMPUS.items():
        n = len(c['names'])
        for i, name in enumerate(c['names']):
            data['stops.csv'].append((campus, i, name, int(i in (0, 4))))
            data['links.csv'].append((campus, i, (i + 1) % n, c['links'][i]))
        for index in range(c['buses']):
            bus = f'{campus}{index + 1}'
            data['vehicles.csv'].append((campus, bus, 14, f'{BEFORE[index]:.2f}', f'{AFTER[index]:.2f}',
                                         1800 + 120 * index, 3600 + 120 * index))
            data['baseline_plan.csv'].append((campus, bus, 120 * index, 0))
        common_seed = c['seed'] + 10 + 100003 * seed_offset
        normal_requests = requests(c, common_seed * 100 + 1)
        normal_factors = factors(c, common_seed * 100 + 2)
        for suffix in ('P1', 'P2', 'P3', 'N', 'R', 'E'):
            case = f'{campus}_{suffix}'
            planning = suffix.startswith('P')
            seed = c['seed'] + int(suffix[1]) + 100003 * seed_offset if planning else common_seed
            seeds[case] = {'passengers': seed * 100 + 1, 'links': seed * 100 + 2}
            if suffix == 'E':
                seeds[case]['extra_passengers'] = seed * 100 + 3
            scenario = {'R': 'rain', 'E': 'event'}.get(suffix, 'normal')
            data['cases.csv'].append((case, campus, 'planning' if planning else 'validation', scenario,
                                      '' if planning else f'{campus}_N',
                                      1800 if suffix == 'R' else 2100 if suffix == 'E' else '',
                                      c['extra'] if suffix == 'E' else 0,
                                      c['event_origin'] if suffix == 'E' else ''))
            rr = requests(c, seed * 100 + 1) if planning else list(normal_requests)
            ff = factors(c, seed * 100 + 2) if planning else list(normal_factors)
            if suffix == 'R':
                ff = [(t0, t1, i, j, round(v * (1.25 if t0 >= 1800 else 1), 6))
                      for t0, t1, i, j, v in ff]
            if suffix == 'E':
                rr += extra_requests(c, seed * 100 + 3)
            for row in sorted(rr, key=lambda a: (a[1], a[0])):
                data['passenger_requests.csv'].append((case, *row))
            for t0, t1, i, j, value in ff:
                data['link_factors.csv'].append((case, t0, t1, i, j, f'{value:.6f}'))
    rules = {
        'schema_version': 1,
        'status': '全部数值、简化路网和运行规则为训练设定，非学校现行运营数据。',
        'source_note': '选题源于用户提供的一条去标识化问卷线索；功能区参考用户地图。原问卷、身份字段和地图不随题公开。',
        'time': {'unit': 'integer second', 'horizon_s': 7200, 'arrival_end_s_exclusive': 5400,
                 'initial_waiting': 0, 'initial_onboard': 0, 'initial_bus_stop': 0,
                 'entry_time_rule': '路段行时在进入时确定；跨300秒边界不重算，7200秒后沿用末段系数。'},
        'network': {'campus_ids': ['Y', 'L'], 'independent_fleets': True,
                    'route': '每车沿0,1,...,n-1,0单向完整环线运行；每站必停，不换向、绕行或短转。',
                    'blocking': '允许车辆交换先后次序；忽略道路和站台阻塞，控车位置有足够空间。',
                    'passengers': '一人一请求，始终在原起点候车，只乘一车至终点，不换乘、不弃乘、不改站。',
                    'travel_time_formula': 'ceil(base_travel_s*driver_factor*link_factor_at_entry)；车速不可控制。'},
        'service': {'door_fixed_s': 10, 'alight_per_person_s': 2, 'board_per_person_s': 3,
                    'capacity_rule': '14个乘客座位，不含司机，不准站立或超载。',
                    'freeze_queue_at_arrival': True,
                    'arrival_order': '同秒旅客到站先于车辆；同秒多车按bus_id字典序分配；旅客按arrival_s再按request_id排序。',
                    'selection': '先下后上；本次只接纳到站瞬间已在队且未被另一车选中的旅客。选中即标记服务中。',
                    'boarding_rule': 'B=min(Q,max(seats-onboard_after_alighting-reserve_seats,0))。',
                    'alight_complete_formula': 'arrival+10+2*A；A名下车者统一在此刻完成。',
                    'board_complete_formula': 'arrival+10+2*A+3*B；B名上车者统一在此刻完成。',
                    'new_arrivals_during_service': '乘降及关门后控车期间到站者等待下一车，不重开门。'},
        'actions': {'reserve_seats_range': [0, 4], 'extra_hold_s_range': [0, 90],
                    'hold_allowed_stops': [0, 4], 'first_service_s_range': [0, 600],
                    'base_hold_s_range': [0, 60],
                    'base_hold_rule': '仅首次以外回到0站时适用；first_service_s是首次驶入0站服务而非离站时刻。',
                    'dynamic_hold_rule': '第三、四问动态extra_hold取代base_hold，不与其相加；其他站不得控车。',
                    'baseline_actions': {'reserve_seats': 0, 'extra_hold_s': 0}},
        'planning': {'case_suffixes': ['P1', 'P2', 'P3'], 'validation_suffixes': ['N', 'R', 'E'],
                     'rule': '第二问只用P样本确定各车first_service_s及base_hold_s，方案固定用于N/R/E；不为不同验证工况换方案。'},
        'information': {'default_delay_s': 60, 'test_delays_s': [0, 60, 120],
                        'instant_fields': ['time_s', 'bus_id', 'stop_id', 'alighting_count',
                                           'onboard_after_alighting', 'eligible_queue_count'],
                        'delayed_fields': ['arrival_departure_times', 'boarding_alighting_counts', 'onboard_totals',
                                           'queue_seen_at_past_arrivals'],
                        'cutoff': '除本车本站即时字段和已知初态/参数外，只读timestamp<=time_s-delay_s的全网历史事件。',
                        'forbidden': ['case_id作为控制输入', '未来真实旅客到站/OD/deadline', '候车者逐人OD/deadline',
                                      '未来真实路段系数或行时', '未来真实上下车时刻'],
                        'shared_prefix_end_s_exclusive': 1800,
                        'replay_only': '验证文件含完整真值只用于环境回放和事后评分；公开文件可见不等于控制器可提前读取。'},
        'handover': {'enabled_only_task': 4, 'duration_s': 120,
                     'rule': '预留、控车和是否交班均在车辆到站t一次决定。仅0站可选交班，若选择则在本次乘降完成ready立即开始；ready须在[start,end-120]，每车在各自窗口内完成一次；车内乘客留车。',
                     'driver_after': '交班120秒完成后改用driver_factor_after；之前用before，交班未完成不得驶出。',
                     'extra_stop_formula': 'max(extra_hold_s,120)；控车与交班重叠，不相加。',
                     'staff': '各车接班人独立分配，在对应窗口内位于0站，不额外争用共享司机。',
                     'missed_window': '未完成交班者过窗后不能继续按原司机运行。'},
        'metrics': {'on_time': '全部请求作分母；alight_time<=deadline_s才按时；T末未完成下车者均不按时并另报未完成人数。',
                    'waiting_s': 'min(board_complete_time,T)-arrival_s；未完成上车者以T代入，包括已被选中但仍在上车者。',
                    'wait_reports': ['全体平均截断候车耗时', '分起点95分位', '最不利起点'],
                    'quantile_95': '起点内样本从小到大排列，取第ceil(0.95*n)个；无请求的起点记NA。',
                    'ride_s': '从board_complete_time至alight_time，未完成者截断到T，另报人数；控车和交班的车内耗时计入。',
                    'checks': ['车辆及驾驶员可用性', '容量', '旅客唯一性', '站内/服务中/在车/完成的人数守恒', 'T末全部未完成者'],
                    'no_unique_weights': True},
        'random_generation': {'seed_offset': seed_offset, 'seeds': seeds,
                              'implementation': 'Python标准库random.Random；泊松数Knuth乘积法，块内独立均匀整数秒，碰撞允许。',
                              'base_rate_per_min': {k: v['rate'] for k, v in CAMPUS.items()},
                              'block_s': 300, 'arrival_profile': PROFILE,
                              'origin_weights': {k: v['weights'] for k, v in CAMPUS.items()},
                              'rotation': {'start_s': 1800, 'end_s_exclusive': 3600,
                                           'forward_stops': {k: v['rotate'] for k, v in CAMPUS.items()}},
                              'hops': {'base_origins_0_1': {'values': [4, 5, 2], 'probabilities': [.55, .25, .20]},
                                       'other_origins': {'values': [1, 2, 3], 'probabilities': [.4, .4, .2]}},
                              'normal_link_factor_range': [.95, 1.08], 'rain_after_s': 1800, 'rain_multiplier': 1.25,
                              'extra_event_arrival_range_s': [2100, 2400], 'extra_event_hops': [2, 3],
                              'extra_event_hop_probabilities': [.5, .5],
                              'deadline_formula': 'arrival+ceil(0.96*OD基础边行时总和)+10*(hops+1)+5+slack；是完成下车期限，非真实课表。',
                              'slack_s': [240, 360, 480, 600], 'slack_probabilities': [.1, .3, .4, .2],
                              'request_id': 'case内唯一；R开头为常规请求，X为活动追加；N/R/E常规ID及记录相同。'},
    }
    out = {}
    for name, rows in data.items():
        stream = io.StringIO(newline='')
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(HEADERS[name])
        writer.writerows(rows)
        out[name] = stream.getvalue().encode('utf-8')
    out['rules.json'] = (json.dumps(rules, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    parser.add_argument('--seed-offset', type=int, default=0)
    args = parser.parse_args()
    canonical = Path(__file__).resolve().parents[1] / 'data'
    if args.seed_offset < 0:
        parser.error('seed_offset须为非负整数。')
    if args.seed_offset and args.output.resolve() == canonical.resolve():
        parser.error('额外重采样须用--output写入其他目录，不能覆盖正式附件。')
    files = build_files(args.seed_offset)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in files.items():
        (args.output / name).write_bytes(value)
    print(json.dumps({'status': 'PASS', 'files': list(files), 'seed_offset': args.seed_offset,
                      'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
