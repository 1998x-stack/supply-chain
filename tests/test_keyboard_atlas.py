import json,sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site,validate_intelligence,research_coverage
from ingest_research import ingest

class KeyboardAtlasTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.graph=json.loads((ROOT/"data/products/keyboard/graph.json").read_text(encoding="utf-8"))
  cls.norm=build_site.convert_atlas_v1(cls.graph)
 def test_graph_ontology_and_primary_evidence(self):
  x=self.graph;r=validate_intelligence.inspect(x)
  self.assertTrue(r["structure_valid"],r["errors"])
  self.assertFalse(r["semantic_truth_verified"])
  self.assertEqual(len(x["nodes"]),165)
  self.assertEqual(len(x["sources"]),17)
  self.assertEqual(len(x["node_intelligence"]),30)
  self.assertEqual(len(x["cross_links"]),27)
  self.assertEqual(len(x["materials"]),13)
  self.assertEqual(len(x["companies"]),6)
  self.assertEqual(len(x["company_relations"]),0)
  self.assertEqual(len(x["markets"]),0)
  self.assertEqual(len(x["shares"]),0)
  self.assertEqual(len({n["id"] for n in x["nodes"]}),165)
  self.assertEqual(len([n for n in x["nodes"] if n["parent"]=="keyboard"]),8)
 def test_no_double_counting_of_variant_bom(self):
  x=self.graph
  byid={c["id"]:c for c in x["product_configurations"]}
  self.assertEqual(set(byid),{"mechanical_usb","hall_usb","membrane_usb","mechanical_ble"})
  self.assertIn("mx_gold_contacts",byid["mechanical_usb"]["primary_nodes"])
  self.assertNotIn("hall_sensor",byid["mechanical_usb"]["primary_nodes"])
  self.assertIn("hall_sensor",byid["hall_usb"]["primary_nodes"])
  self.assertNotIn("mx_gold_contacts",byid["hall_usb"]["primary_nodes"])
  self.assertIn("pet_membrane",byid["membrane_usb"]["primary_nodes"])
  self.assertNotIn("liion_cell",byid["mechanical_usb"]["primary_nodes"])
  self.assertFalse(any("liion_cell" in c["primary_nodes"] for c in byid.values()),
   "Battery chemistry must remain an open choice, even within wireless configurations")
 def test_cross_links_are_distinct_from_tree_edges_and_no_procurement_is_inferred(self):
  x=self.graph;tree={n["id"]:n for n in x["nodes"]}
  keys=set()
  for r in x["cross_links"]:
   key=(r["from"],r["to"],r["relation_type"])
   self.assertNotIn(key,keys)
   keys.add(key)
   self.assertNotEqual(tree[r["from"]]["parent"],r["to"] if tree[r["from"]]["relation_type"]==r["relation_type"] else None)
   self.assertNotEqual(r["evidence_status"],"verified")
  self.assertFalse(x["company_relations"])
  self.assertTrue(all("not" in c["role"] or "product" in c["role"] or "publishes" in c["role"] or "retail" in c["role"]
                     for c in x["company_material"]))
 def test_twelve_ledgers_and_dossiers_are_drafts_and_referenced(self):
  seed=self.norm
  docs=build_site.read_public_research("keyboard",{n["node_id"] for n in seed["tree_node"]})
  self.assertEqual(len(docs),12)
  self.assertTrue(all(d["review_state"]=="reviewable_draft" for d in docs))
  self.assertTrue(all(d["semantic_review_status"]=="pending" for d in docs))
  self.assertTrue(all(len(d["claims"])>=1 and len(d["sources"])>=1 for d in docs))
  cov=research_coverage.build_coverage("keyboard",seed,docs)
  self.assertEqual(cov["metrics"]["nodes"],165)
  self.assertEqual(cov["metrics"]["dossiers"],12)
  self.assertEqual(cov["metrics"]["approved_dossiers"],0)
  self.assertEqual(len(cov["nodes"]),165)
  self.assertGreaterEqual(cov["metrics"]["navigation_nodes"],8)
  self.assertEqual(cov["metrics"]["needs_semantic_review"],12)
 def test_products_three_and_full_sqlite_sources(self):
  reg=build_site.discover_products()
  self.assertEqual({m["slug"] for m,_ in reg},{"eyewear","henkel-adhesives","keyboard"})
  with tempfile.TemporaryDirectory() as td:
   dbpath=Path(td)/"research.sqlite"
   build_site.add_sqlite(build_site.unpack_seed(),dbpath)
   build_site.add_additional_products(reg,dbpath)
   stats=ingest(dbpath,slug="keyboard")
   self.assertEqual(stats["dossiers"],12)
   self.assertEqual(stats["claims"],12)
   with sqlite3.connect(dbpath) as db:
    self.assertEqual(db.execute("SELECT COUNT(*) FROM product").fetchone()[0],3)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM product_view_node WHERE product_id='PRODUCT:KEYBOARD'").fetchone()[0],165)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM node_dossier WHERE product_id='PRODUCT:KEYBOARD'").fetchone()[0],12)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM edge WHERE edge_id LIKE 'XL:keyboard:%'").fetchone()[0],27)
    self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())
    self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
 def test_compact_snapshot_exposes_configs_research_and_notes(self):
  docs=build_site.read_public_research("keyboard",{n["node_id"] for n in self.norm["tree_node"]})
  cov=research_coverage.build_coverage("keyboard",self.norm,docs)
  data=build_site.compact(self.norm,docs,None,cov)
  self.assertEqual(len(data["n"]),165)
  self.assertEqual(len(data["research"]),12)
  self.assertEqual(len(data["insights"]),30)
  self.assertEqual(len(data["configurations"]),4)
  self.assertEqual(len(data["xl"]),27)
  self.assertEqual(len(data["coverage"]),165)

if __name__=="__main__":unittest.main()
