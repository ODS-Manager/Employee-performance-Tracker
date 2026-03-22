"""
Examiner Weekly Targets API Routes
Manage weekly productivity targets for examiners set by team leads.

Business Logic:
- Target is per examiner PER TEAM (each team lead sets target for their team members)
- Examiner can have different targets in different teams
- Examiner's total target = SUM of targets from all teams they belong to
- Productivity = Total Score / Sum of All Team Targets × 100

Example:
- Examiner X in Team A: target = 20 (set by Team A lead)
- Examiner X in Team B: target = 15 (set by Team B lead)
- Examiner X total target = 20 + 15 = 35
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta
from app.database import get_db
from app.core.dependencies import (
    get_current_active_user, get_user_teams,
    ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD
)
from app.models.user import User
from app.models.team import Team
from app.models.user_team import UserTeam
from app.models.examiner_weekly_target import ExaminerWeeklyTarget
from app.schemas.examiner_weekly_target import WeeklyTargetBulkCreate

router = APIRouter()


def get_week_boundaries(reference_date: date) -> tuple[date, date]:
    """
    Get the Sunday-Saturday week boundaries for a given date.
    Returns (week_start_date, week_end_date) where:
    - week_start_date is Sunday
    - week_end_date is Saturday
    """
    day_of_week = reference_date.weekday()
    
    if day_of_week == 6:  # Sunday
        week_start = reference_date
    else:
        days_since_sunday = day_of_week + 1
        week_start = reference_date - timedelta(days=days_since_sunday)
    
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def serialize_weekly_target(target: ExaminerWeeklyTarget) -> dict:
    """Serialize weekly target to camelCase dict"""
    return {
        "id": target.id,
        "userId": target.user_id,
        "teamId": target.team_id,  # Team context for this target
        "weekStartDate": target.week_start_date.isoformat() if target.week_start_date else None,
        "weekEndDate": target.week_end_date.isoformat() if target.week_end_date else None,
        "target": target.target,
        "createdBy": target.created_by,
        "createdAt": target.created_at.isoformat() if target.created_at else None,
        "modifiedAt": target.modified_at.isoformat() if target.modified_at else None
    }


@router.get("/current-week")
async def get_current_week_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get information about the current week (Sunday-Saturday)"""
    today = date.today()
    week_start, week_end = get_week_boundaries(today)
    
    return {
        "weekStartDate": week_start.isoformat(),
        "weekEndDate": week_end.isoformat(),
        "today": today.isoformat(),
        "isCurrentWeek": True,
        "canEdit": True
    }


