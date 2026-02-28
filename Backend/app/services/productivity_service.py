"""
Productivity Service
Business logic for calculating examiner productivity scores based on weekly targets.

Business Logic:
- Target is per examiner PER TEAM (each team lead sets target for their team members)
- Score is calculated across ALL teams the examiner belongs to
- Each team has its own score multipliers (step1_score, step2_score, single_seat_score)
- Examiner's total target = SUM of targets from all teams for that week
- Productivity = Total Score (all teams) / Total Target (sum from all teams) × 100

Attendance-Driven Target:
- Working week is Mon–Fri (5 days). Weekends are never counted.
- Daily target = weekly_target / 5
- Expected target = number of days the examiner was marked PRESENT (Mon–Fri) × daily_target
- Absent, leave, and unmarked days do NOT accumulate target
- This means if an examiner is absent on Tuesday, that day's target is simply dropped

Example:
- Weekly target = 10  →  daily target = 2
- Mon: present (2), Tue: absent (0), Wed: present (2)  →  expected target = 4
- Orders completed = 3  →  Productivity = 3/4 × 100 = 75%

Multi-team:
- Examiner X in Team A: target = 20 (set by Team A lead)
- Examiner X in Team B: target = 15 (set by Team B lead)
- Examiner X total weekly target = 35  →  daily target = 35 / 5 = 7
"""
# pyright: reportGeneralTypeIssues=false
# pyright: reportArgumentType=false
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from decimal import Decimal
from app.models.order import Order
from app.models.user import User
from app.models.team import Team
from app.models.user_team import UserTeam
from app.models.examiner_weekly_target import ExaminerWeeklyTarget
from app.services.attendance_service import AttendanceService


