#!/usr/bin/env python3
"""Offline validator and prioritized work-order generator, not automatic web scraping."""
from pathlib import Path
import argparse, subprocess, sys

ROOT=Path(__file__).resolve().parents[4]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--check",action="store_true")
 p.add_argument("--limit",type=int,default=15)
 p.add_argument("--priority",choices=("P0","P1","P2","all"),default="P0")
 a=p.parse_args()
 graph=ROOT/"data"/"products"/"keyboard"/"graph.json"
 v=subprocess.run([sys.executable,str(ROOT/"scripts"/"validate_intelligence.py"),str(graph)],cwd=ROOT,check=False)
 if v.returncode:return v.returncode
 if a.check:return 0
 args=[sys.executable,str(ROOT/"scripts"/"research_coverage.py"),"--product","keyboard",
       "--priority",a.priority,"--limit",str(a.limit),
       "--output","build/research/keyboard_agent_batch.json",
       "--report","build/research/keyboard_agent_coverage.json"]
 return subprocess.call(args,cwd=ROOT)
if __name__=="__main__":raise SystemExit(main())
