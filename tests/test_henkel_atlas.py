import json,sys,tempfile,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site,validate_intelligence
class HenkelPortfolioTests(unittest.TestCase):
 def load(self):
  return json.loads((ROOT/"data/products/henkel-adhesives/graph.json").read_text(encoding="utf-8"))
 def test_source_scoped_portfolio(self):
  g=self.load();r=validate_intelligence.inspect(g)
  self.assertTrue(r["structure_valid"],r["errors"])
  self.assertFalse(r["semantic_truth_verified"])
  self.assertEqual(r["stats"]["nodes"],73)
  self.assertEqual(r["stats"]["insights"],42)
  self.assertEqual(r["stats"]["sources"],17)
  self.assertEqual(len(g["company_relations"]),0)
  self.assertEqual(g["shares"],[])
 def test_business_revenue_is_not_vendor_market_share(self):
  g=self.load()
  root=next(x for x in g["node_intelligence"] if x["node_id"]=="henkel")
  values=[(m["value"],m["unit"],m["period"]) for m in root["metrics"]]
  self.assertIn((10667,"百万欧元","FY2025"),values)
  self.assertIn((8561,"百万欧元","2026Q1–Q3"),values)
  self.assertFalse(any("pct"==m["unit"] for m in root["metrics"]))
 def test_typed_edges_and_node_notes_preserved(self):
  g=self.load()
  a=build_site.convert_atlas_v1(g)
  self.assertEqual(len(a["tree_node"]),73)
  self.assertEqual(len(a["node_intelligence"]),42)
  self.assertEqual(next(n for n in a["tree_node"] if n["node_id"]=="brand")["relation_type"],"associated_with")
  self.assertEqual(next(n for n in a["tree_node"] if n["node_id"]=="reactors")["relation_type"],"uses_equipment")
 def test_second_product_in_shared_sqlite(self):
  reg=build_site.discover_products()
  self.assertEqual({meta["slug"] for meta,_ in reg},{"eyewear","henkel-adhesives"})
  henkel=next(x for meta,x in reg if meta["slug"]=="henkel-adhesives")
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"test.sqlite"
   build_site.add_sqlite(build_site.unpack_seed(),path)
   build_site.add_additional_products(reg,path)
   with sqlite3.connect(path) as db:
    self.assertEqual(db.execute("SELECT COUNT(*) FROM product").fetchone()[0],2)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM product_view_node WHERE product_id='PRODUCT:HENKEL_ADHESIVES'").fetchone()[0],73)
    self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())
    self.assertEqual(db.execute("SELECT relation_type FROM edge WHERE edge_id='EDGE:henkel-adhesives:brand'").fetchone()[0],"associated_with")
 def test_validator_catches_unattributed_fact(self):
  g=self.load();next(x for x in g["node_intelligence"] if x["node_id"]=="henkel")["metrics"][0]["source_id"]="S404"
  self.assertFalse(validate_intelligence.inspect(g)["structure_valid"])
 def test_cross_branch_links_are_typed_and_audited(self):
  g=self.load()
  self.assertEqual(len(g["cross_links"]),23)
  self.assertTrue(all("relation_type" in c and "evidence_status" in c for c in g["cross_links"]))
  row=next(x for x in g["cross_links"] if x["from"]=="ethylene" and x["to"]=="evaresin")
  self.assertEqual(row["relation_type"],"associated_with")
  self.assertEqual(row["evidence_status"],"hypothesis")
  g["cross_links"][0]["source_id"]="MISSING"
  self.assertFalse(validate_intelligence.inspect(g)["structure_valid"])
 def test_no_claim_of_current_procurement_from_brand(self):
  g=self.load()
  self.assertEqual(g["company_relations"],[])
  self.assertTrue(all(x["role"].startswith("product_") for x in g["company_material"]))
 def test_henkel_evidence_dossiers_in_shared_sqlite(self):
  registry=build_site.discover_products()
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"all.sqlite"
   build_site.add_sqlite(build_site.unpack_seed(),path)
   build_site.add_additional_products(registry,path)
   from ingest_research import ingest
   stats=ingest(path,"henkel-adhesives")
   self.assertEqual(stats["dossiers"],6)
   self.assertEqual(stats["claims"],11)
   with sqlite3.connect(path) as db:
    self.assertEqual(db.execute("SELECT COUNT(*) FROM node_dossier WHERE product_id='PRODUCT:HENKEL_ADHESIVES'").fetchone()[0],6)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_claim WHERE entity_id LIKE 'NODE:henkel-adhesives:%'").fetchone()[0],11)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_claim WHERE semantic_review_status='approved' AND entity_id LIKE 'NODE:henkel-adhesives:%'").fetchone()[0],0)
    self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())

if __name__=="__main__":unittest.main()
