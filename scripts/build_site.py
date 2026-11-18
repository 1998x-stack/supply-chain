#!/usr/bin/env python3
"""Build a read-only GitHub Pages site and a normalized SQLite research database.
No third-party Python dependencies required. Run from repository root.
"""
from __future__ import annotations
import argparse, gzip, json, sqlite3, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data'/'products'/'eyewear'/'intelligence_data.json.gz'

def unpack_seed():
    with gzip.open(SRC,'rt',encoding='utf-8') as f: return json.load(f)

def check_seed(x):
    nodes=x['tree_node']; ids={n['node_id'] for n in nodes};assert len(ids)==len(nodes)
    assert sum(n['parent_id'] is None for n in nodes)==1
    for n in nodes:
        if n['parent_id']:assert n['parent_id'] in ids
    company={c['company_id'] for c in x['company']};materials={m['material_id'] for m in x['material']}
    for s in x['market_share']:
        assert 0<=s['share_pct']<=100
        assert s['company_id'] is None or s['company_id'] in company
    for r in x['company_relation']:
        assert r['upstream_company_id'] in company and r['downstream_company_id'] in company
        assert r['material_id'] in materials
    for r in x['procurement_concentration']:
        if not r['supplier_identity_disclosed']:assert r['supplier_public_name']=='未披露名称'
    return {'nodes':len(nodes),'companies':len(company),'materials':len(materials),'sources':len(x['source'])}

def compact(x):
    # Array encoding reduces Pages payload size; unpacked using a versioned field dictionary in frontend.
    return {
     'n':[[t['node_id'],t['name'],t['parent_id'],t['kind'],t['branch'],t['description'] or ''] for t in x['tree_node']],
     'm':[[v['material_id'],v['name'],v['representative_node_id']] for v in x['material']],
     'c':[[v['company_id'],v['name_zh'],v['name_en'],v['official_website']] for v in x['company']],
     'cm':[[v['company_id'],v['material_id'],v['role']] for v in x['company_material']],
     'r':[[v['upstream_company_id'],v['downstream_company_id'],v['material_id'],v['relation_type'],v['source_id'],v['scope_note']] for v in x['company_relation']],
     'mk':[[v['market_id'],v['name'],v['geography'],v['year'],v['metric'],v['denominator_scope'],v['material_id']] for v in x['market']],
     's':[[v['market_id'],v['company_id'],v['label'],v['share_pct'],v['rank'],v['source_id']] for v in x['market_share']],
     'o':[[v['material_id'],v['china_candidate_company_id'],v['benchmark_company_id'],v['topic'],v['validation_gap']] for v in x['substitution_opportunity']],
     'src':[[v['source_id'],v['title'],v['url']] for v in x['source']],
     'pc':[[v['buyer_company_id'],v['supplier_rank'],v['share_of_buyer_procurement_pct'],v['supplier_identity_disclosed']] for v in x['procurement_concentration']]
    }