@router.get("/team/{team_id}")
async def get_team_weekly_targets(
    team_id: int,
    week_start_date: Optional[date] = Query(None, description="Sunday of the week to get targets for"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly targets for all team members for a specific week.
    If week_start_date is not provided, uses the current week.
    
    Note: Targets are per examiner PER TEAM. This endpoint shows 
    targets set for examiners within this specific team context.
    """
    # Check team access
    user_teams = get_user_teams(current_user, db)
    if team_id not in user_teams and current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this team"
        )
    
    # Get the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Determine the week
    today = date.today()
    if week_start_date:
        if week_start_date.weekday() != 6:  # 6 = Sunday
            week_start, week_end = get_week_boundaries(week_start_date)
        else:
            week_start = week_start_date
            week_end = week_start + timedelta(days=6)
    else:
        week_start, week_end = get_week_boundaries(today)
    
    # Determine week status
    current_week_start, _ = get_week_boundaries(today)
    is_current_week = week_start == current_week_start
    is_past_week = week_start < current_week_start
    can_edit = not is_past_week  # Can edit current and future weeks
    
    # Get all active team members (employees only)
    team_members = db.query(User, UserTeam).join(
        UserTeam, UserTeam.user_id == User.id
    ).filter(
        UserTeam.team_id == team_id,
        UserTeam.is_active == True,
        User.is_active == True,
        User.user_role == "examiner"
    ).all()
    
    # Get user IDs of team members
    member_user_ids = [user.id for user, _ in team_members]
    
    # Get targets for these employees for this week FOR THIS SPECIFIC TEAM
    targets = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id.in_(member_user_ids),
        ExaminerWeeklyTarget.team_id == team_id,  # Filter by team
        ExaminerWeeklyTarget.week_start_date == week_start
    ).all()
    
    # Create a map of user_id -> target
    target_map = {t.user_id: t for t in targets}
    
    # Get previous week's targets for reference (for this team)
    prev_week_start = week_start - timedelta(days=7)
    prev_targets = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id.in_(member_user_ids),
        ExaminerWeeklyTarget.team_id == team_id,  # Filter by team
        ExaminerWeeklyTarget.week_start_date == prev_week_start
    ).all()
    prev_target_map = {t.user_id: t.target for t in prev_targets}
    
    # Build response
    members = []
    for user, user_team in team_members:
        current_target_obj = target_map.get(user.id)
        members.append({
            "userId": user.id,
            "userName": user.user_name,
            "examinerId": user.examiner_id,
            "currentTarget": current_target_obj.target if current_target_obj else None,
            "previousTarget": prev_target_map.get(user.id),
            "targetId": current_target_obj.id if current_target_obj else None
        })
    
    # Sort by userName
    members.sort(key=lambda x: x["userName"] or "")
    
    return {
        "teamId": team_id,
        "teamName": team.name,
        "weekInfo": {
            "weekStartDate": week_start.isoformat(),
            "weekEndDate": week_end.isoformat(),
            "isCurrentWeek": is_current_week,
            "isPastWeek": is_past_week,
            "canEdit": can_edit
        },
        "members": members
    }


@router.post("/team/{team_id}")
async def set_team_weekly_targets(
    team_id: int,
    data: WeeklyTargetBulkCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Set or update weekly targets for multiple team members within this team.
    Only team leads can set targets for their team members.
    Cannot set targets for past weeks.
    
    Note: Targets are per examiner PER TEAM. Setting a target here
    sets the target for examiners within this team's context only.
    Employee's total target = SUM of targets from all their teams.
    """
    # Check if user is team lead or admin
    if current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leads and admins can set weekly targets"
        )
    
    # Check team access
    user_teams = get_user_teams(current_user, db)
    if team_id not in user_teams and current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this team"
        )
    
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Validate week_start_date is a Sunday
    week_start = data.week_start_date
    if week_start.weekday() != 6:  # 6 = Sunday
        week_start, _ = get_week_boundaries(week_start)
    
    week_end = week_start + timedelta(days=6)
    
    # Check if this is a past week
    today = date.today()
    current_week_start, _ = get_week_boundaries(today)
    if week_start < current_week_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set targets for past weeks"
        )
    
    # Get valid team member user IDs
    valid_member_ids = set(
        row[0] for row in db.query(UserTeam.user_id).filter(
            UserTeam.team_id == team_id,
            UserTeam.is_active == True
        ).all()
    )
    
    created_count = 0
    updated_count = 0
    
    for entry in data.targets:
        # Validate user is a team member
        if entry.user_id not in valid_member_ids:
            continue  # Skip invalid users
        
        # Check if target already exists for this employee + team + week
        existing = db.query(ExaminerWeeklyTarget).filter(
            ExaminerWeeklyTarget.user_id == entry.user_id,
            ExaminerWeeklyTarget.team_id == team_id,  # Filter by team
            ExaminerWeeklyTarget.week_start_date == week_start
        ).first()
        
        if existing:
            # Update existing target
            existing.target = entry.target
            existing.modified_at = datetime.utcnow()
            updated_count += 1
        else:
            # Create new target with team_id
            new_target = ExaminerWeeklyTarget(
                user_id=entry.user_id,
                team_id=team_id,  # Set team context
                week_start_date=week_start,
                week_end_date=week_end,
                target=entry.target,
                created_by=current_user.id
            )
            db.add(new_target)
            created_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Targets saved: {created_count} created, {updated_count} updated",
        "createdCount": created_count,
        "updatedCount": updated_count,
        "weekStartDate": week_start.isoformat(),
        "weekEndDate": week_end.isoformat()
    }


