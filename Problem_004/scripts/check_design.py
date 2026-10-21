#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Only check component choices, cost and budget, not structural/hydraulic feasibility."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,json,math
from pathlib import Path

def need(ok,m):
 if not ok:raise ValueError(m)
def check(x,directory,budget):
 need(isinstance(x,dict) and set(x)=={'stiffening','left_x_m','right_x_m','left_area_m2','right_area_m2'},'设计字段不完整或含多余字段')
 p=json.loads((directory/'parameters.json').read_text());r=json.loads((directory/'rules.json').read_text());dr=p['drain']
 need(budget in r['design']['budgets_cny'],'预算须为1500或7500')
 with (directory/'stiffening_options.csv').open(newline='') as f:options={a['stiffening_id']:a for a in csv.DictReader(f)}
 need(isinstance(x['stiffening'],str) and x['stiffening'] in options,'未知加固档位')
 for k in ['left_x_m','right_x_m','left_area_m2','right_area_m2']:need(isinstance(x[k],(int,float)) and not isinstance(x[k],bool) and math.isfinite(x[k]),'字段必须为有限数值: '+k)
 need(x['left_x_m'] in dr['left_positions_m'] and x['right_x_m'] in dr['right_positions_m'],'排水口位置不允许')
 need(all(dr['area_range_m2'][0]<=x[k]<=dr['area_range_m2'][1] for k in ['left_area_m2','right_area_m2']),'排水口面积越界')
 price=p['pricing'];base=float(options[x['stiffening']]['added_cost_cny'])
 move=price['relocate_each_cny']*sum(v!=o for v,o in zip([x['left_x_m'],x['right_x_m']],dr['original_positions_m']))
 enlarge=price['area_added_cost_cny_per_m2']*(x['left_area_m2']+x['right_area_m2']-2*dr['original_area_m2']);total=base+move+enlarge
 need(total<=budget+1e-8,'超预算')
 return {'status':'PASS','scope':'仅选型、费用与预算；未判断挠度、弯矩、积水或顶撑可行性。','cost_cny':{'stiffening':base,'relocation':move,'enlargement':enlarge,'total':total},'budget_cny':budget}
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('design',type=Path);a.add_argument('--budget',required=True,type=float);a.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data');args=a.parse_args()
 try:result=check(json.loads(args.design.read_text()),args.data_dir,args.budget)
 except (ValueError,KeyError,TypeError,OSError) as e:print(json.dumps({'status':'FAIL','reason':str(e)},ensure_ascii=False));return 1
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
