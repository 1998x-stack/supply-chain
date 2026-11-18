'use strict';
/*
 * Evidence-aware universal node inspector.
 * A tree node is a projection; neither a material alias nor a company
 * product listing proves a contractual supplier/customer relationship.
 */
window.SupplyNodePanel=(()=>{
 const e=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const link=url=>/^https:\/\//i.test(String(url||''))?e(url):'#';
 const TABS=[['summary','总览'],['technical','技术与原料'],['market','市场与企业'],['trace','上下游'],['evidence','原始证据'],['gaps','风险与待办']];
 function empty(text){return '<div class="sc-empty">'+e(text)+'</div>';}
 function badge(text,tone='muted'){return '<span class="sc-badge '+e(tone)+'">'+e(text)+'</span>';}
 function tagSource(id){return id?'<span class="sc-source-id">'+e(id)+'</span>':'';}
 function sources(insight,dossier,data){
  const ids=new Set([...(insight?.source_ids||[])]);
  for(const v of [...(insight?.facts||[]),...(insight?.metrics||[])])if(v.source_id)ids.add(v.source_id);
  const own=(data.src||[]).filter(v=>ids.has(v.id)).map(v=>({id:v.id,title:v.title,url:v.url,publisher:'研究来源'}));
  const fromDossier=(dossier?.sources||[]);
  const merged=new Map([...own,...fromDossier].map(v=>[v.id,v]));
  return [...merged.values()];
 }
 function facts(insight){return [...(insight?.facts||[]),...(insight?.metrics||[])];}
 function factCards(rows){
  if(!rows.length)return empty('暂无可公开核实的量化指标。待补充同口径来源与测试条件。');
  return '<div class="sc-kpi-grid">'+rows.map(x=>'<article class="sc-kpi"><span class="sc-kpi-label">'+e(x.label)+'</span><strong>'+e(x.value)+ (x.unit?' <small>'+e(x.unit)+'</small>':'')+'</strong><div class="sc-kpi-meta">'+e(x.period||x.condition||x.scope||'')+'</div>'+tagSource(x.source_id)+'</article>').join('')+'</div>';
 }
 function renderValues(value){
  if(value==null||value===''||(Array.isArray(value)&&!value.length))return empty('该维度暂无已整理数据。');
  if(Array.isArray(value))return '<div class="sc-record-list">'+value.map(v=>'<div class="sc-record">'+renderValues(v)+'</div>').join('')+'</div>';
  if(typeof value==='object')return '<dl class="sc-dl">'+Object.entries(value).map(([key,v])=>'<div class="sc-dl-row"><dt>'+e(key.replace(/_/g,' '))+'</dt><dd>'+((v&&typeof v==='object')?renderValues(v):e(v))+'</dd></div>').join('')+'</dl>';
  return '<p class="sc-value">'+e(value)+'</p>';
 }
 function panelHeader(ctx){
  const {node,product,identity,dossier,insight}=ctx;
  const approved=dossier?.review_state==='publishable'&&dossier?.semantic_review_status==='approved';
  const hasResearch=Boolean(dossier||insight);
  const scope=product.spec.slug==='henkel-adhesives'?'企业产品组合视图':'产品技术视图';
  return '<header class="sc-header"><div class="sc-eyebrow">NODE / '+e(product.spec.slug)+' / '+e(node.id)+'</div><h2>'+e(node.name)+'</h2><div class="sc-header-pills">'+badge(node.kind||'未分类')+badge(node.branch||scope)+badge(approved?'已审核可发布':hasResearch?'研究草稿 · 待复核':'尚未研究',approved?'good':hasResearch?'draft':'muted')+'</div><p>'+e(node.description||'仅有供应链结构节点，尚无充分研究证据。')+'</p><div class="sc-status"><span>实体身份：</span><code>'+e(identity?.canonical||('NODE:'+product.spec.slug+':'+node.id))+'</code><span>'+e(identity?.state==='curated_exact'?'严格映射':'本产品上下文节点')+'</span></div><p class="sc-warn">技术分类与可能原料 ≠ 已确认采购。品牌、配方和工艺不能按名称推断实际合同。</p></header>';
 }
 function renderSummary(ctx){
  const {insight,dossier,node,product}=ctx;
  const allFacts=facts(insight);
  const summary= allFacts.length ? factCards(allFacts):dossier?.sections?.technical?.properties?.length?
     factCards(dossier.sections.technical.properties.map(x=>({label:x.attribute,value:x.value,unit:x.unit,source_id:x.source_id,condition:x.test_condition||x.grade}))):empty('暂未整理量化指标或同条件物性。');
  const claims=[...(insight?.claims||[]),...(dossier?.claims||[])];
  return '<section><h3>关键指标与来源</h3>'+summary+'</section><section><h3>研究结论</h3>'+
    (claims.length?claims.map(c=>'<article class="sc-claim"><div>'+badge(c.status||'待复核','draft')+' '+(c.source_ids||[]).map(tagSource).join(' ')+'</div><p>'+e(c.text)+'</p></article>').join(''):empty('尚无成文的原子论断；请从一手来源开始研究。'))+
    '</section><section><h3>覆盖与限制</h3><div class="sc-record"><b>关联内容</b><p>该节点属于 '+e(product.spec.title)+' 的技术/业务视图；图谱边可能是材料、分类、设备或行业应用关系。</p><p>源数据状态：'+e(insight?.review_status||dossier?.review_state||'unreviewed')+'。机器结构校验不代表事实已完成语义审核。</p></div></section>';
 }
 function renderTechnical(ctx){
  const {insight,dossier,node}=ctx;
  const sec=dossier?.sections||{};
  const upstream=sec.upstream||[],downstream=sec.downstream||[];
  return '<section><h3>技术参数 / 测试条件</h3>'+factCards(facts(insight))+
     (sec.technical?'<h4>节点技术研究</h4>'+renderValues(sec.technical):'')+
     (sec.identity?'<h4>牌号、身份与标准</h4>'+renderValues(sec.identity):'')+'</section>'+
     '<section><h3>工艺投入与应用</h3><p class="sc-note">此处是技术类属或工艺候选，不是企业采购清单。</p>'+
     (upstream.length?'<h4>研究报告记录的投入</h4>'+renderValues(upstream):'')+
     (downstream.length?'<h4>研究报告记录的用途</h4>'+renderValues(downstream):empty('暂无独立验证的原料配方或技术投入清单。'))+'</section>';
 }
 function renderMarket(ctx){
  const {data,matIds,dossier,insight}=ctx;
  const markets=(data.mk||[]).filter(x=>matIds.has(x.material));
  const companyRefs=(data.cm||[]).filter(x=>matIds.has(x.material));
  const sourcesById=new Map((data.src||[]).map(x=>[x.id,x]));
  let out='<section><h3>市场统计与可比口径</h3>';
  if(markets.length)out+=markets.map(m=>'<article class="sc-record"><h4>'+e(m.name)+'</h4><p>区域：'+e(m.geo)+' · 期间：'+e(m.year)+'</p><p>指标：'+e(m.metric)+'</p><p>统计分母：'+e(m.scope)+'</p>'+data.s.filter(s=>s.market===m.id&&s.pct!==null&&s.pct!==undefined&&Number.isFinite(Number(s.pct))).map(s=>'<div class="sc-market"><span>'+e(s.label)+'</span><strong>'+e(s.pct)+'%</strong></div>').join('')+'</article>').join('');
  else out+=empty('没有可核实的同口径市场份额 TOP3；不从部门销售额或原料产能推算。');
  if(dossier?.sections?.market?.length)out+='<h4>研究档案中的原始统计观察</h4>'+renderValues(dossier.sections.market);
  if((insight?.metrics||[]).length)out+='<h4>其他数值（非市场份额）</h4>'+factCards(insight.metrics);
  out+='</section><section><h3>相关企业及角色</h3><p class="sc-note">公司经营材料/技术，不代表其向指定厂商实际供货。</p>';
  if(companyRefs.length)out+=companyRefs.map(cm=>{
    const company=(data.c||[]).find(c=>c.id===cm.company);
    return '<article class="sc-record"><b><a href="#" data-company="'+e(cm.company)+'">'+e(company?.zh||company?.en||cm.company)+'</a></b><p>'+e(cm.role)+'</p></article>';
  }).join('');
  else out+=empty('本节点暂无可核验企业关联。');
  if(dossier?.sections?.companies?.length)out+='<h4>档案中的企业调查</h4>'+renderValues(dossier.sections.companies);
  return out+'</section>';
 }
 function renderTrace(ctx){
  const {product,node,data,reverse,catalog,matIds}=ctx;
  const cross=(data.xl||[]).filter(x=>x.from===node.id||x.to===node.id);
  const children=(product.children.get(node.id)||[]);
  const ancestor=[];let id=node.parent;while(id&&ancestor.length<25){const item=product.byId.get(id);if(!item)break;ancestor.push(item);id=item.parent;}
  const branch=(title,list)=>'<section><h3>'+title+'</h3>'+(list.length?
    list.map(n=>'<a href="#" class="sc-trace-link" data-node="'+e(n.id)+'"><span>'+e(n.name)+'</span><small>'+e(n.relationType||'关联')+'</small></a>').join(''):empty('无更多可见关联'))+'</section>';
  const all=new Set([product.spec.slug]);for(const mid of matIds)
    for(const slug of (reverse?.material_to_products?.[mid]||[]))all.add(slug);
  const products=[...all].map(slug=>catalog.products.find(p=>p.slug===slug)).filter(Boolean);
  const connections=cross.length?'<section><h3>跨分支材料与技术关联</h3>'+
    cross.map(x=>{const other=product.byId.get(x.from===node.id?x.to:x.from);
      return '<div class="sc-record"><a href="#" data-node="'+e(other?.id)+'">'+e(other?.name||'关联节点')+' ↗</a>'+
        '<div class="sc-header-pills">'+badge(x.type)+badge(x.status,x.status==='hypothesis'?'draft':'muted')+'</div>'+
        '<p>'+e(x.note||'')+'</p>'+(x.source?'<small>来源：'+e(x.source)+'</small>':'<small>尚未独立验证</small>')+'</div>';
    }).join('')+'</section>':'';
  return '<div class="sc-explain">边的类型决定含义：分类≠原料，原料≠企业采购，行业应用≠指定客户订单。</div>'+
    connections+branch('下一层节点（仅按树状图）',children)+branch('向成品/业务入口回溯',ancestor)+
    '<section><h3>跨产品反向查询</h3>'+products.map(p=>'<a class="sc-trace-link" href="#/products/'+e(p.slug)+'"><span>'+e(p.icon)+' '+e(p.title)+'</span><small>技术关联</small></a>').join('')+'</section>';
 }
 function renderEvidence(ctx){
  const {insight,dossier,data}=ctx, refs=sources(insight,dossier,data);
  const claims=[...(insight?.claims||[]),...(dossier?.claims||[])];
  let out='<section><h3>原子论断</h3>'+(claims.length?claims.map(c=>'<div class="sc-claim"><div>'+badge(c.status||'pending','draft')+(c.source_ids||[]).map(tagSource).join(' ')+'</div><p>'+e(c.text)+'</p><small>'+e(c.analysis||'')+'</small></div>').join(''):empty('尚无证据论断'))+'</section>';
  out+='<section><h3>原始来源与位置</h3><p class="sc-note">查看厂商原文/TDS。多个汉高官网页面不是相互独立的市场验证来源。</p>';
  out+=refs.length?refs.map(s=>'<article class="sc-source"><div class="sc-source-top">'+tagSource(s.id)+badge(s.published_at||'日期未录入')+'</div><a href="'+link(s.url)+'" rel="noopener noreferrer" target="_blank">'+e(s.title||s.url)+' ↗</a><small>'+e(s.publisher||'官方或公开资料')+'</small></article>').join(''):empty('暂无附着在本节点的独立来源');
  return out+'</section>';
 }
 function renderGaps(ctx){
  const {insight,dossier}=ctx;
  const gaps=[...(insight?.gaps||[]),...(dossier?.sections?.open_questions||[])];
  const risks=dossier?.sections?.risk||[];
  return '<section><h3>下一轮 Deep Search 任务</h3>'+(gaps.length?gaps.map((g,i)=>'<article class="sc-task"><b>P'+(i<3?'0':'1')+'</b><span>'+e(g)+'</span></article>').join(''):empty('未研究的节点应先建立身份、工艺与市场分母的问题清单。'))+'</section>'+
    '<section><h3>风险、冲突与不确定性</h3>'+(risks.length?renderValues(risks):empty('不代表无风险；只是尚未做专门的供应链风险研究。'))+'</section>';
 }
 function render(ctx){
  const {node,product}=ctx,data=product.data;
  const identity=(data.identity||[]).find(r=>r.id===node.id);
  const matches=identity?.canonical?(data.m||[]).filter(m=>'MAT:'+m.id===identity.canonical):
    (product.spec.slug!=='eyewear'?(data.m||[]).filter(m=>m.node===node.id):[]);
  const dossier=(data.research||[]).find(v=>v.node_id===node.id);
  const insight=(data.insights||[]).find(v=>v.node_id===node.id);
  const state={...ctx,data,identity,dossier,insight,matIds:new Set(matches.map(x=>x.id))};
  const tabs=TABS.map(([id,name],i)=>'<button class="sc-tab'+(i===0?' is-active':'')+'" data-sc-tab="'+id+'" role="tab" aria-selected="'+(i===0?'true':'false')+'">'+name+'</button>').join('');
  const sections={summary:renderSummary,technical:renderTechnical,market:renderMarket,trace:renderTrace,evidence:renderEvidence,gaps:renderGaps};
  const html=panelHeader(state)+'<nav class="sc-tabs" role="tablist" aria-label="节点研究内容">'+tabs+'</nav>'+
    Object.entries(sections).map(([id,fn])=>'<div class="sc-tabpane" data-sc-panel="'+id+'" '+(id!=='summary'?'hidden':'')+'>'+fn(state)+'</div>').join('')+
    '<footer class="sc-footer">数据快照 · '+e(insight?.updated_at||dossier?.as_of||'未记录')+' · 引用可打开原始来源。缺失项不补造数值。</footer>';
  return html;
 }
 function bind(root,actions){
  root.addEventListener('click',event=>{
   const tab=event.target.closest('[data-sc-tab]');
   if(tab){const id=tab.getAttribute('data-sc-tab');root.querySelectorAll('[data-sc-tab]').forEach(b=>{const active=b.getAttribute('data-sc-tab')===id;b.classList.toggle('is-active',active);b.setAttribute('aria-selected',active?'true':'false')});root.querySelectorAll('[data-sc-panel]').forEach(p=>p.hidden=p.getAttribute('data-sc-panel')!==id);return;}
   const hit=event.target.closest('[data-node],[data-company]');
   if(hit){event.preventDefault();if(hit.dataset.node)actions.onNode(hit.dataset.node);else if(hit.dataset.company)actions.onCompany(hit.dataset.company);}
  });
 }
 return {render,bind};
})();