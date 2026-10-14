#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate input completeness, experiment units, scenario conservation and reproducibility."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[1]
SCHEMAS={
 'cultivar_genotypes.csv':['cultivar_id','cultivar_name','S_allele_1','S_allele_2','source_url'],
 'cultivar_planning.csv':['cultivar_id','role','flower_number_multiplier','replant_cost_yuan'],
 'orchard.csv':['tree_id','row_id','column_id','x_m','y_m','current_cultivar_id','reference_flower_number'],
 'bloom_profiles.csv':['day','cultivar_id','new_open_fraction'],
 'visitation.csv':['day','reference_bouts'],
 'movement_trials.csv':['bee_id','role','step','from_row','from_column','to_row','to_column'],
 'carryover_trials.csv':['bee_id','role','recipient_order','total_deposited_grains','labelled_grains'],
 'fruit_set_trials.csv':['batch_id','role','cultivar_id','compatible_grains','flowers','initial_fruits'],
 'scenarios.csv':['scenario_id','A_shift_days','B_shift_days','C_shift_days','D_shift_days','E_shift_days',
                 'low_activity_start_day','low_activity_end_day','bout_multiplier']}


def require(condition,message):
    if not condition: raise ValueError(message)


def read(directory,name):
    with (directory/name).open(encoding='utf-8',newline='') as f:
        r=csv.DictReader(f);require(r.fieldnames==SCHEMAS[name],f'Wrong fields: {name}')
        rows=list(r)
    require(all(None not in row and all(v not in [None,''] for v in row.values()) for row in rows),f'Missing/extra cells: {name}')
    return rows


