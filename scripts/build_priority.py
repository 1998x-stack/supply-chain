#!/usr/bin/env python3
"""Prioritize every eyewear tree node without pretending it has been researched."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P0={
 "N0004","N0005","N0019","N0020","N0021","N0025","N0032","N0033",
 "N0034","N0042","N0074","N0088","N0096","N0124","N0125",
 "N0162","N0163","N0164","N0170","N0194","N0195",
 "N0221","N0222","N0224","N0266","N0277","N0316","N0321",
}
P1_KINDS={"基材","聚合物","精细化学品","中间体","加工工艺","冶炼材料","矿物加工","设备与耗材","功能层"}
def prioritize(seed, dossiers=None):
    dossiers=dossiers or {}
    nodes=seed["tree_node"]; records=[]
    for n in nodes:
        nid=n["node_id"];kind=n.get("kind","")
        tier="P0" if nid in P0 else "P1" if kind in P1_KINDS else "P2"
        doc=dossiers.get(nid,{})
        approved=(doc.get("semantic_review") or {}).get("status")=="approved"
        open_items=doc.get("sections",{}).get("open_questions",[])
        records.append({
            "node_id":nid,"label":n["name"],"branch":n.get("branch"),
            "node_kind":kind,"tier":tier,
            "research_state":doc.get("review_state","unreviewed"),
            "semantic_approved":approved,
            "claim_count":len(doc.get("claim_ids",[])),
            "open_questions_count":len(open_items),
            "next_action":"independent_source_review" if doc and not approved else
                "refresh_sources" if approved else "primary_source_discovery",
            "reason":"Manually designated supply-chain anchor" if nid in P0 else
                 "Intermediate/material/equipment manufacturing node" if tier=="P1" else
                 "Contextual resource/support/assembly node",
        })
    return {"schema_version":"1.0","product":"eyewear",
        "research_depth":"research_planning_only",
        "total_nodes":len(records),
        "tier_counts":{t:sum(x["tier"]==t for x in records) for t in ("P0","P1","P2")},
        "nodes_with_dossiers":sum(x["research_state"]!="unreviewed" for x in records),
        "semantic_approved_count":sum(x["semantic_approved"] for x in records),
        "records":sorted(records,key=lambda r:("P0","P1","P2").index(r["tier"])*10000+int(r["node_id"][1:])),
        "notice":"Heuristic research triage; priorities are analyst-designed, not economic market shares."
    }
def load_dossiers():
    docs={}
    for p in (ROOT/"research"/"dossiers"/"eyewear").glob("*.json"):
        d=json.loads(p.read_text(encoding="utf-8"))
        if d["node_id"] in docs:raise ValueError("duplicate dossier "+d["node_id"])
        docs[d["node_id"]]=d
    return docs
def main():
    from build_site import unpack_seed
    p=argparse.ArgumentParser();p.add_argument("--output",default="build/research/eyewear_priority.json")
    args=p.parse_args()
    x=prioritize(unpack_seed(),load_dossiers())
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRIORITY_READY",x["tier_counts"],"dossiers=",x["nodes_with_dossiers"])
if __name__=="__main__":main()