class ProductivityService:
    """
    Service for calculating examiner productivity scores
    
    Score System:
    - Step 1: Configurable per team (team.step1_score)
    - Step 2: Configurable per team (team.step2_score)
    - Single Seat: Configurable per team (team.single_seat_score)
    
    Productivity Formula:
    Productivity % = (Total Actual Score / Total Target) × 100
    - Score is summed across ALL teams
    - Target is sum of per-team targets (each team lead sets target for their team)
    
    Example:
    - Examiner X in Team A: target = 20, score = 18
    - Examiner X in Team B: target = 15, score = 12
    - Total target = 35, Total score = 30
    - Productivity = 30/35 × 100 = 85.7%
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_present_weekdays_in_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> int:
        """
        Count Mon–Fri days within [start_date, end_date] on which the examiner
        has an attendance record with status = 'present'.

        Weekends (Saturday=5, Sunday=6 in Python's weekday()) are always excluded.
        Absent, leave, and unmarked days are NOT counted.

        Returns:
            Integer count of present weekdays.
        """
        from app.models.attendance import AttendanceRecord

        records = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.user_id == user_id,
            AttendanceRecord.status == 'present',
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).all()

        count = 0
        for record in records:
            # weekday(): Mon=0 … Fri=4, Sat=5, Sun=6
            if record.date.weekday() <= 4:  # type: ignore[union-attr]
                count += 1

        return count

    def get_week_boundaries(self, reference_date: date) -> Tuple[date, date]:
        """
        Get the Sunday-Saturday week boundaries for a given date.
        Returns (week_start_date, week_end_date)
        """
        day_of_week = reference_date.weekday()
        
        # Calculate Sunday of this week
        if day_of_week == 6:  # Sunday
            week_start = reference_date
        else:
            days_since_sunday = day_of_week + 1
            week_start = reference_date - timedelta(days=days_since_sunday)
        
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    def get_weeks_in_range(self, start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """
        Get all weeks (Sunday-Saturday) that overlap with the given date range.
        Returns list of (week_start, week_end) tuples.
        """
        weeks = []
        current_week_start, current_week_end = self.get_week_boundaries(start_date)
        
        while current_week_start <= end_date:
            weeks.append((current_week_start, current_week_end))
            current_week_start = current_week_start + timedelta(days=7)
            current_week_end = current_week_start + timedelta(days=6)
        
        return weeks
    
    def get_weekly_target_for_range(
        self, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> Tuple[float, Optional[int], List[Dict]]:
        """
        Calculate total expected target for a date range using attendance-driven logic.

        Formula:
            daily_target       = weekly_target / 5   (Mon–Fri working week)
            expected_target    = present_weekdays × daily_target

        Where present_weekdays = days within the overlap of [week_start, week_end] and
        [start_date, end_date] on which the examiner was marked 'present' on a Mon–Fri.

        Absent, leave, unmarked, and weekend days contribute 0 to the expected target.
        For weeks without explicit targets, the last known target is carried forward per team.

        Target is per examiner PER TEAM — we sum targets from all teams.

        Returns:
            Tuple of (total_target, weekly_target_used, weekly_breakdown)
            - total_target: Sum of attendance-driven targets for all weeks and all teams
            - weekly_target_used: The total weekly target value (sum from all teams)
            - weekly_breakdown: List of week details with targets per team
        """
        weeks = self.get_weeks_in_range(start_date, end_date)
        total_target = 0.0
        weekly_breakdown = []
        
        # Get all targets for this user across all teams, ordered by week
        all_targets = self.db.query(ExaminerWeeklyTarget).filter(
            ExaminerWeeklyTarget.user_id == user_id
        ).order_by(ExaminerWeeklyTarget.week_start_date).all()
        
        # Create a map of (week_start, team_id) -> target
        target_map: Dict[Tuple[date, int], int] = {}
        for t in all_targets:
            week_date = t.week_start_date  # type: ignore
            team_id = int(t.team_id)  # type: ignore
            target_map[(week_date, team_id)] = int(t.target)  # type: ignore
        
        # Find the most recent target per team before start_date for carryforward
        last_known_per_team: Dict[int, int] = {}
        for t in all_targets:
            t_week_start = t.week_start_date  # type: ignore
            team_id = int(t.team_id)  # type: ignore
            if t_week_start < start_date:
                last_known_per_team[team_id] = int(t.target)  # type: ignore
        
        # Get all teams the user is a member of
        user_team_ids = [
            int(ut.team_id) for ut in self.db.query(UserTeam).filter(  # type: ignore
                UserTeam.user_id == user_id,
                UserTeam.is_active == True
            ).all()
        ]
        
        for week_start, week_end in weeks:
            week_total_target = 0
            team_targets_for_week = []
            
            for team_id in user_team_ids:
                # Check if we have a target for this week and team
                key = (week_start, team_id)
                if key in target_map:
                    last_known_per_team[team_id] = target_map[key]
                
                team_target = last_known_per_team.get(team_id)
                if team_target is not None:
                    team_targets_for_week.append({
                        "teamId": team_id,
                        "target": team_target
                    })
                    week_total_target += team_target
            
            if week_total_target > 0:
                # Clamp the week overlap to the requested date range
                overlap_start = max(week_start, start_date)
                overlap_end = min(week_end, end_date)

                # Count Mon–Fri days the examiner was present within this overlap
                present_weekdays = self.get_present_weekdays_in_range(
                    user_id=user_id,
                    start_date=overlap_start,
                    end_date=overlap_end
                )

                # daily_target = weekly_target / 5 working days
                daily_target = week_total_target / 5.0
                attendance_driven_target = present_weekdays * daily_target
                total_target += attendance_driven_target
                
                weekly_breakdown.append({
                    "weekStart": week_start.isoformat(),
                    "weekEnd": week_end.isoformat(),
                    "totalTarget": week_total_target,
                    "dailyTarget": round(daily_target, 2),
                    "teamTargets": team_targets_for_week,
                    "presentWeekdays": present_weekdays,
                    "attendanceDrivenTarget": round(attendance_driven_target, 2)
                })
            else:
                weekly_breakdown.append({
                    "weekStart": week_start.isoformat(),
                    "weekEnd": week_end.isoformat(),
                    "totalTarget": None,
                    "dailyTarget": 0,
                    "teamTargets": [],
                    "presentWeekdays": 0,
                    "attendanceDrivenTarget": 0
                })
        
        # The current week's total target for display (sum across all teams)
        current_week_total = sum(last_known_per_team.values()) if last_known_per_team else None
        
        return total_target, current_week_total, weekly_breakdown
    
    def get_working_days_in_month(self, year: int, month: int) -> int:
        """
        Calculate working days (Mon–Fri) in a given month.
        Weekends are excluded.
        """
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start = date(year, month, 1)
        end = date(year, month, last_day)
        return self.get_working_days_in_range(start, end)
    
    def get_working_days_in_range(self, start_date: date, end_date: date) -> int:
        """
        Calculate working days (Mon–Fri) between two dates, inclusive.
        Weekends (Saturday=5, Sunday=6) are excluded.
        """
        count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() <= 4:  # Mon=0 … Fri=4
                count += 1
            current += timedelta(days=1)
        return count
    
    def get_examiner_team_score(
        self,
        user_id: int,
        team_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calculate score for an examiner in a specific team (orders only from this team).
        Uses team-specific score multipliers.
        
        Returns:
            Dict with step counts and scores for this team
        """
        # Get team settings for score multipliers
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {
                "teamId": team_id,
                "teamName": "Unknown",
                "completions": {"step1Only": 0, "step2Only": 0, "singleSeat": 0, "total": 0},
                "scores": {"step1Score": 0, "step2Score": 0, "singleSeatScore": 0, "totalScore": 0},
                "scoreMultipliers": {"step1": 0.5, "step2": 0.5, "singleSeat": 1.0}
            }
        
        # Base query for orders in this team within the date range (based on entry_date)
        # Count work based on step assignments, regardless of order status.
        base_query = self.db.query(Order).filter(
            Order.team_id == team_id,
            Order.deleted_at == None,
            Order.entry_date >= start_date,
            Order.entry_date <= end_date
        )
        
        # Count Step 1 completions (user did step 1, but NOT step 2)
        step1_only_count = base_query.filter(
            Order.step1_user_id == user_id,
            or_(
                Order.step2_user_id != user_id,
                Order.step2_user_id == None
            )
        ).count()
        
        # Count Step 2 completions (user did step 2, but NOT step 1)
        step2_only_count = base_query.filter(
            Order.step2_user_id == user_id,
            or_(
                Order.step1_user_id != user_id,
                Order.step1_user_id == None
            )
        ).count()
        
        # Count Single Seat completions (user did BOTH steps)
        single_seat_count = base_query.filter(
            Order.step1_user_id == user_id,
            Order.step2_user_id == user_id
        ).count()
        
        # Calculate scores using team-specific scoring configuration
        step1_multiplier = float(team.step1_score) if team.step1_score else 0.5
        step2_multiplier = float(team.step2_score) if team.step2_score else 0.5
        single_seat_multiplier = float(team.single_seat_score) if team.single_seat_score else 1.0
        
        step1_score = step1_only_count * step1_multiplier
        step2_score = step2_only_count * step2_multiplier
        single_seat_score = single_seat_count * single_seat_multiplier
        
        total_score = step1_score + step2_score + single_seat_score
        
        return {
            "teamId": team_id,
            "teamName": team.name,
            "completions": {
                "step1Only": step1_only_count,
                "step2Only": step2_only_count,
                "singleSeat": single_seat_count,
                "total": step1_only_count + step2_only_count + single_seat_count
            },
            "scores": {
                "step1Score": step1_score,
                "step2Score": step2_score,
                "singleSeatScore": single_seat_score,
                "totalScore": total_score
            },
            "scoreMultipliers": {
                "step1": step1_multiplier,
                "step2": step2_multiplier,
                "singleSeat": single_seat_multiplier
            }
        }
    
    def calculate_examiner_score(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calculate productivity score for an examiner.
        
        This aggregates:
        - Scores from ALL teams the examiner is assigned to (using each team's multipliers)
        - Targets from ALL teams (sum of per-team targets set by respective team leads)
        
        Productivity = Total Score (all teams) / Total Target (sum from all teams) × 100
        
        Example:
        - Examiner X in Team A: target = 20, score = 18
        - Examiner X in Team B: target = 15, score = 12
        - Total target = 35, Total score = 30
        - Productivity = 30/35 × 100 = 85.7%
        
        NOTE: Only calculates for users with role 'examiner'
        
        Returns:
            Dict with step counts, scores, and productivity percentage
        """
        # Verify user is an examiner (not team_lead, admin, superadmin)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.user_role != 'examiner':  # type: ignore
            return {"error": "Productivity is only calculated for examiners"}
        
        # Adjust end_date to not exceed today's date
        today = date.today()
        actual_end_date = min(end_date, today)
        
        # Get ALL active teams the examiner is assigned to
        user_teams = self.db.query(UserTeam).filter(
            UserTeam.user_id == user_id,
            UserTeam.is_active == True
        ).all()
        
        user_team_ids = [int(ut.team_id) for ut in user_teams]  # type: ignore
        
        if not user_team_ids:
            return {
                "error": "Examiner is not assigned to any teams",
                "userId": user_id
            }
        
        # Calculate scores from ALL teams
        total_step1_count = 0
        total_step2_count = 0
        total_single_seat_count = 0
        total_step1_score = 0.0
        total_step2_score = 0.0
        total_single_seat_score = 0.0
        total_score = 0.0
        team_breakdown = []
        
        for tid in user_team_ids:
            team_score_data = self.get_examiner_team_score(
                user_id=user_id,
                team_id=tid,
                start_date=start_date,
                end_date=actual_end_date
            )
            
            total_step1_count += team_score_data["completions"]["step1Only"]
            total_step2_count += team_score_data["completions"]["step2Only"]
            total_single_seat_count += team_score_data["completions"]["singleSeat"]
            total_step1_score += team_score_data["scores"]["step1Score"]
            total_step2_score += team_score_data["scores"]["step2Score"]
            total_single_seat_score += team_score_data["scores"]["singleSeatScore"]
            total_score += team_score_data["scores"]["totalScore"]
            
            # Only include in breakdown if there's activity
            if team_score_data["completions"]["total"] > 0:
                team_breakdown.append(team_score_data)
        
        # Calculate working days (up to today, not future dates)
        working_days = self.get_working_days_in_range(start_date, actual_end_date)
        
        # Get expected target from weekly targets.
        # attendance_driven_target = present weekdays × (weekly_target / 5)
        # weekly_target_used      = the full weekly target (sum from all teams, for display)
        attendance_driven_target, weekly_target_used, weekly_breakdown = self.get_weekly_target_for_range(
            user_id=user_id,
            start_date=start_date,
            end_date=actual_end_date
        )
        
        has_weekly_target = weekly_target_used is not None
        
        # expected_target for display = attendance-driven total (present days × daily_target)
        expected_target = attendance_driven_target
        
        # Calculate attendance using manual attendance records
        # Use AttendanceService to get attendance summary
        attendance_service = AttendanceService(self.db)
        attendance_summary = attendance_service.get_examiner_attendance_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=actual_end_date
        )
        
        days_present = attendance_summary.days_present
        days_absent = attendance_summary.days_absent
        days_leave = attendance_summary.days_leave
        attendance_percentage = attendance_summary.attendance_percent
        
        # Calculate productivity percentage:
        # Productivity % = total_score / (present_weekdays × daily_target) × 100
        # If no target is configured, productivity is None (not 0)
        productivity_percent = None
        if expected_target > 0:
            productivity_percent = round((total_score / expected_target) * 100, 2)
        
        return {
            "userId": user_id,
            "userName": user.user_name,
            "examinerId": user.examiner_id,
            "teamsIncluded": user_team_ids,
            # weeklyTarget: full weekly target (sum across all teams) — for reference
            "weeklyTarget": weekly_target_used,
            # dailyTarget: weekly_target / 5 working days
            "dailyTarget": round(weekly_target_used / 5.0, 2) if weekly_target_used else None,
            # expectedTarget: attendance-driven = present weekdays × daily_target
            "expectedTarget": round(expected_target, 2),
            "period": {
                "startDate": start_date.isoformat(),
                "endDate": actual_end_date.isoformat(),
                "requestedEndDate": end_date.isoformat(),
                "workingDays": working_days
            },
            "attendance": {
                "daysPresent": days_present,
                "daysAbsent": days_absent,
                "daysLeave": days_leave,
                "attendancePercent": round(attendance_percentage, 2)
            },
            "completions": {
                "step1Only": total_step1_count,
                "step2Only": total_step2_count,
                "singleSeat": total_single_seat_count,
                "total": total_step1_count + total_step2_count + total_single_seat_count
            },
            "scores": {
                "step1Score": total_step1_score,
                "step2Score": total_step2_score,
                "singleSeatScore": total_single_seat_score,
                "totalScore": total_score
            },
            "teamBreakdown": team_breakdown,
            "productivityPercent": productivity_percent,
            "weeklyBreakdown": weekly_breakdown,
            "hasWeeklyTarget": has_weekly_target
        }
    
    def calculate_team_productivity(
        self,
        team_id: int,
        start_date: date,
        end_date: date,
        include_examiners: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate productivity for all active members of a team.
        Shows each examiner's score ONLY for this team (not aggregated across all teams).
        
        Returns:
            Dict with team info and list of examiner productivity scores for this team
        """
        # Get team
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"error": "Team not found"}
        
        # Adjust end_date to not exceed today's date
        today = date.today()
        actual_end_date = min(end_date, today)
        
        # Get active team members - ONLY examiners (not team_lead, admin, superadmin)
        team_members = self.db.query(
            User.id,
            User.user_name,
            User.examiner_id,
        ).join(
            UserTeam, User.id == UserTeam.user_id
        ).filter(
            UserTeam.team_id == team_id,
            UserTeam.is_active == True,
            User.user_role == 'examiner'
        ).all()

        member_user_ids = [int(member.id) for member in team_members]  # type: ignore

        # Fast path: no active examiners in the team
        if not member_user_ids:
            step1_multiplier = float(team.step1_score) if team.step1_score else 0.5
            step2_multiplier = float(team.step2_score) if team.step2_score else 0.5
            single_seat_multiplier = float(team.single_seat_score) if team.single_seat_score else 1.0

            return {
                "teamId": team_id,
                "teamName": team.name,
                "monthlyTarget": team.monthly_target,
                "dailyTarget": team.daily_target,
                "step2ScoreMultiplier": step2_multiplier,
                "scoreMultipliers": {
                    "step1": step1_multiplier,
                    "step2": step2_multiplier,
                    "singleSeat": single_seat_multiplier
                },
                "period": {
                    "startDate": start_date.isoformat(),
                    "endDate": actual_end_date.isoformat(),
                    "requestedEndDate": end_date.isoformat(),
                    "workingDays": self.get_working_days_in_range(start_date, actual_end_date)
                },
                "activeMembers": 0,
                "totalTeamScore": 0.0,
                "totalExpectedTarget": float(team.monthly_target) if team.monthly_target else 0.0,
                "examinerTargetSum": 0.0,
                "teamProductivityPercent": 0.0,
                "examiners": []
            }

        base_order_filters = [
            Order.team_id == team_id,
            Order.deleted_at == None,
            Order.entry_date >= start_date,
            Order.entry_date <= actual_end_date,
        ]

        # Aggregate completion counts for all members in this team in bulk
        step1_rows = self.db.query(
            Order.step1_user_id,
            func.count(Order.id)
        ).filter(
            *base_order_filters,
            Order.step1_user_id.in_(member_user_ids),
            or_(
                Order.step2_user_id != Order.step1_user_id,
                Order.step2_user_id == None,
            )
        ).group_by(
            Order.step1_user_id
        ).all()

        step2_rows = self.db.query(
            Order.step2_user_id,
            func.count(Order.id)
        ).filter(
            *base_order_filters,
            Order.step2_user_id.in_(member_user_ids),
            or_(
                Order.step1_user_id != Order.step2_user_id,
                Order.step1_user_id == None,
            )
        ).group_by(
            Order.step2_user_id
        ).all()

        single_seat_rows = self.db.query(
            Order.step1_user_id,
            func.count(Order.id)
        ).filter(
            *base_order_filters,
            Order.step1_user_id.in_(member_user_ids),
            Order.step1_user_id == Order.step2_user_id,
        ).group_by(
            Order.step1_user_id
        ).all()

        step1_count_map = {int(user_id): int(count) for user_id, count in step1_rows if user_id is not None}
        step2_count_map = {int(user_id): int(count) for user_id, count in step2_rows if user_id is not None}
        single_seat_count_map = {int(user_id): int(count) for user_id, count in single_seat_rows if user_id is not None}

        # Bulk fetch latest known target per examiner for this team (carry-forward up to end_date)
        target_rows = self.db.query(
            ExaminerWeeklyTarget.user_id,
            ExaminerWeeklyTarget.target,
            ExaminerWeeklyTarget.week_start_date,
        ).filter(
            ExaminerWeeklyTarget.team_id == team_id,
            ExaminerWeeklyTarget.user_id.in_(member_user_ids),
            ExaminerWeeklyTarget.week_start_date <= actual_end_date,
        ).order_by(
            ExaminerWeeklyTarget.user_id,
            ExaminerWeeklyTarget.week_start_date,
        ).all()

        latest_target_by_user: Dict[int, float] = {}
        for user_id, target, _week_start_date in target_rows:
            if user_id is None:
                continue
            latest_target_by_user[int(user_id)] = float(target)

        examiner_scores = []
        total_team_score = 0.0
        total_expected = 0.0

        step1_multiplier = float(team.step1_score) if team.step1_score else 0.5
        step2_multiplier = float(team.step2_score) if team.step2_score else 0.5
        single_seat_multiplier = float(team.single_seat_score) if team.single_seat_score else 1.0
        
        for membership in team_members:
            uid = int(membership.id)  # type: ignore
            step1_only_count = step1_count_map.get(uid, 0)
            step2_only_count = step2_count_map.get(uid, 0)
            single_seat_count = single_seat_count_map.get(uid, 0)

            step1_score = step1_only_count * step1_multiplier
            step2_score = step2_only_count * step2_multiplier
            single_seat_score = single_seat_count * single_seat_multiplier
            team_score = step1_score + step2_score + single_seat_score

            # Weekly target for this examiner on this team (latest known, carry-forward)
            weekly_target_for_team = latest_target_by_user.get(uid, 0.0)

            # Attendance-driven expected target:
            # daily_target = weekly_target / 5 working days (Mon–Fri)
            # expected     = present weekdays × daily_target
            if weekly_target_for_team > 0:
                present_weekdays = self.get_present_weekdays_in_range(
                    user_id=uid,
                    start_date=start_date,
                    end_date=actual_end_date
                )
                daily_target = weekly_target_for_team / 5.0
                examiner_expected = present_weekdays * daily_target
            else:
                examiner_expected = 0.0

            # Calculate productivity % for this examiner in this team
            examiner_productivity = None
            if examiner_expected > 0:
                examiner_productivity = round((team_score / examiner_expected) * 100, 2)
            
            if include_examiners:
                examiner_data = {
                    "userId": uid,
                    "userName": membership.user_name,
                    "examinerId": membership.examiner_id,
                    "completions": {
                        "step1Only": step1_only_count,
                        "step2Only": step2_only_count,
                        "singleSeat": single_seat_count,
                        "total": step1_only_count + step2_only_count + single_seat_count,
                    },
                    "scores": {
                        "step1Score": step1_score,
                        "step2Score": step2_score,
                        "singleSeatScore": single_seat_score,
                        "totalScore": team_score,
                    },
                    # weeklyTarget: full weekly target for reference
                    "weeklyTarget": weekly_target_for_team if weekly_target_for_team > 0 else None,
                    # expectedTarget: attendance-driven (present weekdays × daily_target)
                    "expectedTarget": round(examiner_expected, 2),
                    "productivityPercent": examiner_productivity,
                    "teamId": team_id,
                    "teamName": team.name
                }

                examiner_scores.append(examiner_data)

            total_team_score += team_score
            total_expected += examiner_expected
        
        # Determine team target: use monthly_target if set, otherwise sum of examiner targets
        team_target: float = float(team.monthly_target) if team.monthly_target else total_expected
        
        # Calculate team productivity percentage using team target
        team_productivity = 0.0
        if team_target > 0:
            team_productivity = (total_team_score / team_target) * 100
        
        return {
            "teamId": team_id,
            "teamName": team.name,
            "monthlyTarget": team.monthly_target,
            "dailyTarget": team.daily_target,
            "step2ScoreMultiplier": step2_multiplier,
            "scoreMultipliers": {
                "step1": step1_multiplier,
                "step2": step2_multiplier,
                "singleSeat": single_seat_multiplier
            },
            "period": {
                "startDate": start_date.isoformat(),
                "endDate": actual_end_date.isoformat(),
                "requestedEndDate": end_date.isoformat(),
                "workingDays": self.get_working_days_in_range(start_date, actual_end_date)
            },
            "activeMembers": len(member_user_ids),
            "totalTeamScore": total_team_score,
            "totalExpectedTarget": team_target,  # Use team target (monthly_target or sum of examiner targets)
            "examinerTargetSum": total_expected,  # Keep track of sum of examiner targets separately
            "teamProductivityPercent": round(float(team_productivity), 2),
            "examiners": examiner_scores if include_examiners else []
        }

    def get_admin_overview(
        self,
        org_id: Optional[int],
        team_id: Optional[int],
        start_date: date,
        end_date: date,
        team_limit: int = 10,
        leaderboard_limit: int = 10,
    ) -> Dict[str, Any]:
        """Get combined leaderboard + team summaries for admin productivity page."""
        teams_query = self.db.query(Team).filter(Team.is_active == True)

        if org_id:
            teams_query = teams_query.filter(Team.org_id == org_id)
        if team_id:
            teams_query = teams_query.filter(Team.id == team_id)

        total_teams = teams_query.count()
        teams = teams_query.order_by(Team.name).limit(team_limit).all()

        leaderboard = self.get_leaderboard(
            org_id=org_id,
            team_id=team_id,
            start_date=start_date,
            end_date=end_date,
            limit=leaderboard_limit,
        )

        team_summaries = []
        for team in teams:
            team_data = self.calculate_team_productivity(
                team_id=int(team.id),  # type: ignore
                start_date=start_date,
                end_date=end_date,
                include_examiners=False,
            )
            if "error" not in team_data:
                team_summaries.append(team_data)

        return {
            "leaderboard": leaderboard,
            "teams": team_summaries,
            "totalTeams": total_teams,
        }
    
    def _get_examiner_target_for_team(
        self,
        user_id: int,
        team_id: int,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Get examiner's weekly target for a specific team.
        Uses latest known target up to end_date (carry-forward behavior).
        """
        # Get all targets for this user and team, ordered by week
        all_targets = self.db.query(ExaminerWeeklyTarget).filter(
            ExaminerWeeklyTarget.user_id == user_id,
            ExaminerWeeklyTarget.team_id == team_id
        ).order_by(ExaminerWeeklyTarget.week_start_date).all()

        # Find latest known target up to end_date for carryforward
        last_known_target: Optional[int] = None
        for t in all_targets:
            if t.week_start_date <= end_date:  # type: ignore
                last_known_target = int(t.target)  # type: ignore

        if last_known_target is None:
            return 0.0

        return float(last_known_target)
    
    def get_monthly_productivity(
        self,
        user_id: int,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Get productivity for a specific month
        """
        import calendar
        
        # Get first and last day of the month
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        result = self.calculate_examiner_score(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        result["month"] = month
        result["year"] = year
        
        return result
    
    def get_leaderboard(
        self,
        org_id: Optional[int],
        team_id: Optional[int],
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top performers by productivity score
        
        Args:
            org_id: Filter by organization (optional)
            team_id: Filter by team (optional)
            start_date: Start of period
            end_date: End of period
            limit: Number of top performers to return
            
        Returns:
            List of examiner productivity scores sorted by total score descending
        """
        # Get teams to query
        teams_query = self.db.query(Team).filter(Team.is_active == True)
        
        if org_id:
            teams_query = teams_query.filter(Team.org_id == org_id)
        if team_id:
            teams_query = teams_query.filter(Team.id == team_id)
        
        teams = teams_query.all()
        
        all_scores = []
        seen_user_ids = set()  # Avoid duplicates if user is in multiple teams
        
        for team in teams:
            team_data = self.calculate_team_productivity(
                team_id=int(team.id),  # type: ignore
                start_date=start_date,
                end_date=end_date
            )
            
            if "examiners" in team_data:
                for examiner in team_data["examiners"]:
                    if examiner["userId"] not in seen_user_ids:
                        all_scores.append(examiner)
                        seen_user_ids.add(examiner["userId"])
        
        # Sort by total score descending
        all_scores.sort(key=lambda x: x["scores"]["totalScore"], reverse=True)
        
        return all_scores[:limit]
