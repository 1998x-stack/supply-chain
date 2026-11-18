# 主张→证据→UI控件映射

| 数据类型 | UI位置 | 最少字段 | 禁止推导 |
|---|---|---|---|
| 技术物性 | 技术与原料 | SKU、值、单位、测试条件、source_id | 把不同牌号数值看作可比 |
| 市场份额 | 市场与企业 | geo、year、metric、denominator、company、percent、source | 以销售额或产量推市场份额 |
| 企业材料领域 | 市场与企业 | company、material、role、source | 企业已向本品牌供货 |
| 商务供货 | 公司合作/证据 | buyer、seller、material、event_date、source、review_status | 历史事件等于当前采购 |
| 技术上游 | 上下游 | from/to、relation_type、evidence_status | 分类边=材料输入 |
| 研究问题 | 风险与待办 | gap、priority、need | 缺失=不存在 |

页面输入只接受经构建脚本清洗验证的公开JSON快照。英文TDS数值与中文说明均需要准确适用范围。编码实现见 `web/assets/node_panel.js`。
