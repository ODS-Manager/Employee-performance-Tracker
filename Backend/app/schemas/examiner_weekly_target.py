"""
Examiner Weekly Target Schemas
Pydantic schemas for managing examiner weekly productivity targets.

Business Logic:
- Target is per examiner PER TEAM (each team lead sets target for their team)
- Examiner's total target = SUM of targets from all teams they belong to
- Productivity = Total Score / Sum of All Team Targets × 100

Example:
- Examiner X in Team A: target = 20 (set by Team A lead)
- Examiner X in Team B: target = 15 (set by Team B lead)
- Examiner X total target = 20 + 15 = 35
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ============ Examiner Weekly Target Schemas ============

class ExaminerWeeklyTargetBase(BaseModel):
    """Base schema for examiner weekly target"""
    user_id: int = Field(..., alias="userId")
    team_id: int = Field(..., alias="teamId")  # Team context for this target
    week_start_date: date = Field(..., alias="weekStartDate")
    week_end_date: date = Field(..., alias="weekEndDate")
    target: int = Field(..., ge=0, le=1000)  # Weekly target for this team

    class Config:
        populate_by_name = True


class ExaminerWeeklyTargetCreate(BaseModel):
    """Schema for creating a weekly target"""
    user_id: int = Field(..., alias="userId")
    team_id: int = Field(..., alias="teamId")  # Team context for this target
    week_start_date: date = Field(..., alias="weekStartDate")
    target: int = Field(..., ge=0, le=1000)

    class Config:
        populate_by_name = True


class ExaminerWeeklyTargetUpdate(BaseModel):
    """Schema for updating a weekly target"""
    target: int = Field(..., ge=0, le=1000)


class ExaminerWeeklyTargetResponse(BaseModel):
    """Response schema for weekly target"""
    id: int
    user_id: int = Field(..., alias="userId")
    team_id: int = Field(..., alias="teamId")  # Team context for this target
    week_start_date: date = Field(..., alias="weekStartDate")
    week_end_date: date = Field(..., alias="weekEndDate")
    target: int
    created_by: int = Field(..., alias="createdBy")
    created_at: datetime = Field(..., alias="createdAt")
    modified_at: datetime = Field(..., alias="modifiedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ExaminerWeeklyTargetWithUserResponse(ExaminerWeeklyTargetResponse):
    """Response schema with user details"""
    user_name: Optional[str] = Field(None, alias="userName")
    team_name: Optional[str] = Field(None, alias="teamName")  # Team name for display

    class Config:
        from_attributes = True
        populate_by_name = True


# ============ Bulk Operations Schemas ============

class WeeklyTargetBulkEntry(BaseModel):
    """Single entry for bulk target update"""
    user_id: int = Field(..., alias="userId")
    target: int = Field(..., ge=0, le=1000)

    class Config:
        populate_by_name = True


class WeeklyTargetBulkCreate(BaseModel):
    """Schema for setting multiple examiner targets at once"""
    week_start_date: date = Field(..., alias="weekStartDate")
    targets: List[WeeklyTargetBulkEntry]

    class Config:
        populate_by_name = True


# ============ Query/Response Schemas ============

class WeekInfo(BaseModel):
    """Information about a week"""
    week_start_date: date = Field(..., alias="weekStartDate")
    week_end_date: date = Field(..., alias="weekEndDate")
    is_current_week: bool = Field(..., alias="isCurrentWeek")
    is_past_week: bool = Field(..., alias="isPastWeek")
    can_edit: bool = Field(..., alias="canEdit")

    class Config:
        populate_by_name = True


class TeamMemberTargetEntry(BaseModel):
    """Target entry for a team member (target is per examiner per team)"""
    user_id: int = Field(..., alias="userId")
    user_name: str = Field(..., alias="userName")
    examiner_id: Optional[str] = Field(None, alias="examinerId")
    current_target: Optional[int] = Field(None, alias="currentTarget")  # Target for THIS team
    previous_target: Optional[int] = Field(None, alias="previousTarget")  # Previous week's target for THIS team
    target_id: Optional[int] = Field(None, alias="targetId")

    class Config:
        populate_by_name = True


class TeamWeeklyTargetsResponse(BaseModel):
    """Response containing all team member targets for a week"""
    team_id: int = Field(..., alias="teamId")
    team_name: str = Field(..., alias="teamName")
    week_info: WeekInfo = Field(..., alias="weekInfo")
    members: List[TeamMemberTargetEntry]

    class Config:
        populate_by_name = True


class ExaminerTargetHistoryResponse(BaseModel):
    """Historical targets for an examiner"""
    user_id: int = Field(..., alias="userId")
    targets: List[ExaminerWeeklyTargetResponse]

    class Config:
        populate_by_name = True
