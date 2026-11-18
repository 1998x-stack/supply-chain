import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site,research_coverage

class CoverageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.products={m["slug"]:x for m,x in build_site.discover_products()}
 def test_coverage_for_both_products_preserves_truthful_dossier_counts(self):
  all=[]
  for slug,count,dossiers in (("eyewear",382,16),("henkel-adhesives",73,6),("keyboard",165,12)):
   seed=self.products[slug]
   doc=build_site.read_public_research(slug,{n["node_id"] for n in seed["tree_node"]})
   result=research_coverage.build_coverage(slug,seed,doc)
   m=result["metrics"]
   self.assertEqual(m["nodes"],count)
   self.assertEqual(m["dossiers"],dossiers)
   self.assertEqual(m["approved_dossiers"],0)
   self.assertEqual(m["needs_semantic_review"],dossiers)
   self.assertEqual(sum(m["by_stage"].values()),count)
   self.assertEqual(sum(m["by_priority"].values()),count)
   self.assertEqual(len({n["node_id"] for n in result["nodes"]}),count)
   all.append(result)
  self.assertEqual(sum(x["metrics"]["nodes"] for x in all),620)
  self.assertEqual(sum(x["metrics"]["dossiers"] for x in all),34)
 def test_navigation_is_not_blocking_research_denominator(self):
  s=self.products["henkel-adhesives"]
  x=research_coverage.build_coverage("henkel-adhesives",s,[])
  nav={r["node_id"] for r in x["nodes"] if r["facet"]=="navigation"}
  self.assertIn("henkel",nav)
  self.assertIn("brand",nav)
  self.assertLess(x["metrics"]["research_targets"],73)
 def test_existing_henkel_note_not_counted_as_approved_dossier(self):
  seed=self.products["henkel-adhesives"]
  result=research_coverage.build_coverage("henkel-adhesives",seed,[])
  doc={r["node_id"]:r for r in result["nodes"]}
  self.assertEqual(doc["243"]["stage"],"source_note")
  self.assertFalse(doc["243"]["approved"])
  self.assertGreater(doc["243"]["sources"],0)
 def test_every_non_navigation_node_has_actionable_research_questions(self):
  for slug,seed in self.products.items():
   d=build_site.read_public_research(slug,{n["node_id"] for n in seed["tree_node"]})
   result=research_coverage.build_coverage(slug,seed,d)
   self.assertTrue(all(r["questions"] for r in result["nodes"] if r["facet"]!="navigation"))
   self.assertTrue(all(not r["questions"] for r in result["nodes"] if r["facet"]=="navigation"))
 def test_no_fake_complete_and_no_vendor_rank_built_from_structure(self):
  seed=self.products["eyewear"]
  result=research_coverage.build_coverage("eyewear",seed,[])
  self.assertEqual(result["metrics"]["approved_dossiers"],0)
  tasks=research_coverage.task_bundle("eyewear",research_coverage.prioritized_queue(result,"P0",5))
  self.assertEqual(len(tasks["tasks"]),5)
  self.assertEqual(tasks["semantic_review"],"not_started")
  self.assertFalse(any("Henkel" in str(t) for t in tasks["tasks"]))
  self.assertTrue(all(t["priority"]=="P0" for t in tasks["tasks"]))
 def test_curated_material_source_is_contextual_not_assumed_procurement(self):
  seed={"tree_node":[
   {"node_id":"root","name":"Root","parent_id":None,"kind":"category","branch":"Test","description":""},
   {"node_id":"old","name":"Legacy alias","parent_id":"root","kind":"material","branch":"Test","description":""},
   {"node_id":"real","name":"Exact material","parent_id":"root","kind":"material","branch":"Test","description":""}],
   "material":[{"material_id":"X","name":"Material X","representative_node_id":"old"}],
   "source":[{"source_id":"S001","title":"Vendor disclosure","url":"https://example.org"}],
   "company_material":[{"company_id":"COMP1","material_id":"X","source_id":"S001","role":"manufacturer"}],
   "node_intelligence":[]}
  identity={"view_nodes":[{"view_node_id":"real","canonical_material_entity_id":"MAT:X"}]}
  report=research_coverage.build_coverage("synthetic",seed,[],identity)
  byid={x["node_id"]:x for x in report["nodes"]}
  self.assertEqual(byid["real"]["stage"],"source_note")
  self.assertEqual(byid["real"]["material_source_ids"],["S001"])
  self.assertEqual(byid["old"]["stage"],"structural_only")
  self.assertEqual(byid["old"]["material_source_ids"],[])
  self.assertFalse(byid["real"]["approved"])

 def test_distinguishes_approved_from_dossier_present(self):
  seed={"tree_node":[{"node_id":"x","name":"合成根","parent_id":None,"kind":"category","branch":"test","description":""},
                     {"node_id":"y","name":"合成测试料","parent_id":"x","kind":"material","branch":"test","description":"高纯度"}],
        "node_intelligence":[],"material":[]}
  doc=[{"node_id":"y","review_state":"publishable","semantic_review_status":"approved",
        "claims":[{"id":"C001","text":"Test"}],"sources":[{"id":"S001","url":"https://example.org"}],
        "sections":{"open_questions":[]}}]
  r=research_coverage.build_coverage("synthetic",seed,doc)
  self.assertEqual(r["metrics"]["approved_dossiers"],1)
  self.assertEqual(r["metrics"]["research_targets"],1)
  self.assertEqual(r["nodes"][1]["stage"],"reviewed")
if __name__=="__main__":unittest.main()
