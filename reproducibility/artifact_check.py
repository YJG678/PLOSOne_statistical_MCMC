#!/usr/bin/env python3
"""Check the final manuscript and machine-readable validation artifacts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "reproducibility/environment.lock.json").read_text())

pdf = ROOT / "stage6_manuscript/main.pdf"
pdfinfo = subprocess.run(["pdfinfo", str(pdf)], check=True, text=True,
                         stdout=subprocess.PIPE).stdout
pages = int(re.search(r"^Pages:\s+(\d+)$", pdfinfo, re.MULTILINE).group(1))
pdftext = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                         text=True, stdout=subprocess.PIPE).stdout

tex_files = [ROOT / "stage6_manuscript/main.tex",
             ROOT / "stage6_manuscript/combined_appendices.tex"]
textext = "\n".join(path.read_text() for path in tex_files)
unescaped = []
pattern = re.compile(r"(?<!\\)(?:sqrt|qquad)|(?<![\\A-Za-z])quad\b")
for path in tex_files:
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if pattern.search(line):
            unescaped.append(f"{path.relative_to(ROOT)}:{number}:{line}")

final_log = (ROOT / "stage6_manuscript/main.log").read_text(errors="replace")
bib_entries = sum(line.startswith("@")
                  for line in (ROOT / "stage6_manuscript/references.bib").read_text().splitlines())
stage5 = json.loads((ROOT / "stage5_outputs/validation.json").read_text())
stage7 = json.loads((ROOT / "stage7_outputs/certification/validation.json").read_text())
stage8 = json.loads((ROOT / "stage8_outputs/theory_landscapes.json").read_text())

checks = {
    "page_count": pages == LOCK["expected_artifacts"]["manuscript_pages"],
    "bibliography_entries": bib_entries == LOCK["expected_artifacts"]["bibliography_entries"],
    "no_unescaped_tex_tokens": not unescaped,
    "no_visible_transcription_tokens": (
        "qquad" not in pdftext
        and "sqrt" not in pdftext
        and not re.search(r"\bquad\b", pdftext)
    ),
    "no_undefined_references": "There were undefined references" not in final_log,
    "no_undefined_citations": "There were undefined citations" not in final_log,
    "no_overfull_boxes": "Overfull \\hbox" not in final_log,
    "no_removed_application_tokens": not re.search(
        r"\bPDE\b|pi_48|prospective illustration|finite-volume|"
        r"contaminant transport|TPFA",
        textext + "\n" + pdftext,
        re.IGNORECASE,
    ),
    "stage5_validation": stage5["status"] == LOCK["expected_artifacts"]["stage5_status"],
    "stage7_validation": stage7["status"] == LOCK["expected_artifacts"]["stage7_status"],
    "stage8_visualization": (
        stage8["status"] == LOCK["expected_artifacts"]["stage8_status"]
        and (ROOT / "stage6_manuscript/figures/theory_landscapes.pdf").stat().st_size > 0
    ),
}
report = {
    "status": "PASS" if all(checks.values()) else "FAIL",
    "checks": checks,
    "observed": {
        "pages": pages,
        "bibliography_entries": bib_entries,
        "unescaped_tokens": unescaped,
        "pdf_bytes": pdf.stat().st_size,
    },
}
print(json.dumps(report, indent=2))
if report["status"] != "PASS":
    sys.exit(1)
