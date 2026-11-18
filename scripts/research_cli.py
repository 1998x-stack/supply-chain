#!/usr/bin/env python3
"""Offline research engineering helpers. These NEVER perform web search, LLM review or semantic truth certification."""
from __future__ import annotations
import argparse, gzip, hashlib, json, re, sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
DIMS={"identity":10,"technical":15,"upstream":15,"downstream":10,"companies":15,"market":15,"risk":10,"open_questions":10}
STATES={"supported","partially_supported","disputed","unverified","refuted"}

def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,x):
    f=Path(p);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def utc():return datetime.now(timezone.utc).isoformat(timespec="seconds")
def result(kind,errors,warnings,**extra):
    return {"kind":kind,"structure_valid":not errors,"semantic_truth_verified":False,"errors":errors,"warnings":warnings,**extra}

def audit_ledger(d):
    errors=[];warnings=[]
    if not isinstance(d,dict) or not isinstance(d.get("sources"),list) or not isinstance(d.get("claims"),list):
        return result("ledger",["Must contain sources[] and claims[]"],[])
    src={};seen=set()
    for s in d["sources"]:
        sid=s.get("id")
        if not isinstance(sid,str) or not re.fullmatch(r"S\d{3,}",sid):
            errors.append("Invalid source ID "+str(sid));continue
        if sid in src:errors.append("Duplicate source "+sid)
        src[sid]=s
        if urlsplit(s.get("url","")).scheme not in ("https","http"):errors.append(sid+" URL must use http(s)")
        if "content_sha256" in s and hashlib.sha256(s.get("content","").encode()).hexdigest()!=s["content_sha256"]:
            errors.append(sid+" content hash mismatch")
        if not s.get("publisher") and not s.get("origin_group"):warnings.append(sid+" unknown independent origin")
    for c in d["claims"]:
        cid=c.get("id")
        if not isinstance(cid,str) or not re.fullmatch(r"C\d{3,}",cid):
            errors.append("Invalid claim ID "+str(cid));continue
        if cid in seen:errors.append("Duplicate claim "+cid)
        seen.add(cid)
        if c.get("status") not in STATES:errors.append(cid+" invalid status")
        if not str(c.get("text","")).strip():errors.append(cid+" empty text")
        evidences=c.get("evidence",[])
        if not isinstance(evidences,list):errors.append(cid+" evidence not a list");continue
        groups=set();positive=0
        for e in evidences:
            s=src.get(e.get("source_id"))
            if s is None:errors.append(cid+" source not found "+str(e.get("source_id")));continue
            if e.get("polarity") not in ("supports","contradicts","context"):errors.append(cid+" invalid polarity")
            q=e.get("quote","")
            if not q or q not in s.get("content",""):errors.append(cid+" quote absent from source content "+s["id"])
            if e.get("polarity")=="supports":
                positive+=1;groups.add(s.get("origin_group") or s.get("publisher") or s.get("url"))
        if c.get("status")=="supported":
            if not positive:errors.append(cid+" marked supported without supporting evidence")
            if len(groups)<2:warnings.append(cid+" fewer than 2 independent origin groups")
            if not c.get("analysis"):warnings.append(cid+" reviewer semantic analysis not recorded")
    return result("ledger",errors,warnings,sources=len(src),claims=len(d["claims"]))

def audit_dossier(d):
    errors=[];warnings=[]
    for k in ("node_id","product_slug","name","node_type","as_of","sections","claim_ids"):
        if not d.get(k) and d.get(k)!=[]:errors.append("Missing "+k)
    sections=d.get("sections",{})
    if not isinstance(sections,dict):sections={};errors.append("sections not object")
    coverage=0
    for k,w in DIMS.items():
        if k not in sections:errors.append("Missing sections."+k)
        elif sections[k] not in (None,[] ,{},"","unknown"):coverage+=w
    if d.get("node_type") in ("rocket_system","rocket_component","spacecraft") and not d.get("configuration_id"):
        errors.append("Complex aerospace node requires configuration_id")
    for i,m in enumerate(sections.get("market",[]) if isinstance(sections.get("market"),list) else []):
        for k in ("geography","year","metric","denominator","unit","source_id"):
            if not m.get(k):errors.append("market["+str(i)+"] missing "+k)
        share=m.get("share")
        if share is not None and (isinstance(share,bool) or not isinstance(share,(int,float)) or not 0<=share<=100):
            errors.append("market["+str(i)+"] share out of range")
    for i,c in enumerate(sections.get("companies",[]) if isinstance(sections.get("companies"),list) else []):
        if c.get("relationship") in ("supplied_to","confirmed_supply") and not c.get("commercial_source_id"):
            errors.append("companies["+str(i)+"] supply assertion lacks commercial source")
        if c.get("supplier_public_label") and not c.get("supplier_id") and c.get("relationship") in ("supplied_to","confirmed_supply"):
            errors.append("companies["+str(i)+"] anonymous supplier cannot be identified")
    if not d.get("claim_ids"):warnings.append("No evidence claim IDs")
    review=d.get("semantic_review") or {}
    if review.get("status")!="approved":warnings.append("Semantic review not approved; do not describe dossier as fact verified")
    if coverage<70:warnings.append("Low field completeness; completeness is NOT factual accuracy")
    return result("dossier",errors,warnings,node_id=d.get("node_id"),field_coverage_percent=coverage,
                  semantic_review_status=review.get("status","missing"))

