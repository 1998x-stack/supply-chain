import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import research_cli

class RealDossierDraftTests(unittest.TestCase):
    def test_pc_ledger_structure(self):
        x=research_cli.read(ROOT/"research/ledgers/eyewear/pc-optical-ledger.json")
        r=research_cli.audit_ledger(x)
        self.assertTrue(r["structure_valid"],r["errors"])
        self.assertEqual(r["sources"],4)
        self.assertFalse(r["semantic_truth_verified"])
    def test_pc_dossier_still_requires_human_review(self):
        x=research_cli.read(ROOT/"research/dossiers/eyewear/pc-optical-draft.json")
        r=research_cli.audit_dossier(x)
        self.assertTrue(r["structure_valid"],r["errors"])
        self.assertEqual(r["semantic_review_status"],"pending")
    def test_industry_share_not_eye_grade_or_third_competitor(self):
        x=research_cli.read(ROOT/"research/dossiers/eyewear/pc-optical-draft.json")
        markets=x["sections"]["market"]
        self.assertEqual(len(markets),2)
        self.assertTrue(all("all-grade PC" in m["denominator"] for m in markets))
        self.assertTrue(all(m["not_equivalent_to"]=="ophthalmic-grade market share" for m in markets))
    def test_no_invented_customer(self):
        x=research_cli.read(ROOT/"research/dossiers/eyewear/pc-optical-draft.json")
        self.assertTrue(all(not c["confirmed_lens_brand_customer"] for c in x["sections"]["companies"]))
        self.assertTrue(all(c["relationship"]!="supplied_to" for c in x["sections"]["companies"]))
    def test_market_pdf_stays_partial(self):
        x=research_cli.read(ROOT/"research/ledgers/eyewear/pc-optical-ledger.json")
        claim=next(c for c in x["claims"] if c["id"]=="C004")
        self.assertEqual(claim["status"],"partially_supported")
        byid={s["id"]:s for s in x["sources"]}
        self.assertEqual(byid["S003"]["origin_group"],byid["S004"]["origin_group"])
if __name__=="__main__":unittest.main()
