from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./ods_db.sqlite')

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print('=' * 80)
    print('DATABASE CLEANUP SUMMARY')
    print('=' * 80)
    
    # Teams
    total_teams = conn.execute(text('SELECT COUNT(*) FROM teams')).fetchone()[0]
    print(f'\n✅ TEAMS: {total_teams} teams (removed 20 duplicates)')
    
    # List all teams with member counts
    result = conn.execute(text('''
        SELECT t.name, COUNT(DISTINCT ut.user_id) as member_count
        FROM teams t
        LEFT JOIN user_teams ut ON t.id = ut.team_id
        GROUP BY t.id, t.name
        ORDER BY t.name
    '''))
    
    for row in result:
        print(f'   {row[0]:30} - {row[1]:3} members')
    
    # Users
    print(f'\n✅ USERS:')
    result = conn.execute(text('''
        SELECT user_role, COUNT(*) as count
        FROM users
        GROUP BY user_role
        ORDER BY 
            CASE user_role
                WHEN 'SUPERADMIN' THEN 1
                WHEN 'ADMIN' THEN 2
                WHEN 'TEAM_LEAD' THEN 3
                WHEN 'EMPLOYEE' THEN 4
            END
    '''))
    
    total = 0
    for row in result:
        print(f'   {row[0]:12}: {row[1]:3} users')
        total += row[1]
    print(f'   TOTAL       : {total:3} users')
    
    # Assignment status
    print(f'\n✅ TEAM ASSIGNMENTS:')
    assigned = conn.execute(text('SELECT COUNT(DISTINCT user_id) FROM user_teams')).fetchone()[0]
    print(f'   Assigned to teams: {assigned} users')
    print(f'   Not assigned:      {total - assigned} users (system accounts)')
    
    # CSV import stats
    print(f'\n✅ FROM CSV IMPORT:')
    csv_employees = conn.execute(text("SELECT COUNT(*) FROM users WHERE examiner_id LIKE 'EMP-IND-%' AND user_role = 'EMPLOYEE'")).fetchone()[0]
    
    csv_team_leads = conn.execute(text("SELECT COUNT(*) FROM users WHERE examiner_id LIKE 'TL-IND-%' AND user_role = 'TEAM_LEAD'")).fetchone()[0]
    
    print(f'   Employees:   {csv_employees} imported')
    print(f'   Team Leads:  {csv_team_leads} imported')
    print(f'   TOTAL:       {csv_employees + csv_team_leads} users from CSV')
    
    # FA Names
    fa_count = conn.execute(text('SELECT COUNT(*) FROM fa_names')).fetchone()[0]
    print(f'\n✅ FA NAMES: {fa_count} FA names configured')
    
    print('\n' + '=' * 80)
