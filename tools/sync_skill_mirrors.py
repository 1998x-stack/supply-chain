#!/usr/bin/env python3
"""Safely validate or materialize cross-harness Agent Skills mirrors.

Canonical source: .agents/skills. Default is --check with NO writes.
--copy is useful on Windows without symlink support. --symlink restores links.
"""
from __future__ import annotations
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOSTS=(".codex",".claude",".pi")

def snapshot(base:Path):
    return {str(p.relative_to(base)):p.read_bytes() for p in base.rglob("*") if p.is_file()}

def sync(root:Path,mode:str):
    source=root/".agents"/"skills"
    if not source.is_dir():
        return ["Missing canonical .agents/skills"],0
    errors=[];count=0
    for skill in sorted(source.iterdir()):
        if not skill.is_dir() or not (skill/"SKILL.md").is_file():continue
        originals=snapshot(skill)
        for host in HOSTS:
            mirror=root/host/"skills"/skill.name
            if mode!="check":
                mirror.parent.mkdir(parents=True,exist_ok=True)
            if mode=="check":
                if not mirror.is_dir() or not (mirror/"SKILL.md").is_file():
                    errors.append(str(mirror)+" missing or broken");continue
                if mirror.resolve()!=skill.resolve() and snapshot(mirror)!=originals:
                    errors.append(str(mirror)+" drifted from canonical")
            else:
                if mirror.is_symlink():
                    mirror.unlink()
                elif mirror.exists():
                    if not mirror.is_dir():
                        errors.append(str(mirror)+" exists and is not a skill directory");continue
                    if snapshot(mirror)!=originals:
                        errors.append(str(mirror)+" differs; refusing to overwrite local edits");continue
                    shutil.rmtree(mirror)
                if mode=="copy":
                    shutil.copytree(skill,mirror)
                else:
                    target=os.path.relpath(skill,mirror.parent)
                    mirror.symlink_to(target,target_is_directory=True)
            count+=1
    return errors,count

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    actions=p.add_mutually_exclusive_group()
    actions.add_argument("--check",action="store_true")
    actions.add_argument("--copy",action="store_true")
    actions.add_argument("--symlink",action="store_true")
    p.add_argument("--root",default=str(ROOT))
    a=p.parse_args(argv)
    mode="copy" if a.copy else "symlink" if a.symlink else "check"
    errors,count=sync(Path(a.root).resolve(),mode)
    for e in errors:print("ERROR:",e,file=sys.stderr)
    print(f"SKILL_MIRRORS_{'OK' if not errors else 'FAILED'} mode={mode} checked={count} errors={len(errors)}")
    return 1 if errors else 0

if __name__=="__main__":
    sys.exit(main())
