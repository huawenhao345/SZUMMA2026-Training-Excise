#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate prescribed geometry, units, inflow bookkeeping and exact reproduction."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,math
from pathlib import Path
from make_inputs import build_files

def need(ok,message):
 if not ok:raise ValueError(message)
def number(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def read_csv(p,fields):
 with p.open(encoding='utf-8',newline='') as f:
  r=csv.DictReader(f);need(r.fieldnames==fields,'字段或顺序错误: '+p.name);a=list(r)
 need(all(None not in row and None not in row.values() for row in a),'CSV行列错误');return a

def check(directory):
 p=json.loads((directory/'parameters.json').read_text());r=json.loads((directory/'rules.json').read_text())
 need(p['schema_version']==r['schema_version']==1,'未知版本');need('非实测' in p['status'],'缺少参数性质声明')
 roof=p['roof']
 for k in ['length_m','width_m','base_EI_N_m2','dead_load_N_m','rho_kg_m3','gravity_m_s2']:
  need(number(roof[k]) and roof[k]>0,'非正或无效物理量: '+k)
 d=p['divider'];dr=p['drain'];L=roof['length_m']
 need(d['x_m']==L/2,'隔坎必须在中点')
 for k in ['height_above_roof_m','notch_width_m','coefficient_m05_s']:need(number(d[k]) and d[k]>0,'隔坎参数错误')
 need(0<dr['Cd']<=1 and dr['lip_above_roof_m']>=0,'出流参数错误')
 need(all(0<x<L/2 for x in dr['left_positions_m']) and all(L/2<x<L for x in dr['right_positions_m']),'排水口区属错误')
 ar=dr['area_range_m2'];need(0<ar[0]<ar[1] and ar[0]<=dr['original_area_m2']<=ar[1],'面积范围错误')
 need(dr['original_positions_m'][0] in dr['left_positions_m'] and dr['original_positions_m'][1] in dr['right_positions_m'],'原口位置不可选')
 rows=read_csv(directory/'inflows.csv',['case_id','start_min','end_min','left_L_min','right_L_min']);groups={k:[] for k in r['design']['case_ids']}
 for row in rows:
  need(row['case_id'] in groups,'未知进水工况');vals=[float(row[k]) for k in ['start_min','end_min','left_L_min','right_L_min']]
  need(all(math.isfinite(v) for v in vals) and vals[0]>=0 and vals[1]>vals[0] and min(vals[2:])>=0,'进水时段或流量错误');groups[row['case_id']].append(vals)
 curves=[]
 for c,a in groups.items():
  need(len(a)==5 and a[0][0]==0 and a[-1][1]==r['duration_min'],'进水时轴不完整: '+c)
  need(all(a[i][1]==a[i+1][0] for i in range(len(a)-1)),'进水时段重叠或间断')
  curves.append([(t0,t1,il+ir) for t0,t1,il,ir in a])
 need(all(v==curves[0] for v in curves),'三工况总进水曲线不同')
 opts=read_csv(directory/'stiffening_options.csv',['stiffening_id','EI_multiplier','M_limit_N_m','added_cost_cny'])
 need(len(opts)==3 and len({x['stiffening_id'] for x in opts})==3,'加固档位缺失或重复')
 need(all(float(x['EI_multiplier'])>=1 and float(x['M_limit_N_m'])>0 and float(x['added_cost_cny'])>=0 for x in opts),'加固参数错误')
 need(r['initial_water_m3']==[0,0] and r['duration_min']==90,'初始状态或观察时间错误')
 need(r['design']['fixed_across_cases'] is True,'方案必须固定')
 j=r['task_4'];need(j['left_drain_block_min']<j['start_min_range'][0]<=j['start_min_range'][1]<r['duration_min'],'堵塞与顶撑时序错误')
 need(j['jack_x_m']==d['x_m'] and j['target_downward_m']>0 and j['upward_rate_mm_min']>0 and j['reaction_limit_N']>0,'顶撑参数错误')
 need(j['remaining_water_requirement_applies'] is False and j['start_fixed_across_cases'] is True,'应急评价口径错误')
 hashes={}
 for name,b in build_files().items():
  need((directory/name).read_bytes()==b,'与确定性重生成不一致: '+name);hashes[name]=hashlib.sha256(b).hexdigest()
 return {'status':'PASS','machine_files':4,'inflow_rows':len(rows),'stiffening_rows':len(opts),'geometry':'PASS','same_total_inflow_curve':True,'time_rules':'PASS','byte_reproducible':True,'sha256':hashes}
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data');args=a.parse_args()
 try:result=check(args.data_dir)
 except (ValueError,KeyError,TypeError,OSError) as e:print(json.dumps({'status':'FAIL','reason':str(e)},ensure_ascii=False));return 1
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
