# 参数附件说明

本题附件为**题设设计参数，不是实测数据**。这里没有车辆运行观测、待拟合样本或实机试验结论。参数用于构造可比较的机理分析与设计工况，不代表实际产品的性能标定、采购价格或安全认证。

附件共五个机器可读文件，全部为 UTF-8 编码。CSV 使用逗号分隔，首行为字段名，小数点为英文句点；JSON 中的数值均使用字段所标示的单位。角度在 `routes.csv` 中以度给出，电角度以弧度给出。温度用摄氏度，温差的数值等于相应开尔文温差。

| 文件 | 内容 | 规模 |
|---|---|---:|
| `parameters.json` | 机械、电机、热体及价格定义 | 1 个 JSON 对象 |
| `routes.csv` | 两条线路的坡度节点 | 12 行，A、B 各 6 行 |
| `gear_options.csv` | 可选齿轮比与增加费用 | 4 行 |
| `cooling_options.csv` | 三种散热包的增加质量、热参数与费用 | 3 行 |
| `rules.json` | 参考装置、正常运输、启停及断相条件 | 1 个 JSON 对象 |

## 1. 机械与电机参数

`parameters.json` 的 `schema_version` 是附件格式版本，`parameter_status` 说明参数性质。其余对象按下表解释。

`mechanical`：

| 字段 | 含义 | 单位 |
|---|---|---|
| `wheel_radius_m` | 车轮半径 | m |
| `base_mass_kg` | 基车质量，含固定构件及任一备选齿轮箱 | kg |
| `wheel_axle_inertia_kg_m2` | 所有车轮和轮轴的总转动惯量，不含发电机转子 | kg·m² |
| `generator_rotor_inertia_kg_m2` | 发电机转子转动惯量 | kg·m² |
| `gravity_m_s2` | 重力加速度 | m/s² |
| `rolling_resistance_coefficient` | 等效滚动阻力系数 | 无量纲 |
| `air_drag_coefficient_kg_m` | 风阻项 (c v^2) 的系数 (c) | kg/m |
| `base_mass_scope`、`wheel_axle_inertia_scope`、`gear_ratio_definition` | 相应定义的文字说明 | — |

车辆平动总质量为基车质量、载荷及散热增加质量之和；齿轮比改变不会另加基车质量。齿轮比 (q) 为发电机机械角速度与轮轴角速度之比。

`generator`：

| 字段 | 含义 | 单位 |
|---|---|---|
| `phase_count`、`phase_order` | 相数及矩阵行列对应的相序 a、b、c | — |
| `pole_pairs` | 极对数 (p) | 无量纲 |
| `phase_flux_peak_wb` | 每相永磁磁链峰值 (psi) | Wb |
| `inductance_matrix_h` | 三相完整电感矩阵；行、列均按 a、b、c 相排序 | 每项均为 H |
| `phase_copper_resistance_20c_ohm` | 20 ℃时的每相铜阻 | Ω |
| `copper_temp_coefficient_per_k` | 铜阻温度系数 | K⁻¹ |
| `copper_reference_temp_c` | 铜阻参考温度 | ℃ |
| `inductance_matrix_definition`、`phase_flux_definition`、`circuit_connection`、`external_resistor_scope` | 电感、永磁磁链、接线与外电阻定义 | — |

电感矩阵的对角项是自感，非对角项是互感，不可将其视为三个独立相电感。每相铜阻按题面给出的线性温度关系变化；外电阻 (R_e) 是**每相**电阻，不是整套电阻箱的合成电阻。两组 Y 星点互不连接，没有中性线。各相电流正向定义为从该相端口流向发电机星点 Ng。

`thermal`：`body_w`、`body_r` 分别定义电机热体与电阻箱热体；`capacity_unit`、`conductance_unit` 分别为 J/K、W/K；`capacity_and_conductance_scope`、`heat_input`、`cooling` 说明总热参数、发热归属和散热条件。热容与散热系数都是**整个热体的总量**，不是单相值。三相铜阻的总焦耳热进入电机热体，三相外电阻的总焦耳热进入电阻箱热体，两热体之间无热交换。

`pricing`：货币 `currency` 为人民币元。`external_box_fixed_cost_cny`、`external_box_cost_per_ohm_cny` 分别是 (R_e>0) 时整套电阻箱费用的固定项与每欧姆系数；(R_e=0) 时该项增加费用为零。`external_box_cost_definition`、`cost_scope`、`mass_scope` 为费用和质量范围说明。基础箱质量及热参数已分别计入基车与 S 包，不应再重复计入。

`idealizations` 列出题设近似条件。滚阻和风阻均阻碍下坡运动。坡度变化处不另计曲率引起的附加阻力。这些参数用于理想化模型的方案比较；超出题给电流、温度限制的计算不能用来推断实机允许的极限工况。

## 2. 坡道、齿轮与散热选项

`routes.csv`：

| 字段 | 含义 | 单位 |
|---|---|---|
| `route_id` | 线路编号 A 或 B | — |
| `x_m` | 自入口沿轨道量取的位置 | m |
| `slope_deg` | 该位置的下坡角度 | ° |

每条线路节点按位置递增排列，相邻节点间对**坡度角**线性插值。全长都是 180 m；两条线路总降高相同，陡坡所在位置不同。降高应由沿线路的坡角求得，附件没有高度观测值。

`gear_options.csv`：`q` 是允许的齿轮比，`added_cost_cny` 为该齿轮选型的增加费用，单位元。

`cooling_options.csv`：

