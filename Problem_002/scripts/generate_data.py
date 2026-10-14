#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Rebuild training inputs and isolated experiments; no orchard yield or planning solver."""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from pathlib import Path

SEED = 20261014
SOURCE = 'https://treefruit.wsu.edu/article/cross-compatibility-of-apple-cultivars-and-pollinizers/'
# Five factual S-genotypes transcribed from WSU's extension article, reviewed 2024-02-13.
# Bloom, prices, flower numbers and all experiment observations below are synthetic.
GENOTYPES = [('A', 'Gala', '2', '5'), ('B', 'Golden Delicious', '2', '3'),
             ('C', 'Mt. Blanc', '3', '58'), ('D', 'Evereste', '20', '26'),
             ('E', 'Frettingham', '24', '25')]
PLANNING = [('A', 'main', 1.0, 0, 9, 2.0),
            ('B', 'main', 1.0, 0, 13, 2.3),
            ('C', 'pollinizer', 1.20, 650, 15, 3.2),
            ('D', 'pollinizer', 1.35, 1150, 9, 3.0),
            ('E', 'pollinizer', 1.55, 850, 11, 1.6)]
NROWS, NCOLS = 8, 18
XSPACING, YSPACING = 3.0, 5.0


def write(directory, name, header, rows):
    with (directory/name).open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(header); w.writerows(rows)


def choose(rng, weights):
    total = sum(weights); u = rng.random()*total; cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if u <= cumulative: return i
    return len(weights)-1


def bloom(center, width):
    weights = [math.exp(-.5*((day-center)/width)**2) if 4 <= day <= 23 else 0.
               for day in range(1, 31)]
    total = sum(weights)
    return [w/total for w in weights]


RULES = {
    'synthetic_experiments_and_planning': True,
    'seed': SEED, 'day_start': 1, 'day_end_inclusive': 30,
    'rows': 8, 'columns': 18, 'row_spacing_m': 5., 'tree_spacing_m': 3.,
    'flower_receptive_days': 2,
    'flower_pollen_production_days': 2,
    'visits_per_bout': 50,
    'start_position_rule': 'proportional_to_current_open_flower_count',
    'entering_transferable_orchard_pollen': 0.,
    'daily_inputs_constant_within_day': True,
    'outside_orchard_compatible_pollen_ignored': True,
    'planning_budgets_yuan': [6000, 10000], 'max_replaced_trees': 12,
    'max_replaced_in_each_row': 2, 'min_remaining_A': 64, 'min_remaining_B': 64,
    'added_bee_units_max': 3, 'added_bee_unit_cost_yuan': 1500,
    'nominal_bout_increase_per_added_unit': .20,
    'stress_bout_increase_per_added_unit': .10,
    'comparison_year': 'all_trees_in_normal_bloom_after_establishment',
    'pollinizer_fruit_included_in_target': False,
    'target': 'expected_initial_fruits_on_remaining_A_and_B_30_days_after_each_flower_opening',
    'fruit_retention_after_day30_modelled': False,
    'budgets_include_only_replanting_and_added_bee_rental': True,
    'scenarios_are_probability_distribution': False,
    'scenario_action_time': 'before_flowering_scenario_is_revealed',
    'movement_trial_conditions': 'equal_flower_number_per_tree; same_spacing_as_orchard',
    'carryover_trial_conditions': 'pure_labelled_load_then_unlabelled_flowers; all_pollen_otherwise_same',
    'fruit_trial_conditions': 'known_compatible_grains_across_all_five_stigmas; equal_pollen_viability; no_later_pollen',
    'pollen_viability_rule': 'equal_across_cultivars_and_consistent_with_fruit_set_trial',
    'experiment_split_unit': 'whole_bee_or_whole_batch',
}


