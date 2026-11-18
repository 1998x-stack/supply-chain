import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const root = process.cwd();
const source=readFileSync(root+'/web/assets/node_panel.js','utf8');
const sandbox={window:{}};
vm.runInNewContext(source,sandbox,{filename:'node_panel.js'});
const panel=sandbox.window.SupplyNodePanel;
const graph=JSON.parse(readFileSync(root+'/data/products/henkel-adhesives/graph.json','utf8'));
function context(nodeId='243'){
 const byId=new Map(graph.nodes.map(n=>[n.id,n]));
 const children=new Map();
 for(const n of graph.nodes)if(n.parent)children.set(n.parent,[...(children.get(n.parent)||[]),n]);
 const insight=graph.node_intelligence;
 const materials=graph.materials.map(m=>({id:m.id,name:m.name,node:m.node}));
 const data={
  insights:insight,research:[],m:materials,
  src:graph.sources.map(s=>({id:s.id,title:s.title,url:s.url})),
  cm:graph.company_material, c:graph.companies.map(c=>({id:c.id,zh:c.zh,en:c.en})),
  mk:[],s:[],xl:graph.cross_links.map(x=>({from:x.from,to:x.to,type:x.relation_type,status:x.evidence_status,source:x.source_id,note:x.note})),
  identity:[],
 };
 return {node:byId.get(nodeId),product:{spec:{slug:'henkel-adhesives',title:'汉高胶黏剂与密封材料',category:'工业装备',icon:'🧪'},data,byId,children},reverse:{material_to_products:{}},catalog:{products:[{slug:'henkel-adhesives',title:'汉高胶黏剂与密封材料',icon:'🧪'}]}};
}
test('six research tabs and source-first UI render for Henkel SKU',()=>{
 const html=panel.render(context('243'));
 assert.equal((html.match(/data-sc-tab="/g)||[]).length,6);
 assert.match(html,/1,300|1300/);
 assert.match(html,/S04/);
 assert.match(html,/市场与企业/);
 assert.match(html,/原始证据/);
 assert.match(html,/缺乏|暂无|没有可核实/);
});
test('polymer paths are typed, hypothetical links explicitly labeled',()=>{
 const html=panel.render(context('evaresin'));
 assert.match(html,/跨分支材料与技术关联/);
 assert.match(html,/hypothesis/);
 assert.match(html,/乙烯/);
});
test('portfolio revenue shows period and scope, not a market share',()=>{
 const html=panel.render(context('henkel'));
 assert.match(html,/10,667|10667/);
 assert.match(html,/FY2025/);
 assert.match(html,/2026Q1/);
 assert.match(html,/业务部门/);
});
test('malicious node names are escaped and not interpolated as raw HTML',()=>{
 const ctx=context();
 ctx.node={...ctx.node,name:'<img src=x onerror=alert(1)>'};
 const html=panel.render(ctx);
 assert.ok(!html.includes('<img src=x onerror=alert(1)>'));
 assert.match(html,/&lt;img src=x/);
});
test('no null market share is ever displayed as a 0% observation',()=>{
 const ctx=context('243');
 ctx.product.data.mk=[{id:'m1',name:'Synthetic Test Market',geo:'Global',year:2025,scope:'Synthetic category',metric:'revenue_share',material:'HNK_DIMETHACRYLATE'}];
 ctx.product.data.s=[{market:'m1',company:'HENKEL_AG',label:'Unknown',pct:null,rank:1,source:'S04'}];
 const html=panel.render(ctx);
 assert.ok(!html.includes('Unknown</span><strong>0%'));
});
