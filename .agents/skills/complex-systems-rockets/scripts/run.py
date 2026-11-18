#!/usr/bin/env python3
"""Thin wrapper for complex-systems-rockets; run from any cwd."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable,str(ROOT/'scripts'/'research_cli.py'),'audit-dossier',*sys.argv[1:]],cwd=ROOT))
