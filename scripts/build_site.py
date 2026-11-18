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

def compact(x,research=None,resolution=None):
    # Array encoding reduces Pages payload size; unpacked using a versioned field dictionary in frontend.
    return {
     'research':research or [],
     'identity':[[r['view_node_id'],r['canonical_material_entity_id'],r['identity_state'],r['label_key']] for r in (resolution or {}).get('view_nodes',[])],
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

def read_public_research(slug, node_ids):
    """Public curated research summary. Source full text stays in research ledger."""
    root=ROOT/'research'
    ledgers={}
    for path in sorted((root/'ledgers'/slug).glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        if data['node_id'] in ledgers:raise ValueError('Duplicate node research ledger')
        from research_cli import audit_ledger
        qa=audit_ledger(data)
        if not qa["structure_valid"]:
            raise ValueError("Invalid evidence ledger "+str(path)+": "+repr(qa["errors"]))
        ledgers[data["node_id"]]=data
    out=[]
    for path in sorted((root/'dossiers'/slug).glob('*.json')):
        doc=json.loads(path.read_text(encoding='utf-8'))
        from research_cli import audit_dossier
        qa=audit_dossier(doc)
        if not qa["structure_valid"]:
            raise ValueError("Invalid research dossier "+str(path)+": "+repr(qa["errors"]))
        node=doc["node_id"]
        if node not in node_ids:raise ValueError('Dossier node not in product: '+node)
        ledger=ledgers.get(node)
        if ledger is None:raise ValueError('Missing node evidence ledger: '+node)
        review=doc.get('semantic_review') or {}
        if doc.get('review_state')=='publishable' and not (
            review.get('status')=='approved' and review.get('reviewer') and review.get('reviewed_at')):
            raise ValueError('Unapproved publishable dossier: '+node)
        by_claim={c['id']:c for c in ledger['claims']}
        ids=doc.get('claim_ids',[])
        if not all(i in by_claim for i in ids):raise ValueError('Unmatched claim id: '+node)
        src_ids={e['source_id'] for cid in ids for e in by_claim[cid].get('evidence',[])}
        sources=[{k:s.get(k) for k in ('id','title','url','published_at')}
                 for s in ledger['sources'] if s['id'] in src_ids]
        if len(sources)!=len(src_ids):raise ValueError('Missing claim source: '+node)
        sections=doc.get('sections',{})
        out.append({'node_id':node,'name':doc['name'],'as_of':doc['as_of'],
          'review_state':doc.get('review_state','draft'),'semantic_review_status':review.get('status','pending'),
          'sections':{k:sections.get(k) for k in ('identity','technical','upstream','downstream','companies','market','risk','open_questions')},
          'claims':[{'id':cid,'text':by_claim[cid]['text'],'status':by_claim[cid]['status'],
                     'analysis':by_claim[cid].get('analysis',''),
                     'source_ids':list(dict.fromkeys(e['source_id'] for e in by_claim[cid].get('evidence',[])))}
                    for cid in ids],
          'sources':sources})
    return out

def discover_products(root=ROOT):
    categories=json.loads((root/'data'/'taxonomy'/'categories.json').read_text(encoding='utf-8'))['categories']
    known={x['id']:x['name'] for x in categories}
    products=[]
    for file in sorted((root/'data'/'products').glob('*/product.json')):
        meta=json.loads(file.read_text(encoding='utf-8'))
        if not meta.get('published',False): continue
        if meta.get('schema_version') != 1 or not meta['slug'].replace('-','').isalnum():
            raise ValueError('Invalid product metadata: '+str(file))
        if meta['slug']!=file.parent.name:
            raise ValueError('Product slug must match directory: '+str(file))
        if known.get(meta['category_id'])!=meta['category']:
            raise ValueError('Unknown taxonomy category or mismatched name: '+str(file))
        adapter=meta.get('adapter','atlas_v1')
        if adapter=='legacy_eyewear_v2':
            with gzip.open(file.parent/meta['source'],'rt',encoding='utf-8') as fh:x=json.load(fh)
        elif adapter=='atlas_v1':
            graph=json.loads((file.parent/meta['source']).read_text(encoding='utf-8'))
            x=convert_atlas_v1(graph)
        else:raise ValueError('Unknown adapter '+adapter)
        check_seed(x)
        products.append((meta,x))
    if not products:raise ValueError('At least one published product required')
    return products

def convert_atlas_v1(g):
    # Public schema uses human-readable objects; internal compatibility shape is the v2 dataset.
    x={k:[] for k in ('tree_node','material','company','company_material','company_relation','market','market_share','substitution_opportunity','source','procurement_concentration','capacity_observation','company_kpi')}
    for n in g.get('nodes',[]):
        x['tree_node'].append({'node_id':n['id'],'name':n['name'],'parent_id':n.get('parent'), 'kind':n.get('kind','材料'), 'branch':n.get('branch','未分类'), 'description':n.get('description',''), 'depth':0})
    by_id={n['node_id']:n for n in x['tree_node']}
    if len(by_id)!=len(x['tree_node']):raise ValueError('Duplicate node id')
    for n in x['tree_node']:
        seen={n['node_id']};parent=n['parent_id']
        while parent:
            if parent not in by_id or parent in seen:raise ValueError('Cycle or missing parent: '+n['node_id'])
            seen.add(parent);n['depth']+=1;parent=by_id[parent]['parent_id']
    if sum(n['parent_id'] is None for n in x['tree_node'])!=1:raise ValueError('Exactly one root required')
    for m in g.get('materials',[]):x['material'].append({'material_id':m['id'],'name':m['name'],'representative_node_id':m.get('node')})
    for c in g.get('companies',[]):x['company'].append({'company_id':c['id'],'name_zh':c.get('zh',''),'name_en':c.get('en',c.get('zh',c['id'])),'official_website':c.get('website'), 'geo':c.get('geo')})
    for c in g.get('company_material',[]):x['company_material'].append({'company_id':c['company'],'material_id':c['material'],'role':c.get('role','industry_participant'), 'source_id':c['source']})
    for r in g.get('company_relations',[]):x['company_relation'].append({'relation_id':r['id'],'upstream_company_id':r['upstream'],'downstream_company_id':r['downstream'],'material_id':r['material'],'relation_type':r.get('type','commercial_collaboration'),'source_id':r['source'],'scope_note':r.get('scope',''),'event_date':r.get('date')})
    for m in g.get('markets',[]):x['market'].append({'market_id':m['id'],'name':m['name'],'geography':m['geo'],'year':m['year'],'metric':m['metric'],'denominator_scope':m['denominator'],'material_id':m['material'],'unit':'%', 'source_id':m['source']})
    for s in g.get('shares',[]):x['market_share'].append({'market_id':s['market'],'company_id':s.get('company'),'label':s['label'],'share_pct':s.get('pct'),'rank':s.get('rank'),'source_id':s['source']})
    for src in g.get('sources',[]):x['source'].append({'source_id':src['id'],'title':src['title'],'url':src['url'],'type':src.get('type','官网/研究'),'checked_on':src.get('checked_on','')})
    for i,o in enumerate(g.get('opportunities',[])):x['substitution_opportunity'].append({'opportunity_id':i+1,'material_id':o['material'],'china_candidate_company_id':o.get('candidate'),'benchmark_company_id':o.get('benchmark'),'topic':o['topic'],'validation_gap':o.get('gap',''),'source_id':o['source']})
    return x

def reverse_catalog(products):
    material_to_products={};company_to_materials={};seen_materials={};seen_companies={}
    for meta,x in products:
        slug=meta['slug']
        for m in x['material']:
            mid=m['material_id']
            if mid in seen_materials and seen_materials[mid]!=m['name']:
                raise ValueError('Conflicting canonical material name for '+mid)
            seen_materials[mid]=m['name']
            material_to_products.setdefault(mid,[])
            if slug not in material_to_products[mid]:material_to_products[mid].append(slug)
        for c in x['company']:
            cid=c['company_id'];name=c['name_en']
            if cid in seen_companies and seen_companies[cid]!=name:raise ValueError('Conflicting company id '+cid)
            seen_companies[cid]=name
        for cm in x['company_material']:
            arr=company_to_materials.setdefault(cm['company_id'],[])
            if cm['material_id'] not in arr:arr.append(cm['material_id'])
    return {'version':1,'material_to_products':material_to_products,'company_to_materials':company_to_materials}

def add_sqlite(x,out):
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():out.unlink()
    db=sqlite3.connect(out)
    for migration in sorted((ROOT/'schema').glob('*.sql')):
        db.executescript(migration.read_text(encoding='utf-8'))
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
            db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,context_product_id,notes) VALUES (?,?,?,?,?,?,?)',('ALIAS:'+m['material_id'],mid,'NODE:EYE:'+m['representative_node_id'],'associated_with','technological','PRODUCT:EYEWEAR','Legacy contextual material linkage; NOT a verified identity or purchase'))
    for c in x['company']:
        eid='COMP:'+c['company_id']
        db.execute('INSERT INTO entity(entity_id,entity_type,name_zh,name_en) VALUES (?,?,?,?)',(eid,'company',c['name_zh'] or c['name_en'],c['name_en']))
        db.execute('INSERT INTO company(company_id,website,headquarters_country) VALUES (?,?,?)',(eid,c['official_website'],c['geo']))
    for row in x['company_material']:
        role=row['role']
        edge_type='manufactures' if role in ('manufacturer','lens_maker','optic_grade_product_family') else 'associated_with'
        eid='CM:'+row['company_id']+':'+row['material_id']
        db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,notes) VALUES (?,?,?,?,?,?)',
                   (eid,'COMP:'+row['company_id'],'MAT:'+row['material_id'],edge_type,'verified','Related business category: '+role+'; not evidence of procurement by eyewear brand'))
        if row['source_id'] in source_ids:
            db.execute('INSERT INTO edge_source(edge_id,source_id,assessment) VALUES (?,?,?)',(eid,row['source_id'],'product or industry relationship, not a customer contract'))
    relationship_types={'announced_supply':'supplied_to','announced_sourcing':'announced_sourcing',
        'commercial_collaboration':'commercial_collaboration','joint_development':'joint_development',
        'confirmed_collection_material':'confirmed_material_adoption','joint_research_production':'joint_research_production'}
    for row in x['company_relation']:
        eid='REL:'+str(row['relation_id'])
        db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,valid_from,notes) VALUES (?,?,?,?,?,?,?)',
                   (eid,'COMP:'+row['upstream_company_id'],'COMP:'+row['downstream_company_id'],relationship_types[row['relation_type']],
                    'verified',row['event_date'],row['scope_note']))
        db.execute('INSERT INTO edge_source(edge_id,source_id,assessment) VALUES (?,?,?)',
                   (eid,row['source_id'],'historical publicly disclosed event; not proof of present-day purchasing'))
    for row in x['capacity_observation']:
        db.execute('INSERT INTO capacity(observation_id,entity_id,company_id,year,value,unit,metric,scope,source_id,notes) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   ('CAP:'+str(row['capacity_id']),'MAT:'+row['material_id'],
                    'COMP:'+row['company_id'] if row['company_id'] else None,row['year'],row['value'],row['unit'],
                    row['measurement'],row['geography'] or 'unknown',row['source_id'],row['note']))
    for row in x['company_kpi']:
        db.execute('INSERT INTO company_kpi(observation_id,company_id,year,metric,value,unit,source_id,notes) VALUES (?,?,?,?,?,?,?,?)',
                   ('KPI:'+str(row['kpi_id']),'COMP:'+row['company_id'],row['year'],row['metric'],row['value'],row['unit'],row['source_id'],row['note']))
    for row in x['substitution_opportunity']:
        db.execute('INSERT INTO substitution_candidate(candidate_id,target_entity_id,candidate_company_id,incumbent_company_id,status,validation_gap,source_id) VALUES (?,?,?,?,?,?,?)',
                   ('SUB:'+str(row['opportunity_id']),'MAT:'+row['material_id'],
                    'COMP:'+row['china_candidate_company_id'] if row['china_candidate_company_id'] else None,
                    'COMP:'+row['benchmark_company_id'] if row['benchmark_company_id'] else None,
                    'idea',row['validation_gap'],row['source_id']))
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

