# CP and MILP models for AeroHousing49

[中文说明](#中文说明)

Both models minimize makespan for the fixed-route AeroHousing49 instance. Each of the 300 operations has a unique ID `o`. The input gives its job (`job[o]`), position in the job route (`operationNo[o]`), assigned machine (`machine[o]`) and processing time (`processing[o]`). The array `nextOperation[o]` gives its job successor, or zero for the last operation. For example, J1's two visits to M3 have distinct operation IDs.

- [`jsp_cp.mod`](jsp_cp.mod) uses one mandatory interval per operation. `endBeforeStart` enforces job precedence and `noOverlap` prevents overlap between operations assigned to each machine.
- [`jsp_milp.mod`](jsp_milp.mod) uses one start-time variable per operation. For each pair of operations from different jobs assigned to the same machine, a binary variable and two big-M inequalities enforce their order. Job precedence already orders operations from the same job, including repeat visits to a machine. The big-M constant is the sum of processing times (1,087 h).

## Run the models

Use `oplrun` from IBM ILOG CPLEX Optimization Studio. The reference experiments used version 22.1.0.0 and the shared [OPL input](aero_housing_49_12_300_1800s.dat). It sets one worker/thread, a time limit of 1,800 s and random seed 20261110. Run both commands from the repository root.

```sh
oplrun models/jsp_cp.mod models/aero_housing_49_12_300_1800s.dat
oplrun models/jsp_milp.mod models/aero_housing_49_12_300_1800s.dat
```

CP writes `cp_schedule.csv` and `cp_summary.csv` in the current directory. MILP writes `cplex_schedule.csv`, `cplex_summary.csv` and an LP export (`jsp_milp.lp`). Schedule and summary files are written when the solver returns a feasible solution.

| Solver | Best feasible makespan (h) | Solver lower bound (h) | Reference result |
|---|---:|---:|---|
| CP Optimizer | 185 | 185 | Optimality proved in 0.08 s |
| CPLEX Optimizer (MILP) | 193 | 183 | Time limit reached, relative MIP gap 5.181% |

The solver input uses 183 h as the initial makespan lower bound (maximum machine load). The separate [analytical bounds](../analytical_bounds.json) give a stronger lower bound of 185 h. Reported runtimes and time-limited results can vary by platform.

## 中文说明

两个模型均以最小化最大完工时间为目标。300 道工序各有独立编号 `o`，由 `job[o]` 和 `operationNo[o]` 对应到工件及其工艺路线中的工序序号。模型通过 `machine[o]` 和 `processing[o]` 读取每道工序的指定设备和加工时间，通过 `nextOperation[o]` 读取同一工件的紧后工序。以 J1 为例，两道在 M3 加工的工序分别建模。

- **CP 模型**为每道工序定义一个必选区间变量，用 `endBeforeStart` 表示工序先后约束，用 `noOverlap` 保证同一设备上的加工区间互不重叠。
- **MILP 模型**为每道工序定义一个开工时间变量。同一设备上属于不同工件的工序对通过二元变量及大 M 约束确定先后关系。同一工件的工序由工艺先后约束排序，包括重复使用同一设备的工序。大 M 取工序加工时间之和 1087 h。

安装 IBM ILOG CPLEX Optimization Studio 后，从仓库根目录执行上方两条 `oplrun` 命令。两种模型使用同一份输入，设为单工作线程、求解时限 1800 s、随机种子 20261110。参考试验采用 22.1.0.0 版本。CP Optimizer 在 0.08 s 内证明最优值为 185 h。CPLEX Optimizer 在时限内得到的最好可行值为 193 h，求解器下界为 183 h，相对间隙为 5.181%。输入中的初始下界 183 h 为最大机器负载，独立计算的解析下界见 [`analytical_bounds.json`](../analytical_bounds.json)。
