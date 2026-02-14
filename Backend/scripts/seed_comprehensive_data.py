"""
Comprehensive Data Seeding Script
Creates realistic test data for the entire Employee Performance Tracker application

This script creates:
- 2 Organizations (ORG-IND, ORG-VNM)
- Multiple users per organization (all roles)
- Multiple teams per organization with states/products
- FA Names pool
- Orders with various statuses and dates (last 3 months)
- Quality audit records
- Attendance records
- Performance metrics
"""

import sys
import os
from datetime import datetime, timedelta, date
import random
from decimal import Decimal

# Add the Backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.team import Team, TeamState, TeamProduct
from app.models.user_team import UserTeam
from app.models.fa_name import FAName
from app.models.team_fa_name import TeamFAName
from app.models.team_user_alias import TeamUserAlias
from app.models.order import Order
from app.models.quality_audit import QualityAudit
from app.models.attendance import AttendanceRecord
from app.models.reference import TransactionType, ProcessType, OrderStatusType, Division
from sqlalchemy import text

# Configuration
DEFAULT_PASSWORD = "Test@123"
START_DATE = datetime.now() - timedelta(days=90)  # 3 months back

# Reference data
TRANSACTION_TYPES = ["Sale/Cash", "Sale w/Mortgage", "Refinance", "HELOC", "Other"]
PROCESS_TYPES = ["Step1", "Step2", "Single Seat"]
ORDER_STATUSES = ["Completed", "On-hold", "BP", "RTI"]
DIVISIONS = ["Direct", "Agency"]

# States by team
TEAM_STATES = {
    "Florida Team": ["FL"],
    "California Team": ["CA"],
    "Texas Team": ["TX"],
    "New York Team": ["NY"],
    "Illinois Team": ["IL"],
    "Georgia Team": ["GA"],
    "GI Clearing Team": ["Multi-State"]
}

# Products by team
TEAM_PRODUCTS = {
    "Florida Team": ["Full Search", "M&B", "Update & DD"],
    "California Team": ["Full Search", "Streamline"],
    "Texas Team": ["Full Search", "M&B", "RS Clear"],
    "New York Team": ["Full Search", "Update & DD"],
    "Illinois Team": ["Full Search", "M&B"],
    "Georgia Team": ["Full Search", "Streamline"],
    "GI Clearing Team": ["GI Clearing"]
}

# Counties
COUNTIES = {
    "FL": ["Miami-Dade", "Broward", "Palm Beach", "Hillsborough", "Orange"],
    "CA": ["Los Angeles", "San Diego", "Orange", "Riverside", "San Bernardino"],
    "TX": ["Harris", "Dallas", "Tarrant", "Bexar", "Travis"],
    "NY": ["Kings", "Queens", "New York", "Suffolk", "Bronx"],
    "IL": ["Cook", "DuPage", "Lake", "Will", "Kane"],
    "GA": ["Fulton", "Gwinnett", "Cobb", "DeKalb", "Clayton"],
    "Multi-State": ["Various"]
}

# FA Names
FA_NAMES = [
    "First American Title", "Fidelity National Title", "Old Republic Title",
    "Stewart Title", "Chicago Title", "Commonwealth Land Title",
    "Lawyers Title", "WFG National Title", "Alliant National Title",
    "North American Title", "Westcor Land Title", "Ticor Title",
    "Nations Title", "Title Resources", "Amrock Title"
]

# Quality Audit Process OFE mapping
QUALITY_PROCESS_OFE = {
    "Full Search": 6,
    "Streamline": 5,
    "Update & DD": 3,
    "GI Clearing": 1
}


