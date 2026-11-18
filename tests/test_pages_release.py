import gzip,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from verify_pages_release import audit_release

class PagesReleaseValidatorTests(unittest.TestCase):
 def _fixture(self,root):
  (root/"data").mkdir(parents=True)
  for asset in ("assets/app.js","assets/node_panel.js","assets/styles.css","assets/node_panel.css"):
   p=root/asset;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("ok")
  products=[]
  for slug,n in [("eyewear",382),("henkel-adhesives",73)]:
   nodes=[["node-"+str(i)] for i in range(n)]
   coverage=[{"node_id":v[0],"stage":"structural_only","priority":"P2","facet":"material"} for v in nodes]
   with gzip.open(root/"data"/(slug+".json.gz"),"wt",encoding="utf-8") as f:
    json.dump({"n":nodes,"research":[],"coverage":coverage},f)
   (root/"data"/(slug+"_research_queue.json")).write_text(json.dumps({
      "product_slug":slug,"semantic_review":"not_started","tasks":[{"node_id":"node-0"}]}))
   products.append({"slug":slug,"nodes":n,"coverage":{
      "nodes":n,"dossiers":0,"approved_dossiers":0,"source_notes_without_dossier":0,
      "needs_dossier":n}})
  data={"build_id":"unit-test-v1","products":products}
  (root/"data/catalog.json").write_text(json.dumps(data),encoding="utf-8")
  (root/"index.html").write_text(" ".join(x+"?v=unit-test-v1" for x in
   ("assets/app.js","assets/node_panel.js","assets/styles.css","assets/node_panel.css")),encoding="utf-8")
 def test_complete_release(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self._fixture(root)
   result=audit_release(root)
   self.assertTrue(result["valid"],result["errors"])
 def test_stale_catalog_with_only_eyewear_is_blocked(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self._fixture(root)
   data=json.loads((root/"data/catalog.json").read_text())
   data["products"]=data["products"][:1]
   (root/"data/catalog.json").write_text(json.dumps(data))
   result=audit_release(root)
   self.assertFalse(result["valid"])
   self.assertTrue(any("Missing required products" in x for x in result["errors"]))
 def test_release_rejects_missing_research_coverage(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self._fixture(root)
   path=root/"data"/"henkel-adhesives.json.gz"
   with gzip.open(path,"wt",encoding="utf-8") as f:json.dump({"n":[["fake"]]*73,"research":[]},f)
   check=audit_release(root)
   self.assertFalse(check["valid"])
   self.assertTrue(any("coverage count" in x for x in check["errors"]))
 def test_unversioned_html_is_blocked(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self._fixture(root)
   (root/"index.html").write_text('<script src="./assets/app.js"></script>')
   self.assertFalse(audit_release(root)["valid"])
if __name__=="__main__":unittest.main()
