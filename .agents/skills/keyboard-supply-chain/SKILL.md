---
name: keyboard-supply-chain
description: 调查有线/无线机械键盘、霍尔磁轴、薄膜/剪刀脚键盘，从开关/键帽/PCB/芯片/电池经精细化工、金属和矿产到设备、下游和可审计商业关系。需要新增、更新键盘产业链节点及证据、排查BOM构型混淆时使用。
---

# 键盘产业链 Deep Search + 产品本体 + 节点证据技能

## 适用场景
更新 `data/products/keyboard/` 的技术图谱，补齐 `research/{ledgers,dossiers}/keyboard/`，或研究同一原材料在键盘/眼镜/胶黏剂之间的用途关联。先读根目录 `AGENTS.md`、`docs/RESEARCH_PIPELINE.md`、`docs/KEYBOARD_SUPPLY_CHAIN.md` 与本技能所有 references。

## 一、构型优先（最重要）
以“外接电脑键盘”而非“所有键盘BOM并集”为研究对象：
- `mechanical_usb`：机械金属接点+键帽+PCB+USB；**没有强制磁传感器或锂电**。
- `hall_usb`：磁体+Hall位置传感器+主控采样+PCB；**不自动拥有CHERRY金交叉点触点**。
- `membrane_usb`：薄膜电路+硅橡胶碗/可选剪刀脚+USB；**不假设MX机械轴**。
- `mechanical_ble`：机械轴+BLE SoC+电池；锂电与AA/AAA方案属于可替代分支。
- 光电轴、2.4G无线、Gasket减震、RGB、热插拔、滚轮/旋钮、铝框等为可选项，必须由具体SKU配置确认。
- 树导航中的 `associated_with` 代表分类/行业通用技术，不能当 `material_input` 或 confirmed procurement。

## 二、八层物料/工艺链
1. 成品/构型 → 物理子系统（键轴、键帽、机壳、定位板、PCB、供电）
2. 部件 → 具体型号/技术规格（金触点、滑块、Hall、ADC、MCU、无线芯片）
3. 复合材料 → PBT/ABS/PC/POM/PA、FR-4/铜箔、硅胶、金属、永久磁体、电池
4. 细分化学/金属 → PTA+BDO、苯乙烯/丙烯腈/丁二烯、氧化铝/电解铜
5. 基础化工 → 芳烃/C4/乙烯、硅氧烷、稀土分离/硅冶炼
6. 原矿/再生 → 铜精矿、铝土矿、稀土矿、石油天然气及回收料
7. 制造设备和公用工程 → 模具、注塑机、SMT、PCB制板、CNC、金属加工与测试。
8. 行业应用/服务 → OEM/ODM、工业软件、零售、售后与回收；单独显示，不混入技术原材料子树。

## 三、Deep Search节点研究闭环
1. `python scripts/research_coverage.py --product keyboard --priority P0 --limit 12` 获取待研究节点，先核对具体SKU/构型。
2. 用 `scripts/research_cli.py plan --product keyboard --node "节点名" --output ...` 生成检索计划；若本地已有 deep-search，可将其交给已连接的受控Agent按预算执行。
3. 至少尝试：厂家产品规格/TDS（例如CHERRY/Gateron）；标准组织USB-IF/Bluetooth SIG；芯片/材料官网（TI/Nordic/Isola）；政府/第三方（关键矿产或制造商财报）；竞争者/反证。
4. 每条事实建立 Claim + 精确Source + 适用型号/条件/地域/年份；引文出现≠语义支持。多篇同厂官网不算独立交叉验证。
5. 真实企业供应必须同时明确 **买方、卖方、料号/品级、交易范围、时间和来源**；“CHERRY有机械轴”不等于“某电脑厂采购CHERRY”。
6. 市场TOP3需要先固定分母：整机按金额/出货量；机械轴按出货件数；PCB按专业用途；磁传感器按应用品级。不同口径禁止相加/排序。
7. 产出 `research/ledgers/keyboard/<node>-ledger.json` 与同ID dossier 草稿；先审核，再SQLite导入和GitHub Pages发布。

## 四、模块特定核验规则
- **机械轴：** 接点结构/镀金体系、弹簧材料、轴芯聚合物、触发行程与寿命只作用于对应型号，CHERRY数据不能当所有轴体性能。
- **霍尔磁轴：** 永磁体与Hall IC需分开识别；磁体NdFeB和SmCo只能是候选，不得假定具体Gateron料号。
- **薄膜：** PET、银浆/碳墨、隔离层、橡胶碗要与机械轴分开；薄膜电路并非无电子控制器。
- **键帽：** PBT成分可能为混配，印字工艺（双色注塑/热升华/激光）不能混为一份材料BOM。
- **PCB：** Isola FR408HR只是公开材料型号，不代表所有FR-4或指定键盘厂家采购。板材品牌和PCB板厂不是同一企业角色。
- **固件协议：** QMK/ZMK是开源固件生态，USB-IF/Bluetooth SIG是标准制定者，不能归为键盘硬件供应商。
- **无线与电池：** 认证涉及BLE HOGP/USB HID/EMC、电池型号，某个Nordic芯片“支持”不等于实际OEM装机。

## 五、质量验收及发布
运行：
```bash
python scripts/validate_intelligence.py data/products/keyboard/graph.json
python scripts/research_coverage.py --product keyboard --priority P0 --limit 15
python -m unittest discover -s tests -v
node --test tests/test_keyboard_atlas.mjs
python scripts/build_site.py
python scripts/verify_pages_release.py --dist dist
```
- 对每条 `cross_links` 检查双端ID、关系枚举、原始来源与假设状态。不要重复与树边相同的(上下游、关系)。
- 新增第三产品后，首页/Pages审核必须同时包含眼镜、汉高、键盘，数据快照节点数、队列和证据状态需一致。
- 研究草稿并不代表被真人语义审查通过；现在的`reviewed`数量不应通过脚本强行提升。

## 资源
- `references/ontology.md`：构型/异或选项/BOM语义与图模型。
- `references/materials.md`：树脂、导电材料、磁性材料、半导体上游以及高风险推断。
- `references/evidence.md`：逐类官方来源与反证要求。
- `assets/task-template.json`：单节点审计任务模板。
- `scripts/run.py`：离线验证数据及输出P0任务。
