// Disjunctive JSP MILP corresponding to manuscript Section 1.2.
// Index each operation separately to allow unequal job lengths and revisits.
int nJobs = ...;
int nMachines = ...;
int nOperations = ...;
range Ops = 1..nOperations;
int job[Ops] = ...;
int operationNo[Ops] = ...;
int machine[Ops] = ...;
int processing[Ops] = ...;
int nextOperation[Ops] = ...; // zero denotes the last operation of a job
int horizon = ...;
int lowerBound = ...;
float timeLimit = ...;
int solverThreads = ...;
int solverSeed = ...;

tuple OperationPair { int a; int b; }
{OperationPair} MachinePairs = {
  <a,b> | a,b in Ops : a < b && machine[a] == machine[b] && job[a] != job[b]
};

// Same-job operation pairs already have an order from job precedence.
dvar float start[Ops] in 0..horizon;
dvar float Cmax in 0..horizon;
// before[<a,b>]=1 means that operation a precedes operation b.
dvar boolean before[MachinePairs];

execute PARAMETERS {
  cplex.tilim = timeLimit;
  cplex.threads = solverThreads;
  cplex.randomseed = solverSeed;
  cplex.epgap = 0;
  cplex.epagap = 1e-9;
  cplex.clocktype = 2;
}

minimize Cmax;
subject to {
  // (1) Technological precedence.
  forall(o in Ops : nextOperation[o] != 0)
    precedence: start[nextOperation[o]] >= start[o] + processing[o];
  // (2)-(3) Disjunctive nonoverlap on each physical machine.
  forall(pair in MachinePairs) {
    machineOrderA: start[pair.a] + processing[pair.a]
                  <= start[pair.b] + horizon*(1-before[pair]);
    machineOrderB: start[pair.b] + processing[pair.b]
                  <= start[pair.a] + horizon*before[pair];
  }
  // (4) Last-operation completion bounds.
  forall(o in Ops : nextOperation[o] == 0)
    makespan: Cmax >= start[o] + processing[o];
  // Valid bound computed only from the input data.
  validLowerBound: Cmax >= lowerBound;
  // (5) Nonnegative starts and binary ordering variables are declared above.
}

execute EXPORT {
  var schedule = new IloOplOutputFile("cplex_schedule.csv");
  schedule.writeln("operation_id,job_id,operation_no,machine_id,processing_h,start_h,end_h");
  for (var o in Ops)
    schedule.writeln(o,",",job[o],",",operationNo[o],",",machine[o],",",
                     processing[o],",",start[o],",",start[o]+processing[o]);
  schedule.close();
  var summary = new IloOplOutputFile("cplex_summary.csv");
  summary.writeln("cmax_h,best_bound_h,relative_gap,status_code,solve_seconds,n_nodes,n_rows,n_cols,order_binaries,threads,time_limit_s,big_m");
  summary.writeln(Cmax,",",cplex.getBestObjValue(),",",cplex.getMIPRelativeGap(),",",
                  cplex.getCplexStatus(),",",cplex.getSolvedTime(),",",cplex.getNnodes(),",",
                  cplex.getNrows(),",",cplex.getNcols(),",",MachinePairs.size,",",
                  solverThreads,",",timeLimit,",",horizon);
  summary.close();
  writeln("RESULT: Cmax=",Cmax," h; bound=",cplex.getBestObjValue(),
          "; gap=",cplex.getMIPRelativeGap(),"; status=",cplex.getCplexStatus());
}

main {
  thisOplModel.generate();
  cplex.exportModel("jsp_milp.lp");
  if (cplex.solve()) thisOplModel.postProcess();
  else writeln("NO FEASIBLE SOLUTION; CPLEX status=",cplex.getCplexStatus());
}
