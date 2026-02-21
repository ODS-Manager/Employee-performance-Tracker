#!/usr/bin/env python3
"""
Add comprehensive dummy data for February 2026 to test all dashboard features
This script adds realistic test data across all tables for the month of February 2026.
"""

import sys
import os
from datetime import datetime, timedelta, time
from decimal import Decimal
import random
import json

# Add the backend to Python path
sys.path.append('/home/buddy/Work/ODS/Employee-performance-Tracker/Backend')

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import *
    from app.core.security import get_password_hash
    
    print("🚀 Adding February 2026 dummy data...")
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL', 'sqlite:///./ods_db.sqlite')
    print(f"📊 Connecting to database: {db_url}")
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # February 2026 date range (Feb 1-28, 2026)
    feb_start = datetime(2026, 2, 1)
    feb_end = datetime(2026, 2, 28)
    
    # Get existing data
    organizations = session.query(Organization).all()
    users = session.query(User).filter(User.user_role.in_(['EMPLOYEE', 'TEAM_LEAD'])).all()
    teams = session.query(Team).all()
    fa_names = session.query(FAName).all()
    
    if not organizations or not users or not teams:
        print("❌ Please run init_database.py first to create basic data")
        sys.exit(1)
    
    print(f"📋 Found {len(organizations)} orgs, {len(users)} users, {len(teams)} teams")
    
    # Create additional employees for more realistic data
    print("👥 Creating additional employees...")
    additional_employees = [
        ("john.doe", "John123!", "EMPLOYEE", "EMP010"),
        ("jane.smith", "Jane123!", "EMPLOYEE", "EMP011"),
        ("mike.johnson", "Mike123!", "EMPLOYEE", "EMP012"),
        ("sarah.wilson", "Sarah123!", "EMPLOYEE", "EMP013"),
        ("david.brown", "David123!", "EMPLOYEE", "EMP014"),
        ("lisa.davis", "Lisa123!", "EMPLOYEE", "EMP015"),
        ("robert.miller", "Robert123!", "EMPLOYEE", "EMP016"),
        ("emma.garcia", "Emma123!", "EMPLOYEE", "EMP017"),
        ("james.rodriguez", "James123!", "EMPLOYEE", "EMP018"),
        ("maria.martinez", "Maria123!", "EMPLOYEE", "EMP019"),
        ("tom.lead", "Tom123!", "TEAM_LEAD", "EMP020"),
        ("anna.lead", "Anna123!", "TEAM_LEAD", "EMP021"),
    ]
    
    new_users = []
    for username, password, role, emp_id in additional_employees:
        # Check if user already exists
        existing = session.query(User).filter(User.user_name == username).first()
        if not existing:
            user = User(
                user_name=username,
                examiner_id=emp_id,
                password_hash=get_password_hash(password),
                user_role=role,
                org_id=organizations[0].id,  # Assign to first org
                is_active=True,
                token_version=1
            )
            session.add(user)
            new_users.append(user)
    
    session.commit()
    
    # Refresh users list
    users = session.query(User).filter(User.user_role.in_(['EMPLOYEE', 'TEAM_LEAD'])).all()
    employees = [u for u in users if u.user_role == 'EMPLOYEE']
    team_leads = [u for u in users if u.user_role == 'TEAM_LEAD']
    
    print(f"✅ Now have {len(employees)} employees and {len(team_leads)} team leads")
    
    # Assign users to teams
    print("🏗️ Assigning users to teams...")
    from app.models.user_team import UserTeam
    
    # Clear existing assignments to avoid duplicates
    session.query(UserTeam).delete()
    session.commit()
    
    # Assign team leads to teams
    for i, team in enumerate(teams):
        if i < len(team_leads):
            team.team_lead_id = team_leads[i].id
            # Add team lead to their team
            user_team = UserTeam(
                user_id=team_leads[i].id,
                team_id=team.id,
                role="lead",
                is_active=True,
                joined_at=feb_start
            )
            session.add(user_team)
    
    # Assign employees to teams (each employee to 1-2 teams)
    for employee in employees:
        num_teams = random.choice([1, 1, 1, 2])  # Most employees in 1 team, some in 2
        assigned_teams = random.sample(teams, min(num_teams, len(teams)))
        
        for team in assigned_teams:
            user_team = UserTeam(
                user_id=employee.id,
                team_id=team.id,
                role="member",
                is_active=True,
                joined_at=feb_start - timedelta(days=random.randint(30, 90))
            )
            session.add(user_team)
    
    session.commit()
    
    # Create reference data
    print("📚 Creating reference data...")
    
    # Transaction Types
    transaction_types = ["Sale/Cash", "Sale w/Mortgage", "Refinance", "HELOC", "Commercial"]
    for trans_type in transaction_types:
        existing = session.query(TransactionType).filter(TransactionType.name == trans_type).first()
        if not existing:
            session.add(TransactionType(name=trans_type, is_active=True))
    
    # Process Types
    process_types = ["Step1", "Step2", "Single Seat"]
    for proc_type in process_types:
        existing = session.query(ProcessType).filter(ProcessType.name == proc_type).first()
        if not existing:
            session.add(ProcessType(name=proc_type, is_active=True))
    
    # Order Status
    order_statuses = ["Completed", "On-hold", "BP and RTI", "In Progress"]
    for status in order_statuses:
        existing = session.query(OrderStatusType).filter(OrderStatusType.name == status).first()
        if not existing:
            session.add(OrderStatusType(name=status, is_active=True))
    
    # Divisions
    divisions = [("Direct", "Direct business"), ("Agency", "Agency business")]
    for name, desc in divisions:
        existing = session.query(Division).filter(Division.name == name).first()
        if not existing:
            session.add(Division(name=name, description=desc))
    
    session.commit()
    
    # Get the created reference data
    trans_types = session.query(TransactionType).all()
    proc_types = session.query(ProcessType).all()
    statuses = session.query(OrderStatusType).all()
    divisions = session.query(Division).all()
    
    print("🧹 Clearing existing February 2026 data...")
    
    # Delete existing February 2026 data
    session.query(Order).filter(
        Order.entry_date >= feb_start,
        Order.entry_date <= feb_end
    ).delete()
    
    session.query(AttendanceRecord).filter(
        AttendanceRecord.date >= feb_start.date(),
        AttendanceRecord.date <= feb_end.date()
    ).delete()
    
    session.query(QualityAudit).filter(
        QualityAudit.audit_date >= feb_start.date(),
        QualityAudit.audit_date <= feb_end.date()
    ).delete()
    
    session.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.week_start_date >= feb_start.date()
    ).delete()
    
    session.query(ExaminerPerformanceMetrics).filter(
        ExaminerPerformanceMetrics.metric_date >= feb_start.date(),
        ExaminerPerformanceMetrics.metric_date <= feb_end.date()
    ).delete()
    
    session.query(TeamPerformanceMetrics).filter(
        TeamPerformanceMetrics.metric_date >= feb_start.date(),
        TeamPerformanceMetrics.metric_date <= feb_end.date()
    ).delete()
    
    session.query(BillingReport).filter(
        BillingReport.billing_month == 2,
        BillingReport.billing_year == 2026
    ).delete()
    
    session.commit()
    print("✅ Cleared existing February 2026 data")
    
    # Create Orders for February 2026
    print("📋 Creating orders for February 2026...")
    
    states = ["Florida", "California", "Arizona", "Texas", "Washington", "Michigan", "Colorado", "Utah", "Oregon"]
    counties = ["Miami-Dade", "Orange", "Los Angeles", "Maricopa", "Harris", "King", "Wayne", "Denver", "Salt Lake", "Multnomah"]
    product_types = ["Full Search", "Update", "Date Down", "Amend Title", "Screening", "M&B", "GI Clearing"]
    
    orders_created = 0
    current_date = feb_start
    global_order_counter = 1  # Global counter for unique file numbers
    
    while current_date <= feb_end:
        # Create 15-25 orders per day
        daily_orders = random.randint(15, 25)
        
        for _ in range(daily_orders):
            # Select random team and get its data
            team = random.choice(teams)
            team_states = [ts.state for ts in team.states]
            team_products = [tp.product_type for tp in team.products]
            
            # Get team members
            team_users = session.query(User).join(UserTeam).filter(
                UserTeam.team_id == team.id,
                UserTeam.is_active == True,
                User.user_role == 'EMPLOYEE'
            ).all()
            
            if not team_users:
                continue
            
            # Create unique file number
            file_number = f"T{team.id:02d}{current_date.strftime('%Y%m%d')}{global_order_counter:06d}"
            global_order_counter += 1
            
            # Determine process type and assign users
            process_type = random.choice(["Single Seat", "Step1", "Step2"])
            step1_user = None
            step2_user = None
            step1_fa = None
            step2_fa = None
            step1_start = None
            step1_end = None
            step2_start = None
            step2_end = None
            
            if process_type == "Single Seat":
                user = random.choice(team_users)
                step1_user = user
                step2_user = user
                step1_fa = random.choice(fa_names) if fa_names else None
                step2_fa = step1_fa
                # Random work duration between 30-120 minutes
                duration = random.randint(30, 120)
                step1_start = datetime.combine(current_date, time(9, random.randint(0, 59)))
                step1_end = step1_start + timedelta(minutes=duration)
                step2_start = step1_end
                step2_end = step2_start + timedelta(minutes=random.randint(5, 15))
            
            elif process_type == "Step1":
                step1_user = random.choice(team_users)
                step1_fa = random.choice(fa_names) if fa_names else None
                duration = random.randint(20, 60)
                step1_start = datetime.combine(current_date, time(9, random.randint(0, 59)))
                step1_end = step1_start + timedelta(minutes=duration)
            
            elif process_type == "Step2":
                step2_user = random.choice(team_users)
                step2_fa = random.choice(fa_names) if fa_names else None
                duration = random.randint(15, 45)
                step2_start = datetime.combine(current_date, time(10, random.randint(0, 59)))
                step2_end = step2_start + timedelta(minutes=duration)
            
            order = Order(
                file_number=file_number,
                entry_date=current_date,
                transaction_type_id=random.choice(trans_types).id,
                process_type_id=random.choice(proc_types).id,
                order_status_id=random.choice(statuses).id,
                division_id=random.choice(divisions).id,
                state=random.choice(team_states) if team_states else random.choice(states),
                county=random.choice(counties),
                product_type=random.choice(team_products) if team_products else random.choice(product_types),
                team_id=team.id,
                org_id=team.org_id,
                step1_user_id=step1_user.id if step1_user else None,
                step2_user_id=step2_user.id if step2_user else None,
                step1_fa_name_id=step1_fa.id if step1_fa else None,
                step2_fa_name_id=step2_fa.id if step2_fa else None,
                step1_start_time=step1_start,
                step1_end_time=step1_end,
                step2_start_time=step2_start,
                step2_end_time=step2_end,
                billing_status=random.choice(["pending", "done"]),
                created_by=random.choice(users).id
            )
            session.add(order)
            orders_created += 1
        
        current_date += timedelta(days=1)
        
        # Commit every few days to avoid memory issues
        if orders_created % 100 == 0:
            session.commit()
            print(f"  📈 Created {orders_created} orders...")
    
    session.commit()
    print(f"✅ Created {orders_created} orders for February 2026")
    
    # Create Attendance Records
    print("📅 Creating attendance records...")
    
    attendance_created = 0
    current_date = feb_start
    
    while current_date <= feb_end:
        # Skip weekends for attendance
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            for user in employees:
                # 95% chance of being present
                status = "present" if random.random() < 0.95 else random.choice(["absent", "leave"])
                
                attendance = AttendanceRecord(
                    user_id=user.id,
                    team_id=teams[0].id,  # Assign to first team for simplicity
                    org_id=user.org_id,
                    date=current_date.date(),
                    status=status,
                    marked_by=random.choice(team_leads).id if team_leads else user.id,
                    marked_at=datetime.combine(current_date, time(9, 0))
                )
                session.add(attendance)
                attendance_created += 1
        
        current_date += timedelta(days=1)
    
    session.commit()
    print(f"✅ Created {attendance_created} attendance records")
    
    # Create Quality Audits
    print("🔍 Creating quality audits...")
    
    quality_audits_created = 0
    
    # Create weekly quality audits for each team
    for week_start in [datetime(2026, 2, 3), datetime(2026, 2, 10), datetime(2026, 2, 17), datetime(2026, 2, 24)]:
        week_end = week_start + timedelta(days=6)
        
        for team in teams:
            team_employees = session.query(User).join(UserTeam).filter(
                UserTeam.team_id == team.id,
                User.user_role == 'EMPLOYEE'
            ).all()
            
            if not team_employees:
                continue
            
            for employee in team_employees[:3]:  # Audit first 3 employees per team per week
                # Random quality metrics
                total_files = random.randint(20, 50)
                files_with_error = random.randint(0, int(total_files * 0.1))  # 0-10% error rate
                total_errors = random.randint(files_with_error, files_with_error * 2)
                files_with_cce = random.randint(0, max(1, files_with_error // 2))
                
                # Calculate OFE based on process type
                process_type = random.choice(["Step1", "Step2", "Single Seat"])
                if process_type == "Step1":
                    ofe = min(total_files, 20)  # Max 20 for Step1
                elif process_type == "Step2":
                    ofe = min(total_files, 15)  # Max 15 for Step2
                else:  # Single Seat
                    ofe = min(total_files, 25)  # Max 25 for Single Seat
                
                audit = QualityAudit(
                    examiner_id=employee.id,
                    team_id=team.id,
                    org_id=team.org_id,
                    process_type=process_type,
                    ofe=ofe,
                    files_with_error=files_with_error,
                    total_errors=total_errors,
                    files_with_cce_error=files_with_cce,
                    total_files_reviewed=total_files,
                    ofe_count=ofe,
                    audit_date=week_start.date(),
                    audit_period_start=week_start.date(),
                    audit_period_end=week_end.date(),
                    created_by=random.choice(team_leads).id if team_leads else employee.id
                )
                
                # Calculate quality percentages
                audit.fb_quality = 1.0 - (files_with_error / total_files) if total_files > 0 else 1.0
                audit.ofe_quality = 1.0 - (total_errors / ofe) if ofe > 0 else 1.0
                audit.cce_quality = 1.0 - (files_with_cce / total_files) if total_files > 0 else 1.0
                
                session.add(audit)
                quality_audits_created += 1
    
    session.commit()
    print(f"✅ Created {quality_audits_created} quality audits")
    
    # Create Employee Weekly Targets
    print("🎯 Creating employee weekly targets...")
    
    targets_created = 0
    
    # Create targets for all 4 weeks of February
    for week_num in range(4):
        week_start = datetime(2026, 2, 3) + timedelta(weeks=week_num)  # Start from first Monday
        week_end = week_start + timedelta(days=6)
        
        for employee in employees:
            # Get employee's teams
            employee_teams = session.query(Team).join(UserTeam).filter(
                UserTeam.user_id == employee.id,
                UserTeam.is_active == True
            ).all()
            
            for team in employee_teams:
                # Set target between 40-60 for the week
                weekly_target = random.randint(40, 60)
                
                target = ExaminerWeeklyTarget(
                    user_id=employee.id,
                    team_id=team.id,
                    week_start_date=week_start.date(),
                    week_end_date=week_end.date(),
                    target=weekly_target,
                    created_by=team.team_lead_id if team.team_lead_id else random.choice(team_leads).id
                )
                session.add(target)
                targets_created += 1
    
    session.commit()
    print(f"✅ Created {targets_created} weekly targets")
    
    # Create Billing Reports
    print("💰 Creating billing reports...")
    
    # Create billing report for February 2026
    for team in teams:
        billing_report = BillingReport(
            org_id=team.org_id,
            team_id=team.id,
            billing_month=2,
            billing_year=2026,
            status="draft",
            created_by=team.team_lead_id if team.team_lead_id else random.choice(team_leads).id
        )
        session.add(billing_report)
        session.commit()  # Get the ID
        
        # Create billing details for each state/product combination
        team_states = [ts.state for ts in team.states]
        team_products = [tp.product_type for tp in team.products]
        
        for state in team_states:
            for product in team_products:
                # Get counts from actual orders
                orders_count = session.query(Order).filter(
                    Order.team_id == team.id,
                    Order.state == state,
                    Order.product_type == product,
                    Order.entry_date >= feb_start,
                    Order.entry_date <= feb_end
                ).count()
                
                if orders_count > 0:
                    # Distribute between different process types
                    single_seat = random.randint(0, orders_count // 2)
                    remaining = orders_count - single_seat
                    step1_only = random.randint(0, remaining)
                    step2_only = remaining - step1_only
                    
                    detail = BillingDetail(
                        report_id=billing_report.id,
                        state=state,
                        product_type=product,
                        single_seat_count=single_seat,
                        only_step1_count=step1_only,
                        only_step2_count=step2_only,
                        total_count=orders_count
                    )
                    session.add(detail)
    
    session.commit()
    print("✅ Created billing reports and details")
    
    # Create Performance Metrics (this would normally be auto-calculated)
    print("📊 Creating performance metrics...")
    
    metrics_created = 0
    current_date = feb_start
    created_metrics = set()  # Track created metrics to avoid duplicates
    
    while current_date <= feb_end:
        for employee in employees:
            # Create only one metric per examiner per day (regardless of teams)
            if (employee.id, current_date.date()) not in created_metrics:
                # Get all orders for this employee on this date across all teams
                employee_orders = session.query(Order).filter(
                    Order.entry_date == current_date.date(),
                    ((Order.step1_user_id == employee.id) | (Order.step2_user_id == employee.id))
                ).all()
                
                if employee_orders:
                    # Get employee's primary team (first team they belong to)
                    primary_team = session.query(Team).join(UserTeam).filter(
                        UserTeam.user_id == employee.id,
                        UserTeam.is_active == True
                    ).first()
                    
                    if primary_team:
                        # Calculate metrics
                        total_orders = len(employee_orders)
                        step1_completed = len([o for o in employee_orders if o.step1_user_id == employee.id])
                        step2_completed = len([o for o in employee_orders if o.step2_user_id == employee.id])
                        single_seat = len([o for o in employee_orders if o.step1_user_id == employee.id and o.step2_user_id == employee.id])
                        
                        # Calculate working time
                        total_minutes = 0
                        for order in employee_orders:
                            if order.step1_user_id == employee.id and order.step1_start_time and order.step1_end_time:
                                total_minutes += (order.step1_end_time - order.step1_start_time).total_seconds() / 60
                            if order.step2_user_id == employee.id and order.step2_start_time and order.step2_end_time:
                                total_minutes += (order.step2_end_time - order.step2_start_time).total_seconds() / 60
                        
                        metric = ExaminerPerformanceMetrics(
                            user_id=employee.id,
                            team_id=primary_team.id,
                            org_id=primary_team.org_id,
                            metric_date=current_date.date(),
                            period_type="daily",
                            total_orders_assigned=total_orders,
                            total_step1_completed=step1_completed,
                            total_step2_completed=step2_completed,
                            total_single_seat_completed=single_seat,
                            total_orders_completed=total_orders,
                            total_working_minutes=int(total_minutes),
                            avg_step1_duration_minutes=30 + random.randint(-10, 20),
                            avg_step2_duration_minutes=20 + random.randint(-5, 15),
                            avg_order_completion_minutes=45 + random.randint(-15, 25),
                            orders_on_hold=random.randint(0, max(1, total_orders // 10)),
                            orders_completed=total_orders - random.randint(0, max(1, total_orders // 20)),
                            orders_bp_rti=random.randint(0, max(1, total_orders // 15)),
                            efficiency_score=round(random.uniform(0.7, 0.98), 4),
                            quality_score=round(random.uniform(0.8, 0.99), 4),
                            calculation_status="completed"
                        )
                        session.add(metric)
                        metrics_created += 1
                        created_metrics.add((employee.id, current_date.date()))
        
        current_date += timedelta(days=1)
        
        # Commit every few days
        if metrics_created % 50 == 0:
            session.commit()
            print(f"  📈 Created {metrics_created} performance metrics...")
    
    session.commit()
    print(f"✅ Created {metrics_created} performance metrics")
    
    # Create Team Performance Metrics
    print("🏆 Creating team performance metrics...")
    
    team_metrics_created = 0
    current_date = feb_start
    
    while current_date <= feb_end:
        for team in teams:
            # Get team orders for the day
            team_orders = session.query(Order).filter(
                Order.team_id == team.id,
                Order.entry_date == current_date.date()
            ).all()
            
            if team_orders:
                # Get active employees count
                active_examiners = session.query(User).join(UserTeam).filter(
                    UserTeam.team_id == team.id,
                    UserTeam.is_active == True,
                    User.user_role == 'EMPLOYEE'
                ).count()
                
                total_orders = len(team_orders)
                completed_orders = len([o for o in team_orders if o.order_status.name == "Completed"])
                in_progress_orders = len([o for o in team_orders if o.order_status.name == "In Progress"])
                on_hold_orders = len([o for o in team_orders if o.order_status.name == "On-hold"])
                
                # Create breakdowns
                transaction_breakdown = {}
                product_breakdown = {}
                state_breakdown = {}
                
                for order in team_orders:
                    # Transaction breakdown
                    trans_name = order.transaction_type.name
                    transaction_breakdown[trans_name] = transaction_breakdown.get(trans_name, 0) + 1
                    
                    # Product breakdown
                    product_breakdown[order.product_type] = product_breakdown.get(order.product_type, 0) + 1
                    
                    # State breakdown
                    state_breakdown[order.state] = state_breakdown.get(order.state, 0) + 1
                
                team_metric = TeamPerformanceMetrics(
                    team_id=team.id,
                    org_id=team.org_id,
                    metric_date=current_date.date(),
                    period_type="daily",
                    total_orders_assigned=total_orders,
                    total_orders_completed=completed_orders,
                    total_orders_in_progress=in_progress_orders,
                    total_orders_on_hold=on_hold_orders,
                    active_examiners_count=active_examiners,
                    team_efficiency_score=round(random.uniform(0.75, 0.95), 4),
                    orders_per_examiner=round(total_orders / max(active_examiners, 1), 2),
                    completion_rate=round(completed_orders / max(total_orders, 1), 4),
                    transaction_breakdown=json.dumps(transaction_breakdown),
                    product_breakdown=json.dumps(product_breakdown),
                    state_breakdown=json.dumps(state_breakdown)
                )
                session.add(team_metric)
                team_metrics_created += 1
        
        current_date += timedelta(days=1)
        
        if team_metrics_created % 20 == 0:
            session.commit()
            print(f"  📈 Created {team_metrics_created} team metrics...")
    
    session.commit()
    print(f"✅ Created {team_metrics_created} team performance metrics")
    
    # # Create some audit logs (commented out due to ID constraint issue)
    # print("📝 Creating audit logs...")
    # 
    # for _ in range(50):  # Create 50 random audit logs
    #     user = random.choice(users)
    #     
    #     audit_log = AuditLog(
    #         entity_type="Order",
    #         entity_id=random.randint(1, orders_created),
    #         entity_name=f"Order #{random.randint(1, orders_created)}",
    #         action="update",
    #         changes=json.dumps({"status": {"old": "In Progress", "new": "Completed"}}),
    #         old_values=json.dumps({"status": "In Progress"}),
    #         new_values=json.dumps({"status": "Completed"}),
    #         user_id=user.id,
    #         username=user.user_name,
    #         user_role=user.user_role,
    #         ip_address="192.168.1.100",
    #         user_agent="Mozilla/5.0...",
    #         endpoint="/api/orders/123",
    #         request_method="PUT",
    #         description="Order status updated",
    #         organization_id=user.org_id,
    #         created_at=feb_start + timedelta(days=random.randint(0, 27), hours=random.randint(0, 23))
    #     )
    #     session.add(audit_log)
    # 
    # session.commit()
    print("✅ Skipped audit logs (not critical for dashboard testing)")
    
    # Final summary
    print("\n🎉 February 2026 dummy data creation completed!")
    print("\n📊 Final Summary:")
    print(f"  📋 Orders: {session.query(Order).filter(Order.entry_date >= feb_start, Order.entry_date <= feb_end).count()}")
    print(f"  📅 Attendance Records: {session.query(AttendanceRecord).filter(AttendanceRecord.date >= feb_start.date(), AttendanceRecord.date <= feb_end.date()).count()}")
    print(f"  🔍 Quality Audits: {session.query(QualityAudit).filter(QualityAudit.audit_date >= feb_start.date(), QualityAudit.audit_date <= feb_end.date()).count()}")
    print(f"  🎯 Weekly Targets: {session.query(ExaminerWeeklyTarget).filter(ExaminerWeeklyTarget.week_start_date >= feb_start.date()).count()}")
    print(f"  📊 Employee Metrics: {session.query(ExaminerPerformanceMetrics).filter(ExaminerPerformanceMetrics.metric_date >= feb_start.date(), ExaminerPerformanceMetrics.metric_date <= feb_end.date()).count()}")
    print(f"  🏆 Team Metrics: {session.query(TeamPerformanceMetrics).filter(TeamPerformanceMetrics.metric_date >= feb_start.date(), TeamPerformanceMetrics.metric_date <= feb_end.date()).count()}")
    print(f"  💰 Billing Reports: {session.query(BillingReport).filter(BillingReport.billing_month == 2, BillingReport.billing_year == 2026).count()}")
    print(f"  👥 Total Users: {session.query(User).count()}")
    print(f"  🏢 Total Teams: {session.query(Team).count()}")
    
    print("\n🔍 Test the following dashboard features:")
    print("  📈 Performance Analytics - Daily/Weekly/Monthly views")
    print("  👥 Employee Management - Individual performance tracking") 
    print("  🏆 Team Management - Team performance comparisons")
    print("  📋 Order Management - Order tracking and status")
    print("  📅 Attendance Tracking - Employee attendance records")
    print("  🔍 Quality Management - Quality audits and scores")
    print("  💰 Billing Reports - Monthly billing breakdown")
    print("  📊 Dashboard Charts - All metrics and KPIs")
    
    session.close()
    print("\n✅ Database is ready for comprehensive testing!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're in the Backend directory and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to add dummy data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)