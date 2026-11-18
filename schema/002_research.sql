-- Versioned research schema: apply after 001_core.sql, never replace historical records silently.
CREATE TABLE IF NOT EXISTS product_configuration(
 configuration_id TEXT PRIMARY KEY,product_id TEXT NOT NULL REFERENCES product(product_id),
 variant_name TEXT NOT NULL,revision TEXT,mission_profile TEXT,effective_from TEXT,effective_to TEXT,
 disclosure_state TEXT NOT NULL DEFAULT 'public_partial'
 CHECK(disclosure_state IN ('public_complete','public_partial','unknown','restricted')),notes TEXT
);
CREATE TABLE IF NOT EXISTS configuration_member(
 configuration_id TEXT NOT NULL REFERENCES product_configuration(configuration_id),
 entity_id TEXT NOT NULL REFERENCES entity(entity_id),quantity REAL CHECK(quantity IS NULL OR quantity>=0),
 quantity_unit TEXT,part_number TEXT NOT NULL DEFAULT '',revision TEXT,source_id TEXT REFERENCES source(source_id),
 PRIMARY KEY(configuration_id,entity_id,part_number)
);
CREATE TABLE IF NOT EXISTS research_run(
 run_id TEXT PRIMARY KEY,product_id TEXT REFERENCES product(product_id),started_at TEXT NOT NULL,
 completed_at TEXT,researcher TEXT,research_scope TEXT NOT NULL,search_budget INTEGER,
 outcome TEXT NOT NULL DEFAULT 'draft' CHECK(outcome IN ('draft','partial','reviewed','blocked')),
 artifact_path TEXT,stop_reason TEXT
);
CREATE TABLE IF NOT EXISTS node_dossier(
 dossier_id TEXT PRIMARY KEY,entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 product_id TEXT REFERENCES product(product_id),configuration_id TEXT REFERENCES product_configuration(configuration_id),
 run_id TEXT REFERENCES research_run(run_id),version TEXT NOT NULL,as_of_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('draft','reviewable','publishable','disputed')),
 weighted_field_coverage REAL CHECK(weighted_field_coverage BETWEEN 0 AND 100),
 semantic_reviewer TEXT,reviewed_at TEXT,file_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS research_claim(
 claim_id TEXT PRIMARY KEY,entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 dossier_id TEXT REFERENCES node_dossier(dossier_id),claim_text TEXT NOT NULL,
 claim_type TEXT NOT NULL DEFAULT 'fact',
 evidence_status TEXT NOT NULL CHECK(evidence_status IN ('supported','partially_supported','disputed','unverified','refuted')),
 geography TEXT,period_start TEXT,period_end TEXT,
 product_configuration_id TEXT REFERENCES product_configuration(configuration_id),
 analysis TEXT,semantic_review_status TEXT NOT NULL DEFAULT 'pending'
 CHECK(semantic_review_status IN ('pending','approved','rejected','needs_rework')),
 last_reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS research_claim_source(
 claim_id TEXT NOT NULL REFERENCES research_claim(claim_id),
 source_id TEXT NOT NULL REFERENCES source(source_id),quote_location TEXT NOT NULL,exact_quote TEXT,
 polarity TEXT NOT NULL CHECK(polarity IN ('supports','contradicts','context')),
 content_hash TEXT,origin_group TEXT,
 PRIMARY KEY(claim_id,source_id,quote_location)
);
CREATE TABLE IF NOT EXISTS technical_spec(
 spec_id TEXT PRIMARY KEY,entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 configuration_id TEXT REFERENCES product_configuration(configuration_id),
 spec_name TEXT NOT NULL,value_num REAL,value_text TEXT,unit TEXT,test_condition TEXT,grade TEXT,
 effective_year INTEGER,source_id TEXT REFERENCES source(source_id),
 claim_id TEXT REFERENCES research_claim(claim_id),
 CHECK(value_num IS NOT NULL OR value_text IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS system_interface(
 interface_id TEXT PRIMARY KEY,from_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 to_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 configuration_id TEXT REFERENCES product_configuration(configuration_id),
 interface_type TEXT NOT NULL,revision TEXT,verification_state TEXT NOT NULL DEFAULT 'unverified',
 source_id TEXT REFERENCES source(source_id),CHECK(from_entity_id<>to_entity_id)
);
CREATE TABLE IF NOT EXISTS relationship_review(
 edge_id TEXT NOT NULL REFERENCES edge(edge_id),reviewer TEXT NOT NULL,reviewed_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('approved','needs_rework','rejected','stale')),
 evidence_scope TEXT,limitation TEXT,PRIMARY KEY(edge_id,reviewer,reviewed_at)
);
CREATE TABLE IF NOT EXISTS entity_resolution_candidate(
 candidate_id TEXT PRIMARY KEY,candidate_a_id TEXT NOT NULL REFERENCES entity(entity_id),
 candidate_b_id TEXT NOT NULL REFERENCES entity(entity_id),similarity_reason TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('proposed','merged','rejected','needs_review')),
 evidence_source_id TEXT REFERENCES source(source_id),reviewer TEXT,reviewed_at TEXT,
 CHECK(candidate_a_id<>candidate_b_id)
);
CREATE TABLE IF NOT EXISTS research_gap(
 gap_id TEXT PRIMARY KEY,entity_id TEXT NOT NULL REFERENCES entity(entity_id),
 dossier_id TEXT REFERENCES node_dossier(dossier_id),question TEXT NOT NULL,
 priority TEXT NOT NULL CHECK(priority IN ('P0','P1','P2','unrated')),
 blocking INTEGER NOT NULL DEFAULT 0 CHECK(blocking IN (0,1)),
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','investigating','resolved','unresolvable')),
 evidence_needed TEXT,resolution_claim_id TEXT REFERENCES research_claim(claim_id)
);
CREATE INDEX IF NOT EXISTS idx_dossier_entity ON node_dossier(entity_id,as_of_date);
CREATE INDEX IF NOT EXISTS idx_claim_entity_status ON research_claim(entity_id,evidence_status);
CREATE INDEX IF NOT EXISTS idx_claim_source ON research_claim_source(source_id);
CREATE INDEX IF NOT EXISTS idx_conf_member_entity ON configuration_member(entity_id);
CREATE INDEX IF NOT EXISTS idx_gap_priority ON research_gap(priority,status);
