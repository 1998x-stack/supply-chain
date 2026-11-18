import sys, tempfile, sqlite3, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site, normalize_eyewear

class EyewearIdentityTests(unittest.TestCase):
 def test_all_nodes_registered_without_unjustified_merge(self):
  x=normalize_eyewear.resolve(build_site.unpack_seed())
  s=x["summary"]
  self.assertEqual(s["registered_view_nodes"],382)
  self.assertEqual(s["unique_normalized_labels"],356)
  self.assertEqual(s["curated_exact_links"],len(normalize_eyewear.EXACT_MATERIAL_BINDINGS))
  self.assertEqual(s["provisional_nodes"]+s["curated_exact_links"],382)
  self.assertGreaterEqual(s["duplicate_candidate_groups"],10)
  self.assertTrue(all(not c["auto_merge"] for c in x["duplicate_label_candidates"]))
 def test_wrong_legacy_links_do_not_become_exact_identifications(self):
  x=normalize_eyewear.resolve(build_site.unpack_seed())
  rev={m["material_id"]:m for m in x["material_reference_reviews"]}
  self.assertEqual(rev["BPA"]["curated_exact_view_nodes"],["N0033"])
  self.assertEqual(rev["ACETIC_ANHYDRIDE"]["curated_exact_view_nodes"],["N0170"])
  self.assertEqual(rev["XDI"]["status"],"associated_only")
  self.assertEqual(rev["ACETATE_RENEW"]["status"],"associated_only")
 def test_sqlite_resolution_references(self):
  with tempfile.TemporaryDirectory() as d:
   dbp=Path(d)/"check.sqlite"
   build_site.add_sqlite(build_site.unpack_seed(),dbp)
   x=normalize_eyewear.resolve(build_site.unpack_seed())
   normalize_eyewear.persist(dbp,x)
   with sqlite3.connect(dbp) as db:
    self.assertEqual(db.execute("SELECT COUNT(*) FROM view_node_resolution").fetchone()[0],382)
    self.assertEqual(db.execute("SELECT canonical_material_id FROM view_node_resolution WHERE view_node_id='N0033'").fetchone()[0],"MAT:BPA")
    self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
    self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())
