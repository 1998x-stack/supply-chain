# AGENTS.md

本仓库是多产品供应链知识图谱，采用证据优先的维护方式。

- 运行前请阅读 README.md、docs/ARCHITECTURE.md 和 docs/DATA_MODEL.md。
- 任何事实都必须写来源，不得虚构企业采购、排名、市场份额、工厂产能。
- 企业 market share（销售额/销量）与国家矿产产量不可混用；不得假设某企业供货给该产品。
- ID约束：一家公司、一个材料、一个工厂全站唯一；同名并不自动等价；按source_id维护证据链。
- 前端页面运行在GitHub Pages，不允许引入敏感密钥、API tokens或可识别个人信息。
- 变更数据库先通过 scripts/build_site.py 和 unittest，再合并；破坏兼容的schema需新迁移文件。
- 对未知数据使用 null / not_disclosed / hypothesis，不得填零或造精确份额。
