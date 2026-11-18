# 来源类型与独立性
A级：原始监管备案、生产商直接产品规格、已审计年报、官方产量数据、同行评审原始研究；依具体论断而定。
B级：行业机构报告原文、交易所公告、第三方检测、专利、标准原文。
C级：官方宣传材料、媒体对原始数据的转述、分析评论。
D级：转载、无来源图表、匿名传闻，仅能作搜索线索，不可单独支撑结论。
同一来源集团、转载链、共同引用第三方数据不构成多份独立证据；每条 Claim 记录 origin_group。
反证查询：revision, correction, retracted, alternate process, manufacturer no longer, patent expired, changed ownership；中文查询“更正”“澄清”“产能与销量区别”“官方回应”。
重要节点需同时寻找反证；公开检索结果未出现某关系不等于证明不存在。
证据状态采用 deep-search supported / partially_supported / disputed / unverified / refuted，和产品事实标签 FACT / INFERENCE / HYPOTHESIS / UNKNOWN 分开。

## 可执行Deep Search适配器

先生成计划：python3 scripts/research_cli.py plan --product eyewear --node PC --output build/research/pc-plan.json 。在可信本地环境单独安装/clone github.com/1998x-stack/deep-search，再明确授权搜索：python3 scripts/deep_search_adapter.py --action search --deep-search-root ../deep-search --input build/research/pc-plan.json --output build/research/search.json --allow-network 。该操作需要已设置TAVILY_API_KEY；无授权时不要自动调用。非联网证据校验：--action validate --input ledger.json；报告引用核验：--action audit --report report.md --ledger ledger.json。--dry-run仅输出命令，不执行外部工具。语义事实审核仍需审阅者。
