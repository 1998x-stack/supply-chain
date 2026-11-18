# 眼镜本轮研究交付说明

**状态：工程身份登记覆盖全部382个技术视图节点；实证市场/交易资料仍为逐节点分批研究。** 本轮16份档案，全部保持 `semantic_review.status=pending`。尚未核实的关键材料TOP3、产能和客户认证不伪造。

## 关键修复

1. 原始29条材料实体曾与仅18个不同的 `representative_node_id` 关联，其中BPA→PC树脂、醋酐→CA粉末、XDI→MR镜片等映射并不是精确的同一性。现在这些旧链接统一降级为 `associated_with`（上下文关联），并在 `material_reference_review` 中保存不一致审阅。
2. 新 `view_node_resolution` 给382个视图节点逐个登记；只有明确校对的15条材料身份建立 `MAT:* `链接，其余不合并。相同原材料显示名称形成候选组，人工审阅后才能共享实体。
3. 重复名称原树有356个不同显示名称，多个石油/苯/丙烯节点在不同分支重复。候选组不能直接合并“原油/天然气”等多原料合并表述。
4. 新增8份一手资料关联的节点研究档案，共16份研究草稿，覆盖CR39、MR、PC、变色、板材、钛、设备和铰链等；所有关系保留时间与来源。
5. 新增 `eyewear_priority.json`，按P0/P1/P2整理全部382节点。P0优先处理配方、专用料号、设备工艺与历史合同。

## 研究数值口径注意

- OBE公开“每年约500,000,000铰链组件”为集团自行披露，**不是全球市场份额**。
- USGS统计的中国2024年加工钛材约172,000吨，不是眼镜专用钛材。
- 历史Eastman-Marchon、Eastman-MYKITA和INEOS-Covestro供应合作须按公告年份解读，不能当2026年采购合同或采购量。
- 三井MR牌号折射率与EMS Grilamid TR90材料性质不等于对某家镜架/镜片品牌已实际供货。

## 质量命令

```bash
python scripts/normalize_eyewear.py
python scripts/build_priority.py
python scripts/audit_eyewear.py --output build/research/eyewear_audit.json
python -m unittest discover -s tests -v
python scripts/build_site.py
```

来源详见各节点 `research/ledgers/eyewear/`。当前没有批准 `publishable` 的语义审阅者，因此所有档案只作为证据未完备的公开研究草稿展示。
