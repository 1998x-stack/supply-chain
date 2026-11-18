#!/usr/bin/env python3
"""Thin wrapper for supplier-relationship-audit; run from any cwd."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.call([sys.executable,str(ROOT/'scripts'/'research_cli.py'),'audit-ledger',*sys.argv[1:]],cwd=ROOT))
