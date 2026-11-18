# Supply Chain Atlas｜跨产品产业链知识图谱

[简体中文](README.md) · [架构](docs/ARCHITECTURE.md) · [数据模型](docs/DATA_MODEL.md) · [新增产品](docs/ADD_PRODUCT.md)

一个产品一个入口、全站共享材料与企业实体的供应链研究仓库。首个产品：**眼镜**，382个技术节点、42个企业实体、41条参考来源。技术树不等于企业采购关系。

## 功能

- 首页产品分类卡片，点击进入该产品供应链视图。
- 产品树可以缩放、拖动、分层折叠、搜索并点选节点。
- 节点详情显示上游/下游、标准材料ID、相关企业、市场份额与口径、技术替代研究和证据来源。
- sqlite3 规范化数据库带完整外键约束；同一材料和企业统一ID，供多个产品复用。
- GitHub Pages 静态托管，无服务器/API/访问令牌；源数据生成只读JSON快照。

## 本地构建

~~~bash
python3 scripts/build_site.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --directory dist
# http://localhost:8000/
~~~

构建结果：dist/ 为GitHub Pages静态网页；build/supply_chain.sqlite 为研究库。仅使用Python标准库和原生浏览器功能。

## 数据目录

- data/products/eyewear/intelligence_data.json.gz：前一阶段研究的源数据压缩快照；研究结论仍需按来源核实。
- schema/001_core.sql：跨产品实体、产品视图、证据关系、市场份额和产能模型。
- scripts/build_site.py：校验源数据、生成前端数据快照和规范化关系库。
- web/：静态网站源码，不含服务器逻辑。
- docs/：架构、Schema、数据治理、新产品注册流程。

## GitHub Pages 发布

Settings → Pages → Build and deployment → Source → **GitHub Actions**。然后把修改合并到 main，workflow 会校验、构建并发布 dist/。
预期URL：https://1998x-stack.github.io/supply-chain/（仅在 Pages 配置与部署成功后可用）。

## 统计口径与证据

- 份额必须保存 geography / year / denominator / metric / source。
- 匿名供应商维持匿名，不得与任一有名企业强行匹配。
- 工艺层面的关系必须标记 technological，不得以此宣称商业供货。
- 国产替代状态独立记录材料级别、认证和客户验证，不因总产能存在就判断已替代。

> 非投资建议。数据和市场份额来源于公开资料及前期归集，部分企业合作关系为历史披露，发布日期不是持续供货的保证。

## 持续扩展产品

~~~bash
python3 scripts/new_product.py smartphone --title 智能手机 --category electronics --icon 📱
~~~

把该产品的技术图谱、材料/企业和来源写入新目录的 graph.json，审核后将 product.json 中 published 改为 true。
构建器会自动扫描已发布产品，生成分类主页、单产品交互图和 material_id → 产品反向索引。
标准类别见 data/taxonomy/categories.json，完整规范见 docs/ADD_PRODUCT.md。

## Research Agent Skills 研究体系

已提供10个跨产品研究技能包，规范入口为 .agents/skills/<name>/SKILL.md，.claude/skills、.pi/skills和.codex/skills使用同步符号链接；Codex规范自动发现路径为.agents/skills。四类研究代理见.codex/agents和.claude/agents，详细流程参见 docs/RESEARCH_PIPELINE.md。

研究工具运行：

~~~bash
python3 scripts/research_cli.py validate-skills
python3 scripts/research_cli.py seed-backlog --product eyewear --output build/research/eyewear-backlog.json
python3 scripts/research_cli.py plan --product eyewear --node "光学级PC材料" --output build/research/pc-plan.json
python3 scripts/research_cli.py audit-ledger --input research/examples/ledger.json
python3 -m unittest discover -s tests -v
~~~

deep-search集成遵守其原始证据schema，但没有自动提供网络或LLM推理能力。Node coverage仅是字段完整度，不是事实正确率。复杂火箭示例是未核实的结构模板，不是SpaceX供应商清单。

### 第一个真实节点研究样例

眼镜/光学级PC档案：research/dossiers/eyewear/pc-optical-draft.json；证据账本：research/ledgers/eyewear/pc-optical-ledger.json；研究解读：research/dossiers/eyewear/pc-optical-report.md。此档案是 **REVIEWABLE DRAFT**，研究引用需要语义复核，PC全品类产能不代表光学级PC产能。其余展示节点仍需逐项研究。
