'use strict';
/*
 * Evidence-aware universal node inspector.
 * A tree node is a projection; neither a material alias nor a company
 * product listing proves a contractual supplier/customer relationship.
 */
window.SupplyNodePanel=(()=>{
 const e=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const link=url=>/^https:\/\//i.test(String(url||''))?e(url):'#';
 const TABS=[['summary','总览'],['technical','技术与原料'],['market','市场与企业'],['trace','上下游'],['evidence','原始证据'],['gaps','研究任务']];
 const STAGE_LABELS={reviewed:'语义审核完成',dossier_pending:'有深度档案 · 待复核',source_note:'已有来源记录 · 待深研',annotated:'已有研究笔记 · 待取证',structural_only:'结构资料 · 待深研'};
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
  return '<div class="sc-kpi-grid">'+rows.map(x=>'<article class="sc-kpi"><span class="sc-kpi-label">'+e(x.label)+'</span><strong>'+e(x.value)+ (x.unit?' <small>'+e(x.unit)+'</small>':'')+'</strong><div class="sc-kpi-meta">'+e([x.period,x.scope,x.condition].filter(Boolean).join(' · '))+'</div>'+tagSource(x.source_id)+'</article>').join('')+'</div>';
 }
 function renderValues(value){
  if(value==null||value===''||(Array.isArray(value)&&!value.length))return empty('该维度暂无已整理数据。');
  if(Array.isArray(value))return '<div class="sc-record-list">'+value.map(v=>'<div class="sc-record">'+renderValues(v)+'</div>').join('')+'</div>';
  if(typeof value==='object')return '<dl class="sc-dl">'+Object.entries(value).map(([key,v])=>'<div class="sc-dl-row"><dt>'+e(key.replace(/_/g,' '))+'</dt><dd>'+((v&&typeof v==='object')?renderValues(v):e(v))+'</dd></div>').join('')+'</dl>';
  return '<p class="sc-value">'+e(value)+'</p>';
 }
 function panelHeader(ctx){
  const {node,product,identity,dossier,insight,coverage}=ctx;
  const approved=coverage?.stage==='reviewed';
  const scope=product.spec.slug==='henkel-adhesives'?'企业产品组合视图':'产品技术视图';
  const stage=coverage?.facet==='navigation'?'目录/分组节点':STAGE_LABELS[coverage?.stage]||'结构资料 · 待深研';
  const priority=coverage?.priority;
  return '<header class="sc-header"><div class="sc-eyebrow">NODE / '+e(product.spec.slug)+' / '+e(node.id)+'</div><h2>'+e(node.name)+'</h2><div class="sc-header-pills">'+
    badge(node.kind||'未分类')+badge(node.branch||scope)+badge(stage,approved?'good':coverage?.stage==='dossier_pending'?'draft':'muted')+
    (priority&&priority!=='NAV'?badge('研究优先级 '+priority):'')+'</div>'+
    '<p>'+e(node.description||'此节点目前只有供应链位置与名称，需要原始资料支持独立技术结论。')+'</p>'+
    '<div class="sc-status"><span>实体身份：</span><code>'+e(identity?.canonical||('NODE:'+product.spec.slug+':'+node.id))+
    '</code><span>'+e(identity?.state==='curated_exact'?'严格材料身份映射':'产品视图中的独立节点')+'</span></div>'+
    '<div class="sc-status"><span>当前节点</span><b>'+e(coverage?.claims||0)+'</b>条原子论断 · <b>'+e(coverage?.sources||0)+'</b>条来源引用 · <b>'+e(coverage?.children||0)+'</b>个下一层节点</div>'+
    '<p class="sc-warn">结构已建立不等于研究完成。技术关联≠真实采购，厂商产品宣传≠独立市场核验。</p></header>';
 }
 function renderSummary(ctx){
  const {insight,dossier,node,product,coverage}=ctx;
  const allFacts=facts(insight);
  const summary=allFacts.length?factCards(allFacts):dossier?.sections?.technical?.properties?.length?
    factCards(dossier.sections.technical.properties.map(x=>({label:x.attribute,value:x.value,unit:x.unit,source_id:x.source_id,condition:x.test_condition||x.grade}))):
    empty('当前节点没有可附带完整来源、单位和口径的量化事实；不自动推算市场份额。');
  const claims=[...(insight?.claims||[]),...(dossier?.claims||[])];
  const path=coverage?.path||[node.name];
  const structural='<section><h3>已建立的产业链结构信息</h3><article class="sc-record"><b>产品内路径</b><p>'+e(path.join(' / '))+'</p>'+
    '<p>节点类型：'+e(coverage?.facet||node.kind||'未分类')+' · 技术树分支：'+e(node.branch||'')+' · 下级节点：'+e(coverage?.children||0)+'</p>'+
    '<p class="sc-note">来自供应链结构数据；可帮助导航，但不作为已验证的技术/市场事实计入档案。</p></article></section>';
  return structural+'<section><h3>技术指标与独立来源</h3>'+summary+'</section>'+
    '<section><h3>已经记录的论断</h3>'+
    (claims.length?claims.map(c=>'<article class="sc-claim"><div>'+badge(c.status||'待复核','draft')+' '+(c.source_ids||[]).map(tagSource).join(' ')+'</div><p>'+e(c.text)+'</p></article>').join(''):
      empty('尚未形成带原始来源的原子论断。请查看“研究任务”标签生成下一轮Deep Search计划。'))+'</section>'+
    '<section><h3>证据审查状态</h3><article class="sc-record"><p>研究状态：'+
    e(STAGE_LABELS[coverage?.stage]||'待深研')+'。资料独立性和具体企业采购合同仍需逐项核实。</p>'+
    '<p>当前档案数：'+e(dossier?1:0)+'；来源记录：'+e(coverage?.sources||0)+
    '。节点说明、上下游和类别只代表结构信息。</p></article></section>';
 }
 function renderTechnical(ctx){
  const {insight,dossier,node}=ctx;
  const sec=dossier?.sections||{};
  const upstream=sec.upstream||[],downstream=sec.downstream||[];
  return '<section><h3>技术参数 / 测试条件</h3>'+factCards(insight?.facts||[])+
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
  const {insight,dossier,coverage,node,product}=ctx;
  const risks=dossier?.sections?.risk||[];
  const custom=[...(insight?.gaps||[]),...(dossier?.sections?.open_questions||[])];
  const gaps=[...new Set([...custom,...(coverage?.questions||[])].filter(Boolean))];
  const priority=coverage?.priority||'P2';
  const isNav=coverage?.facet==='navigation';
  const prompt=['你是供应链产业研究Agent。研究以下节点，必须打开原始来源并做反证核验。',
    '产品：'+product.spec.title+' ('+product.spec.slug+')',
    '节点：'+node.name+' ['+node.id+']',
    '产业链位置：'+(coverage?.path||[]).join(' > '),
    '现有证据等级：'+(coverage?.stage||'structural_only'),
    '研究优先级：'+priority,
    '调查问题：',...gaps.map((q,i)=>(i+1)+'. '+q),
    '交付：逐来源证据台账、身份/技术/上游/下游/公司/市场/风险八维档案。',
    '严格保留年份、地区、单位、分母、牌号、测试条件和来源，区分商业采购与技术关系。',
    '禁止编造市场TOP3、企业采购合同和报告原文。未知项写UNKNOWN。'].join('\n');
  const tasks=isNav?empty('这是产品导航/分类节点；无需为每个目录项单独调查供应商，请深入具体材料、牌号或工艺节点。'):
    gaps.length?gaps.map((g)=>'<article class="sc-task">'+badge(priority,'draft')+'<span>'+e(g)+'</span></article>').join(''):
      empty('暂无优先问题，先验证节点身份和原始来源。');
  return '<section><h3>可执行研究计划</h3>'+tasks+'</section>'+
    (isNav?'':'<section><h3>交给本地 Codex / Pi / Claude</h3><p class="sc-note">以下是待执行的Deep Search任务，不代表已联网检索或完成调查。</p>'+
      '<details class="sc-research-prompt"><summary>展开研究指令</summary><pre class="sc-task-text">'+e(prompt)+'</pre>'+
      '<button type="button" class="sc-copy-task" data-sc-copy-task>复制研究指令</button></details></section>')+
    '<section><h3>已记录风险与分歧</h3>'+
      (risks.length?renderValues(risks):empty('风险尚未充分调查，不等于风险不存在。'))+'</section>';
 }
 function render(ctx){
  const {node,product}=ctx,data=product.data;
  const identity=(data.identity||[]).find(r=>r.id===node.id);
  const matches=identity?.canonical?(data.m||[]).filter(m=>'MAT:'+m.id===identity.canonical):
    (product.spec.slug!=='eyewear'?(data.m||[]).filter(m=>m.node===node.id):[]);
  const dossier=(data.research||[]).find(v=>v.node_id===node.id);
  const insight=(data.insights||[]).find(v=>v.node_id===node.id);
  const coverage=(data.coverage||[]).find(v=>v.node_id===node.id);
  const state={...ctx,data,identity,dossier,insight,coverage,matIds:new Set(matches.map(x=>x.id))};
  const tabs=TABS.map(([id,name],i)=>'<button class="sc-tab'+(i===0?' is-active':'')+'" data-sc-tab="'+id+'" role="tab" aria-selected="'+(i===0?'true':'false')+'">'+name+'</button>').join('');
  const sections={summary:renderSummary,technical:renderTechnical,market:renderMarket,trace:renderTrace,evidence:renderEvidence,gaps:renderGaps};
  const html=panelHeader(state)+'<nav class="sc-tabs" role="tablist" aria-label="节点研究内容">'+tabs+'</nav>'+
    Object.entries(sections).map(([id,fn])=>'<div class="sc-tabpane" data-sc-panel="'+id+'" '+(id!=='summary'?'hidden':'')+'>'+fn(state)+'</div>').join('')+
    '<footer class="sc-footer">数据快照 · '+e(insight?.updated_at||dossier?.as_of||'未记录')+' · 引用可打开原始来源。缺失项不补造数值。</footer>';
  return html;
 }
 function bind(root,actions){
  root.addEventListener('click',event=>{
   const copy=event.target.closest('[data-sc-copy-task]');
   if(copy){
     const content=root.querySelector('.sc-task-text')?.textContent||'';
     if(typeof navigator!=='undefined'&&navigator.clipboard?.writeText){
       navigator.clipboard.writeText(content).then(()=>{copy.textContent='研究任务已复制';},
         ()=>{copy.textContent='复制失败，请手动选择文本';});
     }else{copy.textContent='请手动选择文本复制';}
     return;
   }
   const tab=event.target.closest('[data-sc-tab]');
   if(tab){const id=tab.getAttribute('data-sc-tab');root.querySelectorAll('[data-sc-tab]').forEach(b=>{const active=b.getAttribute('data-sc-tab')===id;b.classList.toggle('is-active',active);b.setAttribute('aria-selected',active?'true':'false')});root.querySelectorAll('[data-sc-panel]').forEach(p=>p.hidden=p.getAttribute('data-sc-panel')!==id);return;}
   const hit=event.target.closest('[data-node],[data-company]');
   if(hit){event.preventDefault();if(hit.dataset.node)actions.onNode(hit.dataset.node);else if(hit.dataset.company)actions.onCompany(hit.dataset.company);}
  });
 }
 return {render,bind};
})();