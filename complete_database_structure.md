DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS employee_weekly_targets CASCADE;
DROP TABLE IF EXISTS password_reset_tokens CASCADE;
DROP TABLE IF EXISTS billing_details CASCADE;
DROP TABLE IF EXISTS billing_reports CASCADE;
DROP TABLE IF EXISTS attendance_audit_log CASCADE;
DROP TABLE IF EXISTS attendance_records CASCADE;
DROP TABLE IF EXISTS team_user_aliases CASCADE;
DROP TABLE IF EXISTS team_fa_names CASCADE;
DROP TABLE IF EXISTS fa_names CASCADE;
DROP TABLE IF EXISTS quality_audits CASCADE;
DROP TABLE IF EXISTS team_performance_metrics CASCADE;
DROP TABLE IF EXISTS employee_performance_metrics CASCADE;
DROP TABLE IF EXISTS order_history CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS divisions CASCADE;
DROP TABLE IF EXISTS order_status CASCADE;
DROP TABLE IF EXISTS process_types CASCADE;
DROP TABLE IF EXISTS transaction_types CASCADE;
DROP TABLE IF EXISTS user_teams CASCADE;
DROP TABLE IF EXISTS team_products CASCADE;
DROP TABLE IF EXISTS team_states CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_organizations_code ON organizations(code);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) UNIQUE NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_last_changed TIMESTAMP,
    must_change_password BOOLEAN DEFAULT false,
    token_version INTEGER DEFAULT 0 NOT NULL,
    user_role VARCHAR(20) NOT NULL,
    org_id INTEGER REFERENCES organizations(id),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    deactivated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_org_role ON users(org_id, user_role);
CREATE INDEX idx_users_employee_id ON users(employee_id);
CREATE INDEX idx_users_username ON users(user_name);
CREATE INDEX idx_users_last_login ON users(last_login);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    team_lead_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    daily_target INTEGER NOT NULL DEFAULT 10,
    monthly_target INTEGER DEFAULT NULL,
    single_seat_score DECIMAL(4,2) NOT NULL DEFAULT 1.0,
    step1_score DECIMAL(4,2) NOT NULL DEFAULT 0.5,
    step2_score DECIMAL(4,2) NOT NULL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_org ON teams(org_id);
CREATE INDEX idx_teams_lead ON teams(team_lead_id);