def plan(a):
    node=a.node.strip();product=a.product.strip()
    if not node or not product:raise ValueError("product and node cannot be empty")
    specs=[
      ("definition","具体用途、技术规格与配方",[node+" technical datasheet original manufacturer",node+" 技术规格 牌号 数据表"]),
      ("process","投入材料、不同工业工艺及上游矿产",[node+" feedstocks intermediates process routes upstream"]),
      ("company","制造商、产能、子公司和工厂",[node+" manufacturer facility capacity annual report"]),
      ("market","市场TOP3及范围和分母",[node+" global China market share shipment volume revenue 2024 2025"]),
      ("commercial","实际客户/供应关系证据",[node+" contract announced supply customer filing"]),
      ("adversarial","反例、纠正、修订及退出",[node+" correction discontinuation competing suppliers revised"]),
      ("risk","国产替代与客户认证",[node+" alternative grade qualified manufacturer certification"])
    ]
    qs=[{"id":"Q%02d"%i,"type":kind,"question":product+" / "+node+": "+text+"?","queries":terms}
        for i,(kind,text,terms) in enumerate(specs,1)]
    return {"schema_version":"1.0","question":product+" "+node+" 供应链多信源调查",
       "created_at":utc(),"scope":{"geography":a.geography,"date_start":None,"date_end":a.as_of},
       "subquestions":qs,"budget":{"max_queries":a.max_queries,"max_results_per_query":a.max_results_per_query,"max_fetch":a.max_fetch},
       "notes":["Starter plan aligned with 1998x-stack/deep-search schema. No search was performed.",
                "Human researcher must inspect actual content, source independence and contradictions."]}

def seed_backlog(a):
    path=ROOT/"data"/"products"/a.product/"intelligence_data.json.gz"
    with gzip.open(path,"rt",encoding="utf-8") as f:seed=json.load(f)
    entries=[{"node_id":n["node_id"],"name":n.get("name"),"branch":n.get("branch"),"parent_id":n.get("parent_id"),
              "research_state":"unreviewed","priority":"unrated","dossier":None,"verified_claims":None}
             for n in seed["tree_node"]]
    return {"schema_version":"1.0","product_slug":a.product,"generated_at":utc(),"nodes":entries,"count":len(entries),
            "notice":"This is a to-do list, not evidence that the 382 nodes have been researched."}

def coverage(a):
    root=Path(a.dossiers);rows=[]
    for f in sorted(root.rglob("*.json")) if root.exists() else []:
        try:
            r=audit_dossier(read(f))
            rows.append({"path":str(f),"node_id":r.get("node_id"),"valid":r["structure_valid"],
                         "coverage":r.get("field_coverage_percent"),"semantic_review":r.get("semantic_review_status")})
        except (ValueError,KeyError,TypeError) as e:rows.append({"path":str(f),"valid":False,"error":str(e)})
    return {"generated_at":utc(),"nodes_with_dossiers":len(rows),"entries":rows,
            "notice":"Coverage is a field-population measure, never scientific truth or multi-source verification."}

def validate_skills():
    errors=[];skills=sorted((ROOT/".agents/skills").glob("*/SKILL.md"))
    if len(skills)<8:errors.append("Expected >=8 skills")
    for md in skills:
        slug=md.parent.name;body=md.read_text(encoding="utf-8")
        if not body.startswith("---\n") or "\n---\n" not in body[4:]:
            errors.append(slug+" lacks frontmatter");continue
        header=body.split("\n---\n",1)[0]
        if "name: "+slug not in header or "description: " not in header:
            errors.append(slug+" invalid frontmatter")
        for file in ("references/methodology.md","references/acceptance.md","scripts/run.py","assets/task-template.json"):
            if not (md.parent/file).is_file():errors.append(slug+" missing "+file)
        for host in (".codex",".claude",".pi"):
            link=ROOT/host/"skills"/slug
            if not link.is_dir() or not (link/"SKILL.md").is_file() or link.resolve()!=md.parent.resolve():
                errors.append(host+" broken or divergent skill "+slug)
    return result("skills",errors,[],skill_count=len(skills))

def main():
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest="cmd",required=True)
    s=subs.add_parser("plan");s.add_argument("--node",required=True);s.add_argument("--product",required=True)
    s.add_argument("--geography",default="China and global")
    s.add_argument("--as-of",default=datetime.now(timezone.utc).date().isoformat())
    s.add_argument("--max-queries",type=int,default=12);s.add_argument("--max-results-per-query",type=int,default=5)
    s.add_argument("--max-fetch",type=int,default=15);s.add_argument("--output",required=True)
    for cmd in ("audit-ledger","audit-dossier"):
        s=subs.add_parser(cmd);s.add_argument("--input",required=True);s.add_argument("--output")
    s=subs.add_parser("seed-backlog");s.add_argument("--product",default="eyewear");s.add_argument("--output",required=True)
    s=subs.add_parser("coverage");s.add_argument("--dossiers",default="research/dossiers");s.add_argument("--output")
    s=subs.add_parser("validate-skills");s.add_argument("--output")
    a=p.parse_args()
    if a.cmd=="plan":
        if not 1<=a.max_queries<=20 or not 1<=a.max_results_per_query<=20 or not 1<=a.max_fetch<=100:
            p.error("deep-search query budget outside schema limits")
        x=plan(a)
    elif a.cmd=="audit-ledger":x=audit_ledger(read(a.input))
    elif a.cmd=="audit-dossier":x=audit_dossier(read(a.input))
    elif a.cmd=="seed-backlog":x=seed_backlog(a)
    elif a.cmd=="coverage":x=coverage(a)
    else:x=validate_skills()
    if getattr(a,"output",None):write(a.output,x);print("Wrote "+str(a.output))
    else:print(json.dumps(x,ensure_ascii=False,indent=2))
    return 1 if x.get("structure_valid") is False else 0

if __name__=="__main__":sys.exit(main())
