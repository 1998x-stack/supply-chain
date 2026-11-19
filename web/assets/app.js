'use strict';
// All views use stable, globally scoped entity IDs. A product tree is only one projection
// of the material / company / product network, not a claim of actual procurement.
const app = document.getElementById('app');
const state = { catalog:null, reverseIndex:null, products:new Map(), datasets:new Map(), product:null, selected:null, collapsed:new Set(), viewport:{x:0,y:0,w:1300,h:800}, search:'', layout:[], drag:null, categories:'全部', requestCounter:0, activeConfiguration:null, researchFocus:'all' };
const $ = (selector,root=document)=>root.querySelector(selector);
const el = (name,attrs={},text='') => {const e=document.createElement(name);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e;};
const esc = text=>String(text===undefined||text===null?'':text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeLink = url=>/^https:\/\//i.test(String(url||''))?url:'#';
const num = value=>Number(value).toLocaleString('zh-CN');
// Every Pages release can coexist with older browser/CDN cache entries.
const cacheBust=path=>path+(path.includes('?')?'&':'?')+'sc_refresh='+Date.now().toString(36)+'_'+(++state.requestCounter);
const fetchJSON=async(path)=>{const url=cacheBust(path);const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status+' · '+path);return r.json();};
async function fetchCompressed(path){const url=cacheBust(path);const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status+' · '+path);if(!('DecompressionStream' in window))throw new Error('浏览器不支持gzip解码，请更新浏览器');const b=await r.blob();const txt=await new Response(b.stream().pipeThrough(new DecompressionStream('gzip'))).text();return JSON.parse(txt);}
async function refreshCatalog(){
 const [catalog,reverse]=await Promise.all([fetchJSON('./data/catalog.json'),fetchJSON('./data/reverse_index.json')]);
 if(!catalog||!Array.isArray(catalog.products)||!catalog.products.every(p=>typeof p.slug==='string'))
  throw new Error('供应链产品目录格式不正确，可能正在更新发布');
 state.catalog=catalog;state.reverseIndex=reverse;
 return catalog;
}
function unpack(x){
 const fields={n:['id','name','parent','kind','branch','description','relationType'],m:['id','name','node'],c:['id','zh','en','website'],cm:['company','material','role'],r:['upstream','downstream','material','type','source','scope'],mk:['id','name','geo','year','metric','scope','material'],s:['market','company','label','pct','rank','source'],o:['material','candidate','benchmark','topic','gap'],src:['id','title','url'],pc:['buyer','rank','pct','disclosed'],identity:['id','canonical','state','labelKey'],xl:['from','to','type','status','source','note']};
 const data={};for(const [k,f] of Object.entries(fields))data[k]=(x[k]||[]).map(row=>Object.fromEntries(f.map((v,i)=>[v,row[i]])));data.research=x.research||[];data.insights=x.insights||[];data.coverage=x.coverage||[];data.configurations=x.configurations||[];return data;
}
async function loadProduct(slug){if(state.products.has(slug))return state.products.get(slug);let spec=state.catalog.products.find(p=>p.slug===slug);if(!spec){
 // A cached 1-product catalog can still be in the browser after deploying product #2.
 await refreshCatalog();
 spec=state.catalog.products.find(p=>p.slug===slug);
}
if(!spec)throw new Error('最新产品目录仍未包含 '+slug+'（版本 '+String(state.catalog.build_id||'未知')+'；当前 '+state.catalog.products.length+' 个产品）。请强制刷新网页，若仍失败请查看Pages发布记录。');const d=unpack(await fetchCompressed('./data/'+slug+'.json.gz'));const nodes=d.n.map(n=>Object.assign({},n,{product:slug,globalId:slug+':'+n.id}));const product={spec,data:d,nodes,byId:new Map(nodes.map(n=>[n.id,n])),children:new Map()};for(const n of nodes){if(n.parent){const arr=product.children.get(n.parent)||[];arr.push(n);product.children.set(n.parent,arr);}}
 state.products.set(slug,product);return product;}
