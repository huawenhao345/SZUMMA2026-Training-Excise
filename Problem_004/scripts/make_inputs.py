#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Recreate prescribed design inputs; no observations, structural solver or answer."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,io,json
from pathlib import Path

def build_files():
 p={'schema_version':1,'status':'原创题设设计参数与工况，非实测数据；费用不是市场报价。',
 'roof':{'length_m':6.,'width_m':4.,'base_EI_N_m2':400000.,'dead_load_N_m':600.,'rho_kg_m3':1000.,'gravity_m_s2':9.81,
 'reference':'梁未加载、两端支承同高的水平线为高程零；向下挠度w为正，屋面高程为-w。',
 'beam':'Euler–Bernoulli小挠度线弹性等效梁；横向刚性；两端竖向位移零且转动自由，锚固可承受上拔。忽略轴向伸长、结构振动与水的附加惯性。',
 'loads':'dead_load已为整个4m宽条带的均布线荷载；水荷载另按真实水深计算。围护承担水平水压。加固增加自重忽略。'},
 'divider':{'x_m':3.,'height_above_roof_m':.04,'notch_width_m':.10,'coefficient_m05_s':1.6,
 'flow':'Q12=Cw*notch_width*([H1-zc]_+^1.5-[H2-zc]_+^1.5)，zc=-w(3)+height；Q12正值从区1流向区2。',
 'motion':'隔坎随屋面移动；除所给过水槽外不跨区漏水。'},
 'drain':{'Cd':.62,'lip_above_roof_m':.005,'area_range_m2':[.0006,.0012],
 'left_positions_m':[.6,1.2,1.8,2.4],'right_positions_m':[3.6,4.2,4.8,5.4],
 'original_positions_m':[1.2,4.8],'original_area_m2':.0006,
 'flow':'Qj=Cd*Aj*sqrt(2*g*[Hj+w(xj)-lip]_+)；下游自由出流、无回流，停雨后仍适用。',
 'motion':'排水口随当地屋面移动，唇口与屋面保持给定高差；排水管出口通大气。'},
 'hydraulics':{'units':'水位H为相对零线的绝对高程，不是平均水深；体积为m3；流量公式用m3/s。',
 'model':'两区各自水面水平；忽略区内水平流动水头损失，水深由水面与变形屋面高差决定，干处为零；无蒸发渗漏和外缘溢流。分区仅通过所给槽交换。',
 'time_scales':'结构与区内水面平衡比进排水快；各时刻按当前各区水量求准静态弹性平衡。'},
 'pricing':{'currency':'CNY','relocate_each_cny':450.,'area_added_cost_cny_per_m2':3000000.,
 'formula':'总增加费=加固费+450*(改变位置的排水口个数)+3000000*((A1-.0006)+(A2-.0006))。保留原位置不收费。'},
 'provenance':'全部数值为可复现的设计设定。文献只支持基本机制，不是数值来源。'}
 rules={'schema_version':1,'status':'题设运行与评价规则，非实测数据。',
 'reference_design':{'stiffening':'B','left_x_m':1.2,'right_x_m':4.8,'left_area_m2':.0006,'right_area_m2':.0006},
 'duration_min':90.,'initial_water_m3':[0.,0.], 'initial_structure':'在恒载下的干屋面平衡；不将初始屋面当作无挠度水平面。',
 'task_1':{'divider_removed':True,'drains_closed':True,'water_volumes_m3':[.1,.5,1.],'maintained_level_m':.01,
 'comparison':'给定有限总水量的封闭试验，对比外接水箱维持给定水位的辅助试验。静力稳定与位移/弯矩限值分别检查。'},
 'task_2':{'cases':['U','L','R'],'reference_design':True,'include_rigid_comparison':True},
 'design':{'budgets_cny':[1500.,7500.],'case_ids':['U','L','R'],'fixed_across_cases':True,
 'limits':{'downward_deflection_m':.12,'remaining_water_m3_at_90min':.18},
 'moment_limit':'使用stiffening_options.csv所选行的M_limit_N_m，正负弯矩均取绝对值。'},
 'task_4':{'base_design':'第三问7500元预算推荐方案，不重新改选组件；考察U/L/R三种进水。',
 'left_drain_block_min':25.,'blockage_after':'左排水口此后完全堵塞，右口不变；无顶撑作为对照。',
 'jack_x_m':3.,'start_min_range':[30.,60.],'target_downward_m':.012,'upward_rate_mm_min':2.,'reaction_limit_N':5000.,
 'jack_rule':'启动前支柱不接触。s0=max(启动前瞬时中点挠度,0.012)，支柱顶高程为-s；启动后s=max(0.012,s0-0.002*(t-tJ))，t以分钟计。',
 'contact':'仅向上承压、不向下拉；梁中点向下挠度不能超过s。若未接触，支柱反力为零。',
 'observation_end_min':90.,'remaining_water_requirement_applies':False,
 'retained_limits':['所选正负弯矩限值','向下挠度0.12m','顶撑反力5000N'],
 'start_fixed_across_cases':True,'restriction':'启动前已经越限的过程不能因后来恢复而判为满足要求。'}}
 rows=[]
 cases={'U':[(0,15,12,12),(15,30,36,36),(30,45,12,12),(45,60,0,0),(60,90,0,0)],
 'L':[(0,15,24,0),(15,30,60,12),(30,45,0,24),(45,60,0,0),(60,90,0,0)],
 'R':[(0,15,0,24),(15,30,12,60),(30,45,24,0),(45,60,0,0),(60,90,0,0)]}
 for c,blocks in cases.items():rows.extend((c,*b) for b in blocks)
 options=[('B',1.,12000.,0.),('S',1.25,14000.,3000.),('T',1.5,16000.,6000.)]
 def csv_bytes(fields,rows):
  f=io.StringIO(newline='');w=csv.writer(f,lineterminator='\n');w.writerow(fields);w.writerows(rows);return f.getvalue().encode()
 def js(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 return {'parameters.json':js(p),'rules.json':js(rules),
 'inflows.csv':csv_bytes(['case_id','start_min','end_min','left_L_min','right_L_min'],rows),
 'stiffening_options.csv':csv_bytes(['stiffening_id','EI_multiplier','M_limit_N_m','added_cost_cny'],options)}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data');a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 for n,b in build_files().items():(a.output/n).write_bytes(b)
 print(json.dumps({'status':'PASS','files':list(build_files()),'output':str(a.output)},ensure_ascii=False))
if __name__=='__main__':main()
