#!/usr/bin/env python3
"""Convert Testcases/C3DC/studies/**/test_*.py → TC*.xlsx. Prefer: convert_study_tests_to_excel.py C3DC"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    cmd = [sys.executable, str(ROOT / "Tools" / "convert_study_tests_to_excel.py"), "C3DC", *sys.argv[1:]]
    raise SystemExit(subprocess.call(cmd))
