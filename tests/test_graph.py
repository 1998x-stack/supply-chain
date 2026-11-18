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
   self.assertEqual(db.execute("SELECT count(*) FROM edge WHERE edge_id LIKE 'REL:%'").fetchone()[0],11)
   self.assertEqual(db.execute("SELECT count(*) FROM edge WHERE edge_id LIKE 'CM:%'").fetchone()[0],46)
   self.assertEqual(db.execute('SELECT count(*) FROM market_share').fetchone()[0],52)
   self.assertEqual(db.execute('SELECT count(*) FROM capacity').fetchone()[0],12)
   self.assertEqual(db.execute('SELECT count(*) FROM substitution_candidate').fetchone()[0],6)
 def test_market_scoping(self):
  data=build_site.unpack_seed()
  self.assertTrue(all(x['denominator_scope'] for x in data['market']))
  self.assertTrue(all(x['source_id'] for x in data['market_share']))
if __name__=='__main__':unittest.main()

class ProductExtensionTest(unittest.TestCase):
 def test_generic_product_import_and_global_reverse_path(self):
  import json,tempfile
  p=ROOT/'examples'/'new-product'
  meta=json.loads((p/'product.json').read_text());meta['published']=True
  graph=json.loads((p/'graph.json').read_text())
  normalized=build_site.convert_atlas_v1(graph)
  build_site.check_seed(normalized)
  base=build_site.unpack_seed()
  rev=build_site.reverse_catalog([({'slug':'eyewear'},base),(meta,normalized)])
  self.assertIn('example-product',rev['material_to_products']['EXAMPLE_MATERIAL'])
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/'graph.sqlite'
   build_site.add_sqlite(base,target)
   build_site.add_additional_products([(meta,normalized)],target)
   db=sqlite3.connect(target)
   self.assertEqual(db.execute('SELECT count(*) FROM product').fetchone()[0],2)
   self.assertFalse(db.execute('PRAGMA foreign_key_check').fetchall())
   trace=db.execute('''WITH RECURSIVE path(node,depth) AS (
     SELECT 'MAT:EXAMPLE_MATERIAL',0 UNION ALL
     SELECT edge.downstream_id,path.depth+1 FROM edge JOIN path ON edge.upstream_id=path.node
     WHERE edge.relation_type IN ('material_input','component_of','processed_into') AND path.depth<12)
     SELECT COUNT(*) FROM path WHERE node='PRODUCT:EXAMPLE_PRODUCT' ''').fetchone()[0]
   self.assertEqual(trace,0, 'A contextual material alias is NOT a proven physical transformation path')
   contextual=db.execute("SELECT COUNT(*) FROM edge WHERE upstream_id='MAT:EXAMPLE_MATERIAL' AND relation_type='associated_with'").fetchone()[0]
   self.assertGreaterEqual(contextual,1)

class TaxonomyTest(unittest.TestCase):
 def test_product_catalog_has_valid_categories(self):
  reg=build_site.discover_products()
  self.assertEqual([meta['slug'] for meta,_ in reg],['eyewear','henkel-adhesives'])
  self.assertEqual(len(build_site.reverse_catalog(reg)['material_to_products']),29)
