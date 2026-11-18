-- All 382 tree entries are view nodes; identity is reviewed separately.
CREATE TABLE IF NOT EXISTS view_node_resolution (
 view_node_id TEXT NOT NULL,
 product_id TEXT NOT NULL REFERENCES product(product_id),
 view_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 canonical_material_id TEXT REFERENCES entity(entity_id),
 label_key TEXT NOT NULL,
 identity_state TEXT NOT NULL CHECK(identity_state IN ('curated_exact','provisional_unique')),
 review_required INTEGER NOT NULL CHECK(review_required IN (0,1)),
 PRIMARY KEY(product_id,view_node_id),
 FOREIGN KEY(product_id,view_node_id) REFERENCES product_view_node(product_id,view_node_id)
);
CREATE INDEX IF NOT EXISTS idx_resolution_canonical ON view_node_resolution(canonical_material_id);
CREATE TABLE IF NOT EXISTS identity_candidate_group(
 group_id TEXT PRIMARY KEY,label_key TEXT NOT NULL,
 review_state TEXT NOT NULL DEFAULT 'needs_semantic_review',
 reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS identity_candidate_member(
 group_id TEXT NOT NULL REFERENCES identity_candidate_group(group_id),
 view_node_id TEXT NOT NULL,
 PRIMARY KEY(group_id,view_node_id)
);
CREATE TABLE IF NOT EXISTS material_reference_review(
 material_id TEXT PRIMARY KEY REFERENCES entity(entity_id),
 legacy_view_node_id TEXT,
 curated_exact_view_node_id TEXT,
 review_state TEXT NOT NULL CHECK(review_state IN ('curated_exact','associated_only')),
 reason TEXT
);
