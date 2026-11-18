#!/usr/bin/env python3
"""Explicit, bounded bridge to the user's optional 1998x-stack/deep-search engine.

No network by default. Actual search requires --allow-network and TAVILY_API_KEY.
No tool automatically calls LLMs or semantically certifies facts.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[1]

def make_command(args):
    if args.action=="search":
        if not args.allow_network:
            raise ValueError("Search requires explicit --allow-network")
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY is missing; connection and permission are required")
        plan=json.loads(Path(args.input).read_text(encoding="utf-8"))
        budget=plan.get("budget",{})
        limit=budget.get("max_queries")
        if not isinstance(limit,int) or not 1<=limit<=20:
            raise ValueError("Search budget must stay within 1..20")
        if not args.output:raise ValueError("Search needs --output")
        return ["search","--input",args.input,"--output",args.output]
    if args.action=="validate":
        if not args.input:raise ValueError("Validate needs --input")
        cmd=["validate","--input",args.input]
        if args.output:cmd+=["--output",args.output]
        return cmd
    if args.action=="audit":
        if not args.report or not args.ledger:
            raise ValueError("Audit needs --report and --ledger")
        cmd=["audit","--report",args.report,"--ledger",args.ledger]
        if args.output:cmd+=["--output",args.output]
        return cmd
    raise ValueError("Unsupported action")

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--action",choices=("search","validate","audit"),required=True)
    p.add_argument("--deep-search-root",default="../deep-search")
    p.add_argument("--input");p.add_argument("--report");p.add_argument("--ledger")
    p.add_argument("--output");p.add_argument("--allow-network",action="store_true")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args(argv)
    try:
        cmd=make_command(a)
    except ValueError as e:
        p.error(str(e))
    root=Path(a.deep_search_root).expanduser().resolve()
    full=[sys.executable,"-m","deep_search",*cmd]
    print("DEEP_SEARCH_COMMAND:",json.dumps(full,ensure_ascii=False))
    if a.dry_run:
        print("DRY_RUN_NO_EXTERNAL_ACTION")
        return 0
    if not (root/"deep_search"/"__main__.py").is_file():
        p.error("deep-search repo not found at "+str(root)+"; clone/install it separately")
    env=os.environ.copy()
    env["PYTHONPATH"]=os.pathsep.join([str(root),env.get("PYTHONPATH","")])
    proc=subprocess.run(full,cwd=REPO_ROOT,env=env,check=False)
    return proc.returncode

if __name__=="__main__":
    sys.exit(main())
