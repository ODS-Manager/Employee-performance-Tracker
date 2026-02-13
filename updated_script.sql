-- Update 148 users (EMP004-EMP151) to have org_id = 1
UPDATE users 
SET org_id = 1,
    modified_at = NOW()
WHERE employee_id >= 'EMP004' AND employee_id <= 'EMP151';