function route(){const match=location.hash.match(/^#\/products\/([a-z0-9-]+)/);if(match)openProduct(match[1]);else renderHome();}
function renderHome(){state.product=null;const groups=['全部',...new Set(state.catalog.products.map(p=>p.category))];const visible=state.catalog.products.filter(p=>state.categories==='全部'||p.category===state.categories);
app.innerHTML='<main class="wrap"><section class="hero"><div><div class="eyebrow">PRODUCT × MATERIAL × COMPANY × EVIDENCE</div><h1>从一个产品，追溯到<br>每一层供应链。</h1><p>以产品为入口，跨越零部件、精细化工、基础工业与自然资源。对每个材料节点，继续查看供应商、市场份额、证据与可能关联的下游产品。</p></div><div class="hero-box"><strong>统一产业链知识图谱</strong><div class="grid"><div class="metric"><b>'+num(state.catalog.stats.nodes)+'</b><small>产业链视图节点</small></div><div class="metric"><b>'+num(state.catalog.stats.companies)+'</b><small>公司实体</small></div><div class="metric"><b>'+num(state.catalog.products.length)+'</b><small>已收录产品</small></div><div class="metric"><b>'+num(state.catalog.stats.sources)+'</b><small>证据来源</small></div></div></div></section><h2>产品供应链目录</h2><div class="chips" id="categories"></div><div class="cards">'+visible.map(p=>'<article class="card"><span class="card-icon">'+esc(p.icon)+'</span><h3>'+esc(p.title)+'</h3><p>'+esc(p.description)+'</p><div class="meta"><span>'+esc(p.category)+'</span><span>'+num(p.nodes)+'个技术节点 · '+num(p.research_dossiers||0)+'份深度档案 · '+num(p.coverage?.source_notes_without_dossier||0)+'条来源笔记 · '+num(p.coverage?.needs_dossier||0)+'个研究目标待建档 · 进入图谱 ↗</span></div><a class="whole" aria-label="打开'+esc(p.title)+'" href="#/products/'+encodeURIComponent(p.slug)+'"></a></article>').join('')+'</div><div class="notice">下一款产品只需按数据协议增加独立产品目录，已有材料与企业通过稳定实体ID复用。</div><footer class="footer">注：技术路径不等于已确认企业采购关系。市场份额必须同时注明年份、地理范围、分母与来源。</footer></main>';
const target=$('#categories');groups.forEach(g=>{const b=el('button',{class:'chip'+(g===state.categories?' active':'')},g);b.addEventListener('click',()=>{state.categories=g;renderHome();});target.appendChild(b);});}
async function openProduct(slug){app.innerHTML='<div class="loading" style="padding:38px">正在载入 '+esc(slug)+'…</div>';try{const p=await loadProduct(slug);state.product=p;state.selected=p.nodes[0];state.search='';state.researchFocus='all';state.activeConfiguration=null;state.collapsed=new Set(p.nodes.filter(n=>n.parent&&getDepth(p,n)>=3).map(n=>n.id));renderProduct();}catch(e){app.innerHTML='<div class="wrap"><h2>无法打开图谱</h2><p>'+esc(e.message)+'</p><p class="small">数据目录版本：'+esc(state.catalog?.build_id||'未获取')+'。若刚发布新产品，可能是浏览器或CDN保留了旧目录。</p><button id="forceRefresh" class="btn primary">重新加载最新版本</button> <a href="#/">返回首页</a></div>';
 const btn=$('#forceRefresh');if(btn)btn.addEventListener('click',()=>{const url=new URL(location.href);url.searchParams.set('reload',String(Date.now()));location.assign(url.toString());});
}}
function getDepth(p,n){let d=0,x=n;while(x&&x.parent&&d<30){d++;x=p.byId.get(x.parent);}return d;}
function descendants(p,id,cap=10000){const out=[],seen=new Set(),queue=[id];while(queue.length&&out.length<cap){const x=queue.shift();if(seen.has(x))continue;seen.add(x);out.push(x);(p.children.get(x)||[]).forEach(n=>queue.push(n.id));}return out;}
function ancestors(p,id){const out=[],seen=new Set();let n=p.byId.get(id);while(n&&!seen.has(n.id)){seen.add(n.id);out.push(n);n=p.byId.get(n.parent);}return out;}
function layoutTree(p){const root=p.nodes.find(n=>!n.parent)||p.nodes[0];const visible=[],tree=new Map();let cursor=0;const walk=(node,depth)=>{const children=state.collapsed.has(node.id)?[]:(p.children.get(node.id)||[]);const entries=children.map(c=>walk(c,depth+1));const y=entries.length?((entries[0].y+entries[entries.length-1].y)/2):(cursor++*82+50);const v={...node,depth,x:depth*258+35,y};visible.push(v);tree.set(node.id,v);return v;};walk(root,0);return{visible,tree,width:Math.max(900,...visible.map(n=>n.x+260)),height:Math.max(450,cursor*82+80)};}
function renderProduct(){const p=state.product;app.innerHTML='<div class="dashboard"><section class="maincol"><div class="toolbar"><div><div class="breadcrumbs"><a href="#/">产品目录</a> / '+esc(p.spec.category)+' / '+esc(p.spec.title)+'</div><div class="titlebar"><strong>'+esc(p.spec.icon)+' '+esc(p.spec.title)+'供应链</strong></div><div class="selection-path" id="selectionPath" aria-live="polite"></div></div><div class="actions">'+(p.data.configurations?.length?'<label class="kb-config-label">构型高亮 <select id="configuration" aria-label="选择典型键盘构型"></select></label>':'')+'<div class="search-control"><label class="sr-only" for="search">搜索节点</label><input id="search" placeholder="搜索材料 / 工艺 / 部件 · / 快捷键" autocomplete="off" aria-label="搜索材料、工艺或部件"/><button type="button" id="clearSearch" aria-label="清空搜索" title="清空搜索">×</button></div><label class="focus-control" for="researchFocus">状态聚焦 <select id="researchFocus" aria-label="聚焦研究状态"><option value="all">全部状态</option><option value="reviewed">语义审核完成</option><option value="dossier_pending">有档案 · 待复核</option><option value="source_note">有来源 · 待深研</option><option value="annotated">研究笔记 · 待取证</option><option value="structural_only">结构信息 · 待深研</option></select></label><button id="expand" class="btn">全部展开</button><button id="collapse" class="btn">逐层折叠</button><button id="fit" class="btn">适配画布</button><button id="zoomIn" class="btn">＋</button><button id="zoomOut" class="btn">－</button></div></div><div class="graph-container" id="graph"><svg id="svg" aria-label="可缩放供应链树状图"><g id="viewport"></g></svg><div class="graph-search-results" id="graphSearchResults" role="region" aria-label="节点检索结果" hidden></div><div class="graph-legend" aria-label="证据状态图例"><span class="reviewed"><i aria-hidden="true"></i>语义审核完成</span><span class="dossier"><i aria-hidden="true"></i>档案待复核</span><span class="source"><i aria-hidden="true"></i>来源待深研</span><span><i aria-hidden="true"></i>结构待研究</span></div><div class="graph-help">滚轮缩放 · 空白拖动 · 单击查看 · 双击折叠 · 方向键导航</div></div><div class="graph-stats"><span id="visibleCount">—</span><span>深度档案：'+num(p.spec.coverage?.dossiers||0)+' · 来源笔记：'+num(p.spec.coverage?.source_notes_without_dossier||0)+' · 待建档研究目标：'+num(p.spec.coverage?.needs_dossier||0)+'</span><a class="linkline" target="_blank" rel="noopener" href="./data/'+encodeURIComponent(p.spec.slug)+'_research_queue.json">导出P0/P1研究任务</a><span class="focus-count" id="researchFocusCount"></span><span id="searchInfo" aria-live="polite"></span><small id="configurationHelp" aria-live="polite"></small></div></section><aside class="side" id="detail"></aside></div>';
const selector=$('#configuration');
if(selector){
 selector.appendChild(el('option',{value:''},'全部技术路径'));
 for(const cfg of p.data.configurations)selector.appendChild(el('option',{value:cfg.id},cfg.label||cfg.id));
 selector.addEventListener('change',()=>{
  state.activeConfiguration=p.data.configurations.find(c=>c.id===selector.value)||null;
  for(const id of state.activeConfiguration?.primary_nodes||[]){
   for(const x of ancestors(p,id))state.collapsed.delete(x.id);
  }
  drawTree();fit();showDetail(state.selected);
  const help=$('#configurationHelp');
  if(help)help.textContent=state.activeConfiguration?'构型高亮仅标记关键研究路径，非已核实的完整BOM。'+state.activeConfiguration.description:'';
 });
}

 const searchInput=$('#search');
 const updateSearch=()=>{
  state.search=searchInput.value.trim().toLowerCase();
  if(state.search){
   for(const n of p.nodes.filter(n=>n.name.toLowerCase().includes(state.search)))
    for(const parent of ancestors(p,n.id).slice(1))state.collapsed.delete(parent.id);
  }
  drawTree();updateSearchResults();
 };
 searchInput.addEventListener('input',updateSearch);
 $('#clearSearch').addEventListener('click',()=>{searchInput.value='';updateSearch();searchInput.focus();});
 $('#researchFocus').addEventListener('change',e=>{state.researchFocus=e.target.value;drawTree();});
 $('#graphSearchResults').addEventListener('click',event=>{
  const hit=event.target.closest('[data-hit]');if(hit)selectNode(hit.getAttribute('data-hit'));
 });
 $('#expand').onclick=()=>{state.collapsed.clear();drawTree();fit();};
 $('#collapse').onclick=()=>{state.collapsed=new Set(p.nodes.filter(n=>getDepth(p,n)>=2).map(n=>n.id));drawTree();fit();};
 $('#fit').onclick=fit;$('#zoomIn').onclick=()=>zoom(.75);$('#zoomOut').onclick=()=>zoom(1.3);
const svg=$('#svg');svg.addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY<0?.86:1.16,e.offsetX,e.offsetY);},{passive:false});svg.addEventListener('pointerdown',e=>{if(e.target.closest('.node'))return;svg.setPointerCapture(e.pointerId);state.drag={x:e.clientX,y:e.clientY,vx:state.viewport.x,vy:state.viewport.y};});svg.addEventListener('pointermove',e=>{if(!state.drag)return;const rect=svg.getBoundingClientRect();state.viewport.x=state.drag.vx-(e.clientX-state.drag.x)*state.viewport.w/rect.width;state.viewport.y=state.drag.vy-(e.clientY-state.drag.y)*state.viewport.h/rect.height;setView();});svg.addEventListener('pointerup',()=>state.drag=null);svg.addEventListener('pointercancel',()=>state.drag=null);
 drawTree();fit();showDetail(state.selected);}
