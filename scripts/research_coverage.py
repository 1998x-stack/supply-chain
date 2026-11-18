#!/usr/bin/env python3
"""Evidence-aware research coverage and prioritized Deep Search task queues.

Important: tree descriptions are topology/context, NOT audited research. This
module never searches the web or labels generated text as verified evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGES=("reviewed","dossier_pending","source_note","annotated","structural_only")
NAVIGATION_KINDS={"category","portfolio","group","directory","root","分类","目录","分类目录"}
MATERIAL_KINDS={"material","chemical","chemical_family","polymer_family","monomer_family",
                "lens_material","frame_material","primary_metal","specialty_chemical","polymer",
                "基材","聚合物","精细化学品","中间体","冶炼材料","矿物加工","功能层"}
PROCESS_KINDS={"process","equipment","functional_layer","工艺","设备与耗材","加工工艺","制造设备"}
SKU_KINDS={"sku","grade","substance_grade"}
EYEWEAR_CRITICAL={
"N0004","N0005","N0019","N0020","N0021","N0025","N0032","N0033",
"N0034","N0042","N0074","N0088","N0096","N0124","N0125",
"N0162","N0163","N0164","N0170","N0194","N0195",
"N0221","N0222","N0224","N0266","N0277","N0316","N0321",
}
STATE_ORD={"structural_only":0,"annotated":1,"source_note":2,
           "dossier_pending":3,"reviewed":4}

def classify(node,has_parent,has_children):
    kind=(node.get("kind") or "").strip().lower()
    if not has_parent or kind in NAVIGATION_KINDS:
        return "navigation"
    if kind in SKU_KINDS:return "sku"
    if kind in MATERIAL_KINDS:return "material"
    if kind in PROCESS_KINDS:return "process"
    if kind in ("brand","family","product_family"):return "brand_family"
    if kind in ("industry","application","application_sector"):return "application"
    # An actual assembly with no material facts is still a distinct research target.
    return "component"

def priority(slug,node,facet):
    nid=node["node_id"]
    if facet=="navigation":return "NAV"
    if slug=="eyewear" and nid in EYEWEAR_CRITICAL:return "P0"
    if facet=="sku":return "P0"
    if facet in ("material","process"):return "P1"
    if slug=="eyewear" and node.get("kind") in (
       "加工工艺","聚合物","中间体","基材","精细化学品","功能层"):return "P1"
    return "P2"

def next_questions(slug,node,facet,sources,existing_gaps):
    name=node["name"]
    label={"navigation":"分类路径","sku":"具体牌号","material":"材料/化学中间体",
           "process":"设备/工业工艺","brand_family":"品牌/产品族",
           "application":"下游应用","component":"组件/资源"}.get(facet,"节点")
    tasks=[]
    if facet=="navigation":
        return []
    if sources==0:
        tasks.append(f"查找「{name}」的定义与产品/工艺边界，获得制造商TDS、行业标准或官方监管文献，不以树状标签充当事实证据")
    if facet=="sku":
        tasks.extend([
          f"调查「{name}」最新适用地区TDS/SDS、牌号、型号版本、性能、测试条件与制造商",
          f"核验「{name}」公开原料组成/聚合物技术族，无法公开的商业配方保持UNKNOWN",
        ])
    elif facet=="material":
        tasks.extend([
          f"调查「{name}」上游前驱体、替代工艺、质量等级/牌号/标准和生产装置",
          f"调查「{name}」主要生产企业、工厂/产能/实际出货量，区分通用级和产品专用级",
        ])
    elif facet=="process":
        tasks.extend([
          f"核查「{name}」工艺流程、设备制造商、关键耗材与适用测试标准",
          f"核查设备产能/工况与实际企业采购关系，不能用设备宣传资料推导采购额",
        ])
    else:
        tasks.append(f"核查「{name}」的组成、原料/工艺关系和下游应用边界，优先制造商原始材料")
    tasks.extend([
       f"调查「{name}」同口径中国/全球TOP3：年份、产品范围、地区、单位、指标与分母；不可查则明确UNKNOWN",
       f"查找「{name}」相关真实供应合同、客户认证/公告；没有证据时禁止将技术关联视为实际供货",
       f"对「{name}」进行至少一次反证搜索：不同牌号、过期文档、来源同源、竞争者统计或相反事实",
    ])
    if existing_gaps:
        tasks=[*existing_gaps[:3],*tasks]
    # Limit repetitive pages, but keep source, market, supplier and a challenge.
    return list(dict.fromkeys(tasks))[:8]

def build_coverage(slug,seed,dossiers,identity=None):
    """All published nodes get a status; only original dossiers can be reviewed."""
    nodes=seed["tree_node"]
    ids={n["node_id"] for n in nodes}
    if len(ids)!=len(nodes):raise ValueError("Duplicate node ids")
    docmap={d["node_id"]:d for d in dossiers}
    if len(docmap)!=len(dossiers):raise ValueError("Duplicate dossier ids")
    if set(docmap)-ids:raise ValueError("Dossier refers to unknown tree nodes: "+repr(sorted(set(docmap)-ids)))
    insightmap={d["node_id"]:d for d in seed.get("node_intelligence",[])}
    if set(insightmap)-ids:raise ValueError("Unrecognized intelligence node")
    byid={n["node_id"]:n for n in nodes}
    children=defaultdict(list)
    for n in nodes:
        if n.get("parent_id"):
            if n["parent_id"] not in ids:raise ValueError("Missing parent "+n["node_id"])
            children[n["parent_id"]].append(n["node_id"])
    curated={r["view_node_id"]:r.get("canonical_material_entity_id")
             for r in (identity or {}).get("view_nodes",[])}
    material_by_node=defaultdict(list)
    for m in seed.get("material",[]):
        if m.get("representative_node_id") in byid:
            material_by_node[m["representative_node_id"]].append(m["material_id"])
    # Only explicitly curated exact identities may carry source-linked material data.
    # Legacy representative_node_id is contextual and must NOT transfer identity.
    available_source_ids={s["source_id"] for s in seed.get("source",[])}
    material_sources=defaultdict(set)
    def related_source(material_id,source_id):
        if material_id and source_id in available_source_ids:
            material_sources[material_id].add(source_id)
    for row in seed.get("company_material",[]):
        related_source(row.get("material_id"),row.get("source_id"))
    market_to_material={m["market_id"]:m["material_id"] for m in seed.get("market",[])}
    for market in seed.get("market",[]):
        related_source(market.get("material_id"),market.get("source_id"))
    for share in seed.get("market_share",[]):
        related_source(market_to_material.get(share.get("market_id")),share.get("source_id"))
    for row in seed.get("capacity_observation",[]):
        related_source(row.get("material_id"),row.get("source_id"))
    for row in seed.get("company_relation",[]):
        related_source(row.get("material_id"),row.get("source_id"))
    counts=Counter()
    priority_counts=Counter()
    records=[]
    for n in nodes:
        nid=n["node_id"];d=docmap.get(nid);hint=insightmap.get(nid)
        source_ids=set()
        if d:source_ids.update(s.get("id") for s in d.get("sources",[]) if s.get("id"))
        if hint:source_ids.update(hint.get("source_ids",[]))
        material_id=curated.get(nid)
        related_material_sources=sorted(material_sources.get(material_id[4:],set())) if material_id else []
        source_ids.update(related_material_sources)
        approved=bool(d and d.get("review_state")=="publishable"
                      and d.get("semantic_review_status")=="approved")
        stage=("reviewed" if approved else "dossier_pending" if d else
               "source_note" if source_ids else
               "annotated" if hint else "structural_only")
        facet=classify(n,bool(n.get("parent_id")),bool(children[nid]))
        p=priority(slug,n,facet)
        claims=(len(d.get("claims",[])) if d else 0)+(len(hint.get("claims",[])) if hint else 0)
        gaps=(d.get("sections",{}).get("open_questions",[]) if d else [])
        gaps=[x for x in gaps if isinstance(x,str)]
        if hint:
            gaps.extend(x for x in hint.get("gaps",[]) if isinstance(x,str))
        path=[];cur=nid;seen=set()
        while cur and cur not in seen:
            seen.add(cur);path.insert(0,byid[cur]["name"]);cur=byid[cur].get("parent_id")
        if cur:raise ValueError("Tree cycle "+nid)
        questions=next_questions(slug,n,facet,len(source_ids),gaps)
        record={
            "node_id":nid,"name":n["name"],"kind":n.get("kind"),"facet":facet,
            "branch":n.get("branch"),"priority":p,"stage":stage,
            "has_dossier":bool(d),"has_source_note":bool(source_ids),
            "approved":approved,"sources":len(source_ids),"claims":claims,
            "children":len(children[nid]),"path":path,
            "canonical_material":curated.get(nid),"contextual_material_ids":material_by_node.get(nid,[]),
            "material_source_ids":related_material_sources,
            "questions":questions,
            "next_action":("browse_only" if facet=="navigation" else
               "refresh_or_update" if approved else "review_claims_and_sources" if d else
               "expand_to_dossier" if source_ids else
               "collect_primary_evidence"),
        }
        records.append(record);counts[stage]+=1;priority_counts[p]+=1
    actionable=sum(r["facet"]!="navigation" for r in records)
    return {
       "schema_version":"coverage_v1","product_slug":slug,
       "metrics":{
          "nodes":len(records),"navigation_nodes":len(records)-actionable,
          "research_targets":actionable,
          "dossiers":sum(r["has_dossier"] for r in records),
          "source_notes_without_dossier":sum(r["has_source_note"] and not r["has_dossier"] for r in records),
          "approved_dossiers":sum(r["approved"] for r in records),
          "needs_dossier":sum(r["facet"]!="navigation" and not r["has_dossier"] for r in records),
          "needs_semantic_review":sum(r["has_dossier"] and not r["approved"] for r in records),
          "by_stage":dict(counts),
          "by_priority":dict(priority_counts),
       },
       "nodes":records,
       "disclaimer":"Structural descriptions and generated research questions are not audited industry claims. "
                    "Only a dossier with human semantic approval can count as approved."
    }

def prioritized_queue(coverage,priority_filter="all",limit=0):
    items=[n for n in coverage["nodes"] if n["priority"]!="NAV"
           and n["stage"]!="reviewed"
           and (priority_filter=="all" or n["priority"]==priority_filter)]
    items.sort(key=lambda x:(
      {"P0":0,"P1":1,"P2":2}.get(x["priority"],3),
      STATE_ORD[x["stage"]],-x["children"],x["node_id"]))
    return items[:limit] if limit else items

def task_bundle(slug,items):
    return {"schema_version":"deep_search_batch_v1","product_slug":slug,
        "network_execution":"not_started","semantic_review":"not_started",
        "tasks":[{
           "node_id":r["node_id"],"node_name":r["name"],"priority":r["priority"],
           "status":r["stage"],"path":r["path"],
           "questions":r["questions"],
           "search_strategy":{
              "primary":"TDS/SDS, annual reports, primary technical manuals, regulator filings",
              "independent":"Government statistics, peer-reviewed studies, disclosed customer announcements",
              "challenge":"One adversarial search for category, timeframe, buyer vs seller and grade mismatch",
              "source_independence_required":True,
              "required_claim_fields":["claim_text","source_id","quote","origin_group",
                                       "publisher","published_at","scope","semantic_review_status"],
              "restrictions":["No invented TOP3 percentages","No inferred procurement from capability",
                              "No source quote without opening original"]
            }
        } for r in items],
        "disclaimer":"This file is a research work order, not completed evidence. Deep Search execution needs a configured external research agent."}

def main():
    from build_site import discover_products,read_public_research
    p=argparse.ArgumentParser()
    p.add_argument("--product",default="eyewear")
    p.add_argument("--priority",choices=("all","P0","P1","P2"),default="all")
    p.add_argument("--limit",type=int,default=15)
    p.add_argument("--output",default="build/research/node_research_batch.json")
    p.add_argument("--report",default="build/research/research_coverage.json")
    a=p.parse_args()
    products=discover_products()
    item=next(((m,x) for m,x in products if m["slug"]==a.product),None)
    if not item:raise ValueError("Unknown product "+a.product)
    meta,seed=item
    dossier=read_public_research(a.product,{n["node_id"] for n in seed["tree_node"]})
    report=build_coverage(a.product,seed,dossier)
    bundle=task_bundle(a.product,prioritized_queue(report,a.priority,a.limit))
    for path,doc in ((Path(a.report),report),(Path(a.output),bundle)):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RESEARCH_COVERAGE",json.dumps(report["metrics"],ensure_ascii=False))
    print("RESEARCH_BATCH",len(bundle["tasks"]),a.priority,a.output)

if __name__=="__main__":main()
