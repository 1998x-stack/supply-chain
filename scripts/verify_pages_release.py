#!/usr/bin/env python3
"""Check actual GitHub Pages build output, not merely repository source paths."""
from __future__ import annotations
import argparse,gzip,json,sys
from pathlib import Path

REQUIRED_PRODUCTS={"eyewear","henkel-adhesives"}
REQUIRED_ASSETS=("assets/app.js","assets/node_panel.js","assets/styles.css","assets/node_panel.css")

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
            counts[slug]={"nodes":nodes,"dossiers":len(graph.get("research",[]))}
        except (OSError,ValueError,TypeError,KeyError) as exc:
            errors.append(slug+" gzip snapshot failed: "+str(exc))
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
