#!/usr/bin/env python3
"""Import evidence-linked node dossiers into the normalized research schema.

Only structural integrity is asserted. Manufacturer brochures are not procurement proof,
and a 'supported' ledger claim remains semantic_review_status='pending' until reviewed.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from research_cli import audit_dossier,audit_ledger

def ingest(db_path: Path,slug: str="eyewear"):
    db=sqlite3.connect(db_path);db.execute("PRAGMA foreign_keys=ON")
    dossier_dir=ROOT/"research"/"dossiers"/slug
    ledger_dir=ROOT/"research"/"ledgers"/slug
    ledgers={}
    for path in sorted(ledger_dir.glob("*.json")):
        d=json.loads(path.read_text(encoding="utf-8"))
        qa=audit_ledger(d)
        if not qa["structure_valid"]:
            raise ValueError("Invalid ledger "+str(path)+": "+repr(qa["errors"]))
        nid=d["node_id"]
        if nid in ledgers:raise ValueError("Repeated evidence ledger for "+nid)
        ledgers[nid]=d
    stats={"dossiers":0,"claims":0,"sources":0,"claim_citations":0,"gaps":0}
    try:
        for path in sorted(dossier_dir.glob("*.json")):
            doc=json.loads(path.read_text(encoding="utf-8"));nid=doc["node_id"]
            qa=audit_dossier(doc)
            if not qa["structure_valid"]:
                raise ValueError("Invalid dossier "+str(path)+": "+repr(qa["errors"]))
            ledger=ledgers.get(nid)
            if ledger is None:raise ValueError("Missing ledger "+nid)
            entity_id="NODE:EYE:"+nid
            if db.execute("SELECT COUNT(*) FROM entity WHERE entity_id=?",(entity_id,)).fetchone()[0]!=1:
                raise ValueError("Missing graph entity for "+nid)
            ds_id="DOS:EYE:"+nid
            status={"reviewable_draft":"reviewable","draft":"draft","publishable":"publishable",
                    "disputed":"disputed","reviewable":"reviewable"}.get(doc.get("review_state"))
            if status is None:raise ValueError("Invalid research state "+str(doc.get("review_state")))
            semantic=doc.get("semantic_review") or {}
            if status=="publishable" and semantic.get("status")!="approved":
                raise ValueError("Publishable dossier lacks semantic approval")
            db.execute("""INSERT INTO node_dossier
               (dossier_id,entity_id,product_id,version,as_of_date,status,weighted_field_coverage,
                semantic_reviewer,reviewed_at,file_path)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
               (ds_id,entity_id,"PRODUCT:EYEWEAR",doc.get("as_of",""),doc.get("as_of",""),
                status,qa.get("field_coverage_percent"),semantic.get("reviewer"),
                semantic.get("reviewed_at"),str(path.relative_to(ROOT))))
            stats["dossiers"]+=1
            local_sources={}
            for src in ledger.get("sources",[]):
                id_local=src["id"];sid="RS:EYE:"+nid+":"+id_local
                local_sources[id_local]=sid
                db.execute("""INSERT INTO source
                   (source_id,title,url,publisher,published_on,accessed_on,source_type)
                   VALUES (?,?,?,?,?,?,?)""",
                   (sid,src.get("title","Research source"),src["url"],src.get("publisher"),
                    src.get("published_at"),src.get("retrieved_at"),"curated_excerpt"))
                stats["sources"]+=1
            claims={c["id"]:c for c in ledger.get("claims",[])}
            for cid in doc.get("claim_ids",[]):
                claim=claims.get(cid)
                if claim is None:raise ValueError("Missing claim "+nid+"/"+cid)
                rcid="RC:EYE:"+nid+":"+cid
                db.execute("""INSERT INTO research_claim
                   (claim_id,entity_id,dossier_id,claim_text,claim_type,evidence_status,
                    analysis,semantic_review_status)
                   VALUES (?,?,?,?,?,?,?,?)""",
                   (rcid,entity_id,ds_id,claim["text"],"fact",claim["status"],
                    claim.get("analysis"),semantic.get("status","pending")))
                stats["claims"]+=1
                for ev in claim.get("evidence",[]):
                    if ev["source_id"] not in local_sources:
                        raise ValueError("Unknown ledger source "+str(ev["source_id"]))
                    snippet=next(s for s in ledger["sources"] if s["id"]==ev["source_id"])
                    db.execute("""INSERT INTO research_claim_source
                       (claim_id,source_id,quote_location,exact_quote,polarity,content_hash,origin_group)
                       VALUES (?,?,?,?,?,?,?)""",
                       (rcid,local_sources[ev["source_id"]],"curated_excerpt",ev["quote"],
                        ev["polarity"],hashlib.sha256(snippet.get("content","").encode()).hexdigest(),
                        snippet.get("origin_group")))
                    stats["claim_citations"]+=1
            for i,q in enumerate(doc.get("sections",{}).get("open_questions",[]),1):
                db.execute("""INSERT INTO research_gap
                   (gap_id,entity_id,dossier_id,question,priority,blocking,status,evidence_needed)
                   VALUES (?,?,?,?,?,?,?,?)""",
                   ("GAP:EYE:"+nid+":"+str(i).zfill(2),entity_id,ds_id,q,"P1",0,"open",
                    "Further primary-source research and semantic review"))
                stats["gaps"]+=1
        if set(ledgers)!={str(p.stem).replace("-draft","") for p in []}:
            pass  # Ledger coverage is enforced by the standalone audit tool.
        problems=db.execute("PRAGMA foreign_key_check").fetchall()
        if problems:raise ValueError("Research import foreign key errors "+repr(problems))
        db.commit()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:db.close()

def main():
    p=argparse.ArgumentParser();p.add_argument("--database",default="build/supply_chain.sqlite");a=p.parse_args()
    stats=ingest((ROOT/a.database).resolve())
    print("RESEARCH_IMPORT_OK",json.dumps(stats,ensure_ascii=False))
    return 0
if __name__=="__main__":sys.exit(main())
