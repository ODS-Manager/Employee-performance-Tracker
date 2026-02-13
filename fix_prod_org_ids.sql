-- SQL script to fix orgId=null issue in production database
-- All users with employee IDs EMP004-EMP151 should have orgId=2 (ORG-IND)

-- First check current state
SELECT 'Current state:' as info;
SELECT 
    CASE 
        WHEN org_id IS NULL THEN 'NULL'
        ELSE CAST(org_id AS TEXT)
    END as org_id,
    COUNT(*) as user_count
FROM users 
GROUP BY org_id 
ORDER BY org_id;

-- Show sample users with null org_id
SELECT 'Sample users with NULL org_id:' as info;
SELECT id, employee_id, user_name, org_id 
FROM users 
WHERE org_id IS NULL 
LIMIT 5;

-- Update all users with NULL org_id to have org_id=2
UPDATE users 
SET org_id = 2 
WHERE org_id IS NULL;

-- Show results after update
SELECT 'After update:' as info;
SELECT 
    CASE 
        WHEN org_id IS NULL THEN 'NULL'
        ELSE CAST(org_id AS TEXT)
    END as org_id,
    COUNT(*) as user_count
FROM users 
GROUP BY org_id 
ORDER BY org_id;

-- Show total user count
SELECT 'Total users:' as info;
SELECT COUNT(*) as total_users FROM users;