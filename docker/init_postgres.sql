-- PostgreSQL Initialization Script for Enterprise AI Act Registry

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL,
    department VARCHAR(64) NOT NULL,
    clearance_level INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_systems (
    system_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    risk_category VARCHAR(64) NOT NULL,
    annex_category VARCHAR(128),
    provider_name VARCHAR(128) NOT NULL,
    deployer_name VARCHAR(128) NOT NULL,
    department VARCHAR(64) NOT NULL,
    intended_purpose TEXT NOT NULL,
    conformity_status VARCHAR(32) DEFAULT 'under_assessment',
    registration_date VARCHAR(32) NOT NULL,
    last_audit_date VARCHAR(32),
    is_public_registry BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS compliance_assessments (
    assessment_id VARCHAR(32) PRIMARY KEY,
    system_id VARCHAR(32) REFERENCES ai_systems(system_id) ON DELETE CASCADE,
    auditor_id VARCHAR(64) NOT NULL,
    auditor_name VARCHAR(128) NOT NULL,
    assessment_type VARCHAR(64) NOT NULL,
    findings TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    risk_score FLOAT DEFAULT 0.0,
    remediation_plan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incident_reports (
    incident_id VARCHAR(32) PRIMARY KEY,
    system_id VARCHAR(32) REFERENCES ai_systems(system_id) ON DELETE CASCADE,
    incident_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    description TEXT NOT NULL,
    reported_to_ai_office BOOLEAN DEFAULT FALSE,
    status VARCHAR(32) DEFAULT 'open',
    occurred_at VARCHAR(32) NOT NULL,
    resolved_at VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS audit_log_records (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(64) NOT NULL,
    user_role VARCHAR(32) NOT NULL,
    action VARCHAR(64) NOT NULL,
    target_resource VARCHAR(128),
    status VARCHAR(32) NOT NULL,
    details TEXT NOT NULL,
    prev_hash VARCHAR(64) NOT NULL,
    record_hash VARCHAR(64) NOT NULL
);

