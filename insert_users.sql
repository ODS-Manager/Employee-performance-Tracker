-- Insert superadmin and test users
INSERT INTO users (user_name, employee_id, password_hash, user_role, org_id, is_active, created_at) VALUES 
('admin', 'SUPER001', '$2b$12$FMuhy7gmmPePI4kCiQKqXeOVqPWymGkDl4l2ALuKUPacs5S9XlN1O', 'superadmin', NULL, true, CURRENT_TIMESTAMP),
('superadmin', 'SUPER002', '$2b$12$NNXMPUGvzk5LM3UxpGCAz.OaJ/icHFepqJvnsLFg3/cvlEWTDVv5O', 'superadmin', NULL, true, CURRENT_TIMESTAMP),
('teamlead', 'TL001', '$2b$12$FMuhy7gmmPePI4kCiQKqXeOVqPWymGkDl4l2ALuKUPacs5S9XlN1O', 'team_lead', 1, true, CURRENT_TIMESTAMP),
('employee', 'EMP001', '$2b$12$FMuhy7gmmPePI4kCiQKqXeOVqPWymGkDl4l2ALuKUPacs5S9XlN1O', 'employee', 1, true, CURRENT_TIMESTAMP);