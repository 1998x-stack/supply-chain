# 数据库 Schema：统一图 + 产品视图 + 证据

**方向约定**：edge.upstream_id → edge.downstream_id，所有原料最终可沿边走向成品。

| 表 | 主键 | 设计目的 |
|---|---|---|
| entity | entity_id | 全局唯一实体：产品/部件/材料/工艺/资源/公司/工厂 |
| entity_alias | entity_id,alias | 中文/英文/化学名/CAS别名，避免文字撞名 |
| product,category | product_id,category_id | 多产品目录与分类 |
| company,facility | company_id,facility_id | 企业集团/法人/工厂分离 |
| edge,edge_source | edge_id, (edge_id,source_id) | 有向关系、有效期、证据等级与出处 |
| product_view_node | (product_id,view_node_id) | 同一张图在各产品下的树状投影与顺序 |
| product_bill_of_materials | product_id,component_id,scenario | BOM数量、单位、可选件及成本占比 |
| market,market_share | market_id, (market_id,label) | 明确年份/区域/统计分母和排名 |
| capacity | observation_id | 工厂/企业/产品产能与单位 |
| procurement_observation | observation_id | 采购集中度；允许供应商匿名，但匿名不得匹配实体 |
| substitution_candidate | candidate_id | 替代从想法→产能→牌号→客户认证→商业化的状态 |
| source | source_id | 数据出处、发表/核验日期、存档链接 |

## 节点类型

product / component / material / chemical / process / resource / equipment / service / company / facility / country

## 关系语义

- material_input：材料或前驱体参与制造，下游是一种产品/工艺。
- component_of：部件属于某产品或子系统。
- processed_into：材料转化为另一材料，存在前提条件。
- supplied_to：有证据的真实企业供货，必须支持证据来源和有效时间。
- owns / located_at：公司组织与生产工厂。
- alternative_to / potential_substitute：替代性研究，不等于实际替代。

**禁止**将 technological 级别的边误显示为 verified supplied_to。

## 常用查询

~~~sql
-- 查询一个原材料能沿技术路径到达哪些最终产品（只显示真实已建边）
WITH RECURSIVE trace(node_id, depth, path) AS (
  SELECT 'MAT:PC_GEN',0,'MAT:PC_GEN'
  UNION ALL
  SELECT e.downstream_id,t.depth+1,t.path||'>'||e.downstream_id
  FROM edge e JOIN trace t ON e.upstream_id=t.node_id
  WHERE e.relation_type IN ('material_input','component_of','processed_into')
    AND t.depth < 16
    AND instr(t.path,e.downstream_id)=0
)
SELECT DISTINCT p.slug, p.product_id FROM trace t JOIN product p ON p.product_id=t.node_id;

-- 查询有真实证据的公司供应关系
SELECT e.upstream_id,e.downstream_id,s.url FROM edge e
JOIN edge_source es USING(edge_id) JOIN source s USING(source_id)
WHERE e.relation_type='supplied_to' AND e.evidence_status='verified';

-- 对单个 market_id 统计前三名，必须先检查前三名是否齐全
SELECT label,rank,share FROM market_share
WHERE market_id='CH_LENS_VAL' AND rank BETWEEN 1 AND 3 ORDER BY rank;
~~~

未来加新产品时，只需在 product 表注册产品，创建与现有 entity_id 的关联，同时拥有独立的 product_view_node 树状布局。千万不要把产品专属树节点直接当作全局material ID。
