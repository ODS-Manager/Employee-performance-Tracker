-- Fix orgId=null issue for 148 newly added users (EMP004-EMP151)
-- Run this in Google Cloud Console SQL editor

-- First, check current state
SELECT 
    CASE 
        WHEN org_id IS NULL THEN 'NULL'
        ELSE CAST(org_id AS VARCHAR)
    END as org_id,
    COUNT(*) as user_count
FROM users 
GROUP BY org_id 
ORDER BY org_id;

-- Update all users with NULL org_id to have org_id=2 (ORG-IND)
UPDATE users 
SET org_id = (SELECT id FROM organizations WHERE name = 'ORG-IND'),
    modified_at = NOW()
WHERE org_id IS NULL;

-- Verify the fix
SELECT 
    CASE 
        WHEN org_id IS NULL THEN 'NULL'
        ELSE CAST(org_id AS VARCHAR)
    END as org_id,
    COUNT(*) as user_count
FROM users 
GROUP BY org_id 
ORDER BY org_id;

-- Show total user count
SELECT COUNT(*) as total_users FROM users;