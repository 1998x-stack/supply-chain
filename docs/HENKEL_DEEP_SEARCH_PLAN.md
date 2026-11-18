# 汉高胶黏剂 Deep Search 研究执行清单（独立于产品静态展示）

研究对象为企业品牌组合，必须逐层拆分，不能把全部物料视为同一SKU。当前73个视图节点、6个证据档案、42个节点情报快照，尚不足以宣称完成了企业供货图谱。

## P0：具体牌号（本轮已初步建档）
| 节点 | 一手核实 | 反证/缺口 | 验收 |
|---|---|---|---|
| LOCTITE 243 | 2025 TDS/SDS、固化条件、不同地区SKU | 供应商名单未知，2026新TDS版本 | TDS数值有单位和工况、版次、source |
| LOCTITE EA 9466 | A/B组分、混合比例、固化测试标准 | 不得把全部BPA/ECH视为具体配方 | resin/hardener准确、不能编客户 |
| TECHNOMELT EVA 5669 | 2022 TDS、应用温度、用途 | 2026牌号是否继续销售，实际上游厂商 | 声明旧版与有效性 |
| TECHNOMELT PUR9340 | 2025 TDS，湿气固化与温度 | 聚醇/异氰酸酯采购厂商未知 | 不与PUR9015物性混用 |
| TEROSON MS940 | 2026公告、SMP材料 | 无异氰酸酯但专有聚合物包未披露 | 不擅自写入PUR原料路线 |
| Henkel业务组合 | 2025年报和2026Q3公告 | 销售额不是市场份额 | 分母为业务部门，年份可比较但不混合 |

## P1：主要原料与设备
EVA、PVAc、PUR、环氧、SMP、多硫醇/氰基丙烯酸、增粘树脂、无机填料、混合脱泡/点胶设备等。
- 检索关键词必须带原料类别、具体牌号、企业制造商名、地区与年度；不能用“胶水TOP3”替代具体市场。
- 对每个材料寻找供应生产商/产能，及与汉高实际采购公告；没有合同就只记录技术供应可能性。
- 使用德国/美国/中国监管机构、厂家官方文件、专利与工业协会交叉核对。
- 含中国/全球份额的节点必须清楚市场产品分母；企业合计CR3不能包含并列第四人选。

## P2：上游资源与应用行业
乙烯、丙烯、醋酸乙烯酯、BPA、环氧氯丙烷、油气资源，以及汽车、电子、包装、轨交、航天等终端行业。
- 一般工业反应路径与具体汉高采购链严格分开。
- 官方案例声明行业应用，不证明SpaceX等任何指定客户认证采购。

## 命令

```bash
python scripts/research_cli.py seed-backlog --product henkel-adhesives --output build/research/henkel-backlog.json
python scripts/research_cli.py plan --product henkel-adhesives --node "TECHNOMELT PUR 9340" --output build/research/pur9340-deep-search-plan.json
python scripts/validate_intelligence.py data/products/henkel-adhesives/graph.json
python -m unittest discover -s tests -v
python scripts/build_site.py
```

**提醒**：`plan` 不自动联网、没有读取原文或调用LLM，必须通过实际researcher/critic/semantic-reviewer依次核查。
