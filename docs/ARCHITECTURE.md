# 架构决策记录：多产品供应链研究平台

## 产品目标

- 首页按品类筛选：消费电子、汽车与交通、光学及医疗、食品与农业等，单产品可独立发布。
- 产品视图：从产品到部件、工艺、材料、化工中间体、自然资源，多级折叠、缩放、搜索、技术路径高亮。
- 节点详情：来源、材料别名、相关企业、产能、市场份额（年份/地区/分母）、替代可行性。
- 反向查询：从原材料或公司查找下游关联产品，明确区分技术可达、披露的业务合作与真实采购。

## 决策：全局属性图 + 多个产品视图

传统树形 JSON 会重复存放PC、甲醇、原油与公司，导致跨产品无法统一查询。
采用全局 entity 表作为 canonical identity，edge 表作为有方向且有证据等级的关系。
产品专属 product_view_node 只存节点呈现和父子路径，不创造新的材料实体。
图的数据方向一律 upstream -> downstream；在 UI 中产品作为根向上游展开，方向是反着画的。

## 同一材料与歧义消除

1. 稳定 entity_id （如 MAT:PC、CHEM:BPA），不使用名称作外键。
2. entity_alias 保存简体中文、英文、化学式、CAS 号等别名；需要同义词人工审核。
3. 镜片光学级PC与通用PC可定义两个 grade 实体；不能用通用PC市场份额直接代替眼镜级市场份额。
4. 生产工艺的 OR 分支、替代供给与真正的多输入配方必须分开标识。

## 数据证明：两种不同性质的边

- material_input/component_of/processed_into：技术/工艺关系，可由专利、生产原理或行业资料支持，不能证明发生企业采购。
- supplied_to：企业供货关系，要求时间、业务范围和出处；新闻披露只能证明对应报道日期。
- potential_substitute：替代研究假设，不等于已完成客户认证。
- 所有市场份额同时保存 subject、geography、year、metric、denominator、source；禁止跨口径相加。
- 未披露供应商不得强行匹配已知企业。

## 三层交付

1. **研究层（authoring）**：每个产品采用独立 data/products/{slug}/ 目录，使用可审核的 JSON/CSV/YAML 维护数据；共享实体用 ID 引用。
2. **处理层（pipeline）**：Python 内置 sqlite3 对数据校验、导入、溯源和统计汇总，构建只读快照。
3. **展示层（public UI）**：GitHub Pages 只托管静态 HTML/CSS/JS 和 JSON / gzip 快照；不运行 SQLite 服务，不处理私有信息。

## 业务查询示例

- 上游追溯：从产品沿 component_of/material_input 边反向进行 BFS，去重并按工艺路线分组。
- 下游影响：从某种原材料沿同类边向最终产品 BFS，返回产品名称、每条技术路径、证据等级。
- 公司集中度：market_share 聚合必须 GROUP BY market_id；CR3 必须有完整前三名且口径一致，匿名和残缺排行禁止给出确定 CR3。
- 实际供货：只能在 supplied_to 且 evidence_status=verified 的关系上查找。

## 未来演进

- 数据量少于 100k 节点：SQLite 作为 source-of-truth，构建期使用 NetworkX/递归 CTE，前端采用可按需装载子图的 SVG 或 Cytoscape。
- 规模扩大后：API 服务提供路由、权限、企业风险、全文检索；可用 PostgreSQL + 递归 CTE 或图数据库投影，但无需第一天上 Neo4j。
- 高质量研究扩展：时间版本、法人/集团映射、工厂点位、HS 编码与贸易流、BOM 占比、不确定性区间、风险模拟。
- 仓库保护：所有自动添加的产品先走 PR + schema validation + source audit；禁止无人校验直接发布市场份额。
