#!/usr/bin/env python3
import csv,json,hashlib
from pathlib import Path
root=Path("stage5_outputs")
A=list(csv.DictReader(open(root/"experiment_A/two_state_results.csv")))
B=list(csv.DictReader(open(root/"experiment_B/selection_repetitions.csv")))
BOR=list(csv.DictReader(open(root/"experiment_B/oracle_resolution.csv")))
BG=list(csv.DictReader(open(root/"experiment_B/gate2_tests.csv")))
BS=json.loads((root/"experiment_B/summary.json").read_text())
BW=list(csv.DictReader(open(root/"experiment_B/work_summary.csv")))
BA=list(csv.DictReader(open(root/"experiment_B/work_accounting.csv")))
expected_work={"local_RWM":(3000,1),"transport_independence":(3000,1),"parallel_tempering":(600,5)}
gate_groups={}
for r in BG:
 key=(r["setting"],r["decision_replicate"],r["algorithm"])
 gate_groups.setdefault(key,[]).append(r["passed"]=="True")
gate_reconstruct=True
for r in B:
 eligible=[a for a in ("local_RWM","transport_independence","parallel_tempering")
           if len(gate_groups.get((r["setting"],r["decision_replicate"],a),[]))==4
           and all(gate_groups[(r["setting"],r["decision_replicate"],a)])]
 gate_reconstruct &= len(eligible)==int(r["eligible_count"])
 gate_reconstruct &= (r["gated"]=="ABORT" if not eligible else r["gated"] in eligible)
checks={
 "A_rows_117":len(A)==117,
 "A_exact_mc_within_5se":all(abs(float(r["mc_all_zero_probability"])-float(r["theorem_all_zero_probability"]))<=5*max(float(r["mc_all_zero_se"]),1/5000) for r in A),
 "A_prevents_false_selection":any(float(r["naive_selection_error"])-float(r["gated_selection_error"])>.05 for r in A),
 "B_decisions_300":len(B)==300,
 "B_oracle_stream_disjoint":all(r["oracle_source"]=="disjoint_2x10000_path_stream" for r in B),
 "B_oracles_resolved_twice":len(BOR)==3 and all(r["oracle_resolved"]=="True" and r["combined_winner"]==r["batch_1_winner"]==r["batch_2_winner"] and float(r["gap_z_score"])>=5 for r in BOR),
 "B_summary_independent_oracle":BS["status"]=="PASS_MATCHED_WORK_WITH_INDEPENDENT_ORACLE" and BS["oracle_paths_per_algorithm_setting"]==20000,
 "B_matched_target_work":BS["matched_target_evaluations_per_path"]==3000 and len(BW)==3 and len(BA)==36 and len({int(r["target_evaluations_per_path"]) for r in BW})==1 and len({int(r["total_recorded_target_evaluations"]) for r in BW})==1 and all(int(r["offline_training_target_evaluations"])==0 for r in BW) and all((int(r["sweeps_per_path"]),int(r["target_evaluations_per_sweep"]))==expected_work[r["algorithm"]] and int(r["target_evaluations_per_path"])==3000 and int(r["total_recorded_target_evaluations"])==385659000 and float(r["total_elapsed_seconds"])>0 for r in BW) and all(int(r["sweeps_per_path"])*int(r["target_evaluations_per_sweep"])==int(r["target_evaluations_per_path"])==3000 and int(r["total_target_evaluations"])==int(r["paths"])*3000 and float(r["elapsed_seconds"])>0 for r in BA),
 "B_frozen_gate2_allocation":len(BG)==300*12 and BS["gate2_tests_per_decision"]==12 and BS["gate2_paths_per_test"]==223 and abs(BS["gate2_familywise_error"]-.01)<1e-15 and abs(BS["gate2_per_test_error"]-1/1200)<1e-15 and all(int(r["paths"])==223 and abs(float(r["per_test_error"])-1/1200)<1e-15 and abs(float(r["z_max"])-.1)<1e-15 for r in BG),
 "B_gate2_decisions_reconstruct":gate_reconstruct,
 "B_matched_work_result_retained":all(r["naive_error"]=="False" and r["gated_error"]=="False" and r["abort"]=="False" for r in B)
}
files=[]
for p in sorted(root.rglob("*")):
 if p.is_file() and p != root/"validation.json": files.append({"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
out={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"files":files}
(root/"validation.json").write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps({"status":out["status"],"checks":checks},indent=2))
