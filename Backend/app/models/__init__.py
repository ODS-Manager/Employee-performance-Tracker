"""
Models Package
Export all SQLAlchemy models for easy importing
"""
# Reference tables
from app.models.reference import (
    TransactionType,
    ProcessType,
    OrderStatusType,
    Division
)

# Core entities
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.team import Team, TeamState, TeamProduct
from app.models.user_team import UserTeam
from app.models.order import Order
from app.models.order_history import OrderHistory

# Performance metrics
from app.models.metrics import (
    ExaminerPerformanceMetrics,
    TeamPerformanceMetrics
)

# Quality audits
from app.models.quality_audit import QualityAudit

# Password reset
from app.models.password_reset import PasswordResetToken

# Examiner weekly targets
from app.models.examiner_weekly_target import ExaminerWeeklyTarget

# Master FA names table
from app.models.fa_name import FAName

# Team FA names (pool-based)
from app.models.team_fa_name import TeamFAName

# Team user aliases
from app.models.team_user_alias import TeamUserAlias

# Attendance
from app.models.attendance import AttendanceRecord, AttendanceAuditLog

# Audit logs
from app.models.audit_log import AuditLog

# Billing
from app.models.billing import BillingReport, BillingDetail

# Allowed duplicate products
from app.models.allowed_duplicate_product import AllowedDuplicateProduct

__all__ = [
    # Reference tables
    "TransactionType",
    "ProcessType", 
    "OrderStatusType",
    "Division",
    # Core entities
    "Organization",
    "User",
    "UserRole",
    "Team",
    "TeamState",
    "TeamProduct",
    "UserTeam",
    "Order",
    "OrderHistory",
    # Performance metrics
    "ExaminerPerformanceMetrics",
    "TeamPerformanceMetrics",
    # Quality audits
    "QualityAudit",
    # Password reset
    "PasswordResetToken",
    # Examiner weekly targets
    "ExaminerWeeklyTarget",
    # Master FA names
    "FAName",
    # Team FA names
    "TeamFAName",
    # Team user aliases
    "TeamUserAlias",
    # Attendance
    "AttendanceRecord",
    "AttendanceAuditLog",
    # Audit logs
    "AuditLog",
    # Billing
    "BillingReport",
    "BillingDetail",
    # Allowed duplicate products
    "AllowedDuplicateProduct"
]
