# Node dossier 数据字典
标识：node_id、canonical_entity_id、name_zh、name_en、category、aliases、product_slug、configuration。
技术：key_specs（数值/单位/工况）、formulation_variants、inputs、outputs、process_routes、equipment、substitutes。
经济：markets（geo/year/metric/denominator/source）、vendors（role/evidence）、capacity、unit_cost_scope、sensitivity。
风险：criticality、single_source、qualification_lead_time、export_controls(需核验)、recycle、substitution.
溯源：claims、sources、source_group、date、quote_location、semantic_review、open_questions。
所有未知值写 null/unknown，禁止统一填0。数量信息不得丢单位。
验证：来源链接可访问≠论断正确；公司拥有产线≠指定高性能牌号达到客户认证。
