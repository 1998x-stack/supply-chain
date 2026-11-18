# 眼镜供应链研究数据入库规范

本批研究有两个数据载体：

- `research/dossiers/eyewear/*-draft.json` 与 `research/ledgers/eyewear/*-ledger.json`：可审计、可逐来源复核的人工研究工件；`semantic_review.status=pending` 表示没有完成原文语义审批。
- `build/supply_chain.sqlite`：由 `scripts/build_site.py` 在构建过程中重新生成的研究数据库，包含 `node_dossier`、`research_claim`、`research_claim_source`、`research_gap`。不要提交二进制数据库作为权威数据源。

## 研究运行命令

```bash
python scripts/audit_eyewear.py --output build/research/eyewear_audit.json
python scripts/research_cli.py seed-backlog --product eyewear --output build/research/eyewear_backlog.json
python -m unittest discover -s tests -v
python scripts/build_site.py
```

当前节点内容经构建流程投放到前端可折叠的节点档案中。各来源使用 `RS:EYE:<node_id>:<local_source_id>` 命名空间，以免不同研究批次的 `S001` 混淆。引文位置一律记录为 `curated_excerpt`，不能假冒PDF页码/全文位置。

## SQLite查询样例

```sql
SELECT d.entity_id, d.status, d.as_of_date, COUNT(c.claim_id) AS claims
FROM node_dossier d LEFT JOIN research_claim c ON c.dossier_id=d.dossier_id
GROUP BY d.dossier_id ORDER BY claims DESC;

SELECT e.name_zh, g.question, g.priority, g.status
FROM research_gap g JOIN entity e ON e.entity_id=g.entity_id
WHERE g.status='open' ORDER BY e.name_zh;

SELECT c.claim_text,c.evidence_status,c.semantic_review_status,s.title,s.url
FROM research_claim c
JOIN research_claim_source r ON r.claim_id=c.claim_id
JOIN source s ON s.source_id=r.source_id
WHERE c.entity_id='NODE:EYE:N0195';
```

## 数据质量边界

`supported` 表示研究台账存在支持证据，但除非 `semantic_review_status=approved` 且有复核人员、复核日期，不得展示为已完成语义认证。该表不构成镜片企业真实采购合同、供应份额、报价或库存的证明。
