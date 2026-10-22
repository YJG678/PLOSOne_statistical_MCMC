#!/usr/bin/env python3
import csv,json,math
from pathlib import Path
root=Path("stage7_outputs/certification")
rows=list(csv.DictReader(open(root/"certification_power.csv")))
s=json.loads((root/"summary.json").read_text())
checks={
 "six_effect_sizes":len(rows)==6,
 "independent_meta_repetitions":all(int(r["meta_repetitions"])==2000 for r in rows),
 "certification_units_551":all(int(r["certification_units"])==551 for r in rows),
 "primary_power_at_least_80_percent":float(rows[0]["certification_power"])>=.8,
 "null_false_rate_within_declared_error":s["null_false_certification_rate"]<=s["delta"],
 "power_decreases_with_exact_improvement":all(float(rows[i]["certification_power"])>=float(rows[i+1]["certification_power"]) for i in range(5)),
 "frozen_radius_matches":abs(float(rows[0]["hoeffding_radius"])-math.sqrt(2*math.log(1/.015)/551))<1e-12
}
out={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks}
(root/"validation.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
