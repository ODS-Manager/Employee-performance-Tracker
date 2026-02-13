-- Add missing team states and products for existing teams
-- Run this SQL script against your existing database

-- First, let's see what teams we have
-- SELECT id, name FROM teams ORDER BY id;

-- Add states for existing teams (modify team IDs based on your actual teams)
-- Assuming you have teams with IDs 1, 2, 3, etc.

INSERT INTO team_states (team_id, state) VALUES 
-- For team ID 1 (replace with actual team ID)
(1, 'FL'),
(1, 'CA'),

-- For team ID 2 (replace with actual team ID) 
(2, 'TX'),
(2, 'NY'),

-- For team ID 3 (replace with actual team ID)
(3, 'AZ'),
(3, 'CO'),

-- For team ID 4 (replace with actual team ID)
(4, 'WA'),
(4, 'OR'),

-- For team ID 5 (replace with actual team ID)
(5, 'MI'),
(5, 'OH')
-- Add more rows as needed for your teams
ON CONFLICT (team_id, state) DO NOTHING;  -- Prevents duplicates if using PostgreSQL

INSERT INTO team_products (team_id, product_type) VALUES
-- For team ID 1
(1, 'Full Search'),
(1, 'Update'), 
(1, 'Date Down'),
(1, 'Amend Title'),

-- For team ID 2
(2, 'Full Search'),
(2, 'Update'),
(2, 'Screening'),
(2, 'M&B'),

-- For team ID 3  
(3, 'GI Clearing'),
(3, 'Full Search'),

-- For team ID 4
(4, 'Full Search'),
(4, 'Update'),
(4, 'Date Down'),

-- For team ID 5
(5, 'Full Search'),
(5, 'Update'),
(5, 'Vendor Exam'),
(5, 'Screening')
-- Add more rows as needed for your teams
ON CONFLICT (team_id, product_type) DO NOTHING;  -- Prevents duplicates if using PostgreSQL

-- Verify the data was inserted
SELECT 
    t.id,
    t.name,
    COUNT(DISTINCT ts.state) as state_count,
    COUNT(DISTINCT tp.product_type) as product_count
FROM teams t
LEFT JOIN team_states ts ON t.id = ts.team_id  
LEFT JOIN team_products tp ON t.id = tp.team_id
GROUP BY t.id, t.name
ORDER BY t.id;