def create_reference_tables(db):
    """Create reference table data"""
    print("\n📋 Creating reference tables...")
    
    # Transaction Types
    for trans_type in TRANSACTION_TYPES:
        if not db.query(TransactionType).filter(TransactionType.name == trans_type).first():
            db.add(TransactionType(name=trans_type))
    
    # Process Types
    for proc_type in PROCESS_TYPES:
        if not db.query(ProcessType).filter(ProcessType.name == proc_type).first():
            db.add(ProcessType(name=proc_type))
    
    # Order Statuses
    for status in ORDER_STATUSES:
        if not db.query(OrderStatusType).filter(OrderStatusType.name == status).first():
            db.add(OrderStatusType(name=status))
    
    # Divisions
    for div in DIVISIONS:
        if not db.query(Division).filter(Division.name == div).first():
            db.add(Division(name=div))
    
    db.commit()
    print("✅ Reference tables created")


def create_organizations(db):
    """Create ORG-IND and ORG-VNM organizations"""
    print("\n🏢 Creating organizations...")
    
    orgs = []
    org_data = [
        {"name": "ODS - India", "code": "ORG-IND"},
        {"name": "ODS - Vietnam", "code": "ORG-VNM"}
    ]
    
    for org_info in org_data:
        org = db.query(Organization).filter(Organization.code == org_info["code"]).first()
        if not org:
            org = Organization(**org_info, is_active=True)
            db.add(org)
            db.flush()
            print(f"  ✅ Created: {org_info['name']} ({org_info['code']})")
        else:
            print(f"  ℹ️  Already exists: {org_info['name']} ({org_info['code']})")
        orgs.append(org)
    
    db.commit()
    return orgs


def create_users(db, org):
    """Create users for an organization"""
    org_suffix = "ind" if org.code == "ORG-IND" else "vnm"
    
    users = []
    
    # 1 Admin per org
    admin_username = f"admin_{org_suffix}"
    admin = db.query(User).filter(User.user_name == admin_username).first()
    if not admin:
        admin = User(
            user_name=admin_username,
            employee_id=f"ADM-{org_suffix.upper()}-001",
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            user_role="ADMIN",
            org_id=org.id,
            is_active=True
        )
        db.add(admin)
    users.append(("ADMIN", admin))
    
    # 3-5 Team Leads per org
    num_team_leads = 4 if org_suffix == "ind" else 3
    for i in range(1, num_team_leads + 1):
        tl_username = f"teamlead{i}_{org_suffix}"
        tl = db.query(User).filter(User.user_name == tl_username).first()
        if not tl:
            tl = User(
                user_name=tl_username,
                employee_id=f"TL-{org_suffix.upper()}-{i:03d}",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                user_role="TEAM_LEAD",
                org_id=org.id,
                is_active=True
            )
            db.add(tl)
        users.append(("TEAM_LEAD", tl))
    
    # 15-20 Employees per org
    num_employees = 18 if org_suffix == "ind" else 15
    for i in range(1, num_employees + 1):
        emp_username = f"employee{i}_{org_suffix}"
        emp = db.query(User).filter(User.user_name == emp_username).first()
        if not emp:
            emp = User(
                user_name=emp_username,
                employee_id=f"EMP-{org_suffix.upper()}-{i:03d}",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                user_role="EMPLOYEE",
                org_id=org.id,
                is_active=True
            )
            db.add(emp)
        users.append(("EMPLOYEE", emp))
    
    db.flush()
    return users


