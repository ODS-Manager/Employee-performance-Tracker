"""
Attendance Schemas
Request/Response models for attendance API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


class AttendanceStatus(str, Enum):
    """Attendance status enum"""
    PRESENT = "present"
    HALF_DAY = "half_day"
    LEAVE = "leave"


class AttendanceRecordCreate(BaseModel):
    """Schema for creating single attendance record"""
    user_id: int = Field(alias="userId")
    team_id: int = Field(alias="teamId")
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class AttendanceBulkCreate(BaseModel):
    """Schema for bulk creating attendance records"""
    team_id: int = Field(alias="teamId")
    date: date
    status: AttendanceStatus
    examiner_ids: List[int] = Field(alias="examinerIds")
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        use_enum_values = True


class AttendanceRecordUpdate(BaseModel):
    """Schema for updating attendance record"""
    status: AttendanceStatus
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = True


class AttendanceRecordResponse(BaseModel):
    """Schema for attendance record response"""
    id: int
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    examiner_id: str = Field(alias="examinerId")
    team_id: int = Field(alias="teamId")
    date: date
    status: str
    marked_by: int = Field(alias="markedBy")
    marked_by_name: str = Field(alias="markedByName")
    marked_at: datetime = Field(alias="markedAt")
    modified_by: Optional[int] = Field(alias="modifiedBy", default=None)
    modified_by_name: Optional[str] = Field(alias="modifiedByName", default=None)
    modified_at: Optional[datetime] = Field(alias="modifiedAt", default=None)
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True


class DailyRosterExaminer(BaseModel):
    """Examiner info for daily roster"""
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    examiner_id: str = Field(alias="employeeId")
    user_role: str = Field(alias="userRole", default="examiner")
    status: Optional[str] = None  # None means not marked
    attendance_id: Optional[int] = Field(alias="attendanceId", default=None)
    notes: Optional[str] = None
    marked_by_name: Optional[str] = Field(alias="markedByName", default=None)
    marked_at: Optional[datetime] = Field(alias="markedAt", default=None)
    modified_by_name: Optional[str] = Field(alias="modifiedByName", default=None)
    modified_at: Optional[datetime] = Field(alias="modifiedAt", default=None)
    
    class Config:
        populate_by_name = True


class DailyRosterResponse(BaseModel):
    """Daily roster response with all team members"""
    team_id: int = Field(alias="teamId")
    team_name: str = Field(alias="teamName")
    date: date
    examiners: List[DailyRosterExaminer]
    summary: Dict[str, int]  # {"present": X, "half_day": Y, "leave": Z, "not_marked": W}
    
    class Config:
        populate_by_name = True


class AttendanceSummary(BaseModel):
    """Attendance summary for an examiner or team"""
    user_id: Optional[int] = Field(alias="userId", default=None)
    user_name: Optional[str] = Field(alias="userName", default=None)
    examiner_id: Optional[str] = Field(alias="examinerId", default=None)
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    working_days: int = Field(alias="workingDays")
    days_present: float = Field(alias="daysPresent")
    days_half_day: int = Field(alias="daysHalfDay", default=0)
    days_leave: int = Field(alias="daysLeave")
    attendance_percent: float = Field(alias="attendancePercent")
    records: List[AttendanceRecordResponse] = Field(alias="records", default=[])
    
    class Config:
        populate_by_name = True


class ExaminerAttendanceDetail(BaseModel):
    """Detailed attendance for single examiner"""
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    examiner_id: str = Field(alias="examinerId")
    summary: AttendanceSummary
    daily_records: List[AttendanceRecordResponse] = Field(alias="dailyRecords")
    
    class Config:
        populate_by_name = True


class TeamAttendanceReport(BaseModel):
    """Team attendance report"""
    team_id: int = Field(alias="teamId")
    team_name: str = Field(alias="teamName")
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    working_days: int = Field(alias="workingDays")
    examiners: List[AttendanceSummary]
    team_summary: Dict[str, float] = Field(alias="teamSummary")  # Weighted aggregate counts
    
    class Config:
        populate_by_name = True


class DailyAttendanceRecord(BaseModel):
    """Daily attendance record for an examiner"""
    date: date
    status: Optional[str] = None  # present, half_day, leave, or None (not marked)
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ExaminerMonthlyAttendance(BaseModel):
    """Monthly attendance for a single examiner"""
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    examiner_id: str = Field(alias="examinerId")
    user_role: str = Field(alias="userRole", default="examiner")
    total_days: int = Field(alias="totalDays")
    days_present: float = Field(alias="daysPresent")
    days_half_day: int = Field(alias="daysHalfDay", default=0)
    days_leave: int = Field(alias="daysLeave")
    days_not_marked: int = Field(alias="daysNotMarked")
    daily_records: List[DailyAttendanceRecord] = Field(alias="dailyRecords")

    class Config:
        populate_by_name = True


class TeamMonthlyAttendanceReport(BaseModel):
    """Team monthly attendance report with daily breakdown"""
    team_id: int = Field(alias="teamId")
    team_name: str = Field(alias="teamName")
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    examiners: List[ExaminerMonthlyAttendance]
    
    class Config:
        populate_by_name = True


class AttendanceAuditLogResponse(BaseModel):
    """Audit log response"""
    id: int
    attendance_record_id: Optional[int] = Field(alias="attendanceRecordId", default=None)
    user_id: int = Field(alias="userId")
    user_name: str = Field(alias="userName")
    team_id: int = Field(alias="teamId")
    team_name: str = Field(alias="teamName")
    date: date
    old_status: Optional[str] = Field(alias="oldStatus", default=None)
    new_status: str = Field(alias="newStatus")
    action: str
    changed_by: int = Field(alias="changedBy")
    changed_by_name: str = Field(alias="changedByName")
    changed_at: datetime = Field(alias="changedAt")
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True
