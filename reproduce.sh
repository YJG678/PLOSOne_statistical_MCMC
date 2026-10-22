#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"
mkdir -p reproducibility

RUN_LOG="$REPO_ROOT/reproducibility/reproduction.log"
exec > >(tee "$RUN_LOG") 2>&1

export PYTHONHASHSEED=0
export SOURCE_DATE_EPOCH=1786320000
export TZ=UTC
export LC_ALL=C.UTF-8
MBS_MPLCONFIG="$(mktemp -d "${TMPDIR:-/tmp}/mbs-mpl.XXXXXX")"
export MPLCONFIGDIR="$MBS_MPLCONFIG"
trap 'rm -rf "$MBS_MPLCONFIG"' EXIT

echo "Measurement Before Selection: one-command reproduction"
echo "Start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 reproducibility/environment_check.py \
  > reproducibility/environment_check_output.json
cat reproducibility/environment_check_output.json

python3 stage2_outputs/verify_two_state.py
python3 stage2_outputs/verify_proxy_lrv.py

python3 stage5_two_state.py
python3 stage5_mixture.py
python3 stage5_make_figures.py
cp stage5_outputs/experiment_A/two_state_mechanism.pdf \
  stage6_manuscript/figures/two_state_mechanism.pdf
cp stage5_outputs/experiment_B/mixture_results.pdf \
  stage6_manuscript/figures/mixture_results.pdf
python3 stage5_validate.py

python3 stage7_certification_benchmark.py
python3 stage7_make_figure.py
cp stage7_outputs/certification/certification_power.pdf \
  stage6_manuscript/figures/certification_power.pdf
python3 stage7_validate.py

python3 theory_landscapes.py
cp stage8_outputs/theory_landscapes.pdf \
  stage6_manuscript/figures/theory_landscapes.pdf

(
  cd stage6_manuscript
  latexmk -C main.tex
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex \
    > clean_compilation.log 2>&1
  cp main.log final_compilation.log
)

python3 reproducibility/artifact_check.py \
  > reproducibility/artifact_check_output.json
cat reproducibility/artifact_check_output.json

while IFS= read -r path; do
  sha256sum "$path"
done < reproducibility/deterministic_outputs.txt \
  > reproducibility/deterministic_outputs.sha256
sha256sum stage6_manuscript/main.pdf \
  > reproducibility/manuscript.sha256

python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd()
stage5 = json.loads((root / "stage5_outputs/validation.json").read_text())
stage7 = json.loads((root / "stage7_outputs/certification/validation.json").read_text())
stage8 = json.loads((root / "stage8_outputs/theory_landscapes.json").read_text())
environment = json.loads((root / "reproducibility/environment_check_output.json").read_text())
artifact = json.loads((root / "reproducibility/artifact_check_output.json").read_text())
status = "PASS" if all(x["status"] == "PASS" for x in
                       (stage5, stage7, stage8, environment, artifact)) else "FAIL"
report = {
    "status": status,
    "completed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "environment_status": environment["status"],
    "stage5_status": stage5["status"],
    "stage7_status": stage7["status"],
    "stage8_status": stage8["status"],
    "artifact_status": artifact["status"],
    "pages": artifact["observed"]["pages"],
    "bibliography_entries": artifact["observed"]["bibliography_entries"],
    "matched_target_evaluations_per_path": 3000,
}
(root / "reproducibility/reproduction_report.json").write_text(
    json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if status != "PASS":
    raise SystemExit(1)
PY

echo "End: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "REPRODUCTION PASS"
