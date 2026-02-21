"""
Examiner Weekly Target Model
Stores weekly productivity targets set by team leads for each examiner per team.
Each team lead sets target for their team members within their team context.
Examiner's total target = sum of targets from all teams they belong to.
"""
from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ExaminerWeeklyTarget(Base):
    """
    Weekly productivity target for an examiner within a specific team.
    
    Business Logic:
    - Team lead sets target for examiner WITHIN their team context
    - Examiner can have different targets in different teams
    - Examiner's total weekly target = SUM of targets from all teams
    - Productivity = Total Score (all teams) / Total Target (sum from all teams) × 100
    
    Example:
    - Examiner X in Team A: target = 20 (set by Team A lead)
    - Examiner X in Team B: target = 15 (set by Team B lead)
    - Examiner X total target = 20 + 15 = 35
    """
    __tablename__ = "examiner_weekly_targets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)  # Team context for this target
    week_start_date = Column(Date, nullable=False)  # Sunday of the week
    week_end_date = Column(Date, nullable=False)    # Saturday of the week
    target = Column(Integer, nullable=False)         # Weekly target for this team
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Team lead who set the target
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="weekly_targets")
    team = relationship("Team", backref="examiner_targets")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    # Indexes - unique constraint on user + team + week (one target per examiner per team per week)
    __table_args__ = (
        Index('unique_user_team_week', 'user_id', 'team_id', 'week_start_date', unique=True),
        Index('idx_weekly_targets_user', 'user_id'),
        Index('idx_weekly_targets_team', 'team_id'),
        Index('idx_weekly_targets_week', 'week_start_date'),
    )
