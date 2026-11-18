# 键盘产业链 Deep Search 第二轮研究计划

以 `python scripts/research_coverage.py --product keyboard --priority P0 --limit 15` 生成动态清单；不依赖本文件硬编码未更新的数量。

## 批次一：核心触发机制
- CHERRY机械轴：批次型号、触点金属/电镀、滑块树脂牌号、弹簧钢等级、操作寿命与原始测试条件。
- Gateron磁轴：微型磁体组分（NdFeB vs SmCo 仍为假设）、Hall IC来源与规格、电流、键程、温度漂移、用户可调触发一致性。
- 薄膜键盘：必须另找薄膜产品厂商的材料表和行业测试标准，不能借用金属触点机械轴结论。

## 批次二：关键塑料与结构
- PBT/ABS/PC/POM/PA各细分材料的制造商、地区产能、键盘级材料和价差，先确定牌号与成型工艺。
- 双/三色注塑模具寿命、键帽精度、字符耐磨、QC工艺与供应商，避免以KBDfans销售资料当树脂商。
- CNC铝板、钢定位板和结构件的材料批次认证、代工厂名单。

## 批次三：PCB、IC与无线电池
- PCB FR-4/铜箔/阻焊/表面处理及制板、SMT工厂；区分材料厂与制板厂。
- MCU、Hall IC、BLE SoC市场按相同用途、区域/年份/出货件数分别研究，不统一称“键盘芯片市场”。
- 确认具体键盘厂的料号认证，再记录客户与供应商关系。
- 有线USB、BLE HOGP、私有2.4GHz协议分开；识别电池方案是否可充电。

## 批次四：石化、矿产与产业集中
- PBT→PTA/BDO；ABS→苯乙烯/丙烯腈/丁二烯；PCB→玻纤/环氧/铜箔；永磁→稀土分离与磁体。
- 对每条矿业来源排除无证据的“同国生产即供给键盘整机”推断。
- 对全球/中国TOP3只提供同口径年份/地域/统计分母，无法核实时交付缺口、非虚构数字。

### 证据检查
使用 `multi-source-deep-search`、`node-dossier`、`industrial-process-tracing`、`company-market-intelligence`、`supplier-relationship-audit`、`cross-product-graph` 与 `research-quality-gate`。一个档案要有独立信源簇、负证搜索、原文定位和具体source_id，不能只“有17条链接”就算验证完成。
