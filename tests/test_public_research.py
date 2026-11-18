import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_site

class PublicResearchTests(unittest.TestCase):
    def test_node_dossier_link_and_draft_status(self):
        seed=build_site.unpack_seed()
        node_ids={x['node_id'] for x in seed['tree_node']}
        dossiers=build_site.read_public_research('eyewear',node_ids)
        self.assertEqual(len(dossiers),1)
        d=dossiers[0]
        self.assertEqual(d['node_id'],'N0032')
        self.assertEqual(d['semantic_review_status'],'pending')
        self.assertNotEqual(d['review_state'],'publishable')
        self.assertEqual(len(d['claims']),4)
        self.assertEqual(len(d['sources']),4)
    def test_source_full_content_not_exported(self):
        ids={x['node_id'] for x in build_site.unpack_seed()['tree_node']}
        d=build_site.read_public_research('eyewear',ids)[0]
        self.assertTrue(all('content' not in s for s in d['sources']))
        self.assertTrue(all('quote' not in s for s in d['claims']))
    def test_invalid_product_node_rejected(self):
        with self.assertRaises(ValueError):
            build_site.read_public_research('eyewear',{'NOT_A_NODE'})
    def test_snapshot_embeds_node_dossiers(self):
        x=build_site.unpack_seed()
        r=build_site.read_public_research('eyewear',{n['node_id'] for n in x['tree_node']})
        body=build_site.compact(x,r)
        self.assertEqual(body['research'][0]['node_id'],'N0032')
        self.assertEqual(len(body['n']),382)

if __name__=='__main__':unittest.main()