CREATE TABLE team_states (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    state VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX unique_team_state ON team_states(team_id, state);
CREATE INDEX idx_team_states_team ON team_states(team_id);

CREATE TABLE team_products (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    product_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX unique_team_product ON team_products(team_id, product_type);
CREATE INDEX idx_team_products_team ON team_products(team_id);

CREATE TABLE user_teams (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX unique_user_team ON user_teams(user_id, team_id);
CREATE INDEX idx_user_teams_user ON user_teams(user_id);
CREATE INDEX idx_user_teams_team ON user_teams(team_id);
CREATE INDEX idx_user_teams_team_active ON user_teams(team_id, is_active);
CREATE INDEX idx_user_teams_active ON user_teams(is_active);

CREATE TABLE transaction_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE process_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE divisions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fa_names (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fa_names_name ON fa_names(name);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    file_number VARCHAR(100) NOT NULL,
    entry_date DATE NOT NULL,
    transaction_type_id INTEGER NOT NULL REFERENCES transaction_types(id),
    process_type_id INTEGER NOT NULL REFERENCES process_types(id),
    order_status_id INTEGER NOT NULL REFERENCES order_status(id),
    division_id INTEGER NOT NULL REFERENCES divisions(id),
    state VARCHAR(5) NOT NULL,
    county VARCHAR(100) NOT NULL,
    product_type VARCHAR(100) NOT NULL,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    step1_user_id INTEGER REFERENCES users(id),
    step1_fa_name_id INTEGER REFERENCES fa_names(id) ON DELETE SET NULL,
    step1_start_time TIMESTAMP,
    step1_end_time TIMESTAMP,
    step2_user_id INTEGER REFERENCES users(id),
    step2_fa_name_id INTEGER REFERENCES fa_names(id) ON DELETE SET NULL,
    step2_start_time TIMESTAMP,
    step2_end_time TIMESTAMP,
    billing_status VARCHAR(20) DEFAULT 'pending',
    created_by INTEGER NOT NULL REFERENCES users(id),
    modified_by INTEGER REFERENCES users(id),
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (step1_end_time IS NULL OR step1_end_time >= step1_start_time),
    CHECK (step2_end_time IS NULL OR step2_end_time >= step2_start_time),
    CHECK (billing_status IN ('pending', 'done'))
);

CREATE UNIQUE INDEX idx_orders_file_product_team ON orders(file_number, product_type, team_id);
CREATE INDEX idx_orders_file_number ON orders(file_number);
CREATE INDEX idx_orders_org_team ON orders(org_id, team_id);
CREATE INDEX idx_orders_status ON orders(order_status_id);
CREATE INDEX idx_orders_dates ON orders(entry_date);
CREATE INDEX idx_orders_step1_user ON orders(step1_user_id);
CREATE INDEX idx_orders_step2_user ON orders(step2_user_id);
CREATE INDEX idx_orders_step1_fa_name ON orders(step1_fa_name_id);
CREATE INDEX idx_orders_step2_fa_name ON orders(step2_fa_name_id);
CREATE INDEX idx_orders_billing_status ON orders(billing_status);
CREATE INDEX idx_orders_step1_user_status ON orders(step1_user_id, order_status_id);
CREATE INDEX idx_orders_step2_user_status ON orders(step2_user_id, order_status_id);
CREATE INDEX idx_orders_team_status_date ON orders(team_id, order_status_id, entry_date);
CREATE INDEX idx_orders_deleted ON orders(deleted_at);

CREATE TABLE order_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    changed_by INTEGER NOT NULL REFERENCES users(id),
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_history_order ON order_history(order_id);
CREATE INDEX idx_history_user ON order_history(changed_by);
CREATE INDEX idx_history_order_time ON order_history(order_id, changed_at);
CREATE INDEX idx_history_change_type ON order_history(change_type);

CREATE TABLE employee_performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    team_id INTEGER REFERENCES teams(id),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    metric_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    total_orders_assigned INTEGER DEFAULT 0,
    total_step1_completed INTEGER DEFAULT 0,
    total_step2_completed INTEGER DEFAULT 0,
    total_single_seat_completed INTEGER DEFAULT 0,
    total_orders_completed INTEGER DEFAULT 0,
    total_working_minutes INTEGER DEFAULT 0,
    avg_step1_duration_minutes INTEGER,
    avg_step2_duration_minutes INTEGER,
    avg_order_completion_minutes INTEGER,
    orders_on_hold INTEGER DEFAULT 0,
    orders_completed INTEGER DEFAULT 0,
    orders_bp_rti INTEGER DEFAULT 0,
    efficiency_score DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    calculation_status VARCHAR(20) DEFAULT 'pending',
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX unique_emp_metrics ON employee_performance_metrics(user_id, metric_date, period_type);
CREATE INDEX idx_emp_metrics_org_period ON employee_performance_metrics(org_id, period_type, metric_date);
CREATE INDEX idx_emp_metrics_team_date ON employee_performance_metrics(team_id, metric_date);
CREATE INDEX idx_emp_metrics_date ON employee_performance_metrics(metric_date);
CREATE INDEX idx_emp_metrics_calc_status ON employee_performance_metrics(calculation_status);
CREATE INDEX idx_emp_metrics_deleted ON employee_performance_metrics(deleted_at);

CREATE TABLE team_performance_metrics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    metric_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    total_orders_assigned INTEGER DEFAULT 0,
    total_orders_completed INTEGER DEFAULT 0,
    total_orders_in_progress INTEGER DEFAULT 0,
    total_orders_on_hold INTEGER DEFAULT 0,
    total_orders_bp_rti INTEGER DEFAULT 0,
    total_team_working_minutes INTEGER DEFAULT 0,
    avg_order_completion_minutes INTEGER,
    active_employees_count INTEGER DEFAULT 0,
    team_efficiency_score DECIMAL(5,2),
    orders_per_employee DECIMAL(5,2),
    completion_rate DECIMAL(5,2),
    transaction_breakdown TEXT,
    product_breakdown TEXT,
    state_breakdown TEXT,
    calculation_status VARCHAR(20) DEFAULT 'pending',
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX unique_team_metrics ON team_performance_metrics(team_id, metric_date, period_type);
CREATE INDEX idx_team_metrics_org_period ON team_performance_metrics(org_id, period_type, metric_date);
CREATE INDEX idx_team_metrics_date ON team_performance_metrics(metric_date);
CREATE INDEX idx_team_metrics_calc_status ON team_performance_metrics(calculation_status);
CREATE INDEX idx_team_metrics_deleted ON team_performance_metrics(deleted_at);

CREATE TABLE quality_audits (
    id SERIAL PRIMARY KEY,
    examiner_id INTEGER NOT NULL REFERENCES users(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    process_type VARCHAR(100) NOT NULL,
    ofe INTEGER NOT NULL,
    files_with_error INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    files_with_cce_error INTEGER NOT NULL DEFAULT 0,
    total_files_reviewed INTEGER NOT NULL,
    ofe_count INTEGER NOT NULL,
    fb_quality DECIMAL(5,4) NOT NULL,
    ofe_quality DECIMAL(5,4) NOT NULL,
    cce_quality DECIMAL(5,4) NOT NULL,
    audit_date DATE NOT NULL,
    audit_period_start DATE,
    audit_period_end DATE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    modified_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    CHECK (ofe > 0),
    CHECK (files_with_error >= 0),
    CHECK (total_errors >= 0),
    CHECK (files_with_cce_error >= 0),
    CHECK (total_files_reviewed >= 0),
    CHECK (fb_quality >= 0 AND fb_quality <= 1),
    CHECK (ofe_quality >= 0 AND ofe_quality <= 1),
    CHECK (cce_quality >= 0 AND cce_quality <= 1)
);

CREATE TABLE team_fa_names (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    fa_name_id INTEGER NOT NULL REFERENCES fa_names(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_team_fa_name_id ON team_fa_names(team_id, fa_name_id);

CREATE TABLE team_user_aliases (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fa_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_team_user_aliases_team_user ON team_user_aliases(team_id, user_id);
CREATE INDEX idx_team_user_aliases_user ON team_user_aliases(user_id);
CREATE UNIQUE INDEX uq_team_user_alias ON team_user_aliases(team_id, user_id);

CREATE TABLE attendance_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    marked_by INTEGER NOT NULL REFERENCES users(id),
    marked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER REFERENCES users(id),
    modified_at TIMESTAMP,
    org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    notes TEXT
);

CREATE INDEX idx_attendance_user_date ON attendance_records(user_id, date);
CREATE INDEX idx_attendance_team_date ON attendance_records(team_id, date);
CREATE INDEX idx_attendance_org_date ON attendance_records(org_id, date);
CREATE INDEX idx_attendance_status ON attendance_records(status);
CREATE INDEX idx_attendance_marked_by ON attendance_records(marked_by);
CREATE UNIQUE INDEX unique_attendance_record ON attendance_records(user_id, team_id, date);

CREATE TABLE attendance_audit_log (
    id SERIAL PRIMARY KEY,
    attendance_record_id INTEGER REFERENCES attendance_records(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(20) NOT NULL,
    notes TEXT
);

CREATE INDEX idx_audit_record ON attendance_audit_log(attendance_record_id);
CREATE INDEX idx_audit_user ON attendance_audit_log(user_id);
CREATE INDEX idx_audit_date ON attendance_audit_log(date);
CREATE INDEX idx_audit_changed_by ON attendance_audit_log(changed_by);

CREATE TABLE billing_reports (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    billing_month INTEGER NOT NULL,
    billing_year INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    created_by INTEGER NOT NULL REFERENCES users(id),
    finalized_by INTEGER REFERENCES users(id),
    finalized_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_billing_org_team_period ON billing_reports(org_id, team_id, billing_year, billing_month);
CREATE INDEX idx_billing_status ON billing_reports(status);
CREATE INDEX idx_billing_period ON billing_reports(billing_year, billing_month);

CREATE TABLE billing_details (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES billing_reports(id) ON DELETE CASCADE,
    state VARCHAR(5) NOT NULL,
    product_type VARCHAR(100) NOT NULL,
    single_seat_count INTEGER DEFAULT 0,
    only_step1_count INTEGER DEFAULT 0,
    only_step2_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_billing_details_report ON billing_details(report_id);
CREATE INDEX idx_billing_details_state_product ON billing_details(state, product_type);

CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_password_reset_user ON password_reset_tokens(user_id);
CREATE UNIQUE INDEX idx_password_reset_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_user_expiry ON password_reset_tokens(user_id, expires_at);
CREATE INDEX idx_password_reset_used ON password_reset_tokens(used_at);

CREATE TABLE employee_weekly_targets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    target INTEGER NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX unique_user_team_week ON employee_weekly_targets(user_id, team_id, week_start_date);
CREATE INDEX idx_weekly_targets_user ON employee_weekly_targets(user_id);
CREATE INDEX idx_weekly_targets_team ON employee_weekly_targets(team_id);
CREATE INDEX idx_weekly_targets_week ON employee_weekly_targets(week_start_date);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    entity_name VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    changes JSON,
    old_values JSON,
    new_values JSON,
    user_id INTEGER,
    username VARCHAR(255),
    user_role VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    endpoint VARCHAR(255),
    request_method VARCHAR(10),
    description TEXT,
    reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER
);

CREATE INDEX idx_audit_entity_action ON audit_logs(entity_type, action);
CREATE INDEX idx_audit_entity_id_created ON audit_logs(entity_type, entity_id, created_at);
CREATE INDEX idx_audit_user_created ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_org_created ON audit_logs(organization_id, created_at);
CREATE INDEX idx_audit_created_desc ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_entity_lookup ON audit_logs(entity_type, entity_id, action);

INSERT INTO organizations (name, code, is_active) VALUES 
('ODS - IND', 'IND', true),
('ODS - VNM', 'VNM', true);

INSERT INTO transaction_types (name, is_active) VALUES 
('Sale/Cash', true),
('Sale w/Mortgage', true),
('Refinance', true),
('HELOC', true);

INSERT INTO process_types (name, is_active) VALUES 
('Step1', true),
('Step2', true),
('Single Seat', true);

INSERT INTO order_status (name, is_active) VALUES 
('Completed', true),
('On-hold', true),
('BP and RTI', true),
('In Progress', true);

INSERT INTO divisions (name, description) VALUES 
('Direct', 'Direct business operations'),
('Agency', 'Agency business operations');

INSERT INTO teams (org_id, name, is_active) VALUES 
(1, 'Florida', true),
(1, 'California', true),
(1, 'GI Clearing', true),
(1, 'Washington', true),
(1, 'Michigan', true),
(1, 'Colorado', true),
(1, 'Utah', true),
(1, 'Oregon', true),
(1, 'Regional Streamline', true),
(1, 'National Streamline', true),
(1, 'FIF', true),
(1, 'SCB & PD', true),
(1, 'Arizona', true),
(1, 'Texas', true),
(1, 'Pennsylvania', true),
(1, 'Ohio', true);

INSERT INTO team_states (team_id, state) VALUES 
(1, 'FL'),
(2, 'CA'),
(3, 'AZ'), (3, 'CA'), (3, 'TX'),
(4, 'WA'),
(5, 'MI'),
(6, 'CO'),
(7, 'UT'),
(8, 'OR'),
(9, 'WA'), (9, 'CA'), (9, 'FL'), (9, 'UT'), (9, 'NV'), (9, 'TX'), (9, 'IL'), (9, 'CO'), (9, 'AZ'), (9, 'HI'), (9, 'IN'), (9, 'MI'), (9, 'PA'), (9, 'GA'), (9, 'MO'), (9, 'OH'), (9, 'OR'), (9, 'SD'), (9, 'ME'), (9, 'KY'), (9, 'NE'), (9, 'OK'), (9, 'KS'), (9, 'WV'), (9, 'CT'), (9, 'NH'), (9, 'AL'), (9, 'SC'), (9, 'NC'), (9, 'DC'), (9, 'IA'), (9, 'VA'), (9, 'TN'), (9, 'MA'), (9, 'WI'), (9, 'ND'), (9, 'RI'),
(10, 'WA'), (10, 'CA'), (10, 'FL'), (10, 'UT'), (10, 'NV'), (10, 'TX'), (10, 'IL'), (10, 'CO'), (10, 'AZ'), (10, 'HI'), (10, 'IN'), (10, 'MI'), (10, 'PA'), (10, 'GA'), (10, 'MO'), (10, 'OH'), (10, 'OR'), (10, 'SD'), (10, 'ME'), (10, 'KY'), (10, 'NE'), (10, 'OK'), (10, 'KS'), (10, 'WV'), (10, 'CT'), (10, 'NH'), (10, 'AL'), (10, 'SC'), (10, 'NC'), (10, 'DC'), (10, 'IA'), (10, 'VA'), (10, 'TN'), (10, 'MA'), (10, 'WI'), (10, 'ND'), (10, 'RI'),
(11, 'NV'), (11, 'AZ'), (11, 'FL'), (11, 'TN'), (11, 'IN'), (11, 'CO'), (11, 'MI'), (11, 'MO'), (11, 'MS'), (11, 'MN'), (11, 'IL'), (11, 'PA'), (11, 'NM'), (11, 'MT'), (11, 'MD'), (11, 'GA'), (11, 'NC'), (11, 'ME'), (11, 'NH'), (11, 'NE'), (11, 'KY'), (11, 'NJ'), (11, 'DC'), (11, 'RI'), (11, 'SC'), (11, 'DE'), (11, 'MA'), (11, 'VT'),
(12, 'WA'), (12, 'CA'), (12, 'FL'), (12, 'UT'), (12, 'NV'), (12, 'TX'), (12, 'IL'), (12, 'CO'), (12, 'AZ'), (12, 'HI'), (12, 'IN'), (12, 'MI'), (12, 'PA'), (12, 'GA'), (12, 'MO'), (12, 'OH'), (12, 'OR'), (12, 'SD'), (12, 'ME'), (12, 'KY'), (12, 'NE'), (12, 'OK'), (12, 'KS'), (12, 'WV'), (12, 'CT'), (12, 'NH'), (12, 'AL'), (12, 'SC'), (12, 'NC'), (12, 'DC'), (12, 'IA'), (12, 'VA'), (12, 'TN'), (12, 'MA'), (12, 'WI'), (12, 'ND'), (12, 'RI'),
(13, 'AZ'),
(14, 'TX'),
(15, 'PA'),
(16, 'OH');

INSERT INTO team_products (team_id, product_type) VALUES 
(1, 'Full Search'), (1, 'Update'), (1, 'Date Down'), (1, 'Amend Title'), (1, 'Screening'), (1, 'M&B'),
(2, 'Full Search'), (2, 'Update'), (2, 'Date Down'), (2, 'Amend Title'),
(3, 'GI Clearing'),
(4, 'Full Search'), (4, 'Update'), (4, 'Date Down'), (4, 'Amend Title'),
(5, 'Full Search'), (5, 'Update'), (5, 'Date Down'), (5, 'Amend Title'),
(6, 'Full Search'), (6, 'Update'), (6, 'Date Down'), (6, 'Amend Title'),
(7, 'Full Search'), (7, 'Update'), (7, 'Date Down'), (7, 'Amend Title'),
(8, 'Full Search'), (8, 'Update'), (8, 'Date Down'), (8, 'Amend Title'),
(9, 'RS Clear'), (9, 'RS Review'), (9, 'RS Search'), (9, 'RS No C2G'),
(10, 'NS Clear'), (10, 'NS Review'), (10, 'NS Search'), (10, 'NS No C2G'),
(11, 'FAST'), (11, 'Traditional'),
(12, 'Schedule B'), (12, 'Product Delivery'),
(13, 'Full Search'), (13, 'Update'), (13, 'Date Down'), (13, 'Amend Title'),
(14, 'Full Search'), (14, 'Update'), (14, 'Date Down'), (14, 'Amend Title'),
(15, 'Search and Exam'), (15, 'Vendor Search'),
(16, 'Full Search'), (16, 'Vendor Exam'), (16, 'Screening'), (16, 'Update');

INSERT INTO fa_names (name, is_active) VALUES 
('Aaron', true), ('Adam', true), ('Alan', true), ('Albert', true), ('Alex', true), ('Alisa', true), ('Ally', true), ('Amelia', true), ('Anding', true), ('Angelina', true), ('Anne', true), ('April', true), ('Arthur', true), ('Asher', true), ('Astin', true), ('Augustin', true), ('Aura', true), ('Aurora', true),
('Benjamin', true), ('Bill', true),
('Calvin', true), ('Camile', true), ('Carter', true), ('Catherine', true), ('Charlie', true), ('Charles', true), ('Claudia', true), ('Colleen', true), ('Cynthia', true),
('Daniel', true), ('David', true), ('Dennis', true), ('Diana', true), ('Dimitar', true), ('Dixon', true), ('Donald', true), ('Dorcas', true), ('Douglas', true), ('Dwayne', true),
('Ebenezer', true), ('Edward', true), ('Edwin', true), ('Elena', true), ('Emily', true), ('Erika', true), ('Esther', true), ('Eva', true),
('Felix', true),
('Gabriella', true), ('Gavril', true), ('Gerald', true), ('Glen', true), ('Gon', true),
('Hananiah', true), ('Hanna', true), ('Harper', true),
('Jack', true), ('Jaime', true), ('Jake', true), ('James', true), ('Jammy', true), ('Janice', true), ('Jason', true), ('Jaxon', true), ('Jeffrey', true), ('Jemimah', true), ('Jennifer', true), ('Jennie', true), ('Jerome', true), ('Jessica', true), ('Jessie', true), ('Jillian', true), ('John', true), ('Johanna', true), ('Joseph', true), ('Justin', true),
('Kelli', true), ('Kevin', true), ('Kimberly', true), ('Kosta', true), ('Kurt', true), ('Kyle', true), ('Kyler', true), ('Kyrie', true),
('Laura', true), ('Leo', true), ('Lily', true), ('Liora', true), ('Lisa', true), ('Livina', true), ('Louise', true), ('Luke', true),
('Madison', true), ('Malena', true), ('Marc', true), ('Marco', true), ('Maria', true), ('Mark', true), ('Martin', true), ('Mary', true), ('Mason', true), ('Matthew', true), ('Mauro', true), ('Maverick', true), ('Maxo', true), ('Maya', true), ('Meghan', true), ('Melvin', true), ('Mercy', true), ('Merylyn', true), ('Mona', true), ('Morgan', true), ('Morris', true),
('Nanny', true), ('Natalie', true), ('Nicholas', true), ('Nija', true), ('Nila', true), ('Nira', true), ('Nyra', true),
('Olivia', true), ('Oliviya', true),
('Parker', true), ('Patricia', true), ('Paula', true),
('Ralph', true), ('Regina', true), ('Rene', true), ('Reni', true), ('Richard', true), ('Robert', true), ('Robinson', true), ('Roger', true), ('Rosa', true), ('Rudolph', true), ('Ruth', true), ('RyanB', true), ('RyanT', true),
('Sam', true), ('Sandy', true), ('Sara', true), ('Sarah', true), ('Scott', true), ('Seren', true), ('Sharon', true), ('Sheila', true), ('Simon', true), ('Sophie', true), ('Stanly', true), ('Stark', true), ('Stephan', true), ('Sylvia', true),
('Teresa', true), ('Tessa', true), ('Thomas', true), ('Tim', true), ('Tommy', true),
('Valerie', true), ('Victor', true), ('Vincent', true),
('White', true), ('William', true),
('Zara', true);

INSERT INTO team_fa_names (team_id, fa_name_id, is_active)
SELECT DISTINCT
    t.team_num as team_id,
    fn.id as fa_name_id,
    true as is_active
FROM (
    SELECT 1 as team_num, 'Erika' as name UNION ALL
    SELECT 1, 'Gerald' UNION ALL SELECT 1, 'Ralph' UNION ALL SELECT 1, 'Mona' UNION ALL SELECT 1, 'Camile' UNION ALL SELECT 1, 'Olivia' UNION ALL SELECT 1, 'John' UNION ALL SELECT 1, 'William' UNION ALL SELECT 1, 'Patricia' UNION ALL SELECT 1, 'Joseph' UNION ALL SELECT 1, 'Alex' UNION ALL SELECT 1, 'Meghan' UNION ALL SELECT 1, 'James' UNION ALL SELECT 1, 'Donald' UNION ALL SELECT 1, 'April' UNION ALL SELECT 1, 'Kyrie' UNION ALL SELECT 1, 'Calvin' UNION ALL SELECT 1, 'Dwayne' UNION ALL SELECT 1, 'Mercy' UNION ALL SELECT 1, 'Richard' UNION ALL SELECT 1, 'Dorcas' UNION ALL SELECT 1, 'Maverick' UNION ALL SELECT 1, 'Augustin' UNION ALL
    SELECT 2, 'Victor' UNION ALL SELECT 2, 'Parker' UNION ALL SELECT 2, 'Angelina' UNION ALL SELECT 2, 'Justin' UNION ALL SELECT 2, 'Paula' UNION ALL SELECT 2, 'White' UNION ALL SELECT 2, 'Claudia' UNION ALL SELECT 2, 'Marc' UNION ALL SELECT 2, 'Luke' UNION ALL SELECT 2, 'Colleen' UNION ALL SELECT 2, 'Thomas' UNION ALL SELECT 2, 'Hananiah' UNION ALL SELECT 2, 'Janice' UNION ALL SELECT 2, 'Kurt' UNION ALL SELECT 2, 'Sam' UNION ALL SELECT 2, 'Sylvia' UNION ALL SELECT 2, 'Simon' UNION ALL SELECT 2, 'Diana' UNION ALL SELECT 2, 'Malena' UNION ALL SELECT 2, 'Elena' UNION ALL SELECT 2, 'Tessa' UNION ALL SELECT 2, 'Jaime' UNION ALL SELECT 2, 'Matthew' UNION ALL SELECT 2, 'Marco' UNION ALL SELECT 2, 'Jessie' UNION ALL SELECT 2, 'Kimberly' UNION ALL
    SELECT 3, 'Jessica' UNION ALL SELECT 3, 'Lisa' UNION ALL SELECT 3, 'Sharon' UNION ALL SELECT 3, 'Jillian' UNION ALL
    SELECT 4, 'Roger' UNION ALL SELECT 4, 'Daniel' UNION ALL SELECT 4, 'Aaron' UNION ALL SELECT 4, 'Mary' UNION ALL SELECT 4, 'Cynthia' UNION ALL SELECT 4, 'Arthur' UNION ALL SELECT 4, 'Asher' UNION ALL SELECT 4, 'Amelia' UNION ALL SELECT 4, 'Sophie' UNION ALL SELECT 4, 'Adam' UNION ALL SELECT 4, 'Madison' UNION ALL SELECT 4, 'Natalie' UNION ALL
    SELECT 5, 'Alisa' UNION ALL SELECT 5, 'Martin' UNION ALL SELECT 5, 'Bill' UNION ALL SELECT 5, 'Reni' UNION ALL SELECT 5, 'Jennifer' UNION ALL SELECT 5, 'Jerome' UNION ALL SELECT 5, 'Kevin' UNION ALL
    SELECT 6, 'Mark' UNION ALL SELECT 6, 'Gabriella' UNION ALL SELECT 6, 'Dennis' UNION ALL SELECT 6, 'Nira' UNION ALL SELECT 6, 'Ally' UNION ALL SELECT 6, 'Felix' UNION ALL
    SELECT 7, 'Jaxon' UNION ALL SELECT 7, 'Maxo' UNION ALL SELECT 7, 'Vincent' UNION ALL SELECT 7, 'Robinson' UNION ALL SELECT 7, 'Jemimah' UNION ALL SELECT 7, 'Seren' UNION ALL SELECT 7, 'Scott' UNION ALL SELECT 7, 'Dixon' UNION ALL
    SELECT 8, 'Harper' UNION ALL SELECT 8, 'Catherine' UNION ALL SELECT 8, 'Hanna' UNION ALL SELECT 8, 'Nila' UNION ALL SELECT 8, 'Jennie' UNION ALL SELECT 8, 'Stark' UNION ALL SELECT 8, 'Livina' UNION ALL SELECT 8, 'Edwin' UNION ALL SELECT 8, 'Charlie' UNION ALL
    SELECT 9, 'Louise' UNION ALL SELECT 9, 'Maria' UNION ALL SELECT 9, 'Aurora' UNION ALL SELECT 9, 'Eva' UNION ALL SELECT 9, 'Jeffrey' UNION ALL SELECT 9, 'James' UNION ALL SELECT 9, 'Laura' UNION ALL SELECT 9, 'David' UNION ALL SELECT 9, 'Sara' UNION ALL SELECT 9, 'Gavril' UNION ALL SELECT 9, 'Zara' UNION ALL SELECT 9, 'Carter' UNION ALL SELECT 9, 'Maya' UNION ALL SELECT 9, 'Jack' UNION ALL SELECT 9, 'Sarah' UNION ALL SELECT 9, 'Kelli' UNION ALL SELECT 9, 'Regina' UNION ALL SELECT 9, 'Ruth' UNION ALL SELECT 9, 'RyanB' UNION ALL SELECT 9, 'Anding' UNION ALL SELECT 9, 'Valerie' UNION ALL SELECT 9, 'Kosta' UNION ALL SELECT 9, 'RyanT' UNION ALL
    SELECT 10, 'Glen' UNION ALL SELECT 10, 'Robert' UNION ALL SELECT 10, 'Anne' UNION ALL SELECT 10, 'Lily' UNION ALL SELECT 10, 'Mason' UNION ALL SELECT 10, 'Aura' UNION ALL SELECT 10, 'Kyler' UNION ALL SELECT 10, 'Astin' UNION ALL SELECT 10, 'Sam' UNION ALL
    SELECT 11, 'Jammy' UNION ALL SELECT 11, 'Leo' UNION ALL SELECT 11, 'Dixon' UNION ALL SELECT 11, 'Rudolph' UNION ALL SELECT 11, 'Claudia' UNION ALL SELECT 11, 'Jessica' UNION ALL SELECT 11, 'Nija' UNION ALL SELECT 11, 'Donald' UNION ALL SELECT 11, 'Nicholas' UNION ALL SELECT 11, 'Mauro' UNION ALL SELECT 11, 'Merylyn' UNION ALL SELECT 11, 'Dimitar' UNION ALL SELECT 11, 'Rosa' UNION ALL
    SELECT 12, 'Jake' UNION ALL SELECT 12, 'Sandy' UNION ALL
    SELECT 13, 'Morgan' UNION ALL SELECT 13, 'Kyle' UNION ALL SELECT 13, 'Liora' UNION ALL SELECT 13, 'Benjamin' UNION ALL SELECT 13, 'Stanly' UNION ALL SELECT 13, 'Edward' UNION ALL SELECT 13, 'Nanny' UNION ALL SELECT 13, 'Jason' UNION ALL SELECT 13, 'Sheila' UNION ALL SELECT 13, 'Teresa' UNION ALL SELECT 13, 'Mercy' UNION ALL
    SELECT 14, 'Tommy' UNION ALL SELECT 14, 'Douglas' UNION ALL SELECT 14, 'Morris' UNION ALL SELECT 14, 'Emily' UNION ALL SELECT 14, 'Mark' UNION ALL SELECT 14, 'Stephan' UNION ALL SELECT 14, 'Esther' UNION ALL SELECT 14, 'Johanna' UNION ALL
    SELECT 15, 'Rene' UNION ALL SELECT 15, 'Alan' UNION ALL SELECT 15, 'Richard' UNION ALL SELECT 15, 'Tim' UNION ALL SELECT 15, 'Gon' UNION ALL SELECT 15, 'Albert' UNION ALL SELECT 15, 'Charles' UNION ALL SELECT 15, 'Nyra' UNION ALL SELECT 15, 'Oliviya' UNION ALL
    SELECT 16, 'Melvin' UNION ALL SELECT 16, 'Ebenezer' UNION ALL SELECT 16, 'Merwin' UNION ALL SELECT 16, 'Jeff'
) t
JOIN fa_names fn ON fn.name = t.name;