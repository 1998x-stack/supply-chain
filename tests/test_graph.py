import sys,unittest,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_site
class SupplyChainTest(unittest.TestCase):
 def test_seed(self):
  stats=build_site.check_seed(build_site.unpack_seed())
  self.assertEqual(stats['nodes'],382)
  self.assertGreaterEqual(stats['companies'],40)
 def test_no_anonymous_supplier_inference(self):
  data=build_site.unpack_seed()
  self.assertTrue(all(not x['supplier_identity_disclosed'] for x in data['procurement_concentration']))
 def test_sqlite_foreign_keys(self):
  import tempfile
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'test.sqlite';build_site.add_sqlite(build_site.unpack_seed(),out)
   db=sqlite3.connect(out)
   self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
   self.assertFalse(db.execute('PRAGMA foreign_key_check').fetchall())
   self.assertEqual(db.execute('SELECT count(*) FROM product_view_node').fetchone()[0],382)
 def test_market_scoping(self):
  data=build_site.unpack_seed()
  self.assertTrue(all(x['denominator_scope'] for x in data['market']))
  self.assertTrue(all(x['source_id'] for x in data['market_share']))
if __name__=='__main__':unittest.main()
