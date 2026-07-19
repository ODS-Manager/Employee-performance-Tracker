"""
Attendance API Endpoints
Team leads mark attendance for their team members
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta

from app.database import get_db
from app.models.user import User
from app.models.team import Team
from app.models.attendance import AttendanceRecord
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceBulkCreate,
    AttendanceRecordUpdate,
    AttendanceRecordResponse,
    DailyRosterResponse,
    AttendanceSummary,
    TeamAttendanceReport,
    TeamMonthlyAttendanceReport
)
from app.core.dependencies import (
    get_current_active_user,
    require_team_lead_or_admin,
    require_admin,
    is_team_lead_of,
    get_user_teams,
    ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD, ROLE_EXAMINER
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark", response_model=AttendanceRecordResponse)
def mark_attendance(
    data: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_lead_or_admin)
):
    """
    Mark attendance for single examiner
    Team leads can only mark for their team, admins for any team
    """
    service = AttendanceService(db)
    
    # Authorization check for team leads
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        # Check if current user is lead of the team (via Team.team_lead_id or UserTeam.role='lead')
        if not is_team_lead_of(current_user.id, data.team_id, db):
            raise HTTPException(
                status_code=403,
                detail="You can only mark attendance for your own team"
            )
    
    return service.mark_attendance_single(
        user_id=data.user_id,
        team_id=data.team_id,
        check_date=data.date,
        status=data.status,
        marked_by=current_user.id,
        notes=data.notes
    )


@router.post("/mark-bulk", response_model=List[AttendanceRecordResponse])
def mark_attendance_bulk(
    data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_lead_or_admin)
):
    """
    Bulk mark attendance for multiple examiners
    Useful for "Mark All as Present" functionality
    """
    service = AttendanceService(db)
    
    # Authorization check for team leads
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        if not is_team_lead_of(current_user.id, data.team_id, db):
            raise HTTPException(
                status_code=403,
                detail="You can only mark attendance for your own team"
            )
    
    return service.mark_attendance_bulk(
        team_id=data.team_id,
        check_date=data.date,
        status=data.status,
        examiner_ids=data.examiner_ids,
        marked_by=current_user.id
    )


@router.get("/roster", response_model=DailyRosterResponse)
def get_daily_roster(
    team_id: int,
    date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_lead_or_admin)
):
    """
    Get daily roster with attendance status for all team members
    """
    service = AttendanceService(db)
    
    # Authorization check for team leads
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        if not is_team_lead_of(current_user.id, team_id, db):
            raise HTTPException(
                status_code=403,
                detail="You can only view roster for your own team"
            )
    
    roster = service.get_daily_roster(team_id=team_id, check_date=date)
    
    # If team lead is viewing, filter to show only examiners
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        # Filter examiners to only include those with examiner role
        filtered_examiners = [e for e in roster.examiners if e.user_role == ROLE_EXAMINER]
        roster.examiners = filtered_examiners
    
    return roster


@router.get("/examiner/{user_id}", response_model=AttendanceSummary)
def get_examiner_attendance(
    user_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get attendance summary for an examiner
    Examiners can view their own, team leads can view their team, admins can view all
    """
    service = AttendanceService(db)
    
    # Authorization check
    if current_user.user_role == "examiner" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own attendance"
        )
    
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        # Check if user is in team lead's team
        from app.models.user_team import UserTeam
        
        # Get all teams led by current user (via both Team.team_lead_id and UserTeam.role='lead')
        led_team_ids = get_user_teams(current_user, db)
        
        # Check if target user is in any of these teams
        membership = db.query(UserTeam).filter(
            UserTeam.user_id == user_id,
            UserTeam.team_id.in_(led_team_ids) if led_team_ids else False
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=403,
                detail="You can only view attendance for your team members"
            )
    
    return service.get_examiner_attendance_summary(user_id, start_date, end_date)


