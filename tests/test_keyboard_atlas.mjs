import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const src=readFileSync('web/assets/node_panel.js','utf8');
const sandbox={window:{}};vm.runInNewContext(src,sandbox,{filename:'node_panel.js'});
const panel=sandbox.window.SupplyNodePanel;
const graph=JSON.parse(readFileSync('data/products/keyboard/graph.json','utf8'));
function ctx(id){
 const byId=new Map(graph.nodes.map(n=>[n.id,n]));
 const children=new Map();
 for(const n of graph.nodes)if(n.parent)children.set(n.parent,[...(children.get(n.parent)||[]),n]);
 const insights=graph.node_intelligence,materials=graph.materials.map(x=>({id:x.id,name:x.name,node:x.node}));
 const node=byId.get(id),sources=graph.sources.map(x=>({id:x.id,title:x.title,url:x.url}));
 const coverage={node_id:id,stage:'source_note',priority:'P0',facet:node.kind,sources:1,claims:0,children:0,path:['电脑键盘',node.name],questions:['核实适用牌号与实际采购']};
 const data={insights,research:[],m:materials,c:graph.companies.map(c=>({id:c.id,zh:c.zh,en:c.en})),src:sources,cm:graph.company_material,
   mk:[],s:[],identity:[],coverage:[coverage],xl:graph.cross_links.map(x=>({from:x.from,to:x.to,type:x.relation_type,status:x.evidence_status,source:x.source_id,note:x.note})),
   configurations:graph.product_configurations};
 return {node,product:{spec:{slug:'keyboard',title:'电脑键盘产业链',icon:'⌨️'},data,byId,children},reverse:{material_to_products:{}},catalog:{products:[{slug:'keyboard',title:'电脑键盘产业链'}]}};
}
test('Keyboard Hall node displays cited actual SKU specs and unknown procurement disclaimer',()=>{
 const html=panel.render(ctx('gateron_ks20'));
 assert.equal((html.match(/data-sc-tab="/g)||[]).length,6);
 assert.match(html,/4.1±0.2/);
 assert.match(html,/Gateron|佳达隆/);
 assert.match(html,/S02/);
 assert.match(html,/并非|不等于|技术关联≠真实采购/);
});
test('Keyboard PBT keycap shows its direct manufacturer-origin reference not invented vendor ranking',()=>{
 const html=panel.render(ctx('pbt_caps'));
 assert.match(html,/KBDfans/);
 assert.match(html,/S09/);
 assert.match(html,/没有可核实的同口径市场份额 TOP3/);
});
test('Keyboard FR-4 specific grade does not get assigned to every keyboard PCB',()=>{
 const html=panel.render(ctx('fr4'));
 assert.match(html,/190/);
 assert.match(html,/Isola/);
 assert.match(html,/S08/);
});
test('Keyboard with a single source note still displays research tasks rather than reviewed',()=>{
 const html=panel.render(ctx('hall_sensor'));
 assert.match(html,/已有来源记录/);
 assert.match(html,/复制研究指令/);
 assert.doesNotMatch(html,/语义审核完成/);
});
