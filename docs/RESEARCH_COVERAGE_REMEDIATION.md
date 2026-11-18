# 节点太多“尚未研究”的修复方案（研究覆盖 V4）

## 诊断
原前端用布尔表达式 Boolean(dossier || insight) 判断是否研究，使没有档案但已有结构信息的节点显示“尚未研究”。当前眼镜382节点/16档案，汉高73节点/6档案，共455节点/22档案；汉高还有42条技术笔记，其中可能与档案重叠。

## 研究成熟度（不等于事实置信度）
| 状态 | 含义 | 可显示 | 禁止 |
|---|---|---|---|
| structural_only | 有节点名、上下游和路径 | 已有结构与待调查问题 | 当作验证事实 |
| annotated | 无原文的研究笔记 | 待核实说明 | 当作真实技术指标 |
| source_note | 有直接来源的节点笔记 | 厂商TDS/公告摘要 | 等同八维深度档案 |
| dossier_pending | 有八维档案、证据论断 | 标注待语义复核的来源与指标 | 宣称已审核 |
| reviewed | 语义审核完成且档案已批准 | 特定范围通过审核的论断 | 推断所有客户合同 |

目录NAV不要求每个分组都做市场TOP3研究。更深的实质性材料、牌号、设备和工艺节点才是研究目标。

## 生成批次
~~~bash
python scripts/research_coverage.py --product eyewear --priority P0 --limit 15 --output build/research/eyewear_p0.json --report build/research/eyewear_coverage.json
python scripts/research_coverage.py --product henkel-adhesives --priority P0 --limit 12 --output build/research/henkel_p0.json --report build/research/henkel_coverage.json
~~~

离线队列包含ID、产业链路径、研究状态、调查问题、可执行Deep Search源类及反证要求；不自动检索、不伪造市场份额。研究者将真实原文写入 paired dossier/ledger，再人工审阅语义。

## Pages产物
- data/research_coverage.json：各产品覆盖率摘要
- data/{slug}_research_queue.json：优先35个深度搜索任务
- data/{slug}.json.gz：节点成熟度及结构化调查任务
- data/catalog.json：实际档案、带来源笔记、待建档目标数量

首页与节点面板现在显示结构性成果、资料成熟度与可复制的Deep Search任务。这个修复改善研究可视化和调度，不等于已经完成433个节点的独立实证工作。

## 后续逐批验收
优先8-15个P0节点：确定牌号与标准、至少一份打开的原始来源、独立反证、公司角色核验、市场分母、材料关系和业务关系的区分。若资料不足则保留UNKNOWN。详细规范参考 docs/RESEARCH_PIPELINE.md。