def create_teams(db, org, users):
    """Create teams for an organization"""
    print(f"\n👥 Creating teams for {org.name}...")
    
    # Get team leads
    team_leads = [u for role, u in users if role == "TEAM_LEAD"]
    employees = [u for role, u in users if role == "EMPLOYEE"]
    
    teams_list = list(TEAM_STATES.keys())
    
    # Create teams based on number of team leads
    teams = []
    for i, team_name in enumerate(teams_list[:len(team_leads)]):
        # Check if team already exists
        team = db.query(Team).filter(
            Team.name == team_name,
            Team.org_id == org.id
        ).first()
        
        if not team:
            team = Team(
                name=team_name,
                org_id=org.id,
                team_lead_id=team_leads[i].id,
                daily_target=random.randint(8, 12),
                monthly_target=random.randint(200, 300),
                single_seat_score=1.0,
                step1_score=0.5,
                step2_score=0.5,
                is_active=True
            )
            db.add(team)
            db.flush()
            
            # Add team states
            for state in TEAM_STATES[team_name]:
                team_state = TeamState(team_id=team.id, state=state)
                db.add(team_state)
            
            # Add team products
            for product in TEAM_PRODUCTS[team_name]:
                team_product = TeamProduct(team_id=team.id, product_type=product)
                db.add(team_product)
            
            print(f"  ✅ Created team: {team_name} (Lead: {team_leads[i].user_name})")
        else:
            print(f"  ℹ️  Already exists: {team_name}")
        
        teams.append(team)
    
    db.flush()
    
    # Assign employees to teams (3-5 employees per team)
    employee_idx = 0
    for team in teams:
        # Check existing memberships
        existing_members = db.query(UserTeam).filter(UserTeam.team_id == team.id).all()
        existing_user_ids = {m.user_id for m in existing_members}
        
        num_members = random.randint(3, 5)
        for _ in range(num_members):
            if employee_idx >= len(employees):
                break
            
            # Skip if already a member
            if employees[employee_idx].id not in existing_user_ids:
                membership = UserTeam(
                    user_id=employees[employee_idx].id,
                    team_id=team.id,
                    role="member",
                    is_active=True
                )
                db.add(membership)
            employee_idx += 1
    
    db.commit()
    return teams


def create_fa_names(db, teams):
    """Create FA names and assign to teams"""
    print("\n📝 Creating FA names...")
    
    fa_names = []
    for fa_name_text in FA_NAMES:
        fa = db.query(FAName).filter(FAName.name == fa_name_text).first()
        if not fa:
            fa = FAName(name=fa_name_text, is_active=True)
            db.add(fa)
            db.flush()
        fa_names.append(fa)
    
    # Assign FA names to teams (pool-based)
    for team in teams:
        # Check existing assignments
        existing_assignments = db.query(TeamFAName).filter(
            TeamFAName.team_id == team.id
        ).all()
        existing_fa_ids = {a.fa_name_id for a in existing_assignments}
        
        # Each team gets 3-5 FA names
        team_fa_count = random.randint(3, 5)
        
        # Calculate how many more FA names we need
        needed_count = max(0, team_fa_count - len(existing_fa_ids))
        
        # Skip already assigned FA names
        available_fas = [fa for fa in fa_names if fa.id not in existing_fa_ids]
        if available_fas and needed_count > 0:
            num_to_select = min(needed_count, len(available_fas))
            selected_fas = random.sample(available_fas, num_to_select)
            
            for fa in selected_fas:
                team_fa = TeamFAName(
                    team_id=team.id,
                    fa_name_id=fa.id,
                    is_active=True
                )
                db.add(team_fa)
    
    db.commit()
    print(f"  ✅ Created {len(fa_names)} FA names and assigned to teams")
    return fa_names


def assign_fa_aliases(db, teams):
    """Assign FA name aliases to users in teams"""
    print("\n🏷️  Assigning FA aliases to users...")
    
    for team in teams:
        # Get team members
        memberships = db.query(UserTeam).filter(
            UserTeam.team_id == team.id,
            UserTeam.is_active == True
        ).all()
        
        # Get team's FA names
        team_fas = db.query(TeamFAName).filter(
            TeamFAName.team_id == team.id,
            TeamFAName.is_active == True
        ).all()
        
        if not team_fas:
            continue
        
        # Assign FA aliases to each team member
        for membership in memberships:
            # Check existing aliases for this user in this team
            existing_alias = db.query(TeamUserAlias).filter(
                TeamUserAlias.team_id == team.id,
                TeamUserAlias.user_id == membership.user_id
            ).first()
            
            # Skip if user already has an alias
            if existing_alias:
                continue
            
            # Each user gets exactly 1 FA alias (unique constraint)
            selected_fa = random.choice(team_fas)
            
            alias = TeamUserAlias(
                team_id=team.id,
                user_id=membership.user_id,
                fa_name=selected_fa.fa_name.name,  # Get the actual FA name string
                is_active=True
            )
            db.add(alias)
    
    db.commit()
    print("  ✅ FA aliases assigned to users")


