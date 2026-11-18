---
name: node-evidence-panel
description: 设计多产品供应链节点研究面板，将TDS物性、公司、市场份额、来源与反向关联转化成可审计可交互界面；修改web前端或引入新领域时使用。
---

# 可审计节点情报面板设计

**调用边界：** 同时阅读 `AGENTS.md`、`docs/NODE_PANEL_DESIGN.md`、本技能 references 的验收规范。先确认对象是单一SKU、技术配方、业务组合，还是行业。

## 输入
- 当前选中节点稳定ID、产品slug、上下游节点类型与身份审核状态。
- `node_intelligence` 或 `research/dossiers` 中已有的技术指标、原子论断、源链接。
- `material_to_products` 与 company_material、market_share 的关系，保留技术/商业分离。

## 执行步骤
1. 首页清晰展示分类与产品，节点详情强制分“总览、技术与原料、市场与企业、上下游、原始证据、风险与待办”六个可切换标签。
2. 数字必须来源可见；物性显示牌号/单位/工况、市场显示地区/年限/指标/分母；不从null导出0%。
3. 证据展示 claims、source_id、原文链接、发布时间和审核状态；避免同来源多网页伪装多源独立验证。
4. 关系追溯显示 typed edge：分类不等于配方，制造技术能力不等于合同，历史合作不等于持续供货。
5. 键盘和小屏可使用；默认打开有价值的摘要，深层数据放折叠或独立标签，禁止简单输出原始JSON冒充UI。
6. 改动后运行前端语法检查、Python资料校验、SQLite外键校验与回归测试；完成必要的浏览器手工回归后才能声称完整UI已验收。

## 输出
`web/assets/node_panel.js`、`web/assets/node_panel.css`、数据模型与测试；对于缺失市场份额、客户名单、SDS的情况显式保留“未核实”。


## 节点面板状态及审查
- structural_only：只含技术树路径与描述，不能称为深度研究。
- annotated：有无来源笔记；source_note：有来源笔记。
- dossier_pending：八维档案与证据台账，但缺语义审查。
- reviewed：通过审阅人/日期的完成档案。
- NAV目录节点单列，不计入强制市场调查分母。应优先展示路径和上下游，而非简单标注“尚未研究”。