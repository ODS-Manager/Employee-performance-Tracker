#!/usr/bin/env python3
"""
Generate team assignment SQL from CSV data
Maps users to teams based on the CSV file data
"""

import csv
import re

def clean_username(name):
    """Convert real name to username format (lowercase, no spaces)"""
    # Remove spaces and special characters, convert to lowercase
    username = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    return username

def get_team_id_mapping():
    """Map team names to their database IDs"""
    return {
        'Operations': 'operations_team_id',  # Will be created
        'California': 1,  # Existing team ID
        'Florida': 2,
        'GI Clearing': 3,
        'Washington': 4, 
        'Michigan': 5,
        'Colorado': 6,
        'Utah': 7,
        'Oregon': 8,
        'Regional Streamline': 9,
        'National Streamline': 10,
        'FIF': 11,
        'SCB & PD': 12,
        'Arizona': 13,
        'Texas': 14,
        'Pennsylvania': 15,
        'Ohio': 16
    }

def role_mapping(csv_role):
    """Map CSV roles to database roles"""
    mapping = {
        'Superadmin': 'superadmin',
        'Admin': 'admin',
        'Team Lead': 'team_lead', 
        'Examiner': 'employee'
    }
    return mapping.get(csv_role, 'employee')

def main():
    team_mapping = get_team_id_mapping()
    
    # Read CSV file
    users_data = []
    with open('/home/buddy/Work/ODS/Employee-performance-Tracker/Users List for Org Ind.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users_data.append({
                'real_name': row['Real Name'].strip(),
                'role': row['Role'].strip(),
                'team_name': row['Team Name'].strip(),
                'username': clean_username(row['Real Name'])
            })
    
    print("-- Team Assignment SQL Script")
    print("-- Generated from CSV data")
    print()
    
    print("-- First, get the Operations team ID after creation")
    print("-- Run create_operations_team.sql first, then get the team ID:")
    print("-- SELECT id FROM teams WHERE name = 'Operations' LIMIT 1;")
    print("-- Replace 'operations_team_id' with the actual ID returned")
    print()
    
    # Generate role updates first
    print("-- Update user roles based on CSV data")
    role_updates = {}
    for user in users_data:
        db_role = role_mapping(user['role'])
        if db_role not in role_updates:
            role_updates[db_role] = []
        role_updates[db_role].append(user['username'])
    
    for db_role, usernames in role_updates.items():
        if usernames:
            username_list = "', '".join(usernames)
            print(f"UPDATE users SET user_role = '{db_role}', modified_at = NOW()")
            print(f"WHERE user_name IN ('{username_list}');")
            print()
    
    print("-- Team memberships")
    print("-- Insert users into teams based on CSV data")
    print()
    
    # Group users by team
    team_assignments = {}
    for user in users_data:
        team_name = user['team_name']
        if team_name not in team_assignments:
            team_assignments[team_name] = []
        team_assignments[team_name].append(user)
    
    for team_name, team_users in team_assignments.items():
        print(f"-- {team_name} team assignments ({len(team_users)} users)")
        
        if team_name == 'Operations':
            team_id_ref = 'operations_team_id'
        else:
            team_id_ref = str(team_mapping.get(team_name, 'UNKNOWN'))
        
        if team_id_ref == 'UNKNOWN':
            print(f"-- WARNING: Team '{team_name}' not found in mapping!")
            continue
            
        for user in team_users:
            member_role = 'lead' if user['role'] == 'Team Lead' else 'member'
            
            print(f"INSERT INTO user_teams (user_id, team_id, role, is_active, joined_at, created_at, modified_at)")
            print(f"SELECT u.id, {team_id_ref}, '{member_role}', true, NOW(), NOW(), NOW()")
            print(f"FROM users u WHERE u.user_name = '{user['username']}'")
            print(f"ON CONFLICT (user_id, team_id) DO UPDATE SET")
            print(f"  role = EXCLUDED.role,")
            print(f"  is_active = true,")
            print(f"  joined_at = CASE WHEN user_teams.is_active = false THEN NOW() ELSE user_teams.joined_at END,")
            print(f"  modified_at = NOW();")
            print()
    
    # Generate team leader assignments
    print("-- Update team_lead_id in teams table for Team Leads")
    print()
    
    for team_name, team_users in team_assignments.items():
        team_leads = [u for u in team_users if u['role'] == 'Team Lead']
        
        if team_leads and team_name != 'Operations':  # Operations doesn't need team leads
            if team_name == 'Operations':
                team_id_ref = 'operations_team_id'
            else:
                team_id_ref = str(team_mapping.get(team_name, 'UNKNOWN'))
                
            if team_id_ref != 'UNKNOWN':
                # Use the first team lead if multiple
                lead_username = team_leads[0]['username']
                print(f"-- Set team lead for {team_name}")
                print(f"UPDATE teams SET team_lead_id = (")
                print(f"  SELECT id FROM users WHERE user_name = '{lead_username}' LIMIT 1")
                print(f"), modified_at = NOW()")
                print(f"WHERE id = {team_id_ref};")
                print()
    
    print("-- Summary:")
    print(f"-- Total users to assign: {len(users_data)}")
    print("-- Teams breakdown:")
    for team_name, team_users in team_assignments.items():
        team_leads_count = len([u for u in team_users if u['role'] == 'Team Lead'])
        members_count = len(team_users) - team_leads_count
        print(f"--   {team_name}: {len(team_users)} users ({team_leads_count} leads, {members_count} members)")

if __name__ == "__main__":
    main()