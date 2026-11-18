#!/usr/bin/env python3
"""Evidence-first structural audit for ALL eyewear research; no semantic truth claims."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site, research_cli

def inspect(root=ROOT):
    if root != ROOT:
        raise ValueError("Run against the checked-out repository root only")
    x=build_site.unpack_seed()
    nodes={n["node_id"]:n for n in x["tree_node"]}
    errors=[];warnings=[];reviewed=[];seen={}
    ledger_paths=sorted((root/"research/ledgers/eyewear").glob("*.json"))
    dossier_paths=sorted((root/"research/dossiers/eyewear").glob("*.json"))
    ledgers={}
    for p in ledger_paths:
        try:
            ledger=json.loads(p.read_text(encoding="utf-8"))
            nid=ledger["node_id"]
            if nid in ledgers:errors.append("Duplicate ledger node "+nid)
            ledgers[nid]=ledger
            r=research_cli.audit_ledger(ledger)
            errors += [p.name+": "+e for e in r["errors"]]
            warnings += [p.name+": "+w for w in r["warnings"]]
        except (ValueError,KeyError,TypeError) as exc:
            errors.append(p.name+": "+str(exc))
    for p in dossier_paths:
        try:
            d=json.loads(p.read_text(encoding="utf-8"));nid=d["node_id"]
            if nid in seen:errors.append("Duplicate dossier node "+nid)
            seen[nid]=p.name
            if nid not in nodes:errors.append("Dossier has unknown tree node "+nid)
            else:
                if d.get("name") != nodes[nid]["name"]:
                    warnings.append(nid+" dossier name differs from tree display label")
            r=research_cli.audit_dossier(d)
            errors += [p.name+": "+e for e in r["errors"]]
            warnings += [p.name+": "+w for w in r["warnings"]]
            ledger=ledgers.get(nid)
            if not ledger:errors.append("Missing ledger for "+nid)
            else:
                if ledger.get("product_slug")!=d.get("product_slug"):
                    errors.append(nid+" product slug mismatch")
                src_ids={s.get("id") for s in ledger.get("sources",[])}
                claims={c.get("id"):c for c in ledger.get("claims",[])}
                for cid in d.get("claim_ids",[]):
                    if cid not in claims:errors.append(nid+" missing claim "+str(cid))
                    elif any(e.get("source_id") not in src_ids for e in claims[cid].get("evidence",[])):
                        errors.append(nid+" source reference not in ledger for "+str(cid))
                for entry in d.get("sections",{}).get("market",[]):
                    if entry.get("source_id") not in src_ids:
                        errors.append(nid+" market source missing from ledger")
                    if entry.get("share") is not None and "all_grade" in str(entry.get("not_equivalent_to","")):
                        warnings.append(nid+" market category scope needs reviewer check")
            reviewed.append({"node_id":nid,"name":d.get("name"),
                "state":d.get("review_state"),"semantic_review":(d.get("semantic_review") or {}).get("status","pending"),
                "claim_count":len(d.get("claim_ids",[])),
                "field_completion_only":r.get("field_coverage_percent"),"path":str(p.relative_to(root))})
        except (ValueError,KeyError,TypeError) as exc:
            errors.append(p.name+": "+str(exc))
    unlinked=sorted(set(ledgers)-set(seen))
    if unlinked:errors += ["Ledger without dossier: "+v for v in unlinked]
    counts=Counter(nodes[x]["branch"] for x in seen if x in nodes)
    return {"schema_version":"1.0","audit_type":"structural_only",
        "semantic_truth_verified":False,"structure_valid":not errors,
        "total_tree_nodes":len(nodes),"nodes_with_dossiers":len(seen),
        "nodes_without_dossiers":len(nodes)-len(seen),"claims":sum(r["claim_count"] for r in reviewed),
        "semantic_approved_dossiers":sum(r["semantic_review"]=="approved" for r in reviewed),
        "reviewed":sorted(reviewed,key=lambda a:a["node_id"]),
        "dossier_branch_counts":dict(sorted(counts.items())),
        "errors":errors,"warnings":warnings,
        "notice":"Excerpt matching and source IDs are structural checks. They do not prove semantic entailment, supplier contracts or market shares."}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output");a=p.parse_args()
    r=inspect()
    text=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
    if a.output:
        out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding="utf-8")
        print("AUDIT",json.dumps({k:r[k] for k in ("structure_valid","total_tree_nodes","nodes_with_dossiers","nodes_without_dossiers","claims")},ensure_ascii=False))
    else:print(text)
    return 0 if r["structure_valid"] else 1

if __name__=="__main__":sys.exit(main())
