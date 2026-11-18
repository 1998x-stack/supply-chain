-- Cross-product evidence-linked observations. Shares, production and technical tests retain distinct bases.
CREATE TABLE IF NOT EXISTS research_observation(
 observation_id TEXT PRIMARY KEY,
 entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 dossier_id TEXT NOT NULL REFERENCES node_dossier(dossier_id),
 observation_type TEXT NOT NULL,
 metric TEXT NOT NULL,
 value_num REAL,
 value_text TEXT,
 unit TEXT,
 geography TEXT,
 observation_year INTEGER,
 denominator TEXT,
 grade TEXT,
 test_condition TEXT,
 source_id TEXT NOT NULL REFERENCES source(source_id),
 origin_field TEXT NOT NULL,
 semantic_review_status TEXT NOT NULL DEFAULT 'pending'
 CHECK(semantic_review_status IN ('pending','approved','rejected','needs_rework')),
 CHECK(value_num IS NOT NULL OR value_text IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_research_observation_entity ON research_observation(entity_id,metric);
CREATE INDEX IF NOT EXISTS idx_research_observation_source ON research_observation(source_id);
