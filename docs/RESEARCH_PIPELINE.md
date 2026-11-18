# 供应链 Deep Search 研究工程规范（v1）

## 一、三层真实关系：不能混淆
- 技术图：部件、材料、化工中间体、工艺、资源的原理和物料关系。
- 产业图：企业经营的产品、产能、工厂、控制关系、市场份额。
- 商业图：特定公司在特定时期向另一公司提供特定料号、认证或服务的有证据关系。

树只是一种展示。全局节点去重、版本、企业别名/母子集团、供应商匿名数据必须在数据库中规范保存。

## 二、九阶段研究闭环

1. **Scope**：产品slug、variant、configuration_id、版本、地区、年份、用途、产品边界，列出未知事项。
2. **WBS & BOM**：从功能分系统、物理BOM、工艺/原料、制造设备、工业服务五种视图建模；不可将功能属于误当作物料依赖。
3. **Triage**：关键性、技术壁垒、成本敏感、国家/企业集中度、待证断言选择P0/P1/P2优先级；382个展示节点须单独研究，不能算已核验。
4. **Deep Search**：运行研究计划，优先年报/财报原文、企业规格书、SEC或交易所、官方统计、标准/论文、专利，必要时第三方行业报告。至少搜索一次核心反证。
5. **Evidence Ledger**：每个原子主张Cxxx关联Sxxx，原文位置、逐字引文、支持/反对/背景、信息发布和抓取时间；转载同源同组，不按链接数量算独立证据。
6. **Dossier**：对每个节点填写 identity/technical/upstream/downstream/companies/market/risk/open_questions 八维档案，记录特定料号、检测条件、工艺备选、供应关系及局限。
7. **Semantic Review**：审核者打开实际原文、逐条检查语义蕴含、年份/分母/单位/范围，检索最强反证。机器只能验证结构/文本哈希/引文出现，不能代替这一环节。
8. **Graph Integration**：先归一entity_id/aliases/企业集团/工厂ID，保留产品配置和时间边界。经审查批准才将候选边转为已验证商业关系。
9. **Release & Refresh**：构建SQLite和Pages JSON只读快照；关键数据过期后重新核验，不覆盖历史观察。

## 三、每个节点的最少调查维度

| 分组 | 调查内容 | 特别注意 |
| --- | --- | --- |
| 身份 | CAS/HS/UNS/型号/牌号、别名、材料族 | 同名不同等级不可合并 |
| 功能 | 在产品中作用、性能参数、技术指标、试验工况 | 单位、检测标准与适用配置 |
| 上游 | 原料、中间体、设备、能耗、副产品、备选工艺 | 典型工艺不一定是该厂实际路线 |
| 下游 | 部件、其他产品、材料需求 | 技术关联不等于真实公司交易 |
| 企业 | 制造商/经销商/代工、集团、工厂、产能 | 母子公司集团并表 |
| 市场 | TOP3/CR3、地域、年份、产品范围、分母 | 产能/销量/销售额/买方采购份额不能混用 |
| 风险 | 单点、质量认证、贸易约束、替代进展 | 通用牌号不能推导光学/航天级认证 |
| 证据 | 原文定位、同源组、反证和研究缺口 | 标注FACT/INFERENCE/HYPOTHESIS/UNKNOWN/DISPUTED |

## 四、研究深度和审核门槛

DRAFT：数据可不完整，但必须可见未知/尚未研究标签。
REVIEWABLE：结构完整、关键来源与反证记录齐备，等待审核者判断原文是否真的支持。
PUBLISHABLE：核心断言语义复审通过，关键商业边有合同/企业公告/真实供货证据，审核者+日期完整。
DISPUTED：有实质冲突，保留双方证据，禁止作为确切结论排序。

字段完备度0-100仅表示档案覆盖，绝不是事实置信度。来源可打开、字符串引文匹配也不等于证实事实。

## 五、统计口径硬约束

MarketKey = product_scope + geography + year + metric + denominator + unit + grade.
只有统一口径且知道前三大经济集团份额才能求CR3。并列名次明确说明。公司的总PC产能不能代替光学PC牌号份额；国家镍矿产量占比不能当镍供应商市场份额。匿名供应商名单只能保留匿名占比，不可与名企猜测关联。

## 六、与deep-search项目的实际集成

参考 https://github.com/1998x-stack/deep-search 。本仓库 scripts/research_cli.py 的 plan 生成该项目 schemas/research-plan.schema.json 兼容的计划初稿。若在可信环境单独安装 deep-search，可用其搜索和审计CLI读取该文件；搜索需要外部授权与API配置，本仓库不会偷偷联网。

~~~bash
python3 scripts/research_cli.py plan --product eyewear --node "PC光学材料" --output build/research/pc-plan.json
python3 scripts/research_cli.py seed-backlog --product eyewear --output build/research/eyewear-backlog.json
python3 scripts/research_cli.py audit-ledger --input research/examples/ledger.json
python3 scripts/research_cli.py audit-dossier --input research/examples/node-dossier.json
python3 scripts/research_cli.py coverage --dossiers research/dossiers --output build/research/coverage.json
python3 scripts/research_cli.py validate-skills
~~~

deep-search证据JSON需要包含sources和claims及原文content；本仓库audit-ledger检查ID/quotes/hash/独立组提示，不会宣称语义事实审核。外部搜索不能未经授权下载版权数据库或绕过访问限制。

## 七、复杂航天产品专有规则

产品配置必须区分 Falcon 9、Falcon Heavy、Starship 等不同系统及不同版本；NASA SLS可作为公开系统工程示例，但不能把SLS子系统/供应商复制为SpaceX事实。version、revision、mission、flight/ground、qualification和interface是独立字段。公开信息没有内部BOM时显示未知。不得猜测保密供应商或敏感军工细节。

参考 NASA Systems Engineering Processes and Requirements (NPR 7123.1B)：https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7123_001B_&page_name=all

## 八、持续维护

- 每个研究PR需要写明：研究问题、来源/日期、原文链接、反证搜索、改变的Claim/Edge、影响产品、测试结果、未知问题。
- 不可将已批准但旧年份数据自动升级为今年数据。提供版本/发布日期标注。
- 每周/每月自动重查属于可选独立自动化任务；仓库的CI不会主动触发LLM/商业搜索API。
- 提交前运行 tests、build_site、research_cli validate-skills 和证据账本审计。测试通过仅代表代码及结构健康。

## Cross-platform skill mirrors

Canonical: .agents/skills. macOS/Linux Git checkout supports symlinked skill directories. Windows without symlink privileges may run python tools/sync_skill_mirrors.py --copy to materialize identical copies; the validator accepts byte-identical copies. Running --check is read-only. --symlink restores links. The copy command refuses overwriting divergent local edits; back them up first. Pi can discover both .agents and .pi, and may show duplicate names depending on its version; prefer the canonical entry.

## Deep Search外部执行适配

研究计划生成不自动联网。在本地另行克隆 deep-search 并设置TAVILY_API_KEY后，由操作者显式运行 python3 scripts/deep_search_adapter.py --action search --deep-search-root ../deep-search --input build/research/pc-plan.json --output build/research/search.json --allow-network 。可用 --dry-run 先查看命令。验证台账或审计引用分别用 --action validate 和 --action audit；该CLI从不自动声称多源事实语义审核已完成。