@router.get("/examiner/{user_id}")
async def get_examiner_weekly_targets(
    user_id: int,
    start_date: Optional[date] = Query(None, description="Start date for range"),
    end_date: Optional[date] = Query(None, description="End date for range"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly targets for a specific examiner.
    Returns targets for all weeks in the specified date range.
    """
    # Check access - user can view their own, team leads/admins can view any
    if user_id != current_user.id:
        if current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own targets"
            )
        
        # Team lead can only view their team members
        if current_user.user_role.lower() == ROLE_TEAM_LEAD:
            # Check if user is in any of the team lead's teams
            user_teams = get_user_teams(current_user, db)
            user_in_teams = db.query(UserTeam).filter(
                UserTeam.user_id == user_id,
                UserTeam.team_id.in_(user_teams),
                UserTeam.is_active == True
            ).first()
            if not user_in_teams:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view targets for your team members"
                )
    
    # Build query
    query = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id == user_id
    )
    
    if start_date:
        query = query.filter(ExaminerWeeklyTarget.week_start_date >= start_date)
    if end_date:
        query = query.filter(ExaminerWeeklyTarget.week_end_date <= end_date)
    
    targets = query.order_by(ExaminerWeeklyTarget.week_start_date.desc()).all()
    
    return {
        "userId": user_id,
        "targets": [serialize_weekly_target(t) for t in targets]
    }


@router.get("/my-target")
async def get_my_current_target(
    week_start_date: Optional[date] = Query(None, description="Sunday of the week"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's total weekly target (sum of all team targets).
    If week_start_date is not provided, uses the current week.
    
    Returns:
    - totalTarget: Sum of targets from all teams for this week
    - teamTargets: Breakdown of targets by team
    """
    # Determine the week
    today = date.today()
    if week_start_date:
        if week_start_date.weekday() != 6:
            week_start, week_end = get_week_boundaries(week_start_date)
        else:
            week_start = week_start_date
            week_end = week_start + timedelta(days=6)
    else:
        week_start, week_end = get_week_boundaries(today)
    
    # Get all targets for this user for this week (one per team)
    targets = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id == current_user.id,
        ExaminerWeeklyTarget.week_start_date == week_start
    ).all()
    
    # Calculate total target (sum from all teams)
    total_target = sum(t.target for t in targets) if targets else None
    
    # Get team breakdown
    team_targets = []
    for t in targets:
        team = db.query(Team).filter(Team.id == t.team_id).first()
        team_targets.append({
            "teamId": t.team_id,
            "teamName": team.name if team else "Unknown",
            "target": t.target,
            "targetId": t.id
        })
    
    # If no targets for this week, check for most recent targets (carryforward)
    is_carry_forward = False
    if not targets:
        prev_targets = db.query(ExaminerWeeklyTarget).filter(
            ExaminerWeeklyTarget.user_id == current_user.id,
            ExaminerWeeklyTarget.week_start_date < week_start
        ).order_by(ExaminerWeeklyTarget.week_start_date.desc()).all()
        
        # Group by team and get the most recent target for each team
        team_latest_targets = {}
        for t in prev_targets:
            if t.team_id not in team_latest_targets:
                team_latest_targets[t.team_id] = t
        
        if team_latest_targets:
            is_carry_forward = True
            total_target = sum(t.target for t in team_latest_targets.values())
            for t in team_latest_targets.values():
                team = db.query(Team).filter(Team.id == t.team_id).first()
                team_targets.append({
                    "teamId": t.team_id,
                    "teamName": team.name if team else "Unknown",
                    "target": t.target,
                    "targetId": t.id
                })
    
    return {
        "weekStartDate": week_start.isoformat(),
        "weekEndDate": week_end.isoformat(),
        "totalTarget": total_target,
        "teamTargets": team_targets,
        "isCarryForward": is_carry_forward
    }


@router.post("/copy-from-previous/{team_id}")
async def copy_targets_from_previous_week(
    team_id: int,
    week_start_date: date = Query(..., description="Sunday of the week to copy TO"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Copy all targets from the previous week to the specified week for team members.
    Only copies for members who don't already have a target set for THIS TEAM.
    
    Note: Copies targets within the same team context only.
    """
    # Check if user is team lead or admin
    if current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_TEAM_LEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leads and admins can copy targets"
        )
    
    # Check team access
    user_teams = get_user_teams(current_user, db)
    if team_id not in user_teams and current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this team"
        )
    
    # Validate and adjust week_start_date
    if week_start_date.weekday() != 6:
        week_start_date, _ = get_week_boundaries(week_start_date)
    
    week_end = week_start_date + timedelta(days=6)
    
    # Check if this is a past week
    today = date.today()
    current_week_start, _ = get_week_boundaries(today)
    if week_start_date < current_week_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set targets for past weeks"
        )
    
    # Get team member IDs
    team_member_ids = [
        row[0] for row in db.query(UserTeam.user_id).filter(
            UserTeam.team_id == team_id,
            UserTeam.is_active == True
        ).all()
    ]
    
    # Get previous week's targets for these team members FOR THIS TEAM
    prev_week_start = week_start_date - timedelta(days=7)
    prev_targets = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id.in_(team_member_ids),
        ExaminerWeeklyTarget.team_id == team_id,  # Filter by team
        ExaminerWeeklyTarget.week_start_date == prev_week_start
    ).all()
    
    if not prev_targets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No targets found for previous week in this team"
        )
    
    # Get existing targets for target week FOR THIS TEAM
    existing_user_ids = set(
        row[0] for row in db.query(ExaminerWeeklyTarget.user_id).filter(
            ExaminerWeeklyTarget.user_id.in_(team_member_ids),
            ExaminerWeeklyTarget.team_id == team_id,  # Filter by team
            ExaminerWeeklyTarget.week_start_date == week_start_date
        ).all()
    )
    
    created_count = 0
    for prev_target in prev_targets:
        if prev_target.user_id not in existing_user_ids:
            new_target = ExaminerWeeklyTarget(
                user_id=prev_target.user_id,
                team_id=team_id,  # Set team context
                week_start_date=week_start_date,
                week_end_date=week_end,
                target=prev_target.target,
                created_by=current_user.id
            )
            db.add(new_target)
            created_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Copied {created_count} targets from previous week",
        "copiedCount": created_count,
        "weekStartDate": week_start_date.isoformat(),
        "weekEndDate": week_end.isoformat()
    }


@router.get("/team-leads")
async def get_team_lead_targets(
    week_start_date: Optional[date] = Query(None, description="Sunday of the week to get targets for"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly targets for all team leads (admin only).
    Team leads have overall targets (not per-team like examiners).
    """
    # Only admins and superadmins can access this
    if current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage team lead targets"
        )
    
    # Determine the week
    today = date.today()
    if week_start_date:
        if week_start_date.weekday() != 6:  # 6 = Sunday
            week_start, week_end = get_week_boundaries(week_start_date)
        else:
            week_start = week_start_date
            week_end = week_start + timedelta(days=6)
    else:
        week_start, week_end = get_week_boundaries(today)
    
    # Determine week status
    current_week_start, _ = get_week_boundaries(today)
    is_current_week = week_start == current_week_start
    is_past_week = week_start < current_week_start
    can_edit = not is_past_week
    
    # Build query for team leads
    query = db.query(User).filter(
        User.user_role == ROLE_TEAM_LEAD,
        User.is_active == True
    )
    
    # For admin, filter by their org
    if current_user.user_role == ROLE_ADMIN:
        query = query.filter(User.org_id == current_user.org_id)
    
    team_leads = query.all()
    
    # Get targets for these team leads for this week
    # For team leads, we use org_id as the team_id in the target record
    team_lead_ids = [tl.id for tl in team_leads]
    targets = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id.in_(team_lead_ids),
        ExaminerWeeklyTarget.week_start_date == week_start
    ).all()
    
    # Create a map of user_id -> target
    target_map = {t.user_id: t for t in targets}
    
    # Get previous week's targets for reference
    prev_week_start = week_start - timedelta(days=7)
    prev_targets = db.query(ExaminerWeeklyTarget).filter(
        ExaminerWeeklyTarget.user_id.in_(team_lead_ids),
        ExaminerWeeklyTarget.week_start_date == prev_week_start
    ).all()
    prev_target_map = {t.user_id: t.target for t in prev_targets}
    
    # Build response
    members = []
    for team_lead in team_leads:
        current_target_obj = target_map.get(team_lead.id)
        members.append({
            "userId": team_lead.id,
            "userName": team_lead.user_name,
            "examinerId": team_lead.examiner_id,
            "currentTarget": current_target_obj.target if current_target_obj else None,
            "previousTarget": prev_target_map.get(team_lead.id),
            "targetId": current_target_obj.id if current_target_obj else None
        })
    
    # Sort by userName
    members.sort(key=lambda x: x["userName"] or "")
    
    return {
        "weekInfo": {
            "weekStartDate": week_start.isoformat(),
            "weekEndDate": week_end.isoformat(),
            "isCurrentWeek": is_current_week,
            "isPastWeek": is_past_week,
            "canEdit": can_edit
        },
        "members": members
    }


@router.post("/team-leads")
async def set_team_lead_targets(
    data: WeeklyTargetBulkCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Set weekly targets for team leads (admin only).
    Each target record uses the team lead's org_id as the team_id.
    """
    # Only admins and superadmins can set team lead targets
    if current_user.user_role not in [ROLE_SUPERADMIN, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can set team lead targets"
        )
    
    # Validate week_start_date
    week_start = data.week_start_date
    if week_start.weekday() != 6:  # 6 = Sunday
        week_start, week_end = get_week_boundaries(week_start)
    else:
        week_end = week_start + timedelta(days=6)
    
    # Check if this is a past week
    today = date.today()
    current_week_start, _ = get_week_boundaries(today)
    if week_start < current_week_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set targets for past weeks"
        )
    
    created_count = 0
    updated_count = 0
    
    for target_data in data.targets:
        # Verify the user is a team lead
        team_lead = db.query(User).filter(
            User.id == target_data.user_id,
            User.user_role == ROLE_TEAM_LEAD
        ).first()
        
        if not team_lead:
            continue
        
        # Check organization access for admin
        if current_user.user_role == ROLE_ADMIN:
            if team_lead.org_id != current_user.org_id:
                continue
        
        # Check if target already exists for this week
        existing_target = db.query(ExaminerWeeklyTarget).filter(
            ExaminerWeeklyTarget.user_id == target_data.user_id,
            ExaminerWeeklyTarget.week_start_date == week_start
        ).first()
        
        # Use org_id as team_id for team lead targets
        team_id_for_record = team_lead.org_id
        
        if existing_target:
            # Update existing target
            existing_target.target = target_data.target
            existing_target.team_id = team_id_for_record  # Ensure org_id is set
            existing_target.modified_at = datetime.utcnow()
            updated_count += 1
        else:
            # Create new target
            new_target = ExaminerWeeklyTarget(
                user_id=target_data.user_id,
                team_id=team_id_for_record,  # Use org_id as team_id
                week_start_date=week_start,
                week_end_date=week_end,
                target=target_data.target,
                created_by=current_user.id
            )
            db.add(new_target)
            created_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Created {created_count} and updated {updated_count} targets",
        "createdCount": created_count,
        "updatedCount": updated_count,
        "weekStartDate": week_start.isoformat(),
        "weekEndDate": week_end.isoformat()
    }
