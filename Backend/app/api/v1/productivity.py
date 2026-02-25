"""
Productivity API Endpoints
Endpoints for examiner and team productivity calculations.

Business Logic:
- Target is per examiner (not per team)
- Score is calculated across ALL teams the examiner belongs to
- Productivity = Total Score (all teams) / Weekly Target × 100
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.user import User
from app.services.productivity_service import ProductivityService

router = APIRouter()

# Role checkers
require_admin_or_higher = RoleChecker(['superadmin', 'admin', 'team_lead'])


@router.get("/examiner/{user_id}")
async def get_examiner_productivity(
    user_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get productivity score for a specific examiner.
    
    Calculates scores across ALL teams the examiner belongs to,
    compared against their single weekly target.
    
    - **user_id**: Examiner's user ID
    - **start_date**: Start of period
    - **end_date**: End of period
    
    Returns score breakdown and productivity percentage.
    """
    # Authorization: superadmin can view all, admin can view their org, team_lead their team, examiner only themselves
    if current_user.user_role == 'examiner' and current_user.id != user_id:  # type: ignore
        raise HTTPException(status_code=403, detail="Can only view your own productivity")
    
    service = ProductivityService(db)
    result = service.calculate_examiner_score(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/examiner/{user_id}/monthly")
async def get_examiner_monthly_productivity(
    user_id: int,
    year: int = Query(..., description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get monthly productivity for an examiner.
    Aggregates scores across all teams for the entire month.
    """
    if current_user.user_role == 'examiner' and current_user.id != user_id:  # type: ignore
        raise HTTPException(status_code=403, detail="Can only view your own productivity")
    
    service = ProductivityService(db)
    result = service.get_monthly_productivity(
        user_id=user_id,
        year=year,
        month=month
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/team/{team_id}")
async def get_team_productivity(
    team_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_higher)
):
    """
    Get productivity scores for all members of a team.
    
    Each employee's score includes their work across ALL teams,
    not just this team.
    
    - **team_id**: Team ID (to filter which examiners to show)
    - **start_date**: Start of period
    - **end_date**: End of period
    
    Returns team summary and individual examiner scores.
    """
    service = ProductivityService(db)
    result = service.calculate_team_productivity(
        team_id=team_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/leaderboard")
async def get_productivity_leaderboard(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    org_id: Optional[int] = Query(None, description="Filter by organization"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    limit: int = Query(10, ge=1, le=1000, description="Number of top performers"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_higher)
):
    """
    Get leaderboard of top performers by productivity score.
    """
    # For admin, default to their org
    if current_user.user_role == 'admin' and org_id is None:  # type: ignore
        org_id = current_user.org_id  # type: ignore
    
    service = ProductivityService(db)
    result = service.get_leaderboard(
        org_id=org_id,
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {"items": result, "total": len(result)}


@router.get("/admin-overview")
async def get_admin_productivity_overview(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    org_id: Optional[int] = Query(None, description="Filter by organization"),
    team_id: Optional[int] = Query(None, description="Filter by team"),
    team_limit: int = Query(10, ge=1, le=100, description="Maximum teams to summarize"),
    leaderboard_limit: int = Query(10, ge=1, le=100, description="Top performers count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_higher)
):
    """
    Optimized payload for admin productivity page.
    Returns leaderboard and summarized team productivity in one response.
    """
    # For admin, default to their org
    if current_user.user_role == 'admin' and org_id is None:  # type: ignore
        org_id = current_user.org_id  # type: ignore

    service = ProductivityService(db)
    return service.get_admin_overview(
        org_id=org_id,
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        team_limit=team_limit,
        leaderboard_limit=leaderboard_limit,
    )


@router.get("/my")
async def get_my_productivity(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get productivity score for the current logged-in user.
    
    Calculates scores across ALL teams the user belongs to,
    compared against their single weekly target.
    """
    service = ProductivityService(db)
    result = service.calculate_examiner_score(
        user_id=int(current_user.id),  # type: ignore
        start_date=start_date,
        end_date=end_date
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
