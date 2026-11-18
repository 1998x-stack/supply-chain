import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
import build_priority,build_site
class EyewearPriorityTests(unittest.TestCase):
 def test_all_nodes_in_queue_no_fake_completion(self):
  a=build_priority.prioritize(build_site.unpack_seed(),build_priority.load_dossiers())
  self.assertEqual(a["total_nodes"],382)
  self.assertEqual(sum(a["tier_counts"].values()),382)
  self.assertEqual(a["nodes_with_dossiers"],16)
  self.assertEqual(a["semantic_approved_count"],0)
  self.assertEqual(len({x["node_id"] for x in a["records"]}),382)
 def test_critical_nodes_not_hidden_behind_primitives(self):
  a=build_priority.prioritize(build_site.unpack_seed(),{})
  d={x["node_id"]:x for x in a["records"]}
  for v in ("N0004","N0019","N0032","N0124","N0163","N0195","N0224","N0266","N0316"):
   self.assertEqual(d[v]["tier"],"P0")
  self.assertEqual(d["N0001"]["tier"],"P2")
if __name__=="__main__":unittest.main()