| 字段 | 含义 | 单位 |
|---|---|---|
| `cooling_id` | 散热包编号 S、M 或 L | — |
| `added_mass_kg` | 在基车基础上增加的质量 | kg |
| `Cw_J_K` | 电机热体总热容 | J/K |
| `Hw_W_K` | 电机热体总散热系数 | W/K |
| `Cr_J_K` | 电阻箱热体总热容 | J/K |
| `Hr_W_K` | 电阻箱热体总散热系数 | W/K |
| `added_cost_cny` | 散热包增加费用 | 元 |

所选散热包的 `Cw_J_K` 等字段是该装置的**完整热参数**，不是在 S 包上累加的增量；只有质量与费用字段表示增加量。

## 3. 运行及故障规则

`rules.json` 的 `route` 描述线路长度、编号及插值规则；`design` 给出允许的齿轮比、每相外电阻闭区间以及散热包编号；`reference_design` 为题面指定的参考装置。`task_1`、`task_2` 分别对应前两问的计算工况，不是第三问的设计安全约束。

`normal_operation` 的数值字段说明如下：

| 字段 | 含义 | 单位 |
|---|---|---|
| `ambient_temp_c` | 正常运行环境温度 | ℃ |
| `initial_Tw_c`、`initial_Tr_c` | 第一趟放行前的两热体温度 | ℃ |
| `payload_kg_range` | 每个十趟试验的固定载荷范围，含端点 | kg |
| `entry_speed_m_s_range` | 每个十趟试验的固定入口速度范围，含端点 | m/s |
| `theta0_rad` | 正常放行的初始转子电角度 | rad |
| `initial_phase_current_a`、`next_release_phase_current_a` | 首次与后续放行的 a、b、c 相电流 | A |
| `run_count_each_case` | 每个正常工况的运行次数 | 次 |
| `release_interval_s` | 相邻两次放行时间间隔 | s |
| `return_and_loading_time_s` | 回程及装卸所需时间 | s |
| `travel_time_limit_s` | 每次下行时间上限 | s |
| `assessment_end_after_last_release_s` | 末次放行至整个正常工况考核结束的时间 | s |

`payload_and_entry_speed_fixed_within_case`、`routes_tested_separately`、`temperature_inherited_between_runs` 是布尔规则：每个十趟试验内载荷和入口速度不变；A、B 线路分别进行试验；温度在相邻运行之间继承。不能把两线路交替使用，也不能每趟把温度重新设为环境温度。

`arrival_and_wait` 描述入口之外的启停安排。到下端后，独立机械装置即时停车并锁住转子，机械动能不加到两个热体；电路继续连接，尾电流衰减产生的热量仍须保留。回程及装卸由外部牵引完成，并与发电机机械脱开；之后等待下一次放行。整个停歇阶段保持相同散热条件。下一趟电流取零，但两热体温度继承。正常工况的末趟也包含尾电流和停歇，考核至该趟放行后 360 s。

`limits` 中 `speed_m_s`、`winding_temp_c`、`resistor_temp_c`、`absolute_phase_current_a` 分别是车辆速度、电机热体温度、电阻箱温度、各相电流瞬时绝对值的上限，单位依次为 m/s、℃、℃、A。上限值本身允许取到。

`fault_operation` 指第四问的第十趟运行：

| 字段 | 含义 | 单位 |
|---|---|---|
| `completed_normal_runs_before_fault` | 故障前已完成的正常运输次数 | 次 |
| `prehistory_payload_kg` | 该九趟正常运输使用的固定载荷 | kg |
| `prehistory_entry_speed_m_s` | 该九趟正常运输使用的固定入口速度 | m/s |
| `failed_phase` | 放行前已断开的相 | — |
| `payload_kg_range` | 故障趟允许的载荷闭区间 | kg |
| `entry_speed_m_s_range` | 故障趟入口速度闭区间 | m/s |
| `theta0_rad_range` | 故障趟未知初始电角度区间 | rad |
| `initial_phase_current_a` | 故障趟放行时各相电流 | A |

`fault_timing`、`remaining_circuit`、`initial_temperature` 分别说明断相时机、剩余电路和热状态继承；不模拟带电开断瞬态。温度来自**同一设计、同一线路**的指定正常前史，环境及发车间隔沿用第三问。`theta0_rad_range` 表示从 0 到 2π 的周期，取值区间为左闭右开；`all_initial_conditions_required` 为真，表示允许下行的载荷必须对所有该区间初始电角度及题给入口速度满足限制。`travel_time_limit_applies` 和 `return_time_applies` 均为假：故障趟免于 300 s 下行要求，不考核随后回程。`assessed_quantities`、`assessment_interval` 给出考核量及其区间，从第十次放行至到达终点停车。

## 4. 重生成与检查

无需下载外部数据，Python 3 标准库即可重建和检查附件：

```sh
python3 scripts/make_inputs.py --output /tmp/problem003-inputs
python3 scripts/check_inputs.py
```

生成程序不使用随机数。`make_inputs.py` 只生成上述五个机器文件，不生成车辆轨迹、试算方案或答案；默认输出到本题 `data/`。检查程序核查字段、参数范围、矩阵正定性、线路降高与发车安排的一致性，并比较五文件与重生成内容的字节和 SHA-256。

选型检查接受自己保存的 JSON 文件，字段为 `q`、`Re_ohm`、`cooling`：

```sh
python3 scripts/check_design.py design.json
```

该程序仅检查选型范围并计算增加费用、散热增加质量和不含载荷的车辆总质量。输出 `PASS` **不表示**速度、温度、电流或运行时间满足要求；这些仍须由参赛队伍的机理模型检验。工具不提供动力学求解器或优化器。

五个机器文件的数值来源为题面设计设定；本附件未转载外部真实数据，也未对这些设定添加实测或产品许可声明。