def add_additional_products(products,out):
    """Attach v1 products to the shared material/company graph without duplicating canonical IDs."""
    db=sqlite3.connect(out);db.execute('PRAGMA foreign_keys=ON')
    for meta,x in products:
        slug=meta['slug']
        if slug=='eyewear':continue
        product_id='PRODUCT:'+slug.upper().replace('-','_')
        cat='CAT:'+meta['category_id']
        db.execute('INSERT OR IGNORE INTO category(category_id,name_zh,icon) VALUES (?,?,?)',(cat,meta['category'],meta['icon']))
        db.execute('INSERT INTO entity(entity_id,entity_type,name_zh) VALUES (?,?,?)',(product_id,'product',meta['title']))
        db.execute('INSERT INTO product(product_id,slug,category_id,summary,icon,published) VALUES (?,?,?,?,?,?)',(product_id,slug,cat,meta['description'],meta['icon'],1))
        sources={}
        for src in x['source']:
            dbid='SRC:'+slug+':'+src['source_id'];sources[src['source_id']]=dbid
            db.execute('INSERT INTO source(source_id,title,url,source_type,accessed_on) VALUES (?,?,?,?,?)',
                       (dbid,src['title'],src['url'],src.get('type','公开资料'),src.get('checked_on','')))
        def material_id(local):return 'MAT:'+local
        def company_id(local):return 'COMP:'+local
        def node_id(local):return 'NODE:'+slug+':'+local
        for n in x['tree_node']:
            db.execute('INSERT INTO entity(entity_id,entity_type,name_zh,description) VALUES (?,?,?,?)',
                       (node_id(n['node_id']),'component' if n['parent_id'] else 'product',n['name'],n.get('description')))
        for n in x['tree_node']:
            db.execute('INSERT INTO product_view_node(product_id,view_node_id,entity_id,parent_view_node_id,display_depth,display_label) VALUES (?,?,?,?,?,?)',
                       (product_id,n['node_id'],node_id(n['node_id']),n['parent_id'],n['depth'],n['name']))
            if n['parent_id']:
                db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,context_product_id) VALUES (?,?,?,?,?,?)',
                           ('EDGE:'+slug+':'+n['node_id'],node_id(n['node_id']),node_id(n['parent_id']),'material_input','technological',product_id))
            else:
                db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,context_product_id) VALUES (?,?,?,?,?,?)',
                           ('ROOT:'+slug,node_id(n['node_id']),product_id,'component_of','technological',product_id))
        for m in x['material']:
            mid=material_id(m['material_id'])
            old=db.execute('SELECT name_zh FROM entity WHERE entity_id=?',(mid,)).fetchone()
            if old:
                if old[0]!=m['name']:raise ValueError('Material ID collision for '+mid)
            else:db.execute('INSERT INTO entity(entity_id,entity_type,name_zh) VALUES (?,?,?)',(mid,'material',m['name']))
            if m['representative_node_id']:
                db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,context_product_id) VALUES (?,?,?,?,?,?)',
                           ('ALIAS:'+slug+':'+m['material_id'],mid,node_id(m['representative_node_id']),'processed_into','technological',product_id))
        for c in x['company']:
            cid=company_id(c['company_id'])
            old=db.execute('SELECT name_en FROM entity WHERE entity_id=?',(cid,)).fetchone()
            if old:
                if old[0]!=c['name_en']:raise ValueError('Company ID collision for '+cid)
            else:
                db.execute('INSERT INTO entity(entity_id,entity_type,name_zh,name_en) VALUES (?,?,?,?)',
                           (cid,'company',c['name_zh'] or c['name_en'],c['name_en']))
                db.execute('INSERT INTO company(company_id,website,headquarters_country) VALUES (?,?,?)',
                           (cid,c['official_website'],c['geo']))
        for cm in x['company_material']:
            edgeid='CM:'+slug+':'+cm['company_id']+':'+cm['material_id']
            db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,notes) VALUES (?,?,?,?,?,?)',
                       (edgeid,company_id(cm['company_id']),material_id(cm['material_id']),'associated_with','verified',cm['role']+'; NOT a purchasing contract'))
            if cm['source_id'] in sources:
                db.execute('INSERT INTO edge_source(edge_id,source_id) VALUES (?,?)',(edgeid,sources[cm['source_id']]))
        for row in x['company_relation']:
            kind={'announced_supply':'supplied_to','announced_sourcing':'announced_sourcing',
                  'commercial_collaboration':'commercial_collaboration','joint_development':'joint_development',
                  'joint_research_production':'joint_research_production','confirmed_collection_material':'confirmed_material_adoption'}[row['relation_type']]
            edgeid='REL:'+slug+':'+str(row['relation_id'])
            db.execute('INSERT INTO edge(edge_id,upstream_id,downstream_id,relation_type,evidence_status,valid_from,notes) VALUES (?,?,?,?,?,?,?)',
                       (edgeid,company_id(row['upstream_company_id']),company_id(row['downstream_company_id']),kind,'verified',row['event_date'],row['scope_note']))
            db.execute('INSERT INTO edge_source(edge_id,source_id) VALUES (?,?)',(edgeid,sources[row['source_id']]))
        for m in x['market']:
            mk='MARKET:'+slug+':'+m['market_id']
            db.execute('INSERT INTO market(market_id,subject_entity_id,name_zh,geography,year,metric,denominator,unit,source_id) VALUES (?,?,?,?,?,?,?,?,?)',
                       (mk,material_id(m['material_id']),m['name'],m['geography'],m['year'],m['metric'],m['denominator_scope'],m['unit'],sources[m['source_id']]))
        for ms in x['market_share']:
            db.execute('INSERT INTO market_share(market_id,competitor_id,label,share,rank,source_id) VALUES (?,?,?,?,?,?)',
                       ('MARKET:'+slug+':'+ms['market_id'],company_id(ms['company_id']) if ms['company_id'] else None,
                        ms['label'],ms['share_pct'],ms['rank'],sources[ms['source_id']]))
    db.commit()
    check=db.execute('PRAGMA foreign_key_check').fetchall()
    db.close()
    if check:raise ValueError('Foreign key errors: '+repr(check))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='dist');a=parser.parse_args()
    products=discover_products()
    from normalize_eyewear import resolve as resolve_eyewear,persist as persist_eyewear
    eyeseed=next((x for m,x in products if m['slug']=='eyewear'),None)
    identity=resolve_eyewear(eyeseed) if eyeseed is not None else None
    reverse=reverse_catalog(products)
    dist=(ROOT/a.output).resolve();shutil.rmtree(dist,ignore_errors=True);shutil.copytree(ROOT/'web',dist)
    d=dist/'data';d.mkdir(parents=True,exist_ok=True)
    catalog={'version':1,'stats':{'nodes':sum(len(x['tree_node']) for _,x in products),'companies':len({c['company_id'] for _,x in products for c in x['company']}),'sources':sum(len(x['source']) for _,x in products)},'products':[]}
    for meta,x in products:
        slug=meta['slug']
        research=read_public_research(slug,{n['node_id'] for n in x['tree_node']})
        (d/(slug+'.json.gz')).write_bytes(gzip.compress(json.dumps(compact(x,research,identity if slug=='eyewear' else None),separators=(',',':'),ensure_ascii=False).encode('utf-8'),compresslevel=9,mtime=0))
        catalog['products'].append({'slug':slug,'title':meta['title'],'category':meta['category'],'icon':meta['icon'],'description':meta['description'],'nodes':len(x['tree_node']),'research_dossiers':len(research)})
    (d/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    (d/'reverse_index.json').write_text(json.dumps(reverse,ensure_ascii=False,indent=2),encoding='utf-8')
    if identity is not None:
        (d/'eyewear_identity.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2),encoding='utf-8')
        catalog['stats']['curated_eyewear_identities']=identity['summary']['curated_exact_links']
        catalog['stats']['unresolved_eyewear_nodes']=identity['summary']['provisional_nodes']
        (d/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    if eyeseed is not None:
        from build_priority import prioritize, load_dossiers
        priority=prioritize(eyeseed,load_dossiers())
        (d/'eyewear_priority.json').write_text(json.dumps(priority,ensure_ascii=False,indent=2),encoding='utf-8')
        catalog['stats']['eyewear_dossiers']=priority['nodes_with_dossiers']
        (d/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    (dist/'.nojekyll').write_text('',encoding='utf-8')
    eyewear=next((x for m,x in products if m['slug']=='eyewear'),None)
    if eyewear is not None:
        add_sqlite(eyewear,ROOT/'build'/'supply_chain.sqlite')
        persist_eyewear(ROOT/'build'/'supply_chain.sqlite',identity)
        add_additional_products(products,ROOT/'build'/'supply_chain.sqlite')
        from ingest_research import ingest
        ingest(ROOT/'build'/'supply_chain.sqlite')
    else:
        raise ValueError('First-version database importer currently requires the eyewear seed')
    print('BUILD_OK',json.dumps(catalog['stats'],ensure_ascii=False),'products=',len(products),'dist=',dist)
if __name__=='__main__':main()
