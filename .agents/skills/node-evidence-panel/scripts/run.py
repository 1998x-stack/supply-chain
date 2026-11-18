#!/usr/bin/env python3
"""Pass product graph to the offline node intelligence validator. No web/LLM calls."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--product",default="henkel-adhesives")
 a=p.parse_args()
 path=ROOT/"data"/"products"/a.product/"graph.json"
 if not path.is_file():p.error("Unknown product graph "+str(path))
 return subprocess.call([sys.executable,str(ROOT/"scripts"/"validate_intelligence.py"),str(path)])
if __name__=="__main__":sys.exit(main())
