-- Complete Database Setup Script
-- Execute these commands in Google Cloud Console in the following order:

-- STEP 1: Create Operations team (if needed)
INSERT INTO teams (org_id, name, is_active, created_at, modified_at)
VALUES (1, 'Operations', true, NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- STEP 2: Get the Operations team ID for later use
-- Run this query and note the returned ID:
SELECT id as operations_team_id FROM teams WHERE name = 'Operations' LIMIT 1;

-- STEP 3: Update user roles based on CSV data
UPDATE users SET user_role = 'superadmin', modified_at = NOW()
WHERE user_name IN ('prasanna');

UPDATE users SET user_role = 'admin', modified_at = NOW()
WHERE user_name IN ('sathishkumar');

UPDATE users SET user_role = 'team_lead', modified_at = NOW()
WHERE user_name IN ('karthik', 'sathiyathirth', 'deepan', 'sathish', 'venkatesh', 'charles', 'priyanka', 'rajeswari');

UPDATE users SET user_role = 'employee', modified_at = NOW()
WHERE employee_id >= 'EMP004' AND employee_id <= 'EMP151'
AND user_name NOT IN ('prasanna', 'sathishkumar', 'karthik', 'sathiyathirth', 'deepan', 'sathish', 'venkatesh', 'charles', 'priyanka', 'rajeswari');

-- STEP 4: Assign users to teams
-- Replace 'OPERATIONS_TEAM_ID' with the actual ID from STEP 2

-- Operations team (2 users: Prasanna-superadmin, Sathishkumar-admin)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, OPERATIONS_TEAM_ID, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('prasanna', 'sathishkumar')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- California team (Karthik-lead, Deepan-lead, Sathish-lead + 12 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('karthik', 'deepan', 'sathish')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('kokila', 'deepa', 'kavitha', 'yuvaraj', 'praveenram', 'selvaraj', 'karthik', 'obulakshmi', 'malathi', 'aravind', 'tharageshwari', 'srikanth', 'pavithra', 'logesh')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Florida team (Sathiyathirth-lead + 12 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sathiyathirth'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('jayakanthan', 'santhoshviji', 'karthikeyan', 'dhanasekaran', 'suruthi', 'sangeetha', 'kamalakannan', 'arunprakash', 'revathy', 'nivetha', 'narayana', 'mohanapriya', 'devagi')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- GI Clearing team (3 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 3, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('menaka', 'saaradhappriya', 'anbukarasi')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Washington team (11 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('dinesh', 'allwin', 'karthikeyamugunthan', 'gunapoorani', 'akhilan', 'vetrivel', 'elakkiya', 'ramya', 'sathish', 'muralidharan', 'sugavaneshwari')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Michigan team (Venkatesh-lead + 4 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'venkatesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('vivek', 'bhuvaneshwari', 'elakkiya', 'arun')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Colorado team (4 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 6, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('pavithra', 'varadharajan', 'sandhiya', 'kavin')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Utah team (Charles-lead + 4 examiners)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'charles'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('suresh', 'arun', 'prabu', 'navanithan', 'reshma')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Oregon team (Priyanka-lead, Rajeswari-lead + remaining users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name IN ('priyanka', 'rajeswari')
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- Assign remaining users to Oregon team (all users not already assigned)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u 
WHERE u.employee_id >= 'EMP004' 
  AND u.employee_id <= 'EMP151'
  AND u.id NOT IN (
    SELECT DISTINCT user_id 
    FROM user_teams 
    WHERE team_id IN (1, 2, 3, 4, 5, 6, 7, OPERATIONS_TEAM_ID)
  )
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  modified_at = NOW();

-- STEP 5: Update team_lead_id in teams table
UPDATE teams SET team_lead_id = (SELECT id FROM users WHERE user_name = 'karthik' LIMIT 1), modified_at = NOW() WHERE id = 1; -- California
UPDATE teams SET team_lead_id = (SELECT id FROM users WHERE user_name = 'sathiyathirth' LIMIT 1), modified_at = NOW() WHERE id = 2; -- Florida  
UPDATE teams SET team_lead_id = (SELECT id FROM users WHERE user_name = 'venkatesh' LIMIT 1), modified_at = NOW() WHERE id = 5; -- Michigan
UPDATE teams SET team_lead_id = (SELECT id FROM users WHERE user_name = 'charles' LIMIT 1), modified_at = NOW() WHERE id = 7; -- Utah
UPDATE teams SET team_lead_id = (SELECT id FROM users WHERE user_name = 'priyanka' LIMIT 1), modified_at = NOW() WHERE id = 8; -- Oregon

-- STEP 6: Verify the setup
SELECT 'Team membership summary:' as info;
SELECT 
    t.name as team_name,
    COUNT(ut.user_id) as member_count,
    COUNT(CASE WHEN ut.role = 'lead' THEN 1 END) as lead_count,
    COUNT(CASE WHEN ut.role = 'member' THEN 1 END) as member_count
FROM teams t
LEFT JOIN user_teams ut ON t.id = ut.team_id AND ut.is_active = true
WHERE t.org_id = 1 AND t.is_active = true
GROUP BY t.id, t.name
ORDER BY t.name;