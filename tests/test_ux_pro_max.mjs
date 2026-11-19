import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const read=path=>readFileSync(path,'utf8');
const nodePanel=read('web/assets/node_panel.js');
const app=read('web/assets/app.js');
const stylesheet=read('web/assets/ux_pro_max.css');
const html=read('web/index.html');
const sandbox={window:{}};
vm.runInNewContext(nodePanel,sandbox,{filename:'node_panel.js'});
const panel=sandbox.window.SupplyNodePanel;

function fixture(){
 const node={id:'x',name:'材料 X',kind:'material',branch:'材料',parent:null,description:'未核实'};
 return {node,product:{
  spec:{slug:'sample',title:'样例产品'},byId:new Map([['x',node]]),children:new Map(),
  data:{identity:[],research:[],insights:[],coverage:[],m:[],src:[],cm:[],c:[],mk:[],s:[],xl:[]}
 },reverse:{material_to_products:{}},catalog:{products:[{slug:'sample',title:'样例产品'}]}};
}

test('all six research tabs expose ARIA tabs and associated panels',()=>{
 const markup=panel.render(fixture());
 assert.equal((markup.match(/role="tab"/g)||[]).length,6);
 assert.equal((markup.match(/role="tabpanel"/g)||[]).length,6);
 for(const tab of ['summary','technical','market','trace','evidence','gaps']){
  assert.ok(markup.includes('id="sc-tab-'+tab+'"'));
  assert.ok(markup.includes('aria-controls="sc-panel-'+tab+'"'));
  assert.ok(markup.includes('aria-labelledby="sc-tab-'+tab+'"'));
 }
 assert.ok(markup.includes('tabindex="-1"'));
 assert.ok(markup.includes('技术关联≠真实采购'));
});

test('node inspector does not accumulate delegated listeners and supports arrow tabs',()=>{
 const makeButton=id=>{
  const attrs={'data-sc-tab':id,'aria-selected':id==='summary'?'true':'false'};
  return {attrs,classList:{toggle(){}},getAttribute:k=>attrs[k],setAttribute:(k,v)=>{attrs[k]=v;},focus(){this.focused=true;}};
 };
 const buttons=['summary','technical','market','trace','evidence','gaps'].map(makeButton);
 const panels=buttons.map(b=>({id:b.attrs['data-sc-tab'],hidden:false,getAttribute(k){return k==='data-sc-panel'?this.id:'';}}));
 const root={querySelectorAll:sel=>sel==='[data-sc-tab]'?buttons:sel==='[data-sc-panel]'?panels:[]};
 panel.bind(root,{onNode(){},onCompany(){}});
 const firstHandler=root.onclick;
 panel.bind(root,{onNode(){},onCompany(){}});
 assert.notEqual(root.onclick,firstHandler);
 let prevented=false;
 root.onkeydown({target:{closest:()=>buttons[0]},key:'ArrowLeft',preventDefault(){prevented=true;}});
 assert.equal(prevented,true);
 assert.equal(buttons[5].attrs['aria-selected'],'true');
 assert.equal(buttons[5].attrs.tabindex,'0');
 assert.equal(panels[0].hidden,true);
 assert.equal(panels[5].hidden,false);
 assert.equal(buttons[5].focused,true);
});

test('atlas graph provides search, status focus, path navigation and escape-safe results',()=>{
 assert.match(app,/function updateSearchResults\(\)/);
 assert.match(app,/function selectNode\(id,focusGraph=false\)/);
 assert.match(app,/function stageOf\(/);
 assert.match(app,/onPath\.has\(n\.id\)/);
 assert.match(app,/id="graphSearchResults"/);
 assert.match(app,/id="researchFocus"/);
 assert.match(app,/data-hit/);
 assert.match(app,/esc\(n\.name\)/);
 assert.match(app,/ArrowDown/);
 assert.match(app,/researchFocusCount/);
 assert.match(html,/href="\.\/assets\/ux_pro_max\.css"/);
 assert.match(html,/class="skip-link"/);
});

test('design system includes focus, reduced-motion, responsive and hidden patterns',()=>{
 for(const selector of [':focus-visible','prefers-reduced-motion','graph-search-results\\[hidden\\]','max-width:700px','min-height:44px']){
  assert.ok(stylesheet.includes(selector.replaceAll('\\','')),selector);
 }
});
