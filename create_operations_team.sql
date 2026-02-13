-- Create Operations team for admin/superadmin users
INSERT INTO teams (org_id, name, is_active, created_at, modified_at)
VALUES (1, 'Operations', true, NOW(), NOW())
ON CONFLICT (name) DO NOTHING;