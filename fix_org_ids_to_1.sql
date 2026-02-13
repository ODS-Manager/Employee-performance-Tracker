-- Update the 148 users (EMP004-EMP151) to have org_id = 1 (ODS India)
-- Run this in Google Cloud Console SQL editor

-- First, check which users need to be updated (EMP004-EMP151 range)
SELECT employee_id, user_name, org_id 
FROM users 
WHERE employee_id >= 'EMP004' AND employee_id <= 'EMP151'
ORDER BY employee_id
LIMIT 10;

-- Count how many users will be affected
SELECT COUNT(*) as users_to_update
FROM users 
WHERE employee_id >= 'EMP004' AND employee_id <= 'EMP151';

-- Update all users with employee IDs EMP004-EMP151 to have org_id = 1
UPDATE users 
SET org_id = 1,
    modified_at = NOW()
WHERE employee_id >= 'EMP004' AND employee_id <= 'EMP151';

-- Verify the update worked
SELECT 
    org_id,
    COUNT(*) as user_count
FROM users 
GROUP BY org_id 
ORDER BY org_id;

-- Show total user count
SELECT COUNT(*) as total_users FROM users;