def create_orders(db, org, teams, fa_names):
    """Create realistic orders for the past 3 months"""
    print(f"\n📦 Creating orders for {org.name}...")
    
    # Get reference data
    transaction_types = db.query(TransactionType).all()
    process_types = db.query(ProcessType).all()
    all_order_statuses = db.query(OrderStatusType).all()
    divisions = db.query(Division).all()
    
    # Filter to only use the 4 main statuses
    status_names = ["Completed", "On-hold", "BP", "RTI"]
    order_statuses = [s for s in all_order_statuses if s.name in status_names]
    
    process_type_map = {pt.name: pt for pt in process_types}
    
    orders_created = 0
    
    for team in teams:
        # Get team members
        memberships = db.query(UserTeam).filter(
            UserTeam.team_id == team.id,
            UserTeam.is_active == True
        ).all()
        
        if not memberships:
            continue
        
        members = [m.user_id for m in memberships]
        
        # Get team's states and products
        team_states = db.query(TeamState).filter(TeamState.team_id == team.id).all()
        team_products = db.query(TeamProduct).filter(TeamProduct.team_id == team.id).all()
        
        if not team_states or not team_products:
            continue
        
        states_list = [ts.state for ts in team_states]
        products_list = [tp.product_type for tp in team_products]
        
        # Get team FA names
        team_fas = db.query(TeamFAName).filter(
            TeamFAName.team_id == team.id,
            TeamFAName.is_active == True
        ).all()
        fa_ids = [tf.fa_name_id for tf in team_fas] if team_fas else None
        
        # Create orders for last 90 days
        num_orders_per_day = random.randint(3, 8)
        
        for day_offset in range(90):
            entry_date = (START_DATE + timedelta(days=day_offset)).date()
            
            # Skip weekends (optional - creates more realistic data)
            if entry_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            orders_today = random.randint(num_orders_per_day - 2, num_orders_per_day + 3)
            
            for order_num in range(orders_today):
                state = random.choice(states_list)
                product = random.choice(products_list)
                
                # Generate unique file number
                file_number = f"{state}-{entry_date.strftime('%Y%m%d')}-{order_num:04d}"
                
                # Select process type with realistic distribution
                process_type_choice = random.choices(
                    ["Single Seat", "Step1", "Step2"],
                    weights=[60, 20, 20]  # 60% single seat, 20% step1, 20% step2
                )[0]
                
                process_type = process_type_map[process_type_choice]
                
                # Select users based on process type
                if process_type_choice == "Single Seat":
                    user = random.choice(members)
                    step1_user_id = user
                    step2_user_id = user
                elif process_type_choice == "Step1":
                    step1_user_id = random.choice(members)
                    step2_user_id = None
                else:  # Step2
                    step1_user_id = None
                    step2_user_id = random.choice(members)
                
                # Select FA names
                step1_fa_id = random.choice(fa_ids) if fa_ids and step1_user_id else None
                step2_fa_id = random.choice(fa_ids) if fa_ids and step2_user_id else None
                
                # Generate timestamps
                work_start = datetime.combine(entry_date, datetime.min.time()) + timedelta(hours=9)
                step1_start = work_start + timedelta(minutes=random.randint(0, 120)) if step1_user_id else None
                step1_end = step1_start + timedelta(minutes=random.randint(30, 120)) if step1_start else None
                step2_start = work_start + timedelta(minutes=random.randint(0, 120)) if step2_user_id else None
                step2_end = step2_start + timedelta(minutes=random.randint(30, 120)) if step2_start else None
                
                # Status distribution: 85% completed, 10% on-hold, 5% others
                status = random.choices(
                    order_statuses,
                    weights=[85, 8, 4, 3]
                )[0]
                
                # Billing status
                billing_status = "done" if status.name == "Completed" and random.random() > 0.1 else "pending"
                
                order = Order(
                    file_number=file_number,
                    entry_date=entry_date,
                    transaction_type_id=random.choice(transaction_types).id,
                    process_type_id=process_type.id,
                    order_status_id=status.id,
                    division_id=random.choice(divisions).id,
                    state=state,
                    county=random.choice(COUNTIES[state]),
                    product_type=product,
                    team_id=team.id,
                    org_id=org.id,
                    step1_user_id=step1_user_id,
                    step1_fa_name_id=step1_fa_id,
                    step1_start_time=step1_start,
                    step1_end_time=step1_end,
                    step2_user_id=step2_user_id,
                    step2_fa_name_id=step2_fa_id,
                    step2_start_time=step2_start,
                    step2_end_time=step2_end,
                    billing_status=billing_status,
                    created_by=random.choice(members),
                    created_at=work_start
                )
                db.add(order)
                orders_created += 1
        
        if orders_created % 100 == 0:
            db.flush()
    
    db.commit()
    print(f"  ✅ Created {orders_created} orders")