function setView(){const v=state.viewport;$('#svg').setAttribute('viewBox',[v.x,v.y,v.w,v.h].join(' '));}
function fit(){const box=layoutTree(state.product);state.viewport={x:-25,y:-30,w:Math.max(900,box.width+70),h:Math.max(520,box.height+70)};setView();}
function zoom(factor,x,y){const svg=$('#svg');const rect=svg.getBoundingClientRect();const v=state.viewport;const a=x===undefined?.5:x/rect.width,b=y===undefined?.5:y/rect.height;const w=Math.min(30000,Math.max(280,v.w*factor)),h=v.h*w/v.w;v.x+=(v.w-w)*a;v.y+=(v.h-h)*b;v.w=w;v.h=h;setView();}

function stageOf(p,id){return (p.data.coverage||[]).find(x=>x.node_id===id)?.stage||'structural_only';}
function updateSearchResults(){
 const box=$('#graphSearchResults'),p=state.product;
 if(!box||!p)return;
 if(!state.search){box.hidden=true;box.innerHTML='';return;}
 const matches=p.nodes.filter(n=>n.name.toLowerCase().includes(state.search));
 const shown=matches.slice(0,12);
 box.hidden=false;
 box.innerHTML='<div class="graph-result-heading" role="status">'+matches.length+' 个节点匹配'+(matches.length>shown.length?' · 显示前 '+shown.length+' 项':'')+'</div>'+
  (shown.length?'<ol>'+shown.map(n=>'<li><button type="button" class="graph-result" data-hit="'+esc(n.id)+'"><b>'+esc(n.name)+'</b><small>'+esc(ancestors(p,n.id).reverse().map(x=>x.name).join(' / '))+'</small></button></li>').join('')+'</ol>':
   '<div class="graph-result-empty">未找到匹配节点。可尝试材料名称、工艺或部件关键词。</div>');
}
function selectNode(id,focusGraph=false){
 const p=state.product,target=p?.byId.get(id);if(!target)return;
 for(const n of ancestors(p,id))state.collapsed.delete(n.id);
 state.selected=target;drawTree();showDetail(target);
 const entry=state.layout.find(n=>n.id===id);
 if(entry){state.viewport.x=entry.x-210;state.viewport.y=entry.y-220;state.viewport.w=880;state.viewport.h=550;setView();}
 if(focusGraph){
  const item=[...document.querySelectorAll('#viewport .node')].find(n=>n.getAttribute('data-node-id')===id);
  item?.focus();
 }
}
function drawTree(){const p=state.product;const {visible,tree}=layoutTree(p);state.layout=visible;const g=$('#viewport');g.innerHTML='';const svgNS='http://www.w3.org/2000/svg';const svgEl=(tag,attrs)=>{const x=document.createElementNS(svgNS,tag);Object.entries(attrs).forEach(([k,v])=>x.setAttribute(k,v));return x;};
for(const n of visible){if(!n.parent||!tree.has(n.parent))continue;const parent=tree.get(n.parent);g.appendChild(svgEl('path',{class:'edge',d:'M'+(parent.x+214)+','+parent.y+' C'+(parent.x+243)+','+parent.y+' '+(n.x-26)+','+n.y+' '+n.x+','+n.y}));}
for(const n of visible){const group=svgEl('g',{class:'node'+(state.selected?.id===n.id?' selected':'')+(state.activeConfiguration?.primary_nodes?.includes(n.id)?' config-primary':''),transform:'translate('+n.x+','+(n.y-23)+')',tabindex:'0',role:'button','aria-label':n.name});const r=svgEl('rect',{x:0,y:0,width:214,height:46,rx:8});group.append(r);const title=svgEl('text',{x:11,y:20});title.textContent=n.name.length>17?n.name.slice(0,16)+'…':n.name;group.append(title);const sub=svgEl('text',{class:'subtext',x:11,y:36});const stage=(p.data.coverage||[]).find(x=>x.node_id===n.id)?.stage;
sub.textContent=(n.kind||n.branch||'材料')+(stage==='reviewed'?' ✓':stage==='dossier_pending'?' · 档案':stage==='source_note'?' · 来源':'');group.append(sub);const count=(p.children.get(n.id)||[]).length;if(count){const flag=svgEl('text',{class:'badgecount',x:202,y:29,'text-anchor':'end'});flag.textContent=(state.collapsed.has(n.id)?'＋':'−')+count;group.append(flag);}if(state.search&&!n.name.toLowerCase().includes(state.search)){group.setAttribute('opacity','.23');}
group.addEventListener('click',e=>{e.stopPropagation();state.selected=p.byId.get(n.id);drawTree();showDetail(state.selected);});group.addEventListener('dblclick',e=>{e.stopPropagation();if(state.collapsed.has(n.id))state.collapsed.delete(n.id);else state.collapsed.add(n.id);drawTree();});group.addEventListener('keydown',e=>{if(e.key==='Enter'){state.selected=p.byId.get(n.id);drawTree();showDetail(state.selected);}if(e.key===' '){e.preventDefault();if(state.collapsed.has(n.id))state.collapsed.delete(n.id);else state.collapsed.add(n.id);drawTree();}});g.appendChild(group);}
$('#visibleCount').textContent=visible.length+' / '+p.nodes.length+' 个节点可见';$('#searchInfo').textContent=state.search?visible.filter(n=>n.name.toLowerCase().includes(state.search)).length+' 个当前可见匹配':'';}
function renderResearchDossier(record){
 const names={identity:'身份、规格和牌号',technical:'性能与试验条件',upstream:'原料与工艺',downstream:'技术下游应用',companies:'相关企业（不等于采购）',market:'市场份额及其分母',risk:'供应风险',open_questions:'未解决问题'};
 const verified=record.review_state==='publishable'&&record.semantic_review_status==='approved';
 let html='<div class="research-dossier"><div class="small">NODE DOSSIER / '+esc(record.node_id)+'</div><h3>深度研究档案 · '+esc(record.name)+'</h3><span class="research-state '+(verified?'research-verified':'research-pending')+'">'+(verified?'经过语义复核':'草稿 · 未完成语义事实核验')+'</span><p class="small">数据基准：'+esc(record.as_of)+'；研究状态：'+esc(record.review_state)+'</p>';
 if(!verified)html+='<p class="research-warning">此档案仍在研究与复核中。技术材料关联不等于真实供货；请查看原文、统计年份和分母。</p>';
 for(const [key,label] of Object.entries(names)){
  const value=record.sections?.[key];if(value===undefined||value===null)continue;
  html+='<details class="research-section"'+(key==='technical'?' open':'')+'><summary>'+esc(label)+'</summary><pre>'+esc(JSON.stringify(value,null,2))+'</pre></details>';
 }
 html+='<h3>原子论断与证据状态</h3>';
 for(const c of record.claims||[])html+='<div class="fact"><b>'+esc(c.id)+' · '+esc(c.status)+'</b><p>'+esc(c.text)+'</p><div class="small">'+esc(c.analysis||'')+'</div><div class="small">来源：'+esc((c.source_ids||[]).join(', '))+'</div></div>';
 html+='<h3>可查阅的原始来源</h3>';
 for(const s of record.sources||[])html+='<a class="linkline" target="_blank" rel="noopener noreferrer" href="'+esc(safeLink(s.url))+'">'+esc(s.id)+' · '+esc(s.title||s.url)+' ↗</a>';
 return html+'</div>';
}

