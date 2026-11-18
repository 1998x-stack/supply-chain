# 拆解标准
- 为对象建立 product_slug、configuration_id、variant、version_date、geography、lifecycle_state。
- 树形 parent 表示“展示层级”，有向 edge 表示有证据的真实物料/制造/组件关系。
- 元素按硬件、软件、测试装备、生产设施、公用工程、物流/回收、监管约束分类。
- 先分解结构再拓展原材料，避免只列原油/矿山而遗漏关键加工工序。
- 禁止把供应链分层当做企业间真实交易历史。
- 对每一个可变配方建立 OR 备选组；对共需物料建立 AND 组。
- 依据 NASA Systems Engineering / WBS 方法识别系统边界，注意供应链内容是研究视图而非官方产品BOM。
- 证据：技术文献、厂商官方材料说明、专利、工业标准、监管文件；每条边均可追溯。