@router.get("/reports/team/{team_id}", response_model=TeamAttendanceReport)
def get_team_attendance_report(
    team_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_lead_or_admin)
):
    """
    Generate team attendance report
    """
    service = AttendanceService(db)
    
    # Authorization check for team leads
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        if not is_team_lead_of(current_user.id, team_id, db):
            raise HTTPException(
                status_code=403,
                detail="You can only generate reports for your own team"
            )
    
    return service.get_team_attendance_report(team_id, start_date, end_date)


@router.put("/{record_id}", response_model=AttendanceRecordResponse)
def update_attendance(
    record_id: int,
    data: AttendanceRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_lead_or_admin)
):
    """
    Update existing attendance record
    """
    from app.models.attendance import AttendanceRecord
    
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Authorization check for team leads
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        if not is_team_lead_of(current_user.id, record.team_id, db):
            raise HTTPException(
                status_code=403,
                detail="You can only update attendance for your own team"
            )
    
    service = AttendanceService(db)
    return service.mark_attendance_single(
        user_id=record.user_id,
        team_id=record.team_id,
        check_date=record.date,
        status=data.status,
        marked_by=current_user.id,
        notes=data.notes
    )


@router.get("/team/{team_id}/monthly-detail", response_model=TeamMonthlyAttendanceReport)
def get_team_monthly_attendance_detail(
    team_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_team_lead_or_admin)
):
    """
    Get detailed monthly attendance with daily breakdown for all team members
    """
    service = AttendanceService(db)
    
    # Authorization check for team leads
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        if not is_team_lead_of(current_user.id, team_id, db):
            raise HTTPException(
                status_code=403,
                detail="You can only view attendance for your own team"
            )
    
    report = service.get_team_monthly_attendance_detail(team_id, start_date, end_date)
    
    # If team lead is viewing, filter to show only examiners
    if current_user.user_role.lower() == ROLE_TEAM_LEAD:
        report.examiners = [e for e in report.examiners if e.user_role == ROLE_EXAMINER]
    
    return report


