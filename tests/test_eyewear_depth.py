import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import audit_eyewear
import build_site

class EyewearDepthResearchTests(unittest.TestCase):
    def test_all_dossiers_and_ledgers_pass_structural_audit(self):
        r=audit_eyewear.inspect()
        self.assertTrue(r["structure_valid"],r["errors"])
        self.assertEqual(r["total_tree_nodes"],382)
        self.assertEqual(r["nodes_with_dossiers"],16)
        self.assertEqual(r["nodes_without_dossiers"],366)
        self.assertEqual(r["semantic_approved_dossiers"],0)
        self.assertFalse(r["semantic_truth_verified"])
    def test_public_snapshot_has_eight_linked_dossiers(self):
        x=build_site.unpack_seed()
        records=build_site.read_public_research("eyewear",{n["node_id"] for n in x["tree_node"]})
        self.assertEqual(len(records),16)
        self.assertTrue(all(r["semantic_review_status"]=="pending" for r in records))
        self.assertTrue(all("sources" in r and "claims" in r for r in records))
    def test_markets_never_treat_sponge_tonnes_as_share(self):
        x=build_site.unpack_seed()
        d=next(r for r in build_site.read_public_research("eyewear",{n["node_id"] for n in x["tree_node"]})
               if r["node_id"]=="N0224")
        self.assertEqual(d["sections"]["market"][0]["metric"],"national_production")
        self.assertIsNone(d["sections"]["market"][0]["share"])
    def test_backlog_tracks_research_without_certifying_claims(self):
        import argparse,research_cli
        b=research_cli.seed_backlog(argparse.Namespace(product="eyewear"))
        self.assertEqual(b["dossier_count"],16)
        self.assertEqual(b["unreviewed_count"],366)
        self.assertTrue(all(n["verified_claims"]==0 for n in b["nodes"]))

if __name__=="__main__":unittest.main()
