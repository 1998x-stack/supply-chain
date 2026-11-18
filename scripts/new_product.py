#!/usr/bin/env python3
"""Create an unpublished product shell. No facts, vendors, or metrics are fabricated."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('slug',help='ASCII lowercase URL slug, e.g. smartphone')
p.add_argument('--title',required=True)
p.add_argument('--category',required=True,help='Taxonomy ID, e.g. electronics')
p.add_argument('--icon',default='🧩')
a=p.parse_args()
if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',a.slug):p.error('slug must be lowercase letters/digits/hyphens')
categories=json.loads((ROOT/'data'/'taxonomy'/'categories.json').read_text())['categories']
category=next((c for c in categories if c['id']==a.category),None)
if not category:p.error('Unknown category ID')
out=ROOT/'data'/'products'/a.slug
if out.exists():p.error('Product directory already exists')
out.mkdir(parents=True)
(out/'product.json').write_text(json.dumps({'schema_version':1,'slug':a.slug,'title':a.title,'category_id':a.category,'category':category['name'],'icon':a.icon,'description':'请填写有来源的产品供应链说明','adapter':'atlas_v1','source':'graph.json','published':False},ensure_ascii=False,indent=2)+'\n')
(out/'graph.json').write_text(json.dumps({'nodes':[{'id':'root','name':a.title,'parent':None,'kind':'产品','branch':'根节点','description':''}], 'materials':[],'companies':[],'company_material':[],'company_relations':[],'markets':[],'shares':[],'sources':[],'opportunities':[],'capacity':[],'procurement':[]},ensure_ascii=False,indent=2)+'\n')
print('CREATED',out,'(published=false until researched and reviewed)')
