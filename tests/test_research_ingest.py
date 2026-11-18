import sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_site,ingest_research

class ResearchSqliteIngestTests(unittest.TestCase):
 def test_import_evidence_claim_sources_and_gaps_without_approval(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/"supply.sqlite"
   build_site.add_sqlite(build_site.unpack_seed(),out)
   stats=ingest_research.ingest(out)
   self.assertEqual(stats["dossiers"],16)
   self.assertEqual(stats["claims"],32)
   self.assertEqual(stats["claim_citations"],32)
   self.assertEqual(stats["gaps"],57)
   self.assertGreaterEqual(stats["observations"],8)
   with sqlite3.connect(out) as db:
    self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
    self.assertEqual(db.execute("SELECT COUNT(*) FROM node_dossier").fetchone()[0],16)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_claim_source").fetchone()[0],32)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_gap").fetchone()[0],57)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_observation").fetchone()[0],stats["observations"])
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_observation WHERE metric='national_production' AND value_num=256000 AND observation_year=2024").fetchone()[0],1)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM research_claim WHERE semantic_review_status='approved'").fetchone()[0],0)
    self.assertEqual(db.execute("SELECT COUNT(*) FROM source WHERE source_type='curated_excerpt'").fetchone()[0],stats["sources"])
    self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())
 def test_research_claim_has_global_entity_id(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/"db.sqlite"
   build_site.add_sqlite(build_site.unpack_seed(),out)
   ingest_research.ingest(out)
   with sqlite3.connect(out) as db:
    names=db.execute("SELECT DISTINCT entity_id FROM research_claim").fetchall()
    self.assertEqual(len(names),16)
    self.assertTrue(all(name[0].startswith("NODE:EYE:N") for name in names))

if __name__=="__main__":unittest.main()
