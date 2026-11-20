// Fixed-route JSP. One mandatory interval per actual operation.
using CP;

int nJobs = ...;
int nMachines = ...;
int nOperations = ...;
range Ops = 1..nOperations;
range Machines = 1..nMachines;
int job[Ops] = ...;
int operationNo[Ops] = ...;
int machine[Ops] = ...;
int processing[Ops] = ...;
int nextOperation[Ops] = ...;
int horizon = ...;
int lowerBound = ...;
float timeLimit = ...;
int solverThreads = ...;
int solverSeed = ...;

dvar interval task[o in Ops] in 0..horizon size processing[o];
dvar sequence machineOrder[k in Machines] in all(o in Ops : machine[o] == k) task[o];
dexpr int makespan = max(o in Ops : nextOperation[o] == 0) endOf(task[o]);

execute PARAMETERS {
  cp.param.TimeLimit = timeLimit;
  cp.param.Workers = solverThreads;
  cp.param.RandomSeed = solverSeed;
}

minimize makespan;

subject to {
  forall(o in Ops : nextOperation[o] != 0)
    endBeforeStart(task[o], task[nextOperation[o]]);
  forall(k in Machines)
    noOverlap(machineOrder[k]);
  makespan >= lowerBound;
}

execute EXPORT {
  var schedule = new IloOplOutputFile("cp_schedule.csv");
  schedule.writeln("operation_id,job_id,operation_no,machine_id,processing_h,start_h,end_h");
  for (var o in Ops)
    schedule.writeln(o, ",", job[o], ",", operationNo[o], ",", machine[o], ",",
                      processing[o], ",", task[o].start, ",", task[o].end);
  schedule.close();

  var summary = new IloOplOutputFile("cp_summary.csv");
  summary.writeln("cmax_h,best_bound_h,relative_gap,workers,time_limit_s");
  summary.writeln(cp.getObjValue(), ",", cp.getObjBound(), ",", cp.getObjGap(), ",",
                  solverThreads, ",", timeLimit);
  summary.close();
  writeln("RESULT: Cmax=", cp.getObjValue(), " h; bound=", cp.getObjBound(),
          "; gap=", cp.getObjGap());
}

main {
  thisOplModel.generate();
  if (cp.solve())
    thisOplModel.postProcess();
  else
    writeln("NO FEASIBLE SOLUTION");
}