def build(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    write(directory, 'cultivar_genotypes.csv',
          ['cultivar_id','cultivar_name','S_allele_1','S_allele_2','source_url'],
          [[*r, SOURCE] for r in GENOTYPES])
    write(directory, 'cultivar_planning.csv',
          ['cultivar_id','role','flower_number_multiplier','replant_cost_yuan'],
          [list(r[:4]) for r in PLANNING])
    positions=[]
    for row in range(NROWS):
        for col in range(NCOLS):
            positions.append((row,col,col*XSPACING,row*YSPACING))
    orchard=[]
    for i,(row,col,x,y) in enumerate(positions):
        flowers = round(1500*(.94+.12*rng.random()))
        orchard.append([f'T{i+1:03d}',row+1,col+1,x,y,'A' if row<4 else 'B',flowers])
    write(directory, 'orchard.csv',
          ['tree_id','row_id','column_id','x_m','y_m','current_cultivar_id','reference_flower_number'],orchard)
    blooms={r[0]:bloom(r[4],r[5]) for r in PLANNING}
    write(directory, 'bloom_profiles.csv',['day','cultivar_id','new_open_fraction'],
          [[day,cid,f'{values[day-1]:.12f}'] for cid,values in blooms.items() for day in range(1,31)])
    activity=[]
    for day in range(1,31):
        factor=.79+.14*math.sin(day*.82)+.07*math.cos(day*.31)
        if day in [7,18]: factor *= .55
        bouts=round(2800*math.exp(-.5*((day-11.5)/5.2)**2)*factor)
        if day<4 or day>24: bouts=0
        activity.append([day,bouts])
    write(directory, 'visitation.csv',['day','reference_bouts'],activity)
    # Position-only trial in an equal-bloom test plot. No pollen or yield calculation.
    moves=[]
    for bee in range(1,101):
        role='calibration' if bee<=80 else 'validation'
        bx=.72*math.exp(rng.gauss(0,.07)); by=1.95*math.exp(rng.gauss(0,.09))
        stay=3.15*math.exp(rng.gauss(0,.06)); i=rng.randrange(len(positions))
        for step in range(1,13):
            r,c,_,_=positions[i]
            weights=[stay if j==i else math.exp(-bx*abs(c-cc)-by*abs(r-rr))
                     for j,(rr,cc,_,_) in enumerate(positions)]
            j=choose(rng,weights); rr,cc,_,_=positions[j]
            moves.append([f'B{bee:03d}',role,step,r+1,c+1,rr+1,cc+1]);i=j
    write(directory, 'movement_trials.csv',
          ['bee_id','role','step','from_row','from_column','to_row','to_column'],moves)
    # Independent fluorescent-label dilution experiment. These constants are not hidden answers.
    carry=[]
    for bee in range(1,31):
        role='calibration' if bee<=22 else 'validation'
        rf=min(.86,max(.55,.70+rng.gauss(0,.025)))
        rs=min(.985,max(.86,.95+rng.gauss(0,.012)))
        slow=min(.3,max(.08,.18+rng.gauss(0,.015)))
        for k in range(1,21):
            n=rng.randint(32,48)
            fraction=(1-slow)*rf**(k-1)+slow*rs**(k-1)
            tagged=sum(rng.random()<fraction for _ in range(n))
            carry.append([f'L{bee:03d}',role,k,n,tagged])
    write(directory,'carryover_trials.csv',
          ['bee_id','role','recipient_order','total_deposited_grains','labelled_grains'],carry)
    dose=[]
    for cultivar,upper,scale in [('A',.72,28.),('B',.68,36.)]:
        for batch in range(1,5):
            role='calibration' if batch<=3 else 'validation'
            batch_scale=scale*math.exp(rng.gauss(0,.045))
            for grains in [0,5,15,30,60,120,240]:
                n=100; prob=upper*(1-math.exp(-grains/batch_scale))
                fruits=sum(rng.random()<prob for _ in range(n))
                dose.append([f'{cultivar}_R{batch}',role,cultivar,grains,n,fruits])
    write(directory,'fruit_set_trials.csv',
          ['batch_id','role','cultivar_id','compatible_grains','flowers','initial_fruits'],dose)
    # Scenario shifts preserve each cultivar's total number of flowers.
    scenarios=[('reference',0,0,0,0,0,0,0,1.),
               ('early_A',-3,0,0,0,0,0,0,1.),
               ('late_B',0,3,0,0,0,0,0,1.),
               ('pollinizer_advance',0,0,-2,-3,-2,0,0,1.),
               ('quiet_early',0,0,0,0,0,8,10,.20),
               ('quiet_late',0,0,0,0,0,13,15,.20),
               ('split_and_quiet',-2,2,0,-2,0,10,12,.25)]
    write(directory,'scenarios.csv',
          ['scenario_id','A_shift_days','B_shift_days','C_shift_days','D_shift_days',
           'E_shift_days','low_activity_start_day','low_activity_end_day','bout_multiplier'],scenarios)
    (directory/'rules.json').write_text(json.dumps(RULES,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    a=p.parse_args();build(a.output_dir);print('Generated training attachments:',a.output_dir)