@router.post("/team-lead", response_model=AttendanceRecordResponse)
def mark_team_lead_attendance(
    data: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Mark attendance for a team lead (admin only)
    Team leads cannot mark their own attendance - only admins can do this
    """
    service = AttendanceService(db)
    
    # Verify the user is a team lead
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.user_role != ROLE_TEAM_LEAD:
        raise HTTPException(status_code=400, detail="User is not a team lead")
    
    # Check organization access for admin
    if current_user.user_role.lower() == ROLE_ADMIN:
        if target_user.org_id != current_user.org_id:
            raise HTTPException(
                status_code=403,
                detail="You can only mark attendance for team leads in your organization"
            )
    
    # Mark attendance for team lead. The frontend sends team_id=0 as a sentinel
    # for team leads who don't belong to a single specific team. We look up the
    # team lead's primary team when available and fall back to the first team in
    # the org (team_id must be a valid FK to teams.id).
    team_id = data.team_id if data.team_id is not None else target_user.org_id
    if data.team_id == 0:
        led_team = db.query(Team).filter(Team.team_lead_id == target_user.id).first()
        if led_team:
            team_id = led_team.id
        else:
            # Fall back to first team in the org to satisfy FK constraint
            any_team = db.query(Team).filter(
                Team.org_id == target_user.org_id,
                Team.is_active == True,
            ).first()
            if any_team:
                team_id = any_team.id

    # Backward compatibility: if an existing record exists for this date under a
    # different team_id (e.g. old code stored org_id as team_id), reuse that
    # team_id so we update rather than create a duplicate record.
    existing_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == data.user_id,
        AttendanceRecord.date == data.date
    ).order_by(AttendanceRecord.id.desc()).first()
    if existing_record:
        team_id = existing_record.team_id

    return service.mark_attendance_single(
        user_id=data.user_id,
        team_id=team_id,
        check_date=data.date,
        status=data.status,
        marked_by=current_user.id,
        notes=data.notes,
        skip_team_validation=True
    )


@router.get("/team-leads/monthly")
def get_team_leads_monthly_attendance(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get monthly attendance summary for all team leads (admin only).
    Returns day-by-day attendance status for each team lead.
    """
    from app.schemas.attendance import ExaminerMonthlyAttendance, TeamMonthlyAttendanceReport
    
    # Get all team leads in the admin's organization
    query = db.query(User).filter(
        User.user_role == ROLE_TEAM_LEAD,
        User.is_active == True
    )
    
    if current_user.user_role.lower() == ROLE_ADMIN:
        query = query.filter(User.org_id == current_user.org_id)
    
    team_leads = query.all()
    
    # Get attendance records for all team leads
    team_lead_ids = [tl.id for tl in team_leads]
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id.in_(team_lead_ids),
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ).all() if team_lead_ids else []
    
    # Group records by user
    records_by_user = {}
    for record in attendance_records:
        if record.user_id not in records_by_user:
            records_by_user[record.user_id] = []
        records_by_user[record.user_id].append(record)
    
    # Calculate working days in the period
    from datetime import timedelta
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() <= 4:  # Monday to Friday
            working_days += 1
        current += timedelta(days=1)
    
    # Build examiners list
    examiners_data = []
    for tl in team_leads:
        user_records = records_by_user.get(tl.id, [])
        days_present = sum(
            1 if r.status == 'present' else 0.5
            for r in user_records
            if r.status in ('present', 'half_day') and r.date.weekday() <= 4
        )
        days_half_day = sum(1 for r in user_records if r.status == 'half_day' and r.date.weekday() <= 4)
        days_leave = sum(1 for r in user_records if r.status == 'leave' and r.date.weekday() <= 4)
        days_not_marked = working_days - sum(
            1 for r in user_records
            if r.date.weekday() <= 4 and r.status in ('present', 'half_day', 'leave')
        )
        
        # Build daily records
        daily_records = []
        current_day = start_date
        while current_day <= end_date:
            day_record = next((r for r in user_records if r.date == current_day), None)
            daily_records.append({
                'date': current_day.isoformat(),
                'status': day_record.status if day_record else None
            })
            current_day += timedelta(days=1)
        
        examiners_data.append({
            'userId': tl.id,
            'userName': tl.user_name,
            'examinerId': tl.examiner_id,
            'totalDays': working_days,
            'daysPresent': days_present,
            'daysHalfDay': days_half_day,
            'daysLeave': days_leave,
            'daysNotMarked': days_not_marked,
            'dailyRecords': daily_records
        })
    
    # Sort by userName
    examiners_data.sort(key=lambda x: x['userName'] or '')
    
    return {
        'teamId': 0,
        'teamName': 'All Team Leads',
        'startDate': start_date.isoformat(),
        'endDate': end_date.isoformat(),
        'examiners': examiners_data
    }


@router.get("/team-lead/{user_id}", response_model=AttendanceSummary)
def get_team_lead_attendance(
    user_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get attendance summary for a team lead
    Team leads can view their own attendance (read-only)
    Admins can view any team lead's attendance
    """
    import logging
    logger = logging.getLogger(__name__)
    
    service = AttendanceService(db)
    
    # Verify the user is a team lead
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.user_role != ROLE_TEAM_LEAD:
        raise HTTPException(status_code=400, detail="User is not a team lead")
    
    # Authorization check
    if current_user.user_role.lower() == ROLE_TEAM_LEAD and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own attendance"
        )
    
    if current_user.user_role.lower() == ROLE_ADMIN:
        if target_user.org_id != current_user.org_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view attendance for team leads in your organization"
            )
    
    logger.info(f"Fetching attendance for user {user_id} from {start_date} to {end_date}")
    result = service.get_examiner_attendance_summary(user_id=user_id, start_date=start_date, end_date=end_date)
    logger.info(f"Found {len(result.records)} records for user {user_id}")
    
    return result
