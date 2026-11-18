import argparse
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import deep_search_adapter

class AdapterTests(unittest.TestCase):
 def args(self,**kw):
  d={"action":"validate","input":"a.json","output":None,"report":None,"ledger":None,
     "allow_network":False,"deep_search_root":"../deep-search","dry_run":True}
  d.update(kw);return argparse.Namespace(**d)
 def test_default_non_network_validate(self):
  cmd=deep_search_adapter.make_command(self.args())
  self.assertEqual(cmd,["validate","--input","a.json"])
 def test_audit_needs_ledger_and_report(self):
  with self.assertRaises(ValueError):
   deep_search_adapter.make_command(self.args(action="audit"))
 def test_search_rejects_implicit_network(self):
  with self.assertRaises(ValueError):
   deep_search_adapter.make_command(self.args(action="search",dry_run=False))
 def test_dry_run_search_needs_no_credentials(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"plan.json"
   path.write_text(json.dumps({"budget":{"max_queries":4}}))
   cmd=deep_search_adapter.make_command(self.args(action="search",input=str(path),output="results.json",dry_run=True))
   self.assertEqual(cmd[0],"search")
 def test_budget_rejected_before_search(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"plan.json"
   path.write_text(json.dumps({"budget":{"max_queries":999}}))
   old=os.environ.get("TAVILY_API_KEY")
   os.environ["TAVILY_API_KEY"]="SYNTHETIC_TEST_VALUE"
   try:
    with self.assertRaises(ValueError):
     deep_search_adapter.make_command(self.args(action="search",allow_network=True,input=str(path),output="x.json"))
   finally:
    if old is None:os.environ.pop("TAVILY_API_KEY",None)
    else:os.environ["TAVILY_API_KEY"]=old
if __name__=="__main__":unittest.main()
