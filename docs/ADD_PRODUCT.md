# 新增一个产品：不用修改前端或专门适配脚本

## 1. 生成产品目录

~~~bash
python3 scripts/new_product.py smartphone --title 智能手机 --category electronics --icon 📱
~~~

该命令创建 data/products/smartphone/product.json 与 graph.json，且默认 published=false；**不会生成任何未经核实的供应链事实**。

## 2. product.json

~~~json
{"schema_version":1,"slug":"smartphone","title":"智能手机","category_id":"electronics","category":"消费电子","icon":"📱","description":"研究范围简介","adapter":"atlas_v1","source":"graph.json","published":false}
~~~

category_id 必须在 data/taxonomy/categories.json 中存在，且分类名称必须匹配。发布前将 published 改为 true。

## 3. graph.json 结构

~~~json
{
  "nodes":[
    {"id":"root","name":"智能手机","parent":null,"kind":"产品","branch":"根节点","description":""},
    {"id":"screen","name":"显示模组","parent":"root","kind":"部件","branch":"显示系统","description":""},
    {"id":"glass","name":"盖板玻璃","parent":"screen","kind":"材料","branch":"显示系统","description":""}
  ],
  "materials":[{"id":"COVER_GLASS","name":"盖板玻璃","node":"glass"}],
  "companies":[],
  "company_material":[],
  "company_relations":[],
  "markets":[],"shares":[],"sources":[],"opportunities":[],"capacity":[],"procurement":[]
}
~~~

- nodes 是该产品专属的树状视图，必须唯一根节点、父节点存在、不得出现环。
- materials 的 id 是全站标准材料标识。**与已有材料相同则使用已有ID和精确相同名称**；名称相似但规格不同不可自动合并。
- companies 的 id 是全站企业ID，中文/英文名必须一致；相同公司多产品引用相同ID。
- company_material 用 {company,material,role,source}；只证明公司从事材料相关业务，不代表公司向具体品牌供货。
- company_relations 必须含 {id,upstream,downstream,material,type,source,scope,date}；历史关系不能自动标为持续供货。
- markets 必须含 {id,name,geo,year,metric,denominator,material,source}；shares 含 {market,company,label,pct,rank,source}。
- sources 含 {id,title,url,type,checked_on}；未知数据缺失，不要填造0。

## 4. 上线流程

~~~bash
# 编辑并审核数据，把 product.json 的 published 改为 true 后：
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
python3 -m http.server 8000 --directory dist
~~~

Pages 读取由构建器生成的 data/catalog.json、各产品 .json.gz 与 data/reverse_index.json。
新产品上线后，主页分类卡片会自动出现；已有材料ID会自动被反向索引映射到所有使用它的产品。

## 5. 证据与质量规则

- 任何TOP3都需年份、地理范围、出货量/金额/产能、分母、来源；缺第三名时不可标CR3。
- 技术路径不等于实际企业供货；所有历史合作需要带生效/公告日期和说明。
- 产能足够不等于具有镜片级、医疗级等特殊牌号认证。
- 为每条重要观察记录权威公开来源与查阅日期。不能把国家产量和公司市场份额混算。
- 所有新增产品采用PR审核，不在网页端直接编辑数据库。
