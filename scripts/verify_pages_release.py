#!/usr/bin/env python3
"""Check actual GitHub Pages build output, not merely repository source paths."""
from __future__ import annotations
import argparse,gzip,json,sys
from pathlib import Path

REQUIRED_PRODUCTS={"eyewear","henkel-adhesives","keyboard"}
REQUIRED_ASSETS=("assets/app.js","assets/node_panel.js","assets/styles.css","assets/node_panel.css","assets/ux_pro_max.css")

def audit_release(root:Path):
    errors=[];report={}
    catalog_path=root/"data/catalog.json"
    if not catalog_path.exists():
        return {"valid":False,"errors":["Missing dist/data/catalog.json"]}
    try:catalog=json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        return {"valid":False,"errors":["Unreadable catalog: "+str(exc)]}
    slugs=[p.get("slug") for p in catalog.get("products",[])]
    build_id=catalog.get("build_id")
    if not isinstance(build_id,str) or len(build_id)<7:
        errors.append("Missing build_id in published catalog")
    if len(set(slugs))!=len(slugs):
        errors.append("Duplicate published product slugs")
    if not REQUIRED_PRODUCTS.issubset(set(slugs)):
        errors.append("Missing required products: "+repr(sorted(REQUIRED_PRODUCTS-set(slugs))))
    index=(root/"index.html")
    if not index.is_file():errors.append("Missing index.html")
    else:
        text=index.read_text(encoding="utf-8")
        for asset in REQUIRED_ASSETS:
            if not (root/asset).is_file():errors.append("Missing JS/CSS file: "+asset)
            if not build_id or asset+"?v="+build_id not in text:
                errors.append("HTML not version-pinned: "+asset)
    counts={}
    for slug in slugs:
        path=root/"data"/(slug+".json.gz")
        if not path.is_file():errors.append("Missing compressed graph "+slug);continue
        try:
            with gzip.open(path,"rt",encoding="utf-8") as f:graph=json.load(f)
            nodes=len(graph.get("n",[]))
            expected=next(p["nodes"] for p in catalog["products"] if p["slug"]==slug)
            if nodes != expected:errors.append(f"{slug} node count mismatch {nodes}!={expected}")
            context=graph.get("coverage",[])
            if len(context)!=nodes:errors.append(f"{slug} coverage count {len(context)}!={nodes}")
            if len({r.get("node_id") for r in context})!=len(context):
                errors.append(slug+" coverage node IDs are not unique")
            ids={row[0] for row in graph.get("n",[]) if row}
            if any(r.get("node_id") not in ids for r in context):
                errors.append(slug+" coverage contains unknown node IDs")
            summary=next((p.get("coverage",{}) for p in catalog["products"] if p["slug"]==slug),{})
            if summary.get("nodes")!=nodes:errors.append(slug+" missing or inconsistent coverage summary")
            if summary.get("dossiers")!=len(graph.get("research",[])):
                errors.append(slug+" dossier counts inconsistent")
            if summary.get("approved_dossiers",0)>summary.get("dossiers",0):
                errors.append(slug+" approved dossier count exceeds dossier count")
            queue_path=root/"data"/(slug+"_research_queue.json")
            if not queue_path.is_file():errors.append(slug+" missing research queue export")
            else:
                queue=json.loads(queue_path.read_text(encoding="utf-8"))
                if queue.get("product_slug")!=slug or queue.get("semantic_review")!="not_started":
                    errors.append(slug+" malformed research queue")
            counts[slug]={"nodes":nodes,"dossiers":len(graph.get("research",[])),
                          "source_notes":summary.get("source_notes_without_dossier",0)}
        except (OSError,ValueError,TypeError,KeyError) as exc:
            errors.append(slug+" gzip snapshot failed: "+str(exc))
    if counts.get("keyboard",{}).get("nodes",0)<160:
        errors.append("Keyboard graph absent or unexpectedly truncated")
    if counts.get("henkel-adhesives",{}).get("nodes",0)<70:
        errors.append("Henkel graph absent or unexpectedly truncated")
    if counts.get("eyewear",{}).get("nodes",0)<300:
        errors.append("Eyewear graph absent or unexpectedly truncated")
    return {"valid":not errors,"build_id":build_id,"slugs":slugs,"snapshots":counts,"errors":errors}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dist",default="dist")
    args=p.parse_args()
    report=audit_release(Path(args.dist))
    print("PAGES_RELEASE_"+("OK" if report["valid"] else "FAILED"),json.dumps(report,ensure_ascii=False))
    return 0 if report["valid"] else 1
if __name__=="__main__":sys.exit(main())
