# 电脑键盘产业链调研报告｜2026-11-18｜研究初版

## 一、范围与结果
新增仓库产品 `keyboard`，覆盖外接电脑键盘及其多种技术构型（**不是一款指定SKU的真实BOM**），包括机械接点键盘、Hall磁轴键盘、橡胶碗薄膜键盘、USB有线、蓝牙BLE和私有2.4GHz无线。

- **165个技术视图节点**、八个一级分支，向上游分解至化学中间体、金属冶炼、矿产和设备公用工程。
- **27条跨分支关系**按 `component_of`、`associated_with`、`uses_equipment` 等类型区分；重复于树的关联不再次建边。
- **17条公开技术/标准来源**、**30条附来源节点笔记**、**12份八维研究草稿**及其证据台账；待人工语义核验，并非完成全部市场和供货调查。
- 标准化实体：13条**键盘作用域的暂定材料/器件实体**，暂不凭字符串相同与眼镜/胶黏剂材料自动合并。
- **市场份额TOP3：未知**。企业技术能力、厂家自报规格和行业应用不作为采购合同或全球市占率。

## 二、八大分支与重要路径

| 分支 | 子系统 | 核心深层材料 |
|---|---|---|
| A 构型 | 机械/磁轴/薄膜；USB/BLE/2.4GHz；电竞/办公/分体 | 多构型选择不是并集BOM |
| B 键轴 | CHERRY MX2A、Gateron KS20、轴芯、金触点、弹簧、Hall IC、永久磁体、薄膜触点 | 工程塑料、弹簧钢、金、磁体材料、电子级硅 |
| C 键帽与框架 | PBT/ABS键帽、双色注塑、热升华、CNC铝机壳、钢/铝/FR-4定位板 | PBT→PTA+BDO；ABS→苯乙烯+丙烯腈+丁二烯；铝土矿→氧化铝→铝 |
| D PCB电子 | FR-4层压板、铜箔、MCU、矩阵二极管、USB、RGB、热插拔 | 玻纤/环氧树脂、铜矿/再生铜、半导体晶圆 |
| E 无线能源 | BLE SoC/天线/接收器、nRF52840、充电电芯、充电IC、ZMK | 2.4GHz射频半导体、电池材料、电源管理 |
| F 原料资源 | PBT、ABS、PC、POM、PET、硅胶、铜、铝、金、永磁及硅晶圆 | 基础化工、矿产/再生料及公用工程 |
| G 制造质检 | 注塑机、卷簧、SMT、PCB蚀刻、CNC、阳极氧化、磁传感校准 | 工厂/设备与耗材，不是交付键盘的物理组成 |
| H 市场循环 | 组装ODM、器件供应商、零售、终端、维修与回收 | 商业与产品下游，不应假设实名采购 |

## 三、基础技术事实（厂家/标准公开，非行业审计）

- CHERRY的MX系列产品公开了塑料滑块、精密弹簧、金交叉点接点、轴体底座结构。资料来源：https://www.cherry.de/en-us/product/mx2a-red
- Gateron KS-20 Magnetic White描述永磁体与霍尔传感检测原理，厂商列出了特定型号的键程和初始磁场指标。这不是所有磁轴的统一性能。来源：https://gateron.com/products/gateron-ks-20-magnetic-white-switch-set
- TI的2025年键盘应用笔记解释用Hall磁场随磁体运动的变化进行位置检测，且位置传感系统与机械接点不同。来源：https://www.ti.com/lit/an/slya093/slya093.pdf
- QMK说明键盘行列矩阵扫描及USB HID的输入处理流程，但不能从QMK代码反推某OEM的MCU采购。来源：https://docs.qmk.fm/how_a_matrix_works
- Bluetooth SIG HOGP v1.2是2026年规范，定义蓝牙LE上的HID通信，不是硬件供应商。来源：https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/hogp_v1-2_1777405843/HOGP_v1.2/out/en/index-en.html
- Nordic nRF52840是公开的SoC候选芯片，其规格不是任意蓝牙键盘已经采用的证据。来源：https://www.nordicsemi.com/Products/nRF52840/GetStarted?lang=zh-CN
- Isola FR408HR为一个FR-4增强材料等级；DSC玻璃化温度等性能只能作用于该型号，不能外推到全部键盘PCB。来源：https://www.isola-group.com/pcb-laminates-prepreg/fr408hr-laminate-and-prepreg/
- KBDfans说明PBTfans键帽可以使用PBT混合配方或ABS，不能假定全部PBT键帽=100% PBT。来源：https://kbdfans.com/pages/about-pbtfans-doubleshot

## 四、集中度、市场份额及国产替代调查缺口

按下列独立市场逐个核验：机械轴全球/中国出货件数、磁轴传感IC份额、键帽制造份额、精密PCB材料、控制MCU、2.4GHz无线SoC、永磁微型磁体、整机电竞/办公键盘。必须按年、区域、产品规格、分母和指标的同口径TOP3；本版本**没有独立可信资料**计算上述产品层级前三名。

可优先研究的替代难点：Hall采样一致性、键轴批次手感和寿命、PBT改性配方/模具稳定性、键盘级无线功耗与射频认证、配套固件测试体系。以上是**研究假设/调查方向**，不是已验证的产业瓶颈排名或国产替代市场规模。

### 高优先级节点
P0：MX机械轴/金触点、Gateron KS20、Hall IC、磁体等级、PBT/ABS键帽、FR4、铜箔、键盘主控、BLE SoC、USB/BLE协议与设备制造工艺。

## 五、数据边界与审计
- 12份档案仍处于 `reviewable_draft` 且 `semantic_review=pending`。
- 所有真实采购关系表在本次无合同证据时保持空数组；公司—材料关系只标记**产品/技术能力类别**，并注明不构成OEM订货。
- 芯片是否用于某品牌必须提供设计资料/联合公告/认证或明确买卖证据。公开芯片规格仅证明供货能力。
- 本轮商品零售价格、CR3、总产能、供货合同、塑料树脂专用级均保留UNKNOWN。
- 研究队列自动生成，但不会自行联网或完成语义审核。

## 六、工具与文件
```bash
python scripts/validate_intelligence.py data/products/keyboard/graph.json
python scripts/research_coverage.py --product keyboard --priority P0 --limit 15
python scripts/research_cli.py seed-backlog --product keyboard --output build/research/keyboard-backlog.json
python scripts/build_site.py
python scripts/verify_pages_release.py --dist dist
```
- 节点图：`data/products/keyboard/graph.json`
- 产品注册：`data/products/keyboard/product.json`
- 档案：`research/dossiers/keyboard/*.json`
- 原子证据台账：`research/ledgers/keyboard/*.json`
- 专业技能：`.agents/skills/keyboard-supply-chain/`（同步至Codex/Pi/Claude）
- 网页：`#/products/keyboard`，会显示节点成熟度、已有来源、研究任务及反向技术关联。