def validate(directory):
    tables={name:read(directory,name) for name in SCHEMAS};rules=json.loads((directory/'rules.json').read_text())
    facts={'A':('2','5'),'B':('2','3'),'C':('3','58'),'D':('20','26'),'E':('24','25')}
    gen=tables['cultivar_genotypes.csv']
    require(len(gen)==5 and {r['cultivar_id'] for r in gen}==set(facts),'Genotype IDs')
    require(all((r['S_allele_1'],r['S_allele_2'])==facts[r['cultivar_id']] for r in gen),'Factual S-genotype transcription changed')
    require(all(r['source_url'].startswith('https://treefruit.wsu.edu/') for r in gen),'Missing factual source')
    planning=tables['cultivar_planning.csv']
    require(len(planning)==5 and {r['cultivar_id'] for r in planning}==set(facts),'Planning IDs')
    require(all(0<float(r['flower_number_multiplier'])<=2 for r in planning),'Flower multiplier range')
    require(all(int(r['replant_cost_yuan'])>0 if r['cultivar_id'] in 'CDE' else int(r['replant_cost_yuan'])==0 for r in planning),'Cost interpretation')
    orchard=tables['orchard.csv'];require(len(orchard)==144,'144 tree positions required')
    require(len({r['tree_id'] for r in orchard})==144,'Tree ID duplicates')
    require({(int(r['row_id']),int(r['column_id'])) for r in orchard}=={(r,c) for r in range(1,9) for c in range(1,19)},'Grid incomplete')
    for r in orchard:
        rr,cc=int(r['row_id']),int(r['column_id'])
        require(float(r['x_m'])==3*(cc-1) and float(r['y_m'])==5*(rr-1),'Grid dimensions/units')
        require(r['current_cultivar_id']==('A' if rr<=4 else 'B'),'Original cultivar arrangement')
        require(1400<=int(r['reference_flower_number'])<=1700,'Flower count range')
    bloom={};bt=tables['bloom_profiles.csv'];require(len(bt)==150,'Bloom matrix incomplete')
    for r in bt:
        key=(r['cultivar_id'],int(r['day']));require(key not in bloom,'Duplicate bloom record');bloom[key]=float(r['new_open_fraction'])
    require(set(bloom)=={(c,d) for c in facts for d in range(1,31)},'Bloom time axis')
    require(all(math.isfinite(v) and 0<=v<=1 for v in bloom.values()),'Bloom fractions')
    require(all(abs(sum(bloom[c,d] for d in range(1,31))-1)<2e-10 for c in facts),'Whole-season bloom mass not 1')
    visits=tables['visitation.csv'];require(len(visits)==30 and {int(r['day']) for r in visits}==set(range(1,31)),'Visitation days')
    require(all(0<=int(r['reference_bouts'])<=5000 for r in visits),'Visitation range')
    require(all(int(r['reference_bouts'])==0 or sum(bloom[c,int(r['day'])]+(bloom[c,int(r['day'])-1] if int(r['day'])>1 else 0) for c in 'AB')>0 for r in visits),'Visits when reference orchard has no open flowers')
    moves=tables['movement_trials.csv'];require(len(moves)==1200,'Movement observations')
    grouped={}
    for r in moves:
        require(r['role'] in ['calibration','validation'],'Movement split')
        for prefix in ['from','to']:
            require(1<=int(r[prefix+'_row'])<=8 and 1<=int(r[prefix+'_column'])<=18,'Movement outside test plot')
        grouped.setdefault(r['bee_id'],[]).append(r)
    require(len(grouped)==100,'Movement bees')
    for ident,group in grouped.items():
        group.sort(key=lambda r:int(r['step']));require([int(r['step']) for r in group]==list(range(1,13)),'Movement sequence')
        role='calibration' if int(ident[1:])<=80 else 'validation'
        require(all(r['role']==role for r in group),'Movement whole-bee split violated')
        require(all((a['to_row'],a['to_column'])==(b['from_row'],b['from_column']) for a,b in zip(group,group[1:])),'Broken movement trajectory')
    carry=tables['carryover_trials.csv'];require(len(carry)==600,'Carryover observations')
    grouped={}
    for r in carry:
        n,y=int(r['total_deposited_grains']),int(r['labelled_grains'])
        require(0<=y<=n and n>0,'Labelled count exceeds deposited count')
        grouped.setdefault(r['bee_id'],[]).append(r)
    require(len(grouped)==30,'Carryover bees')
    for ident,group in grouped.items():
        group.sort(key=lambda r:int(r['recipient_order']))
        require([int(r['recipient_order']) for r in group]==list(range(1,21)),'Carryover order')
        role='calibration' if int(ident[1:])<=22 else 'validation'
        require(all(r['role']==role for r in group),'Carryover whole-bee split violated')
        require(int(group[0]['labelled_grains'])==int(group[0]['total_deposited_grains']),'Pure initial label inconsistent')
    dose=tables['fruit_set_trials.csv'];require(len(dose)==56,'Fruit-set observations')
    require(all(r['cultivar_id'] in 'AB' and 0<=int(r['initial_fruits'])<=int(r['flowers']) and int(r['flowers'])==100 for r in dose),'Fruit/flower counts')
    for c in 'AB':
        for b in range(1,5):
            g=[r for r in dose if r['batch_id']==f'{c}_R{b}'];require(len(g)==7,'Dose batch missing')
            require({int(r['compatible_grains']) for r in g}=={0,5,15,30,60,120,240},'Dose support')
            require(all(r['role']==('calibration' if b<=3 else 'validation') for r in g),'Whole-batch split violated')
    scenarios=tables['scenarios.csv'];require(len(scenarios)==7 and len({r['scenario_id'] for r in scenarios})==7,'Scenario IDs')
    for r in scenarios:
        for c in facts:
            shift=int(r[c+'_shift_days']);require(-3<=shift<=3,'Scenario shift range')
            shifted=sum(bloom.get((c,d-shift),0.) for d in range(1,31))
            require(abs(shifted-1)<2e-10,f'Scenario silently loses flowers: {r["scenario_id"]}/{c}')
        a,b=int(r['low_activity_start_day']),int(r['low_activity_end_day'])
        require((a==b==0) or 1<=a<=b<=30,'Low-activity interval')
        require(0<float(r['bout_multiplier'])<=1,'Activity multiplier')
    require(rules['max_replaced_trees']==12 and rules['max_replaced_in_each_row']==2,'Replanting rules')
    require(rules['min_remaining_A']==rules['min_remaining_B']==64,'Retained variety rules')
    require(rules['planning_budgets_yuan']==[6000,10000] and rules['added_bee_units_max']==3,'Budget/bee rules')
    require(rules['flower_receptive_days']==rules['flower_pollen_production_days']==2 and rules['visits_per_bout']==50,'Exposure accounting')
    # A nonzero permitted intervention must exist at both budgets; no yield is calculated.
    require(min(int(r['replant_cost_yuan']) for r in planning if r['cultivar_id'] in 'CDE')<=6000,'No affordable pollinizer')
    return {'status':'PASS','checks':10,'row_counts':{n:len(r) for n,r in tables.items()},
            'total_csv_rows':sum(len(r) for r in tables.values()),
            'original_flower_number':sum(int(r['reference_flower_number']) for r in orchard),
            'source_fact_rows':len(gen),'synthetic_csv_rows':sum(len(r) for r in tables.values())-len(gen)}


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=Path,default=ROOT/'data');p.add_argument('--report',type=Path)
    a=p.parse_args();report=validate(a.data_dir)
    spec=importlib.util.spec_from_file_location('p002_generator',ROOT/'scripts/generate_data.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    names=[*SCHEMAS,'rules.json'];hashes={}
    with tempfile.TemporaryDirectory(prefix='p002-data-check-') as temp:
        generated=Path(temp);mod.build(generated)
        for name in names:
            actual=(a.data_dir/name).read_bytes();other=(generated/name).read_bytes()
            require(actual==other,f'Regeneration mismatch: {name}');hashes[name]=hashlib.sha256(actual).hexdigest()
    report['regenerated_files']=len(names);report['sha256']=hashes
    if a.report:a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'PASS: {report["checks"]} groups, {len(names)} exact regenerated files, {report["total_csv_rows"]} CSV rows')


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,FileNotFoundError) as e:raise SystemExit('FAIL: '+str(e))