def add_sqlite(x,out):
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():out.unlink()
    db=sqlite3.connect(out)
    db.executescript((ROOT/'schema'/'001_core.sql').read_text())
    db.execute('INSERT INTO category(category_id,name_zh,icon) VALUES (?,?,?)',('optical','光学与消费医疗','👓'))
    db.execute("INSERT INTO entity(entity_id,entity_type,name_zh) VALUES ('PRODUCT:EYEWEAR','product','眼镜')")
    db.execute("INSERT INTO product(product_id,slug,category_id,summary,icon,published) VALUES (?,?,?,?,?,1)",('PRODUCT:EYEWEAR','eyewear','optical','眼镜产业链：镜片、镜架、膜层、精密配件、设备和原料','👓'))
    source_ids=set()
    for s in x['source']:
        db.execute('INSERT INTO source(source_id,title,url,source_type,accessed_on) VALUES (?,?,?,?,?)',(s['source_id'],s['title'],s['url'],s['type'],s['checked_on']));source_ids.add(s['source_id'])
    for n in x['tree_node']:
        eid='NODE:EYE:'+n['node_id']
        db.execute('INSERT INTO entity(entity_id,entity_type,name_zh,description) VALUES (?,?,?,?)',(eid,'resource' if not n['parent_id'] else 'material',n['name'],n['description']))
    for n in x['tree_node']:
        db.execute('INSERT INTO product_view_node(product_id,view_node_id,entity_id,parent_view_node_id,display_depth,display_label) VALUES (?,?,?,?,?,?)',('PRODUCT:EYEWEAR',n['node_id'],'NODE:EYE:'+n['node_id'],n['parent_id'],n['depth'],n['name']))
        if n['parent_id']:
            # Tree edges are technical-only, never empirical supply contracts.
            db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,context_product_id) VALUES (?,?,?,?,?,?)',('EDGE:EYE:'+n['node_id'],'NODE:EYE:'+n['node_id'],'NODE:EYE:'+n['parent_id'],'material_input','technological','PRODUCT:EYEWEAR'))
    for m in x['material']:
        mid='MAT:'+m['material_id']
        db.execute('INSERT INTO entity(entity_id,entity_type,name_zh) VALUES (?,?,?)',(mid,'material',m['name']))
        # Explicit curated equivalence; no automatic name-merging.
        if m['representative_node_id']:
            db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,context_product_id,notes) VALUES (?,?,?,?,?,?,?)',('ALIAS:'+m['material_id'],mid,'NODE:EYE:'+m['representative_node_id'],'processed_into','technological','PRODUCT:EYEWEAR','Curated material representative mapping'))
    for c in x['company']:
        eid='COMP:'+c['company_id']
        db.execute('INSERT INTO entity(entity_id,entity_type,name_zh,name_en) VALUES (?,?,?,?)',(eid,'company',c['name_zh'] or c['name_en'],c['name_en']))
        db.execute('INSERT INTO company(company_id,website,headquarters_country) VALUES (?,?,?)',(eid,c['official_website'],c['geo']))
    for m in x['market']:
        db.execute('INSERT INTO market(market_id,subject_entity_id,name_zh,geography,year,metric,denominator,unit,source_id) VALUES (?,?,?,?,?,?,?,?,?)',
        (m['market_id'],'MAT:'+m['material_id'],m['name'],m['geography'],m['year'],m['metric'],m['denominator_scope'],m['unit'],m['source_id']))
    for s in x['market_share']:
        db.execute('INSERT INTO market_share(market_id,competitor_id,label,share,rank,source_id) VALUES (?,?,?,?,?,?)',
                   (s['market_id'],'COMP:'+s['company_id'] if s['company_id'] else None,s['label'],s['share_pct'],s['rank'],s['source_id']))
    for r in x['procurement_concentration']:
        db.execute('INSERT INTO procurement_observation(observation_id,buyer_id,supplier_id,supplier_public_label,supplier_rank,year,share_of_purchase,disclosed,source_id,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',
        ('PROC:'+str(r['record_id']),'COMP:'+r['buyer_company_id'],None,r['supplier_public_name'],r['supplier_rank'],r['year'],r['share_of_buyer_procurement_pct'],int(r['supplier_identity_disclosed']),r['source_id'],'Buyer annual-report procurement ratio; unnamed supplier'))
    db.commit()
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
    issues=db.execute('PRAGMA foreign_key_check').fetchall()
    db.close()
    assert integrity=='ok' and not issues,(integrity,issues)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='dist');a=parser.parse_args()
    x=unpack_seed();stats=check_seed(x)
    dist=(ROOT/a.output).resolve();shutil.rmtree(dist,ignore_errors=True);shutil.copytree(ROOT/'web',dist)
    d=dist/'data';d.mkdir(parents=True,exist_ok=True)
    (d/'eyewear.json.gz').write_bytes(gzip.compress(json.dumps(compact(x),separators=(',',':'),ensure_ascii=False).encode('utf-8'),compresslevel=9,mtime=0))
    catalog={'version':1,'stats':{'nodes':stats['nodes'],'companies':stats['companies'],'sources':stats['sources']},'products':[{'slug':'eyewear','title':'眼镜','category':'光学与消费医疗','icon':'👓','description':'镜片、镜架、五金、功能镀膜、制造装备，以及直至石油、天然气和矿产的上游路径。','nodes':stats['nodes']}]}
    (d/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    (dist/'.nojekyll').write_text('',encoding='utf-8')
    add_sqlite(x,ROOT/'build'/'supply_chain.sqlite')
    print('BUILD_OK',json.dumps(stats,ensure_ascii=False), 'dist=',dist)
if __name__=='__main__':main()
