#!/usr/bin/env python3
"""Versioned, conservative identity resolution for the 382 eyewear *view nodes*.

Every view node gets an identity record. Only carefully curated exact material
matches receive a shared MAT:<id> key; duplicate labels generate review
candidates, never automatic chemical or supplier merges.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sys
from pathlib import Path

# Explicitly reviewed name/scope matches. Product assemblies, process steps,
# multi-substance categories and generic material families are not merged.
EXACT_MATERIAL_BINDINGS = {
    "N0005":"CR39", "N0032":"PC_OPT", "N0033":"BPA",
    "N0034":"PHENOL","N0042":"ACETONE",
    "N0163":"ACETATE_SHEET","N0164":"CA",
    "N0170":"ACETIC_ANHYDRIDE","N0195":"TR90",
    "N0222":"TITANIUM_WIRE","N0224":"TITANIUM_SPONGE",
    "N0097":"TIO2_FILM","N0074":"HARDCOAT",
    "N0266":"HINGE","N0277":"NOSEPAD",
}
# Review policies: may be a useful *associated* entity, but is NOT an exact
# identity of the representative tree node.
NON_EQUIVALENT = {
    "PHOTO_LENS":"Function versus product",
    "MR":"Broad high-index lens family versus chemical/material grade",
    "XDI":"Specific XDI is not the complete high-index lens material",
    "DMT":"Unresolved chemical identification",
    "ALLYL_ALCOHOL":"Substance is not the assembled CR-39 lens",
    "ACETATE_RENEW":"Trademark/recycled grade is not generic CA powder",
    "TRITAN_RENEW":"Grade differs from mixed polymer feedstock",
    "TENITE_RENEW":"Grade differs from mixed polymer feedstock",
    "TIO2_PIGMENT":"Pigment is not optical coating grade",
    "LENS_MATERIALS":"Multiple lens families, not one material",
    "OPT_LENS":"Finished lens is not optical base-material group",
    "PC_GEN":"All-grade commodity PC differs from optical grade",
    "OPT_EQUIP":"Manufacturing system is not one piece of equipment",
    "EYEWEAR_FRAME":"Finished frame differs from frame structural tree branch",
}

def normalize_label(s):
    x = re.sub(r"\s+","",s).lower()
    return re.sub(r"[，,·•（）()\-/]", "",x)

def resolve(seed):
    nodes=seed["tree_node"]; materials=seed["material"]
    nmap={n["node_id"]:n for n in nodes}
    mmap={m["material_id"]:m for m in materials}
    if len(nmap)!=len(nodes):raise ValueError("Duplicate view IDs")
    reverse=collections.defaultdict(list)
    for m in materials:
        if m.get("representative_node_id"):
            reverse[m["representative_node_id"]].append(m["material_id"])
    for node,mid in EXACT_MATERIAL_BINDINGS.items():
        if node not in nmap or mid not in mmap:
            raise ValueError("Curated identity binding not in source seed: "+node+"/"+mid)
    rows=[];by_label=collections.defaultdict(list)
    for n in sorted(nodes,key=lambda x:x["node_id"]):
        vid=n["node_id"]; label=n["name"]
        key=normalize_label(label)
        # This is a view-node registration, not independent chemical research.
        curated=EXACT_MATERIAL_BINDINGS.get(vid)
        rows.append({
          "view_node_id":vid,"label":label,"label_key":key,
          "view_branch":n.get("branch"),"view_kind":n.get("kind"),
          "view_entity_id":"NODE:EYE:"+vid,
          "canonical_material_entity_id":("MAT:"+curated if curated else None),
          "identity_state":"curated_exact" if curated else "provisional_unique",
          "reference_material_ids":reverse.get(vid,[]),
          "evidence_state":"curated_identity_mapping_not_procurement" if curated else "unreviewed",
          "review_required":not bool(curated)
        })
        by_label[key].append(vid)
    candidates=[]
    for label,ids in sorted(by_label.items()):
        if len(ids)<2:continue
        # No implicit merge: one label can denote alternate routes or broad mixed feedstocks.
        candidates.append({
           "candidate_group_id":"DUP:"+hashlib.sha256(label.encode()).hexdigest()[:16],
           "label_key":label,"view_node_ids":sorted(ids),
           "candidate_status":"needs_semantic_review",
           "reason":"Same normalized display label in several technical branches; identity not established",
           "auto_merge":False
        })
    discrepancies=[]
    for m in materials:
        mid=m["material_id"]; legacy=m.get("representative_node_id")
        mapped=[node for node,realmid in EXACT_MATERIAL_BINDINGS.items() if realmid==mid]
        state="curated_exact" if mapped else "associated_only"
        discrepancies.append({
         "material_id":mid,
         "legacy_representative_node_id":legacy,
         "curated_exact_view_nodes":mapped,
         "status":state,
         "reason":None if mapped else NON_EQUIVALENT.get(mid,"Legacy reference is context/grade/adjacent process rather than proven equivalence")
        })
    return {
        "schema_version":"2.0",
        "product_slug":"eyewear",
        "method":"conservative_curated_identity_plus_candidate_only",
        "view_nodes":rows,
        "duplicate_label_candidates":candidates,
        "material_reference_reviews":discrepancies,
        "summary":{
            "registered_view_nodes":len(rows),
            "unique_normalized_labels":len(by_label),
            "curated_exact_links":sum(x["identity_state"]=="curated_exact" for x in rows),
            "provisional_nodes":sum(x["identity_state"]=="provisional_unique" for x in rows),
            "duplicate_candidate_groups":len(candidates),
            "duplicate_node_occurrences":sum(len(x["view_node_ids"]) for x in candidates),
            "legacy_material_reference_count":len(materials),
            "material_references_needing_review":sum(x["status"]!="curated_exact" for x in discrepancies)
        },
        "warning":"All 382 view nodes are registered, but provisional rows are NOT semantically normalized materials or verified supplier edges."
    }

def persist(db_path:Path, resolution):
    import sqlite3
    db=sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys=ON")
    try:
        for n in resolution["view_nodes"]:
            db.execute("""INSERT INTO view_node_resolution(view_node_id,product_id,view_entity_id,
               canonical_material_id,label_key,identity_state,review_required)
               VALUES (?,?,?,?,?,?,?)""",(
               n["view_node_id"],"PRODUCT:EYEWEAR",n["view_entity_id"],
               n["canonical_material_entity_id"],n["label_key"],
               n["identity_state"],int(n["review_required"])
            ))
        for g in resolution["duplicate_label_candidates"]:
            db.execute("INSERT INTO identity_candidate_group(group_id,label_key,review_state,reason) VALUES (?,?,?,?)",
                (g["candidate_group_id"],g["label_key"],g["candidate_status"],g["reason"]))
            for vid in g["view_node_ids"]:
                db.execute("INSERT INTO identity_candidate_member(group_id,view_node_id) VALUES (?,?)",
                    (g["candidate_group_id"],vid))
        for row in resolution["material_reference_reviews"]:
            db.execute("""INSERT INTO material_reference_review
               (material_id,legacy_view_node_id,curated_exact_view_node_id,review_state,reason)
               VALUES (?,?,?,?,?)""",(
                "MAT:"+row["material_id"],row["legacy_representative_node_id"],
                row["curated_exact_view_nodes"][0] if row["curated_exact_view_nodes"] else None,
                row["status"],row["reason"]))
        errors=db.execute("PRAGMA foreign_key_check").fetchall()
        if errors:raise ValueError("Identity foreign key violations "+repr(errors))
        db.commit()
    except Exception:
        db.rollback();raise
    finally:db.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="build/research/eyewear_identity.json")
    args=p.parse_args()
    from build_site import unpack_seed
    data=resolve(unpack_seed())
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("IDENTITY_REGISTERED",json.dumps(data["summary"],ensure_ascii=False))
    return 0

if __name__=="__main__":sys.exit(main())
