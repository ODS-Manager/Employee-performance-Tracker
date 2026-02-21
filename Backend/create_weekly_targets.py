"""
Create examiner_weekly_targets table and populate with sample data
"""
import sqlite3
from datetime import datetime, timedelta, date

conn = sqlite3.connect('ods_db.sqlite')
cursor = conn.cursor()

print("=" * 100)
print("CREATING examiner_weekly_targets TABLE")
print("=" * 100)

# Create the examiner_weekly_targets table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS examiner_weekly_targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        week_start_date DATE NOT NULL,
        week_end_date DATE NOT NULL,
        target INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (team_id) REFERENCES teams(id),
        FOREIGN KEY (created_by) REFERENCES users(id),
        UNIQUE (user_id, team_id, week_start_date)
    )
""")

# Create indexes
cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_targets_user ON examiner_weekly_targets(user_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_targets_team ON examiner_weekly_targets(team_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_targets_week ON examiner_weekly_targets(week_start_date)")

print("✅ Table created successfully")

print("\n" + "=" * 100)
print("GENERATING WEEKLY TARGETS FOR ALL EXAMINERS")
print("=" * 100)

# Get all teams with their team leads
cursor.execute("""
    SELECT t.id, t.name, t.team_lead_id
    FROM teams t
    WHERE t.is_active = 1
    ORDER BY t.id
""")
teams = cursor.fetchall()

def get_sunday_of_week(ref_date):
    """Get the Sunday of the week for a given date"""
    day_of_week = ref_date.weekday()
    if day_of_week == 6:  # Sunday
        return ref_date
    else:
        days_since_sunday = day_of_week + 1
        return ref_date - timedelta(days=days_since_sunday)

# Generate targets for the last 8 weeks
today = date.today()
weeks = []
for i in range(8):
    week_start = get_sunday_of_week(today - timedelta(weeks=i))
    week_end = week_start + timedelta(days=6)
    weeks.append((week_start, week_end))

weeks.reverse()  # Oldest to newest

targets_created = 0

print(f"\nGenerating targets for {len(weeks)} weeks ({weeks[0][0]} to {weeks[-1][1]})")
print("-" * 100)

for team_id, team_name, team_lead_id in teams:
    # Get all examiners in this team
    cursor.execute("""
        SELECT u.id, u.user_name
        FROM users u
        JOIN user_teams ut ON u.id = ut.user_id
        WHERE ut.team_id = ? AND u.user_role = 'examiner' AND ut.is_active = 1
    """, (team_id,))
    examiners = cursor.fetchall()
    
    if not examiners:
        print(f"  Team {team_id:3} ({team_name:25}): No examiners - SKIPPED")
        continue
    
    # Use team lead as creator, or fallback to superadmin (user_id=2)
    created_by = team_lead_id if team_lead_id else 2
    
    team_targets = 0
    
    # Create targets for each examiner for each week
    for user_id, user_name in examiners:
        # Vary targets slightly for realism: base 20, but 15-25 range
        import random
        base_target = random.randint(15, 25)
        
        for week_start, week_end in weeks:
            # Small weekly variation
            weekly_target = base_target + random.randint(-2, 2)
            weekly_target = max(10, weekly_target)  # Minimum 10
            
            try:
                cursor.execute("""
                    INSERT INTO examiner_weekly_targets 
                    (user_id, team_id, week_start_date, week_end_date, target, created_by, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, team_id,
                    week_start.isoformat(), week_end.isoformat(),
                    weekly_target, created_by,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                team_targets += 1
                targets_created += 1
            except sqlite3.IntegrityError:
                # Duplicate - skip
                pass
    
    print(f"  Team {team_id:3} ({team_name:25}): {team_targets:4} targets ({len(examiners)} examiners × {len(weeks)} weeks)")

conn.commit()

print("-" * 100)
print(f"\n✅ SUCCESS: Created {targets_created} weekly targets for all examiners")

# Show summary
print("\n" + "=" * 100)
print("WEEKLY TARGETS SUMMARY")
print("=" * 100)

cursor.execute("""
    SELECT 
        COUNT(DISTINCT user_id) as examiner_count,
        COUNT(DISTINCT team_id) as team_count,
        COUNT(DISTINCT week_start_date) as week_count,
        COUNT(*) as total_targets,
        AVG(target) as avg_target,
        MIN(target) as min_target,
        MAX(target) as max_target
    FROM examiner_weekly_targets
""")
stats = cursor.fetchone()

print(f"  Total Examiners with Targets: {stats[0]}")
print(f"  Total Teams with Targets: {stats[1]}")
print(f"  Total Weeks Covered: {stats[2]}")
print(f"  Total Target Records: {stats[3]}")
print(f"  Average Weekly Target: {stats[4]:.1f}")
print(f"  Min/Max Targets: {stats[5]} / {stats[6]}")

# Show sample targets by team
print(f"\nSample Targets by Team:")
cursor.execute("""
    SELECT 
        t.name as team_name,
        COUNT(*) as target_count,
        AVG(ewt.target) as avg_target
    FROM examiner_weekly_targets ewt
    JOIN teams t ON ewt.team_id = t.id
    GROUP BY t.name
    ORDER BY target_count DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row[0]:25}: {row[1]:4} targets, avg {row[2]:.1f}")

conn.close()

print("\n" + "=" * 100)
print("🎉 Weekly targets setup complete!")
print("=" * 100)
