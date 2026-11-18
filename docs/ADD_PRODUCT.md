# 增加一个新产品

最小流程：注册分类 → 产出独立研究包 → 规范化材料/企业ID → 完成证据审查 → 构建快照 → PR发布。

## 建议的产品文件目录

~~~text
data/products/{slug}/
  product.json        # id/slug/title/category/icon/status/versions
  components.csv      # 部件、工艺、物料，优先引用已有entity_id
  view_nodes.csv      # 可折叠产品树专属布局；可多次引用一个实体
  links.csv           # upstream_id,downstream_id,relation_type,confidence,source_id
  market_share.csv    # market_id,company_id,share,rank,year,denominator
  company.csv         # 新公司属性，仅新增，已有公司ID必须复用
  evidence.csv        # 披露原文、日期、URL、位置、可信度
  images/             # 产品照片和节点示意图（保留版权/来源）
~~~

## 质量检查门槛

1. slug全站唯一，分类从taxonomy读取，产品封面/图标拥有许可。
2. 每个新实体赋予持久ID；已存在的PC、苯酚或三井化学应复用全站entity_id。
3. 依赖图不得发生无解释的环路；工艺的替代路线不可误画成全需材料。
4. 任何TOP3都需明确年份、地理范围、出货量/金额/产能、分母、来源；缺第三名时不可标CR3。
5. 实际采购关系要求公开公告/合同/年报佐证；行业原理只能作为技术关系。
6. 自动构建审查通过并有预览截图后再合并PR。

## 后续功能

原料节点「查看下游产品」必须对整个数据库递归查询，而不是简单关键词搜索。
企业节点「关联产品」要区分：明确商业供货（有来源）、技术上可能相关（未证实采购）、品牌直接销售。

## 当前版本限制

首发UI从压缩的眼镜研究快照构建；通用 schema 已就绪。新增产品的生成器将逐步替换眼镜专用 build_site.py，不应复制眼镜的数据表与前端代码。
