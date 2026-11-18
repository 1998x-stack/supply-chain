# 眼镜382节点分批研究执行计划

以 `python scripts/build_priority.py` 输出作为计划；**P0/P1/P2仅为研究价值的规则性优先级**，不是供应商重要性、市占率或成本贡献的客观评分。

## 四条工作流（每轮必须全部审核）
1. **镜片原料 (P0)：** ADC/CR39（单体、加工）、MR高折射（多硫醇、异氰酸酯、光学参数）、光学级PC/BPA及历史苯酚采购链、体内与表面变色工艺、偏光与镀膜材料。用 `multi-source-deep-search` + `node-dossier` + `company-market-intelligence`。
2. **镜架 (P0/P1)：** 醋酸纤维素粉末/板材、TR90=PA MACM12、钛丝→海绵钛→氯化/镁还原、精密铰链与鼻托。用 `industrial-process-tracing` + `supplier-relationship-audit`。
3. **精密设备和功能层 (P0/P1)：** 车房自由曲面数控、AR真空镀膜、加硬旋涂/浸涂与光学膜料、真空泵/离子源、抛光耗材。区分设备商、耗材商、材料商、镜片OEM与终端品牌。
4. **全量身份 (382)：** 先稳定 `NODE:EYE:<node_id>`；只有 `curated_exact` 才关联 `MAT:<ID>`；同名不同级别或多原料混合表述只能提交去重候选。原有 `representative_node_id` 只可做上下文提示，不能自动产生采购或材料相同边。

## 每个P0节点的最低深度
- 基础身份：标准名、别名、CAS/UNS、牌号、配方属性（无法确认则null）。
- 关键制造：前驱体、可替代工艺、设备、产品层级、对应来源。
- 企业：制造商、分销商、业务合作、实际供货分别列出；客户来源有时间与产品范围。
- 数据：出货量/销售额/产能/产量按 **产品范围+区域+年份+计量单位+分母** 分别登记。
- Sources：至少一个一手资料与反证检索记录；重要市场排序尽量多来源独立核查，不强行凑3。
- 风险：替代路线、客户认证、产能地点、时效、对下游产品的影响。
- 论断：claim到source映射、摘要/原文区别、同源转载分组，语义复核状态和待研究项。
- 对所有未验证领域必须显著显示UNKNOWN。

## 验证与导出
```bash
python scripts/normalize_eyewear.py
python scripts/build_priority.py
python scripts/audit_eyewear.py --output build/research/eyewear_audit.json
python -m unittest discover -s tests -v
python scripts/build_site.py
```

可复核输出：
- `dist/data/eyewear_identity.json`：382条身份登记 + 同名候选组 + 原有29条材料代表节点审阅结果。
- `dist/data/eyewear_priority.json`：382条P0/P1/P2及研究现状。
- `build/supply_chain.sqlite`：规范化关系库与所有有证据的档案观测值。

**完成定义**：全量身份证书与研究优先级 ≠ 全部节点的行业资料认证。禁止把后者描述为完成。
