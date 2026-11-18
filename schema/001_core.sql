PRAGMA foreign_keys=ON;
-- Core model: one canonical entity across all products; edges are directed upstream -> downstream.
CREATE TABLE IF NOT EXISTS entity (
  entity_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL CHECK(entity_type IN ('product','component','material','chemical','process','resource','equipment','service','company','facility','country')),
  name_zh TEXT NOT NULL, name_en TEXT, description TEXT, status TEXT NOT NULL DEFAULT 'active', canonical_key TEXT UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS entity_alias (
  entity_id TEXT NOT NULL REFERENCES entity(entity_id), alias TEXT NOT NULL, language TEXT DEFAULT 'zh',
  PRIMARY KEY(entity_id,alias)
);
CREATE TABLE IF NOT EXISTS category (
  category_id TEXT PRIMARY KEY, parent_id TEXT REFERENCES category(category_id), name_zh TEXT NOT NULL, icon TEXT
);
CREATE TABLE IF NOT EXISTS product (
  product_id TEXT PRIMARY KEY REFERENCES entity(entity_id), slug TEXT NOT NULL UNIQUE,
  category_id TEXT NOT NULL REFERENCES category(category_id), summary TEXT,
  icon TEXT, cover_image TEXT, published INTEGER NOT NULL DEFAULT 0 CHECK(published IN (0,1)), version TEXT NOT NULL DEFAULT '1'
);
CREATE TABLE IF NOT EXISTS company (
  company_id TEXT PRIMARY KEY REFERENCES entity(entity_id), group_id TEXT REFERENCES company(company_id),
  website TEXT, headquarters_country TEXT, ticker TEXT, ownership_note TEXT
);
CREATE TABLE IF NOT EXISTS facility (
  facility_id TEXT PRIMARY KEY REFERENCES entity(entity_id), operator_company_id TEXT REFERENCES company(company_id), country TEXT,
  latitude REAL, longitude REAL, start_date TEXT, end_date TEXT
);
CREATE TABLE IF NOT EXISTS source (
  source_id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
  publisher TEXT, published_on TEXT, accessed_on TEXT, source_type TEXT, archived_url TEXT
);
CREATE TABLE IF NOT EXISTS edge (
  edge_id TEXT PRIMARY KEY, upstream_id TEXT NOT NULL REFERENCES entity(entity_id),
  downstream_id TEXT NOT NULL REFERENCES entity(entity_id),
  relation_type TEXT NOT NULL CHECK(relation_type IN ('material_input','component_of','manufactures','market_participant','associated_with','produced_by','processed_into','supplied_to','announced_sourcing','commercial_collaboration','joint_development','joint_research_production','confirmed_material_adoption','uses_equipment','located_at','owns','alternative_to','potential_substitute')),
  evidence_status TEXT NOT NULL CHECK(evidence_status IN ('verified','technological','hypothesis','disputed','unknown')),
  valid_from TEXT, valid_to TEXT, geography TEXT, context_product_id TEXT REFERENCES product(product_id),
  condition TEXT, notes TEXT, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK(upstream_id <> downstream_id),
  UNIQUE(upstream_id,downstream_id,relation_type,context_product_id)
);
CREATE TABLE IF NOT EXISTS edge_source (
  edge_id TEXT NOT NULL REFERENCES edge(edge_id), source_id TEXT NOT NULL REFERENCES source(source_id),
  quote_location TEXT, assessment TEXT, PRIMARY KEY(edge_id,source_id)
);
CREATE TABLE IF NOT EXISTS product_view_node (
  product_id TEXT NOT NULL REFERENCES product(product_id), view_node_id TEXT NOT NULL,
  entity_id TEXT NOT NULL REFERENCES entity(entity_id), parent_view_node_id TEXT,
  display_label TEXT, display_order INTEGER NOT NULL DEFAULT 0,
  display_depth INTEGER, relation_note TEXT,
  PRIMARY KEY(product_id,view_node_id),
  FOREIGN KEY(product_id,parent_view_node_id) REFERENCES product_view_node(product_id,view_node_id)
);
CREATE TABLE IF NOT EXISTS product_bill_of_materials (
  product_id TEXT NOT NULL REFERENCES product(product_id), component_id TEXT NOT NULL REFERENCES entity(entity_id),
  quantity REAL, quantity_unit TEXT, share_percent REAL CHECK(share_percent BETWEEN 0 AND 100),
  scenario TEXT NOT NULL DEFAULT 'typical', alternative_group TEXT, source_id TEXT REFERENCES source(source_id),
  PRIMARY KEY(product_id,component_id,scenario)
);
CREATE TABLE IF NOT EXISTS market (
  market_id TEXT PRIMARY KEY, subject_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
  name_zh TEXT NOT NULL, geography TEXT NOT NULL, year INTEGER NOT NULL,
  metric TEXT NOT NULL, denominator TEXT NOT NULL, unit TEXT NOT NULL,
  methodology TEXT, source_id TEXT NOT NULL REFERENCES source(source_id)
);
CREATE TABLE IF NOT EXISTS market_share (
  market_id TEXT NOT NULL REFERENCES market(market_id), competitor_id TEXT REFERENCES company(company_id),
  label TEXT NOT NULL, share REAL CHECK(share BETWEEN 0 AND 100), rank INTEGER,
  estimated INTEGER NOT NULL DEFAULT 0, source_id TEXT REFERENCES source(source_id), notes TEXT,
  PRIMARY KEY(market_id,label)
);
CREATE TABLE IF NOT EXISTS capacity (
  observation_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL REFERENCES entity(entity_id),
  company_id TEXT REFERENCES company(company_id), facility_id TEXT REFERENCES facility(facility_id),
  year INTEGER NOT NULL, value REAL NOT NULL CHECK(value>=0), unit TEXT NOT NULL,
  metric TEXT NOT NULL, scope TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES source(source_id), notes TEXT
);
CREATE TABLE IF NOT EXISTS procurement_observation (
  observation_id TEXT PRIMARY KEY, buyer_id TEXT NOT NULL REFERENCES company(company_id),
  supplier_id TEXT REFERENCES company(company_id), supplier_public_label TEXT, supplier_rank INTEGER,
  year INTEGER NOT NULL, share_of_purchase REAL CHECK(share_of_purchase BETWEEN 0 AND 100),
  disclosed INTEGER NOT NULL CHECK(disclosed IN (0,1)), source_id TEXT NOT NULL REFERENCES source(source_id), notes TEXT,
  CHECK(disclosed=1 OR supplier_id IS NULL)
);
CREATE TABLE IF NOT EXISTS substitution_candidate (
  candidate_id TEXT PRIMARY KEY, target_entity_id TEXT NOT NULL REFERENCES entity(entity_id),
  candidate_company_id TEXT REFERENCES company(company_id), incumbent_company_id TEXT REFERENCES company(company_id),
  status TEXT NOT NULL CHECK(status IN ('idea','capacity_verified','grade_qualified','customer_qualified','commercialized','rejected')),
  validation_gap TEXT NOT NULL, source_id TEXT REFERENCES source(source_id), updated_on TEXT
);
CREATE INDEX IF NOT EXISTS idx_edge_up ON edge(upstream_id,relation_type);
CREATE INDEX IF NOT EXISTS idx_edge_down ON edge(downstream_id,relation_type);
CREATE INDEX IF NOT EXISTS idx_edge_context ON edge(context_product_id);
CREATE INDEX IF NOT EXISTS idx_pvn_entity ON product_view_node(entity_id);
CREATE INDEX IF NOT EXISTS idx_market_subject ON market(subject_entity_id,year,metric,geography);
CREATE INDEX IF NOT EXISTS idx_alias_text ON entity_alias(alias);
-- Upstream-to-product trace: only material_input/component_of/processed_into edges here.
-- Separately query supplied_to with evidence_status=verified for proven commercial relationships.

CREATE TABLE IF NOT EXISTS company_kpi (
  observation_id TEXT PRIMARY KEY,company_id TEXT NOT NULL REFERENCES company(company_id),
  year INTEGER NOT NULL,metric TEXT NOT NULL,value REAL NOT NULL,unit TEXT,
  source_id TEXT NOT NULL REFERENCES source(source_id),notes TEXT
);
