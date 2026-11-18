import argparse
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import research_cli
import build_site

class ResearchCliTests(unittest.TestCase):
    def test_skill_mirrors_and_metadata(self):
        r=research_cli.validate_skills()
        self.assertTrue(r["structure_valid"],r["errors"])
        self.assertEqual(r["skill_count"],12)
        self.assertFalse(r["semantic_truth_verified"])

    def test_plan_deep_search_schema_shape(self):
        args=argparse.Namespace(node="Optical PC",product="eyewear",geography="China",
            as_of="2026-11-18",max_queries=10,max_results_per_query=5,max_fetch=12)
        p=research_cli.plan(args)
        self.assertEqual(p["schema_version"],"1.0")
        self.assertEqual(p["budget"]["max_queries"],10)
        self.assertGreaterEqual(len(p["subquestions"]),5)
        self.assertTrue(all(q["queries"] for q in p["subquestions"]))
        self.assertIn("No search was performed",p["notes"][0])

    def test_synthetic_ledger_valid_but_not_truth(self):
        d=research_cli.read(ROOT/"research/examples/ledger.json")
        r=research_cli.audit_ledger(d)
        self.assertTrue(r["structure_valid"],r["errors"])
        self.assertFalse(r["semantic_truth_verified"])

    def test_ledger_rejects_bogus_quote(self):
        d=research_cli.read(ROOT/"research/examples/ledger.json")
        d["claims"][0]["evidence"][0]["quote"]="NEVER PRESENT IN SOURCE"
        r=research_cli.audit_ledger(d)
        self.assertFalse(r["structure_valid"])
        self.assertTrue(any("quote absent" in e for e in r["errors"]))

    def test_supported_without_positive_evidence_blocked(self):
        d=research_cli.read(ROOT/"research/examples/ledger.json")
        d["claims"][0]["evidence"]=[]
        self.assertFalse(research_cli.audit_ledger(d)["structure_valid"])

    def test_dossier_template_valid_with_pending_review(self):
        d=research_cli.read(ROOT/"research/examples/node-dossier.json")
        r=research_cli.audit_dossier(d)
        self.assertTrue(r["structure_valid"],r["errors"])
        self.assertNotEqual(r["semantic_review_status"],"approved")
        self.assertFalse(r["semantic_truth_verified"])

    def test_publishable_requires_semantic_review(self):
        d=research_cli.read(ROOT/"research/examples/node-dossier.json")
        d["review_state"]="publishable"
        r=research_cli.audit_dossier(d)
        self.assertFalse(r["structure_valid"])
        self.assertTrue(any("PUBLISHABLE" in e for e in r["errors"]))

    def test_market_denominator_and_share_range_block(self):
        d=research_cli.read(ROOT/"research/examples/node-dossier.json")
        d["sections"]["market"]=[{"geography":"Global","year":2025,"metric":"capacity",
                                  "denominator":"","unit":"pct","source_id":"S001","share":101}]
        r=research_cli.audit_dossier(d)
        self.assertFalse(r["structure_valid"])
        self.assertTrue(any("denominator" in x for x in r["errors"]))

    def test_anonymous_suppliers_never_inferred(self):
        d=research_cli.read(ROOT/"research/examples/node-dossier.json")
        d["sections"]["companies"]=[{"relationship":"supplied_to","supplier_public_label":"Supplier 1"}]
        r=research_cli.audit_dossier(d)
        self.assertFalse(r["structure_valid"])

    def test_rocket_version_required(self):
        d=research_cli.read(ROOT/"research/examples/node-dossier.json")
        d["node_type"]="rocket_system"
        d["configuration_id"]=None
        r=research_cli.audit_dossier(d)
        self.assertFalse(r["structure_valid"])

    def test_backlog_reflects_existing_dossiers_but_not_semantic_approval(self):
        args=argparse.Namespace(product="eyewear")
        b=research_cli.seed_backlog(args)
        self.assertEqual(b["count"],382)
        self.assertEqual(b["dossier_count"],16)
        self.assertEqual(b["unreviewed_count"],366)
        self.assertTrue(all(n["verified_claims"]==0 for n in b["nodes"]))
        self.assertTrue(all(n["priority"]=="unrated" for n in b["nodes"]))

    def test_second_product_backlog_with_six_pending_dossiers(self):
        x=research_cli.seed_backlog(argparse.Namespace(product="henkel-adhesives"))
        self.assertEqual(x["count"],73)
        self.assertEqual(x["dossier_count"],6)
        self.assertEqual(x["unreviewed_count"],67)
        self.assertTrue(all(n["verified_claims"]==0 for n in x["nodes"]))

    def test_sqlite_research_migration_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            dbp=Path(tmp)/"test.sqlite"
            build_site.add_sqlite(build_site.unpack_seed(),dbp)
            with sqlite3.connect(dbp) as db:
                tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                required={"product_configuration","configuration_member","research_claim","research_claim_source",
                          "node_dossier","system_interface","research_gap","entity_resolution_candidate"}
                self.assertTrue(required.issubset(tables),required-tables)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
                self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())
                self.assertEqual(db.execute("SELECT count(*) FROM research_claim").fetchone()[0],0)
if __name__=="__main__":
    unittest.main()
