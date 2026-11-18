import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';

const app=readFileSync('web/assets/app.js','utf8');
const start=app.indexOf('const cacheBust=');
const end=app.indexOf('function unpack(',start);
const beginLoad=app.indexOf('async function loadProduct(');
const endLoad=app.indexOf('function route()',beginLoad);
assert.ok(start>=0&&end>start&&beginLoad>end&&endLoad>beginLoad,
          'Cache/retry implementation must be present');
const helpers=app.slice(start,end);
const loader=app.slice(beginLoad,endLoad);
function createRuntime(initialCatalog){
 const attempts=[];
 const state={catalog:initialCatalog,reverseIndex:{},requestCounter:0,products:new Map()};
 const latest={build_id:'new-release-123',products:[
  {slug:'eyewear',title:'眼镜'},
  {slug:'henkel-adhesives',title:'汉高胶黏剂'}
 ]};
 const fetch=async(url,opts)=>{
  attempts.push({url,opts});
  assert.equal(opts?.cache,'no-store');
  return {ok:true,json:async()=>url.includes('catalog.json')?latest:{material_to_products:{}}};
 };
 const sandbox={state,fetch,Date,Map,window:{}};
 vm.runInNewContext(helpers+'\n'+loader+
   "\nfunction unpack(x){return x;}\nfetchCompressed=async()=>({n:[{id:'root',parent:null,name:'汉高'}]});\nglobalThis.api={cacheBust,refreshCatalog,loadProduct};",sandbox);
 return {api:sandbox.api,state,attempts};
}
test('stale single-product catalog auto-refreshes before declaring Henkel nonexistent',async()=>{
 const old={build_id:'previous-release',products:[{slug:'eyewear',title:'眼镜'}]};
 const {api,state,attempts}=createRuntime(old);
 const product=await api.loadProduct('henkel-adhesives');
 assert.equal(product.spec.title,'汉高胶黏剂');
 assert.equal(state.catalog.products.length,2);
 assert.equal(state.catalog.build_id,'new-release-123');
 assert.equal(attempts.length,2);
 assert.match(attempts[0].url,/\?sc_refresh=/);
 assert.match(attempts[1].url,/\?sc_refresh=/);
});
test('catalog reads have unique cache keys even within the same millisecond',()=>{
 const {api}=createRuntime({products:[]});
 const x=api.cacheBust('./data/catalog.json');
 const y=api.cacheBust('./data/catalog.json');
 assert.notEqual(x,y);
});
test('already available product does not unnecessarily refresh catalog',async()=>{
 const current={build_id:'current',products:[{slug:'henkel-adhesives',title:'汉高胶黏剂'}]};
 const {api,attempts}=createRuntime(current);
 await api.loadProduct('henkel-adhesives');
 assert.equal(attempts.length,0);
});
