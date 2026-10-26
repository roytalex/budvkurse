from datetime import datetime
from .common import InputModel, ReadModel


class AttendanceWrite(InputModel):
    attended: bool


class AttendanceRead(ReadModel):
    event_id: int
    user_id: int
    attended: bool
    confirmed_at: datetime | None


class AchievementRead(ReadModel):
    code: str
    title: str
    description: str
    metric: str
    target: int
    progress: int
    points: int
    earned: bool


class AchievementSummary(ReadModel):
    user_id: int
    name: str
    attendance_count: int
    olympiad_count: int
    points: int
    earned_count: int
    rank: int | None = None
    achievements: list[AchievementRead]


class LeaderboardEntry(ReadModel):
    user_id: int
    name: str
    attendance_count: int
    olympiad_count: int
    points: int
    earned_count: int
    rank: int