def create_quality_audits(db, org, teams):
    """Create quality audit records"""
    print(f"\n🔍 Creating quality audits for {org.name}...")
    
    audits_created = 0
    
    for team in teams:
        # Get team members
        memberships = db.query(UserTeam).filter(
            UserTeam.team_id == team.id,
            UserTeam.is_active == True
        ).all()
        
        if not memberships:
            continue
        
        # Get team products for process types
        team_products = db.query(TeamProduct).filter(TeamProduct.team_id == team.id).all()
        products_list = [tp.product_type for tp in team_products]
        
        # Create audits for last 90 days (weekly)
        for week_offset in range(0, 13):  # ~13 weeks in 90 days
            audit_date = (START_DATE + timedelta(weeks=week_offset)).date()
            
            # Create audit for 2-3 team members per week
            audited_members = random.sample(memberships, min(3, len(memberships)))
            
            for membership in audited_members:
                # Select a product type that this team handles
                process_type = random.choice([p for p in products_list if p in QUALITY_PROCESS_OFE])
                ofe = QUALITY_PROCESS_OFE[process_type]
                
                # Get files reviewed count from orders
                total_files_reviewed = random.randint(20, 50)
                ofe_count = total_files_reviewed * ofe
                
                # Generate error metrics (realistic quality)
                files_with_error = random.randint(0, max(1, int(total_files_reviewed * 0.1)))  # ~10% error rate
                total_errors = files_with_error + random.randint(0, files_with_error)
                files_with_cce_error = random.randint(0, files_with_error)
                
                # Calculate quality metrics
                fb_quality = 1 - (files_with_error / total_files_reviewed) if total_files_reviewed > 0 else 1.0
                ofe_quality = 1 - (total_errors / ofe_count) if ofe_count > 0 else 1.0
                cce_quality = 1 - (files_with_cce_error / total_files_reviewed) if total_files_reviewed > 0 else 1.0
                
                audit = QualityAudit(
                    examiner_id=membership.user_id,
                    team_id=team.id,
                    org_id=org.id,
                    process_type=process_type,
                    ofe=ofe,
                    files_with_error=files_with_error,
                    total_errors=total_errors,
                    files_with_cce_error=files_with_cce_error,
                    total_files_reviewed=total_files_reviewed,
                    ofe_count=ofe_count,
                    fb_quality=Decimal(str(round(fb_quality, 4))),
                    ofe_quality=Decimal(str(round(ofe_quality, 4))),
                    cce_quality=Decimal(str(round(cce_quality, 4))),
                    audit_date=audit_date,
                    audit_period_start=audit_date - timedelta(days=7),
                    audit_period_end=audit_date,
                    created_by=team.team_lead_id
                )
                db.add(audit)
                audits_created += 1
    
    db.commit()
    print(f"  ✅ Created {audits_created} quality audits")


