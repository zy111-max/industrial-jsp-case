# Aerospace housing JSP: AeroHousing49

[中文说明](README_转换说明.md)

A reproducible **49-job, 12-machine, 300-operation** fixed-route job-shop instance derived from a published aerospace housing machining case. Processing times are in **hours**. Operation routes, eligible machines and processing times come from the source thesis. The order quantities and the fixed machine allocation are this repository's research-design choices.

## Source

Xie Jin (谢晋). *Job shop scheduling method based on hybrid genetic tabu search algorithm* (基于混合遗传禁忌搜索算法的作业车间调度方法). PhD thesis, Huazhong University of Science and Technology, Wuhan, 2022.

Section 6.2 (printed pp. 109–111, Tables 6.1–6.6) and Appendix 6 (printed pp. 154–155, Tables 1–5) describe a machining workshop of an aerospace equipment manufacturer. Drawings and machining features were withheld by the enterprise.

The source problem is a flexible job shop:
- 10 housing types with 5 pieces each, i.e. 50 jobs;
- 12 machines and 265 operations;
- 130 eligible machine/time pairs.

The thesis reports a makespan of 549 h for the enterprise schedule and 463 h for its HGTSA algorithm on that FJSP. These values are not comparable with this fixed-route derivative.

`source_fjsp_families.json` transcribes all 10 types and all 130 pairs. `original_fjsp_50_12_265.json` expands the original 50-job FJSP.

## Instance

| Item | Value |
|---|---|
| Jobs / machines / operations | 49 / 12 / 300 |
| Source types used | 1, 6, 7, 8, 9, 10 |
| Pieces per type | 10, 18, 15, 3, 2, 1 (jobs J1–J10, J11–J28, J29–J43, J44–J46, J47–J48, J49) |
| Operations per job | 5, 4, 10, 2, 9, 4 by type; counts are 2: 3 jobs, 4: 19, 5: 10, 9: 2, 10: 15 |
| Time unit | hours (h), unchanged from the source |
| Objective | minimize makespan |
| Lower bound | 185 h (see below) |
| Known optimum | 185 h (`optimal_schedule.csv` attains the lower bound) |

### Machines

The machines and allocated loads are as follows (loads in hours):

| Machines | Resource type | Allocated load (h) |
|---|---|---|
| M1–M3 | fitter benches (钳工) | 59, 51, 56 |
| M4–M5 | CNC horizontal boring–milling machines (数控卧式镗铣床) | 181, 183 |
| M6–M7 | CNC vertical lathes (数控立车) | 164, 171 |
| M8–M10 | oil-seal / cleaning stations (油封工) | 38, 38, 36 |
| M11–M12 | inspection stations (检验) | 55, 55 |

**Why these quantities.** Equal quantities would leave the two boring–milling machines as the only bottleneck. The chosen quantities bring them closer to the vertical lathes. Jobs of the same type keep the same route and times; no operation is split, removed, added or perturbed.

**Why only six types.** In Tables 6.3–6.6, some inspection operations of types 2–5 list M4/M5, which Table 6.1 classifies as boring–milling machines. This repository keeps those entries unchanged in the raw transcription and does not guess a correction. Instead, it uses only the six types whose machine assignments agree with the equipment table.

## Deterministic machine allocation

1. For each job, sum the shortest eligible processing time of every operation.
2. Visit jobs by descending sum, ties by ascending job number.
3. Within a job, in route order, choose the eligible machine minimizing `(allocated load + processing time, processing time, machine number)` lexicographically. Then add the time to that machine's load.
4. Freeze the assignments before scheduling. Every selected duration is the published duration on the chosen machine.

## Model

- All jobs are available at time zero.
- Operations are nonpreemptive.
- Job precedence and unit machine capacity apply.
- Transport, setup, shifts and breakdowns are not modelled.
- 26 of the 49 jobs revisit a machine (for example, J1 visits M3 twice and J11 visits M7 twice), and jobs have different numbers of operations. A loader must read the actual number of machine/time pairs on each line, not assume one operation per machine.

## Lower bound and optimum

The bound is `max(longest job, max over machines of (shortest job head before the machine + machine load + shortest job tail after it))`. It evaluates to **185 h** on M5; per-machine values are in `analytical_bounds.json`.

`optimal_schedule.csv` has makespan **185 h**, which equals the bound, so it is optimal. It was found by a hybrid KOA–tabu-search algorithm. The schedule was checked independently for route, durations, precedence and machine capacity. `greedy_schedule.csv` is a simple feasible schedule at 187 h used for validation.

## Files

| File | Contents |
|---|---|
| `aero_housing_49_12_300.txt` | Solver input: first line `n m`, then one job per line of **zero-based** machine/time pairs |
| `aero_housing_49_12_300.json` | Jobs, types, operation names and fixed assignments; **one-based** machines |
| `jobs.csv`, `operations.csv`, `machines.csv` | The same data as tables |
| `aero_housing_49_12_300.dat` | The same data for CPLEX OPL |
| `source_fjsp_families.json` | Transcription of all 10 source types and 130 eligible pairs, with page references and the noted source inconsistency |
| `original_fjsp_50_12_265.json` | The original 50-job FJSP expanded from the source |
| `analytical_bounds.json` | Per-machine lower bounds |
| `optimal_schedule.csv` | Optimal schedule, makespan 185 h (`job_id, operation_no, machine_id, start_h, end_h`) |
| `greedy_schedule.csv`, `validation_report.json` | Feasible greedy schedule and data checks |
| `build_instance.py` | Rebuilds every derived file from `source_fjsp_families.json` (Python 3.9+, standard library) |

```text
python build_instance.py --check   # byte-for-byte check of the derived files
python build_instance.py           # rebuild them
```

## Citation and license

Please cite the source thesis and this repository when using the instance. See `DATA_LICENSE.md` for the scope of rights; the MIT license in `LICENSE` covers the code and documentation written for this repository only.
