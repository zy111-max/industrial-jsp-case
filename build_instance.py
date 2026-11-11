"""Build a traceable fixed-machine JSP derivative of the housing workshop case.

Python 3.9+; standard library only. Batch quantities are research design values.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

NAME='aero_housing_49_12_300'
FAMILIES=[1,6,7,8,9,10]
QUANTITIES={1:10,6:18,7:15,8:3,9:2,10:1}
N_JOBS=49
N_OPERATIONS=300


def json_bytes(x):
    return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def csv_bytes(header,rows):
    stream=io.StringIO(newline='')
    writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8-sig')


def construct(source,source_hash):
    original={f['source_family_id']:f for f in source['families']}
    assert source['time_unit']=='h' and len(source['machines'])==12
    conflicts={c['source_family_id'] for c in source['observed_source_conflicts']}
    assert not conflicts.intersection(FAMILIES)
    for f in source['families']:
        assert [o['operation_no'] for o in f['operations']]==list(range(1,len(f['operations'])+1))
        for op in f['operations']:
            seen=set()
            for a in op['alternatives']:
                assert type(a['machine_id']) is int and 1<=a['machine_id']<=12
                assert type(a['processing_time_h']) is int and a['processing_time_h']>0
                assert a['machine_id'] not in seen
                seen.add(a['machine_id'])
    jobs=[]
    for family_id in FAMILIES:
        family=original[family_id]
        for serial in range(1,QUANTITIES[family_id]+1):
            jobs.append({'job_id':len(jobs)+1,'source_family_id':family_id,
                         'serial_within_family':serial,'operations':family['operations']})
    score={j['job_id']:sum(min(a['processing_time_h'] for a in o['alternatives']) for o in j['operations']) for j in jobs}
    priority=sorted(jobs,key=lambda j:(-score[j['job_id']],j['job_id']))
    loads={m:0 for m in range(1,13)}
    fixed={}
    for job in priority:
        ops=[]
        for op in job['operations']:
            chosen=min(op['alternatives'],key=lambda a:(loads[a['machine_id']]+a['processing_time_h'],a['processing_time_h'],a['machine_id']))
            m,p=chosen['machine_id'],chosen['processing_time_h']
            loads[m]+=p
            ops.append({'operation_no':op['operation_no'],'name_zh':op['name_zh'],
                        'machine_id':m,'processing_time_h':p})
        fixed[job['job_id']]={**job,'operations':ops}
    instance={
        'instance_name':NAME,'n_jobs':N_JOBS,'n_machines':12,'n_operations':N_OPERATIONS,
        'time_unit':'h','machine_index_base':1,
        'problem':'fixed-route, nonpreemptive JSP with repeated machine visits',
        'data_status':'industrial-source derivative with a designed order mix and fixed machine assignments',
        'source_fjsp_sha256':source_hash,'source_author':'谢晋','source_year':2022,
        'source_family_ids':FAMILIES,'designed_order_quantities':QUANTITIES,
        'original_quantity_per_family':5,
        'batch_note':'Family quantities are experimental order design values, not a recorded enterprise order.',
        'machine_assignment_rule':{
            'job_order':'descending sum of minimum eligible operation times; ties by job_id',
            'machine_choice':'minimum (allocated_load + processing_time, processing_time, machine_id)',
            'allocated_load_definition':'sum of durations already assigned to the physical machine',
            'job_allocation_order':[j['job_id'] for j in priority],
            'frozen_before_scheduling':True},
        'model_assumptions':[
            'all jobs released at time zero',
            'each operation has one preassigned eligible machine',
            'original operation order and selected-machine processing times retained',
            'nonpreemptive operations; one operation at a time on each resource',
            'repeated visits to the same physical machine are retained',
            'transport, sequence-dependent setup, breakdowns and resource calendars omitted',
            'fitting, oil-sealing and inspection stations modeled as unit-capacity resources',
            'no fictitious operations, time jitter or operation splitting added'],
        'machines':source['machines'],'machine_processing_loads_h':[loads[m] for m in range(1,13)],
        'jobs':[fixed[j] for j in range(1,N_JOBS+1)]
    }
    return instance,original


def greedy_schedule(instance):
    next_op=[0]*N_JOBS; ready=[0]*N_JOBS; machine_ready=[0]*12; rows=[]
    for _ in range(N_OPERATIONS):
        candidates=[]
        for j,job in enumerate(instance['jobs']):
            k=next_op[j]
            if k==len(job['operations']):continue
            op=job['operations'][k]; m=op['machine_id']; p=op['processing_time_h']
            start=max(ready[j],machine_ready[m-1])
            candidates.append((start,start+p,j,k,m))
        start,end,j,k,m=min(candidates)
        rows.append({'job_id':j+1,'operation_no':k+1,'machine_id':m,'start_h':start,'end_h':end})
        ready[j]=machine_ready[m-1]=end; next_op[j]+=1
    return rows


def validate(instance,original,rows):
    assert len(instance['jobs'])==N_JOBS and sum(len(j['operations']) for j in instance['jobs'])==N_OPERATIONS
    expected={(j['job_id'],o['operation_no']):o for j in instance['jobs'] for o in j['operations']}
    actual={(r['job_id'],r['operation_no']):r for r in rows}
    assert len(rows)==len(actual)==N_OPERATIONS and actual.keys()==expected.keys()
    allowed_resource={'钳工':{1,2,3},'镗工':{4,5},'铣工':{4,5},'车工':{6,7},
                      '立车':{6,7},'打印':{1,2,3},'清洗':{8,9,10},'包装':{8,9,10},'检验':{11,12}}
    for job in instance['jobs']:
        raw=original[job['source_family_id']]['operations']
        assert len(job['operations'])==len(raw)
        for op,source_op in zip(job['operations'],raw):
            pair=op['machine_id'],op['processing_time_h']
            assert op['name_zh']==source_op['name_zh']
            assert pair in {(a['machine_id'],a['processing_time_h']) for a in source_op['alternatives']}
            assert op['machine_id'] in allowed_resource[op['name_zh']]
            row=actual[job['job_id'],op['operation_no']]
            assert row['machine_id']==op['machine_id'] and row['start_h']>=0
            assert row['end_h']-row['start_h']==op['processing_time_h']
            if op['operation_no']>1:
                assert actual[job['job_id'],op['operation_no']-1]['end_h']<=row['start_h']
    for m in range(1,13):
        same=sorted((r for r in rows if r['machine_id']==m),key=lambda r:r['start_h'])
        assert same and all(a['end_h']<=b['start_h'] for a,b in zip(same,same[1:]))


def artifacts(source_path):
    raw=source_path.read_bytes(); source=json.loads(raw)
    instance,original=construct(source,hashlib.sha256(raw).hexdigest())
    schedule=greedy_schedule(instance); validate(instance,original,schedule)
    operations=[(j,o) for j in instance['jobs'] for o in j['operations']]
    pairs=[(u,v) for u,v in combinations(range(N_OPERATIONS),2)
           if operations[u][0]['job_id']!=operations[v][0]['job_id']
           and operations[u][1]['machine_id']==operations[v][1]['machine_id']]
    job_totals=[sum(o['processing_time_h'] for o in j['operations']) for j in instance['jobs']]
    counts=Counter(len(j['operations']) for j in instance['jobs'])
    lb=max(job_totals+instance['machine_processing_loads_h'])
    report={
        'instance_name':NAME,'n_jobs':N_JOBS,'n_machines':12,'n_operations':N_OPERATIONS,'time_unit':'h',
        'job_operation_count_distribution':dict(sorted(counts.items())),
        'maximum_share_of_jobs_with_same_operation_count':max(counts.values())/N_JOBS,
        'machine_operation_counts':[sum(o['machine_id']==m for j,o in operations) for m in range(1,13)],
        'machine_processing_loads_h':instance['machine_processing_loads_h'],
        'job_processing_totals_h':job_totals,'simple_lower_bound_h':lb,
        'greedy_feasible_makespan_h':max(r['end_h'] for r in schedule),
        'greedy_is_not_an_optimum_claim':True,
        'milp_size':{'binary_machine_order_variables':len(pairs),'continuous_variables':N_OPERATIONS+1,
                     'constraints_including_simple_lower_bound':N_OPERATIONS+1+2*len(pairs)},
        'baseline_47_operation_order_binaries':120,
        'checks':{'all_300_operations_retained':True,'all_selected_pairs_from_source':True,
                  'all_processing_names_match_source':True,'all_resource_types_match_equipment_table':True,
                  'all_12_physical_resources_used':True,'positive_durations':True,
                  'feasible_schedule_coverage':True,'feasible_schedule_precedence':True,
                  'feasible_schedule_machine_capacity':True},
        'greedy_schedule':schedule
    }
    text=['# Aerospace housing JSP derived from Xie Jin (2022), Section 6.2 and Appendix 6.',
          '# 49 jobs, 12 physical resources, 300 operations. Processing times: hours.',
          '# One job per line; zero-based machine/time pairs. Job lengths vary; revisits are intentional.',
          '# Families 1,6,7,8,9,10; designed quantities 10,18,15,3,2,1 respectively.','49 12']
    for job in instance['jobs']:
        text.append(' '.join(str(x) for op in job['operations'] for x in (op['machine_id']-1,op['processing_time_h'])))
    txt=('\n'.join(text)+'\n').encode('utf-8')
    parsed=[list(map(int,line.split())) for line in text[5:]]
    assert len(parsed)==N_JOBS
    for line,job in zip(parsed,instance['jobs']):
        assert list(zip(line[::2],line[1::2]))==[(o['machine_id']-1,o['processing_time_h']) for o in job['operations']]
    arrays={
      'job':[j['job_id'] for j,o in operations], 'operationNo':[o['operation_no'] for j,o in operations],
      'machine':[o['machine_id'] for j,o in operations], 'processing':[o['processing_time_h'] for j,o in operations],
      'nextOperation':[i+2 if i<N_OPERATIONS-1 and operations[i+1][0]['job_id']==j['job_id'] else 0 for i,(j,o) in enumerate(operations)]}
    dat=['// Processing-time unit: hours. Frozen assignments from the supplied instance JSON.',
         'nJobs = 49;','nMachines = 12;','nOperations = 300;']
    dat += [k+' = '+json.dumps(v)+';' for k,v in arrays.items()]
    dat += [f"horizon = {sum(arrays['processing'])};",f'lowerBound = {lb};',
            'timeLimit = 60;','solverThreads = 1;','solverSeed = 20261110;']
    return {
      NAME+'.json':json_bytes(instance),NAME+'.txt':txt,NAME+'.dat':('\n'.join(dat)+'\n').encode('utf-8'),
      'validation_report.json':json_bytes(report),
      'operations.csv':csv_bytes(['job_id','source_family_id','serial_within_family','operation_no','operation_name','machine_id_1based','processing_h'],
        [[j['job_id'],j['source_family_id'],j['serial_within_family'],o['operation_no'],o['name_zh'],o['machine_id'],o['processing_time_h']] for j,o in operations]),
      'jobs.csv':csv_bytes(['job_id','source_family_id','serial_within_family','n_operations','job_processing_total_h'],
        [[j['job_id'],j['source_family_id'],j['serial_within_family'],len(j['operations']),sum(o['processing_time_h'] for o in j['operations'])] for j in instance['jobs']]),
      'machines.csv':csv_bytes(['machine_id_1based','resource_type','source_equipment_code'],
        [[m['machine_id'],m['resource_type_zh'],m['source_equipment_code']] for m in instance['machines']]),
      'greedy_schedule.csv':csv_bytes(['job_id','operation_no','machine_id','start_h','end_h'],
        [[r[k] for k in ['job_id','operation_no','machine_id','start_h','end_h']] for r in schedule])
    }


def main():
    base=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=base)
    parser.add_argument('--source',type=Path,default=base/'source_fjsp_families.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args(); built=artifacts(args.source)
    args.output_dir.mkdir(exist_ok=True,parents=True)
    for name,data in built.items():
        path=args.output_dir/name
        if args.check:
            assert path.read_bytes()==data,'Reproduction mismatch: '+name
        else:path.write_bytes(data)
    print('PASS:', 'byte-for-byte reproduction of' if args.check else 'generated', len(built),'files;',N_JOBS,'jobs;',12,'resources;',N_OPERATIONS,'operations.')


if __name__=='__main__':main()
