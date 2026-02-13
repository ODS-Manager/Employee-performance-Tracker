-- Team Assignment SQL Script
-- Generated from CSV data

-- First, get the Operations team ID after creation
-- Run create_operations_team.sql first, then get the team ID:
-- SELECT id FROM teams WHERE name = 'Operations' LIMIT 1;
-- Replace 'operations_team_id' with the actual ID returned

-- Update user roles based on CSV data
UPDATE users SET user_role = 'superadmin', modified_at = NOW()
WHERE user_name IN ('prasanna');

UPDATE users SET user_role = 'admin', modified_at = NOW()
WHERE user_name IN ('sathishkumar');

UPDATE users SET user_role = 'team_lead', modified_at = NOW()
WHERE user_name IN ('karthik', 'sathiyathirth', 'deepan', 'sathish', 'venkatesh', 'charles', 'priyanka', 'rajeswari', 'naagarjun', 'vairavel', 'karthikeyan', 'naveenkumar', 'balaji', 'daniel', 'mohanraj');

UPDATE users SET user_role = 'employee', modified_at = NOW()
WHERE user_name IN ('jayakanthan', 'santhoshviji', 'karthikeyan', 'dhanasekaran', 'suruthi', 'sangeetha', 'kamalakannan', 'arunprakash', 'revathy', 'nivetha', 'narayana', 'mohanapriya', 'devagi', 'kokila', 'deepa', 'kavitha', 'yuvaraj', 'praveenram', 'selvaraj', 'kavitha', 'karthik', 'obulakshmi', 'malathi', 'aravind', 'tharageshwari', 'srikanth', 'pavithra', 'logesh', 'menaka', 'saaradhappriya', 'anbukarasi', 'dinesh', 'allwin', 'karthikeyamugunthan', 'gunapoorani', 'akhilan', 'vetrivel', 'elakkiya', 'ramya', 'sathish', 'muralidharan', 'sugavaneshwari', 'vivek', 'bhuvaneshwari', 'elakkiya', 'arun', 'pavithra', 'varadharajan', 'sandhiya', 'kavin', 'suresh', 'arun', 'prabu', 'navanithan', 'reshma', 'obulirajan', 'janardanan', 'poornima', 'banupriya', 'chandramouleeswaran', 'gnanasiva', 'nithya', 'gopalakrishnan', 'mohana', 'mahesh', 'vanitha', 'mohanraj', 'naveen', 'sabarinathan', 'tejaswini', 'gunasekaran', 'indhuja', 'jayapriya', 'surya', 'rajkumar', 'nathiya', 'sneka', 'keerthi', 'sanjay', 'navin', 'nantha', 'venkateswari', 'srivenkatesan', 'venkatagopi', 'venkatraj', 'arun', 'ragu', 'harini', 'dinesh', 'boobalan', 'jothi', 'logeshwaran', 'shalini', 'sivaranjani', 'giridharan', 'priyanka', 'selvamani', 'sangeetha', 'dineshkumar', 'dharanishree', 'saravanan', 'santhosh', 'gokul', 'sridevi', 'sivaranjani', 'sridha', 'karthikeyan', 'revankanth', 'aarthy', 'kavipriya', 'sowmiya', 'raveendirakumar', 'niyamathulla', 'ravishankar', 'vigneshwaran', 'jayanthi', 'kowsalya', 'ramya', 'dinesh', 'sushmitha', 'kishor', 'sanjith', 'varatharaj', 'sarathkumar', 'sasi', 'thangam', 'sudhir', 'hamritha', 'muruganandam', 'vinothkumar', 'krishnasamy');

-- Team memberships
-- Insert users into teams based on CSV data

