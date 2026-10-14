#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check attachment integrity and design feasibility; no chlorine-network solution.

Run from any directory. Uses only Python's standard library. The optional JSON
report stores checks and data hashes, not a transport or control benchmark.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import tempfile
import sys

sys.dont_write_bytecode = True

import generate_data as generator

FIELDS = {
    'network_nodes.csv': ['node_id','node_type','label'],
    'pipes.csv': ['pipe_id','from_node','to_node','length_m','diameter_m','volume_m3',
        'material','flow_limit_m3_h','wall_rate20_min_h_1','wall_rate20_max_h_1'],
    'tanks.csv': ['tank_id','working_volume_m3','level_policy'],
    'users.csv': ['user_id','tank_id','normal_mean_reference_m3_h','flush_max_m3_h'],
    'forcing.csv': ['time_h','day_index','hour_of_day','stage','source_chlorine_mg_L','water_temperature_C'],
    'demands.csv': ['time_h','user_id','nominal_demand_m3_h'],
    'bottle_tests.csv': ['batch_id','replicate_id','water_temperature_C',
        'nominal_initial_chlorine_mg_L','sample_time_h','measured_chlorine_mg_L','role'],
    'tank_tracer.csv': ['experiment_id','tank_id','role','flow_m3_h','sample_time_h',
        'inlet_step_value','measured_outlet_fraction','measurement_status'],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def number(value: str, label: str) -> float:
    require(value != '', f'Missing numeric value: {label}')
    result = float(value)
    require(math.isfinite(result), f'Nonfinite numeric value: {label}')
    return result


def check(directory: Path) -> dict:
    data = {}
    for filename, expected_fields in FIELDS.items():
        with (directory/filename).open(encoding='utf-8',newline='') as stream:
            reader = csv.DictReader(stream)
            require(reader.fieldnames == expected_fields, f'Unexpected header: {filename}')
            rows = list(reader)
        require(bool(rows), f'Empty file: {filename}')
        require(all(None not in r and len(r) == len(expected_fields) for r in rows), f'Ragged CSV: {filename}')
        for index,row in enumerate(rows):
            for field,value in row.items():
                require(value is not None and (value != '' or (filename == 'tank_tracer.csv'
                    and field == 'measured_outlet_fraction' and row['measurement_status'] == 'missing')),
                    f'Unexpected missing value: {filename}:{index+2}:{field}')
        data[filename] = rows
    rules = json.loads((directory/'operating_rules.json').read_text(encoding='utf-8'))
    require(rules['synthetic'] is True, 'Synthetic label missing')
    require(rules['initial_chlorine_mg_L'] == .75 and rules['initial_water_age_h'] == 12, 'Incorrect initial state')
    require(rules['initial_water_age_distribution'] == 'point_mass_at_12_h_everywhere', 'Ambiguous initial water age')
    require(rules['flush_start_hour'] == 6 and rules['flush_end_hour_exclusive'] == 22, 'Ambiguous flushing hours')
    require(rules['max_simultaneous_flush_ports'] == 2, 'Incorrect simultaneous-control limit')
    require(rules['weekly_flush_budgets_m3'] == [60,120,180], 'Incorrect budget cases')
    require(rules['capacity_demand_factor'] == 1.25, 'Robust hydraulic margin missing')

    nodes = {r['node_id']:r['node_type'] for r in data['network_nodes.csv']}
    require(len(nodes) == len(data['network_nodes.csv']) == 10, 'Duplicate or missing nodes')
    require(nodes == dict([('S','source'),('J','junction'),('T1','tank'),('T2','tank')]
        + [(f'U{i}','user') for i in range(1,7)]), 'Unexpected topology nodes')
    pipes = data['pipes.csv']
    require(len(pipes) == len({p['pipe_id'] for p in pipes}) == 9, 'Duplicate or missing pipes')
    require({p['pipe_id'] for p in pipes} == {f'P{i}' for i in range(9)}, 'Unexpected pipe IDs')
    incoming = {n:0 for n in nodes}
    outgoing = {n:[] for n in nodes}
    for p in pipes:
        require(p['from_node'] in nodes and p['to_node'] in nodes, 'Unknown pipe endpoint')
        incoming[p['to_node']] += 1
        outgoing[p['from_node']].append(p['to_node'])
        length = number(p['length_m'],'pipe length')
        diameter = number(p['diameter_m'],'pipe diameter')
        volume = number(p['volume_m3'],'pipe volume')
        require(length > 0 and diameter > 0 and volume > 0, 'Invalid pipe geometry')
        require(abs(volume-math.pi*diameter**2*length/4) <= .00000051, 'Pipe volume disagrees with geometry')
        require(number(p['flow_limit_m3_h'],'pipe capacity') > 0, 'Invalid pipe capacity')
        lower = number(p['wall_rate20_min_h_1'],'wall lower rate')
        upper = number(p['wall_rate20_max_h_1'],'wall upper rate')
        require(0 < lower <= upper < .02, 'Invalid wall-rate interval')
    require(incoming['S'] == 0 and all(incoming[n] == 1 for n in nodes if n != 'S'), 'Network is not a rooted tree')
    visiting = set()
    visited = set()
    def descendants(node: str) -> set[str]:
        require(node not in visiting, 'Cycle in tree')
        visiting.add(node)
        found = {node} if nodes[node] == 'user' else set()
        for nxt in outgoing[node]:
            found |= descendants(nxt)
        visiting.remove(node)
        visited.add(node)
        return found
    source_users = descendants('S')
    require(visited == set(nodes) and source_users == {f'U{i}' for i in range(1,7)}, 'Unreachable node or missing user')
    pipe_users = {p['pipe_id']:descendants(p['to_node']) for p in pipes}
    tank_map = {t['tank_id']:number(t['working_volume_m3'],'tank volume') for t in data['tanks.csv']}
    require(tank_map == {'T1':18,'T2':14}, 'Tank working-volume mismatch')
    require(all(t['level_policy'] == 'constant' for t in data['tanks.csv']), 'Tank policy mismatch')
    users = {u['user_id']:u for u in data['users.csv']}
    require(set(users) == source_users and len(users) == len(data['users.csv']), 'User IDs inconsistent')
    for user,row in users.items():
        require(row['tank_id'] in tank_map and user in descendants(row['tank_id']), 'User-tank connection mismatch')
        require(number(row['flush_max_m3_h'],'flush capacity') == 2.2, 'Unexpected flush maximum')
        require(number(row['normal_mean_reference_m3_h'],'reference demand') > 0, 'Nonpositive reference demand')

    forcing = data['forcing.csv']
    times = [int(r['time_h']) for r in forcing]
    require(times == list(range(-72,168)), 'Forcing timeline has duplicate, missing or unsorted times')
    concentrations = []
    temperatures = []
    for row in forcing:
        t = int(row['time_h'])
        require(int(row['day_index']) == t//24 and int(row['hour_of_day']) == t%24, 'Inconsistent calendar')
        require(row['stage'] == ('normal_history' if t < 0 else 'low_demand'), 'Stage mismatch')
        c = number(row['source_chlorine_mg_L'],'source concentration')
        temp = number(row['water_temperature_C'],'water temperature')
        require(.65 <= c <= .90 and 20 <= temp <= 30, 'External input out of nominal range')
        require(rules['source_chlorine_physical_bounds_mg_L'][0] <= c-.05 and c+.05 <= rules['source_chlorine_physical_bounds_mg_L'][1], 'Source perturbation violates physical bounds')
        require(rules['water_temperature_physical_bounds_C'][0] <= temp-2 and temp+2 <= rules['water_temperature_physical_bounds_C'][1], 'Temperature perturbation violates physical bounds')
        concentrations.append(c)
        temperatures.append(temp)
    require(concentrations[0] == .75 and temperatures[0] == 24, 'Initial forcing mismatch')
    demands = {t:{} for t in times}
    for row in data['demands.csv']:
        t,user = int(row['time_h']),row['user_id']
        require(t in demands and user in users and user not in demands[t], 'Unknown or duplicate demand key')
        demands[t][user] = number(row['nominal_demand_m3_h'],'demand')
        require(0 < demands[t][user] < 2, 'Demand outside expected training range')
    require(len(data['demands.csv']) == 1440 and all(set(q) == source_users for q in demands.values()), 'Incomplete demand grid')
    def capacity_feasible(t: int, extra: dict[str,float]) -> bool:
        total = {u:rules['capacity_demand_factor']*q+extra.get(u,0) for u,q in demands[t].items()}
        return sum(total.values()) <= rules['source_capacity_m3_h']+1e-9 and all(
            sum(total[u] for u in pipe_users[p['pipe_id']]) <= float(p['flow_limit_m3_h'])+1e-9 for p in pipes)
    require(all(capacity_feasible(t,{}) for t in times), 'Zero-flush robust demand exceeds capacity')
    allowed = [t for t in range(168) if rules['flush_start_hour'] <= t%24 < rules['flush_end_hour_exclusive']]
    require(len(allowed) == 112, 'Invalid weekly control-window duration')
    # An existence check for each volume case, with no chlorine performance target.
    # This does not rank controls or solve any of the competition questions.
    budget_feasible = {}
    for budget in rules['weekly_flush_budgets_m3']:
        rate = budget/(rules['max_simultaneous_flush_ports']*len(allowed))
        found = any(all(rate <= float(users[u]['flush_max_m3_h']) for u in pair)
                    and all(capacity_feasible(t,{u:rate for u in pair}) for t in allowed)
                    for pair in itertools.combinations(sorted(users),2))
        require(found, f'No verified capacity-feasible plan using volume {budget}')
        budget_feasible[str(budget)] = True

    bottle_groups = {}
    for row in data['bottle_tests.csv']:
        key = (row['batch_id'],int(row['replicate_id']))
        bottle_groups.setdefault(key,[]).append(row)
        require(float(row['water_temperature_C']) in (20,25,30), 'Unknown bottle temperature')
        require(float(row['nominal_initial_chlorine_mg_L']) in (.4,.85), 'Unknown bottle dose')
        require(row['role'] == ('validation' if int(row['replicate_id']) == 3 else 'calibration'), 'Bottle split leakage')
        c = number(row['measured_chlorine_mg_L'],'bottle concentration')
        require(rules['bottle_detection_limit_mg_L'] < c < .90, 'Bottle concentration out of range or below detection')
    require(len(bottle_groups) == 18 and len(data['bottle_tests.csv']) == 162, 'Incomplete bottle matrix')
    for key,rows in bottle_groups.items():
        require([int(r['sample_time_h']) for r in rows] == generator.BOTTLE_TIMES, 'Bottle time grid incomplete')
        values = [float(r['measured_chlorine_mg_L']) for r in rows]
        require(all(v1 > v2 for v1,v2 in zip(values,values[1:])), 'Bottle decay trend inconsistent')
        nominal = float(rows[0]['nominal_initial_chlorine_mg_L'])
        require(abs(values[0]-nominal) < .014 and values[-1] < .7*values[0], 'Implausible bottle decay range')
    for initial in (.4,.85):
        late = {temp:statistics.mean(float(r['measured_chlorine_mg_L']) for r in data['bottle_tests.csv']
               if float(r['nominal_initial_chlorine_mg_L']) == initial
               and int(r['water_temperature_C']) == temp and int(r['sample_time_h']) == 96) for temp in (20,25,30)}
        require(late[20] > late[25] > late[30], 'Bottle temperature trend inconsistent')

    tracer_groups = {}
    missing_count = 0
    residuals = []
    tracer_design = {t[0]:t for t in generator.TANKS}
    for row in data['tank_tracer.csv']:
        key = row['experiment_id']
        tracer_groups.setdefault(key,[]).append(row)
        require(row['tank_id'] in tank_map and row['inlet_step_value'] == '1', 'Tracer inlet or tank ID mismatch')
        require(row['measurement_status'] in ('observed','missing'), 'Unknown measurement status')
        if row['measurement_status'] == 'missing':
            require(row['measured_outlet_fraction'] == '' and row['role'] == 'calibration', 'Missing tracer incorrectly marked')
            missing_count += 1
        else:
            val = number(row['measured_outlet_fraction'],'tracer fraction')
            require(0 <= val <= 1, 'Tracer concentration outside physical bounds')
    require(len(tracer_groups) == 6 and len(data['tank_tracer.csv']) == 96 and missing_count == 4, 'Incomplete tracer design')
    mean_residence = {}
    for exp,rows in tracer_groups.items():
        require([int(r['sample_time_h']) for r in rows] == generator.TRACER_TIMES, 'Tracer timeline incomplete')
        tank,volume,f,g,flows = tracer_design[rows[0]['tank_id']]
        q = float(rows[0]['flow_m3_h'])
        exp_num = int(exp[-1])
        expected_role = 'validation' if exp_num == 3 else 'calibration'
        require(all(r['tank_id'] == tank and float(r['flow_m3_h']) == q and r['role'] == expected_role for r in rows), 'Tracer experiment attributes drift')
        require(q == flows[exp_num-1], 'Tracer flow mismatch')
        require(rows[0]['measured_outlet_fraction'] == '0.0000', 'Nonzero initial tracer concentration')
        # The synthetic mechanism conserves both volume and flux. Infinite tail
        # integral is analytic; finite 200h observations need not reach a plateau.
        mean_age = g*(f*volume/(g*q))+(1-g)*((1-f)*volume/((1-g)*q))
        require(abs(q*mean_age-volume) < 1e-10, 'Tracer mass/volume conservation broken')
        mean_residence[exp] = round(mean_age,6)
        for row in rows:
            if row['measurement_status'] == 'observed':
                t = float(row['sample_time_h'])
                exact = g*(1-math.exp(-g*q*t/(f*volume)))+(1-g)*(1-math.exp(-(1-g)*q*t/((1-f)*volume)))
                residuals.append(float(row['measured_outlet_fraction'])-exact)
        require(float(rows[-1]['measured_outlet_fraction']) > .90, 'Insufficient tracer tail coverage')
    tracer_rmse = math.sqrt(statistics.mean(e*e for e in residuals))
    require(tracer_rmse < .012, 'Tracer generation-noise check failed')

    expected_files = set(FIELDS) | {'operating_rules.json','README.md'}
    actual_files = {p.name for p in directory.iterdir() if p.is_file()}
    require(actual_files == expected_files, 'Attachment set has missing or unexpected files')
    with tempfile.TemporaryDirectory(prefix='problem001-data-check-') as tmp:
        regenerated = Path(tmp)
        generator.build(regenerated)
        require({p.name for p in regenerated.iterdir()} == expected_files, 'Regeneration file set changed')
        for filename in sorted(expected_files):
            require((directory/filename).read_bytes() == (regenerated/filename).read_bytes(), f'Nonreproducible data file: {filename}')
    pipe_volume = sum(float(p['volume_m3']) for p in pipes)
    normal_totals = [sum(q.values()) for t,q in demands.items() if t < 0]
    low_totals = [sum(q.values()) for t,q in demands.items() if t >= 0]
    return {
        'status': 'PASS', 'python_standard_library_only': True,
        'checks': ['exact schemas and IDs', 'rooted acyclic connected tree', 'geometry volumes',
            'complete hourly inputs', 'ranges and perturbation bounds', 'robust zero-flush capacity',
            'capacity-feasible existence for each budget', 'bottle matrix, split and trends',
            'tracer split, missingness, conservation and noise', 'complete byte-for-byte regeneration'],
        'row_counts': {name:len(rows) for name,rows in data.items()},
        'pipe_volume_m3': round(pipe_volume,6), 'tank_volume_m3': sum(tank_map.values()),
        'normal_mean_total_demand_m3_h': round(statistics.mean(normal_totals),6),
        'normal_max_total_demand_m3_h': round(max(normal_totals),6),
        'low_mean_total_demand_m3_h': round(statistics.mean(low_totals),6),
        'low_max_total_demand_m3_h': round(max(low_totals),6),
        'nominal_source_chlorine_range_mg_L': [min(concentrations),max(concentrations)],
        'nominal_water_temperature_range_C': [min(temperatures),max(temperatures)],
        'budget_capacity_feasibility': budget_feasible,
        'tracer_mean_residence_h': mean_residence, 'tracer_generation_rmse': round(tracer_rmse,6),
        'sha256': {name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in sorted(expected_files)},
        'scope': 'attachment checks only; no network chlorine benchmark or optimal strategy',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    parser.add_argument('--json-report',type=Path)
    args = parser.parse_args()
    report = check(args.data_dir)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True,exist_ok=True)
        args.json_report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"PASS: {len(report['checks'])} check groups, {len(report['sha256'])} reproducible attachments")
    print(f"Rows: {sum(report['row_counts'].values())}; pipes {report['pipe_volume_m3']:.3f}m3; tanks {report['tank_volume_m3']:.1f}m3")
    print(f"Mean total demand: normal {report['normal_mean_total_demand_m3_h']:.3f}, low {report['low_mean_total_demand_m3_h']:.3f}m3/h")


if __name__ == '__main__':
    main()
