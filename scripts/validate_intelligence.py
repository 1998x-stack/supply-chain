#!/usr/bin/env python3
"""Validate a public supply-chain product graph and node intelligence snapshot.
This verifies structural links, scopes and completeness only, not factual truth.
"""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
ALLOWED_RELATIONS={"material_input","component_of","associated_with","processed_into","uses_equipment"}
ALLOWED_REVIEW={"draft","reviewable_draft","reviewable","publishable","disputed"}
def inspect(graph):
 errors=[];warnings=[]
 def err(s): errors.append(s)
 if not isinstance(graph,dict):return {"structure_valid":False,"errors":["root object expected"],"warnings":[]}
 nodes=graph.get("nodes",[]);sources=graph.get("sources",[]);insights=graph.get("node_intelligence",[])
 if not nodes:err("No nodes")
 node_by={};roots=[]
 for n in nodes:
  vid=n.get("id")
  if not isinstance(vid,str) or not vid:err("Missing node id");continue
  if vid in node_by:err("Duplicate node "+vid)
  node_by[vid]=n
  if n.get("parent") is None:roots.append(vid)
  if n.get("relation_type","associated_with") not in ALLOWED_RELATIONS:err(vid+" unsupported relation")
 if len(roots)!=1:err("Exactly one root required")
 for vid,n in node_by.items():
  if n.get("parent") is not None and n["parent"] not in node_by:err(vid+" parent missing")
  seen={vid};parent=n.get("parent")
  while parent is not None and parent in node_by:
   if parent in seen:err(vid+" cycle");break
   seen.add(parent);parent=node_by[parent].get("parent")
 source_by={}
 for s in sources:
  sid=s.get("id")
  if not sid:err("Missing source id");continue
  if sid in source_by:err("Duplicate source "+sid)
  source_by[sid]=s
  if not re.match(r"^https://",str(s.get("url") or "")):err("Non-HTTPS source "+sid)
 ids=set()
 for x in insights:
  vid=x.get("node_id")
  if vid not in node_by:err("Insight references missing node "+str(vid))
  if vid in ids:err("Duplicate insight "+str(vid))
  ids.add(vid)
  if x.get("review_status") not in ALLOWED_REVIEW:err(str(vid)+" invalid review status")
  for sid in x.get("source_ids",[]):
   if sid not in source_by:err(str(vid)+" unknown source "+str(sid))
  for dimension in ("facts","metrics"):
   for row in x.get(dimension,[]):
    if not row.get("label"):err(str(vid)+" missing "+dimension+" label")
    if row.get("value") is None or row.get("value")=="":err(str(vid)+" missing "+dimension+" value")
    if row.get("source_id") not in source_by:err(str(vid)+" missing "+dimension+" source")
    if dimension=="metrics":
     for key in ("unit","period","scope"):
      if not row.get(key):err(str(vid)+" numeric business observation lacks "+key)
     if row.get("unit") in ("pct","%") and "denominator" not in row:err(str(vid)+" percent lacks denominator")
    else:
     if isinstance(row.get("value"),(int,float)) and not row.get("unit"):
      err(str(vid)+" numeric technical value lacks unit")
     if not (row.get("condition") or row.get("period") or row.get("scope")):
      warnings.append(str(vid)+" technical fact lacks test condition, edition or scope")
  for c in x.get("claims",[]):
   if not c.get("text"):err(str(vid)+" empty claim")
   for sid in c.get("source_ids",[]):
    if sid not in source_by:err(str(vid)+" claim source unknown "+str(sid))
   if c.get("status") in ("verified","publishable") and x.get("review_status")!="publishable":
    err(str(vid)+" stronger claim status than dossier review")
 company={c.get("id") for c in graph.get("companies",[])}
 material={m.get("id") for m in graph.get("materials",[])}
 for row in graph.get("company_material",[]):
  if row.get("company") not in company or row.get("material") not in material or row.get("source") not in source_by:
   err("Invalid company_material reference "+str(row))
 for link in graph.get("cross_links",[]):
  if link.get("from") not in node_by or link.get("to") not in node_by:
   err("Cross link references missing node "+str(link.get("id")))
  if link.get("from")==link.get("to"):err("Cross link has self-loop")
  if link.get("relation_type") not in ALLOWED_RELATIONS:err("Cross link has invalid relation type")
  if link.get("evidence_status") not in ("technological","hypothesis","verified","unknown","disputed"):
   err("Cross link has invalid evidence status")
  if link.get("source_id") and link["source_id"] not in source_by:
   err("Cross link references unavailable evidence")
  if link.get("evidence_status")=="verified" and not link.get("source_id"):
   err("Verified cross link lacks direct source")
 for r in graph.get("company_relations",[]):
  if not all(r.get(k) for k in ("source","type","date","scope")):err("Commercial edge lacks source/type/date/scope")
  if r.get("source") not in source_by:err("Commercial edge source unknown")
 if graph.get("shares") and not graph.get("markets"):err("Share without market")
 for s in graph.get("shares",[]):
  if s.get("pct") is None:continue
  if not isinstance(s.get("pct"),(int,float)) or not 0<=s["pct"]<=100:err("Market share out of range")
 for m in graph.get("markets",[]):
  for k in ("geo","year","metric","denominator","material","source"):
   if not m.get(k):err("Market missing "+k)
  if m.get("source") not in source_by:err("Market source unknown")
 # A manufacturer's sales do not magically define material market share.
 for x in insights:
  for m in x.get("metrics",[]):
   if "销售额" in m.get("label","") and "market_share" in str(m.get("metric","")):
    err("Revenue incorrectly declared as market share")
 return {"structure_valid":not errors,"semantic_truth_verified":False,"errors":errors,"warnings":warnings,
         "stats":{"nodes":len(nodes),"sources":len(sources),"insights":len(insights),"materials":len(graph.get("materials",[])),
                  "companies":len(graph.get("companies",[]))}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("graph",nargs="?",default="data/products/henkel-adhesives/graph.json")
 p.add_argument("--output")
 a=p.parse_args()
 data=json.loads(Path(a.graph).read_text(encoding="utf-8"));result=inspect(data)
 text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if a.output:
  path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding="utf-8")
 else:print(text)
 return 0 if result["structure_valid"] else 1
if __name__=="__main__":sys.exit(main())