def create_attendance_records(db, org, teams):
    """Create attendance records for the past 3 months"""
    print(f"\n📅 Creating attendance records for {org.name}...")
    
    records_created = 0
    
    for team in teams:
        # Get team members
        memberships = db.query(UserTeam).filter(
            UserTeam.team_id == team.id,
            UserTeam.is_active == True
        ).all()
        
        if not memberships:
            continue
        
        # Create attendance for last 90 days
        for day_offset in range(90):
            attendance_date = (START_DATE + timedelta(days=day_offset)).date()
            
            # Skip weekends
            if attendance_date.weekday() >= 5:
                continue
            
            # Mark attendance for each team member
            for membership in memberships:
                # 90% present, 5% absent, 5% leave
                status = random.choices(
                    ["present", "absent", "leave"],
                    weights=[90, 5, 5]
                )[0]
                
                # Only create records for present and leave (sparse storage)
                if status in ["present", "leave"]:
                    record = AttendanceRecord(
                        user_id=membership.user_id,
                        team_id=team.id,
                        date=attendance_date,
                        status=status,
                        marked_by=team.team_lead_id,
                        marked_at=datetime.combine(attendance_date, datetime.min.time()) + timedelta(hours=9),
                        org_id=org.id
                    )
                    db.add(record)
                    records_created += 1
        
        if records_created % 100 == 0:
            db.flush()
    
    db.commit()
    print(f"  ✅ Created {records_created} attendance records")


def main():
    print("=" * 70)
    print("🚀 COMPREHENSIVE DATA SEEDING SCRIPT")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create reference tables
        create_reference_tables(db)
        
        # Step 2: Create organizations
        orgs = create_organizations(db)
        
        # Process each organization
        for org in orgs:
            print(f"\n{'=' * 70}")
            print(f"📍 Processing Organization: {org.name} ({org.code})")
            print(f"{'=' * 70}")
            
            # Step 3: Create users
            print(f"\n👤 Creating users for {org.name}...")
            users = create_users(db, org)
            db.commit()
            print(f"  ✅ Created {len(users)} users")
            
            # Step 4: Create teams
            teams = create_teams(db, org, users)
            
            # Step 5: Create FA names
            fa_names = create_fa_names(db, teams)
            
            # Step 6: Assign FA aliases to users
            assign_fa_aliases(db, teams)
            
            # Step 7: Create orders
            create_orders(db, org, teams, fa_names)
            
            # Step 8: Create quality audits
            create_quality_audits(db, org, teams)
            
            # Step 9: Create attendance records
            create_attendance_records(db, org, teams)
        
        print("\n" + "=" * 70)
        print("✅ DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        # Print summary
        print("\n📊 SUMMARY:")
        print(f"  Organizations: {db.query(Organization).count()}")
        print(f"  Users: {db.query(User).count()}")
        print(f"  Teams: {db.query(Team).count()}")
        print(f"  FA Names: {db.query(FAName).count()}")
        print(f"  Orders: {db.query(Order).count()}")
        print(f"  Quality Audits: {db.query(QualityAudit).count()}")
        print(f"  Attendance Records: {db.query(AttendanceRecord).count()}")
        
        print("\n🔑 LOGIN CREDENTIALS:")
        print("  Default Password for all users: Test@123")
        print("\n  Sample Users:")
        print("  - admin_ind / Test@123 (Admin - ORG-IND)")
        print("  - admin_vnm / Test@123 (Admin - ORG-VNM)")
        print("  - teamlead1_ind / Test@123 (Team Lead - ORG-IND)")
        print("  - employee1_ind / Test@123 (Employee - ORG-IND)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
