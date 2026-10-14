#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check tree-position, retained-cultivar and budget rules; never estimate fruit set."""
import argparse
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def validate(plan,bees,budget):
    orchard=load(ROOT/'data/orchard.csv');cost={r['cultivar_id']:int(r['replant_cost_yuan']) for r in load(ROOT/'data/cultivar_planning.csv')}
    proposed=load(plan)
    if not proposed or set(proposed[0])!={'tree_id','cultivar_id'}:raise ValueError('Plan needs tree_id,cultivar_id fields.')
    if any(set(r)!={'tree_id','cultivar_id'} or any(v in [None,''] for v in r.values()) for r in proposed):raise ValueError('Missing or extra plan fields.')
    if len(proposed)!=144 or len({r['tree_id'] for r in proposed})!=144:raise ValueError('List all 144 unique tree positions.')
    values={r['tree_id']:r['cultivar_id'] for r in proposed}
    if set(values)!={r['tree_id'] for r in orchard}:raise ValueError('Tree positions do not match the attachment.')
    if bees not in range(4) or budget not in [6000,10000]:raise ValueError('Unsupported bee units or budget.')
    rows=[0]*9;retained={'A':0,'B':0};changes=0;total=1500*bees
    for r in orchard:
        new=values[r['tree_id']];old=r['current_cultivar_id']
        if new==old:retained[old]+=1
        elif new in 'CDE' and len(new)==1:
            changes+=1;rows[int(r['row_id'])]+=1;total+=cost[new]
        else:raise ValueError('Changed tree positions can only use C, D or E.')
    if changes>12 or max(rows)>2:raise ValueError('Replant count or per-row limit exceeded.')
    if min(retained.values())<64:raise ValueError('Each main cultivar needs at least 64 retained trees.')
    if total>budget:raise ValueError(f'Cost {total} exceeds budget {budget}.')
    return {'changes':changes,'retained':retained,'bee_units':bees,'cost_yuan':total,'budget_yuan':budget}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--bees',type=int,required=True);p.add_argument('--budget',type=int,required=True);a=p.parse_args()
    try:print('PASS:',validate(a.plan,a.bees,a.budget))
    except (ValueError,KeyError,FileNotFoundError) as e:raise SystemExit('FAIL: '+str(e))
