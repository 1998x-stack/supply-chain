import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
const sandbox={window:{}};
vm.runInNewContext(readFileSync('web/assets/node_panel.js','utf8'),sandbox);
const panel=sandbox.window.SupplyNodePanel;
function fixture(opts={}){
 const root={id:'root',name:'示例产品',kind:'category',branch:'产品',parent:null,description:'分支入口'};
 const child={id:'MAT01',name:opts.name||'光学材料甲',kind:'material',branch:'材料',parent:'root',description:'工业材料的技术关联'};
 const node=opts.nav?root:child;
 const coverage=opts.coverage||{node_id:'MAT01',stage:'structural_only',priority:'P0',facet:'material',children:0,sources:0,claims:0,path:['示例产品','光学材料甲'],questions:['核查原始TDS','核实供应商']};
 const data={coverage:[coverage],research:[],insights:opts.insight?[opts.insight]:[],identity:[],m:[],cm:[],mk:[],c:[],s:[],src:[],xl:[]};
 const byId=new Map([root,child].map(v=>[v.id,v]));const children=new Map([['root',[child]]]);
 return {node,product:{spec:{slug:'example',title:'示例产品'},data,children,byId},reverse:{material_to_products:{}},catalog:{products:[{slug:'example',title:'示例产品'}]}};
}
test('a structural node shows actual topology and a pending research instruction',()=>{
 const html=panel.render(fixture());
 assert.match(html,/结构资料 · 待深研/);
 assert.match(html,/已建立的产业链结构信息/);
 assert.match(html,/示例产品 \/ 光学材料甲/);
 assert.match(html,/复制研究指令/);
 assert.doesNotMatch(html,/语义审核完成/);
});
test('a source note never becomes a reviewed dossier automatically',()=>{
 const coverage={node_id:'MAT01',stage:'source_note',priority:'P1',facet:'material',sources:1,claims:1,children:0,path:['示例产品','光学材料甲'],questions:['追踪具体客户']};
 const html=panel.render(fixture({coverage,insight:{node_id:'MAT01',source_ids:['S001'],claims:[{text:'企业自报材料',status:'draft',source_ids:['S001']}],facts:[],metrics:[]}}));
 assert.match(html,/已有来源记录 · 待深研/);
 assert.match(html,/研究优先级 P1/);
 assert.match(html,/企业自报材料/);
 assert.doesNotMatch(html,/语义审核完成/);
});
test('a navigation group is not a mandatory material dossier',()=>{
 const coverage={node_id:'root',stage:'structural_only',priority:'NAV',facet:'navigation',sources:0,claims:0,children:1,path:['示例产品'],questions:[]};
 const html=panel.render(fixture({nav:true,coverage}));
 assert.match(html,/目录\/分组节点/);
 assert.match(html,/无需为每个目录项单独调查供应商/);
 assert.doesNotMatch(html,/data-sc-copy-task/);
});
test('research work order escapes injected HTML in names',()=>{
 const html=panel.render(fixture({name:'<img src=x onerror=alert(1)>'}));
 assert.doesNotMatch(html,/<img src=x onerror=alert\(1\)>/);
 assert.match(html,/&lt;img src=x/);
 assert.match(html,/交给本地 Codex \/ Pi \/ Claude/);
});
