#!/usr/bin/env python3
"""Verify the exact software lock before a confirmatory reproduction."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "reproducibility/environment.lock.json").read_text())


def first_line(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, text=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    return completed.stdout.splitlines()[0]


requirements: dict[str, str] = {}
for line in (ROOT / LOCK["python"]["requirements_file"]).read_text().splitlines():
    if line and not line.startswith("#"):
        name, version = line.split("==", 1)
        requirements[name.lower()] = version

observed_packages = {
    name: importlib.metadata.version(name) for name in requirements
}
package_checks = {
    name: observed_packages[name] == expected
    for name, expected in requirements.items()
}

observed_commands = {
    "latexmk": first_line(["latexmk", "-v"]),
    "pdftex": first_line(["pdflatex", "--version"]),
    "bibtex": first_line(["bibtex", "--version"]),
    "pdftoppm": first_line(["pdftoppm", "-v"]),
    "zip": "\n".join(subprocess.run(["zip", "-v"], check=True, text=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT).stdout.splitlines()[:3]),
}
command_checks = {
    "latexmk": bool(re.search(r"Version\s+" + re.escape(LOCK["executables"]["latexmk"]),
                               observed_commands["latexmk"])),
    "pdftex": LOCK["executables"]["pdftex"] in observed_commands["pdftex"],
    "bibtex": LOCK["executables"]["bibtex"] in observed_commands["bibtex"],
    "pdftoppm": LOCK["executables"]["pdftoppm"] in observed_commands["pdftoppm"],
    "zip": ("Zip " + LOCK["executables"]["zip"]) in observed_commands["zip"],
}

checks = {
    "python": platform.python_version() == LOCK["python"]["version"],
    "platform": platform.platform() == LOCK["operating_system"]["platform"],
    "architecture": platform.machine() == LOCK["operating_system"]["architecture"],
    "packages": all(package_checks.values()),
    "executables": all(command_checks.values()),
}
report = {
    "status": "PASS" if all(checks.values()) else "FAIL",
    "checks": checks,
    "package_checks": package_checks,
    "command_checks": command_checks,
    "observed": {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "packages": observed_packages,
        "commands": observed_commands,
    },
}
print(json.dumps(report, indent=2))
if report["status"] != "PASS":
    sys.exit(1)