-- Operations team assignments (2 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, operations_team_id, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'prasanna'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, operations_team_id, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sathishkumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- California team assignments (18 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'karthik'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kokila'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'deepa'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kavitha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'deepan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sathish'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'yuvaraj'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'praveenram'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'selvaraj'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kavitha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'karthik'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'obulakshmi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'malathi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'aravind'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'tharageshwari'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'srikanth'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'pavithra'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 1, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'logesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Florida team assignments (19 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'jayakanthan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sathiyathirth'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'santhoshviji'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'karthikeyan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'dhanasekaran'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'suruthi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sangeetha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kamalakannan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'arunprakash'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'revathy'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'nivetha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'narayana'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'mohanapriya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'devagi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sudhir'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'hamritha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'mohanraj'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'muruganandam'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 2, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'vinothkumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- GI Clearing team assignments (3 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 3, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'menaka'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 3, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'saaradhappriya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 3, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'anbukarasi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Washington team assignments (11 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'dinesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'allwin'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'karthikeyamugunthan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'gunapoorani'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'akhilan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'vetrivel'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'elakkiya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'ramya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sathish'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'muralidharan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 4, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sugavaneshwari'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Michigan team assignments (5 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'venkatesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'vivek'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'bhuvaneshwari'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'elakkiya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 5, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'arun'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Colorado team assignments (4 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 6, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'pavithra'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 6, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'varadharajan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 6, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sandhiya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 6, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kavin'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Utah team assignments (6 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'charles'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'suresh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'arun'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'prabu'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'navanithan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 7, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'reshma'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Oregon team assignments (8 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'priyanka'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'rajeswari'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'obulirajan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'janardanan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'poornima'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'banupriya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'chandramouleeswaran'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 8, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'gnanasiva'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Regional Streamline team assignments (17 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'nithya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'gopalakrishnan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'mohana'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'naagarjun'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'vairavel'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'mahesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'vanitha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'mohanraj'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'tejaswini'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'indhuja'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'jayapriya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'rajkumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'nathiya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'nantha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'venkateswari'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'srivenkatesan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 9, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'venkatagopi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- National Streamline team assignments (8 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'naveen'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sabarinathan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'gunasekaran'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'surya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sneka'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'keerthi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sanjay'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 10, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'navin'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- FIF team assignments (3 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 11, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'karthikeyan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 11, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'venkatraj'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 11, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'arun'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- SCB & PD team assignments (12 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'ragu'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'harini'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'dinesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'boobalan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'jothi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'logeshwaran'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'shalini'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sivaranjani'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'giridharan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'priyanka'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'selvamani'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 12, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sangeetha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Arizona team assignments (3 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 13, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'dineshkumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 13, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'dharanishree'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 13, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'saravanan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Texas team assignments (12 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'naveenkumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'santhosh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'gokul'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sridevi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sivaranjani'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sridha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'karthikeyan'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'revankanth'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'aarthy'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kavipriya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sowmiya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 14, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'krishnasamy'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Pennsylvania team assignments (8 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'balaji'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'raveendirakumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'niyamathulla'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'ravishankar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'vigneshwaran'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'jayanthi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kowsalya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 15, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'ramya'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Ohio team assignments (9 users)
INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'lead', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'daniel'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'dinesh'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sushmitha'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'kishor'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sanjith'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'varatharaj'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sarathkumar'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'sasi'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)
SELECT u.id, 16, 'member', true, NOW(), NOW(), NOW()
FROM users u WHERE u.user_name = 'thangam'
ON CONFLICT (user_id, team_id) DO UPDATE SET
  role = EXCLUDED.role,
  is_active = true,
  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,
  modified_at = NOW();

-- Update team_lead_id in teams table for Team Leads

-- Set team lead for California
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'karthik' LIMIT 1
), modified_at = NOW()
WHERE id = 1;

-- Set team lead for Florida
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'sathiyathirth' LIMIT 1
), modified_at = NOW()
WHERE id = 2;

-- Set team lead for Michigan
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'venkatesh' LIMIT 1
), modified_at = NOW()
WHERE id = 5;

-- Set team lead for Utah
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'charles' LIMIT 1
), modified_at = NOW()
WHERE id = 7;

-- Set team lead for Oregon
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'priyanka' LIMIT 1
), modified_at = NOW()
WHERE id = 8;

-- Set team lead for Regional Streamline
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'naagarjun' LIMIT 1
), modified_at = NOW()
WHERE id = 9;

-- Set team lead for FIF
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'karthikeyan' LIMIT 1
), modified_at = NOW()
WHERE id = 11;

-- Set team lead for Texas
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'naveenkumar' LIMIT 1
), modified_at = NOW()
WHERE id = 14;

-- Set team lead for Pennsylvania
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'balaji' LIMIT 1
), modified_at = NOW()
WHERE id = 15;

-- Set team lead for Ohio
UPDATE teams SET team_lead_id = (
  SELECT id FROM users WHERE user_name = 'daniel' LIMIT 1
), modified_at = NOW()
WHERE id = 16;

-- Summary:
-- Total users to assign: 148
-- Teams breakdown:
--   Operations: 2 users (0 leads, 2 members)
--   California: 18 users (3 leads, 15 members)
--   Florida: 19 users (2 leads, 17 members)
--   GI Clearing: 3 users (0 leads, 3 members)
--   Washington: 11 users (0 leads, 11 members)
--   Michigan: 5 users (1 leads, 4 members)
--   Colorado: 4 users (0 leads, 4 members)
--   Utah: 6 users (1 leads, 5 members)
--   Oregon: 8 users (2 leads, 6 members)
--   Regional Streamline: 17 users (2 leads, 15 members)
--   National Streamline: 8 users (0 leads, 8 members)
--   FIF: 3 users (1 leads, 2 members)
--   SCB & PD: 12 users (0 leads, 12 members)
--   Arizona: 3 users (0 leads, 3 members)
--   Texas: 12 users (1 leads, 11 members)
--   Pennsylvania: 8 users (1 leads, 7 members)
--   Ohio: 9 users (1 leads, 8 members)