function showDetail(node){
 if(!node)return;
 const p=state.product;
 const target=$('#detail');
 target.innerHTML=window.SupplyNodePanel.render({node,product:p,reverse:state.reverseIndex,catalog:state.catalog});
 window.SupplyNodePanel.bind(target,{
  onCompany:companyId=>showCompanyDetail(companyId),
  onNode:id=>{
   const targetNode=p.byId.get(id);
   if(!targetNode)return;
   let parent=targetNode.parent;
   while(parent){state.collapsed.delete(parent);parent=p.byId.get(parent)?.parent;}
   state.selected=targetNode;drawTree();showDetail(state.selected);
   const entry=state.layout.find(n=>n.id===id);
   if(entry){state.viewport.x=entry.x-180;state.viewport.y=entry.y-250;state.viewport.w=900;state.viewport.h=560;setView();}
  }
 });
}
async function showCompanyDetail(companyId){
 const p=state.product;if(!p)return;const d=p.data;const company=d.c.find(c=>c.id===companyId);if(!company)return;
 const materialIds=new Set((state.reverseIndex?.company_to_materials?.[companyId]||[]));
 for(const row of d.cm.filter(x=>x.company===companyId))materialIds.add(row.material);
 const materials=Array.from(materialIds).map(id=>({role:d.cm.find(x=>x.company===companyId&&x.material===id)?.role||'其他产品材料关系',material:d.m.find(m=>m.id===id)||{id:id,name:id}}));
 const rels=d.r.filter(r=>r.upstream===companyId||r.downstream===companyId);
 const products=new Set();for(const item of materials){if(!item.material)continue;for(const slug of state.reverseIndex?.material_to_products?.[item.material.id]||[])products.add(slug);}
 let html='<a href="#" class="linkline" id="backToNode">← 返回节点</a><div class="small">COMPANY / '+esc(companyId)+'</div><h2>'+esc(company.zh||company.en)+'</h2><p>'+esc(company.en)+'</p>'+(company.website?'<a class="linkline" target="_blank" rel="noopener" href="'+esc(safeLink(company.website))+'">企业官网 ↗</a>':'');
 html+='<h3>材料 / 产品领域（并非采购确认）</h3>'+(materials.length?materials.map(item=>'<div class="fact"><b>'+esc(item.material?.name||'未映射材料')+'</b><p class="small">'+esc(item.role)+'</p></div>').join(''):'<div class="empty">暂无企业材料关系</div>');
 html+='<h3>技术上相关的下游产品</h3>'+(products.size?Array.from(products).map(slug=>{const spec=state.catalog.products.find(pr=>pr.slug===slug);return spec?'<a class="linkline" href="#/products/'+esc(slug)+'">'+esc(spec.title)+' · '+esc(spec.category)+' ↗</a>':'';}).join(''):'<div class="empty">暂无跨产品连接</div>')+'<p class="small">关联基于企业经营材料×产品材料，不表示该企业实际向该产品制造商供货。</p>';
 html+='<h3>公开披露的合作关系</h3>'+(rels.length?rels.map(r=>{const other=d.c.find(c=>c.id===(r.upstream===companyId?r.downstream:r.upstream));const source=d.src.find(s=>s.id===r.source);return '<div class="fact"><b>'+esc(other?.zh||other?.en||'相关企业')+'</b><div class="small">'+esc(r.type)+' · '+esc(r.scope||'')+'</div>'+(source?'<a class="linkline" href="'+esc(safeLink(source.url))+'" target="_blank" rel="noopener">查阅原始证据 ↗</a>':'')+'</div>';}).join(''):'<div class="empty">暂无已收录合作证据</div>');
 const sh=d.s.filter(s=>s.company===companyId&&s.pct!==null);html+='<h3>市场份额（必须看统计口径）</h3>'+(sh.length?sh.map(s=>{const mk=d.mk.find(m=>m.id===s.market);return '<div class="fact"><b>'+esc(mk?.name)+' · '+esc(mk?.year)+'</b><p>'+esc(s.pct)+'%</p><div class="small">'+esc(mk?.geo)+' / '+esc(mk?.metric)+' / '+esc(mk?.scope)+'</div></div>';}).join(''):'<div class="empty">无可核实份额记录</div>');
 $('#detail').innerHTML=html;$('#backToNode').addEventListener('click',e=>{e.preventDefault();showDetail(state.selected);});
}
async function init(){try{await refreshCatalog();window.addEventListener('hashchange',route);route();}catch(e){app.innerHTML='<main class="wrap"><h1>数据载入失败</h1><p>'+esc(e.message)+'</p><p>请通过 HTTP 服务器或 GitHub Pages 打开本项目，而不是直接打开本地 file:// 文件。</p></main>';}}
init();
