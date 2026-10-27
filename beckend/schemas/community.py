from datetime import datetime
from typing import Literal
from pydantic import Field
from .common import InputModel, ReadModel, Page, Pagination
from .achievements import AchievementSummary, AttendanceRead


class TeamWrite(InputModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=10, max_length=2000)
    looking_for: str = Field(min_length=2, max_length=200)
    capacity: int = Field(default=4, ge=2, le=12)
    status: Literal["open", "closed"] = "open"


class TeamJoin(InputModel):
    skills: str = Field(min_length=2, max_length=300)


class TeamDecision(InputModel):
    accept: bool


class MemberRead(ReadModel):
    user_id: int
    name: str
    status: str
    skills: str


class TeamRead(ReadModel):
    id: int
    event_id: int
    event_title: str
    starts_at: datetime
    captain_id: int
    name: str
    description: str
    looking_for: str
    capacity: int
    status: str
    member_count: int
    my_status: str | None
    members: list[MemberRead]
    requests: list[MemberRead]


class ReviewWrite(InputModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=5, max_length=2000)


class ReviewRead(ReadModel):
    id: int
    user_id: int
    name: str
    rating: int
    text: str
    created_at: datetime
    updated_at: datetime


class ReviewsRead(Page[ReviewRead]):
    average: float | None
    mine: ReviewRead | None
    can_review: bool


class VisitRead(ReadModel):
    event_id: int
    title: str
    category: str
    ends_at: datetime
    confirmed_at: datetime


class PassportRead(ReadModel):
    summary: AchievementSummary
    interests: list[str]
    visits: Page[VisitRead]


class ChallengeRead(ReadModel):
    code: str
    title: str
    description: str
    progress: int
    target: int
    earned: bool


class ChallengesRead(ReadModel):
    month: str
    timezone: str
    challenges: list[ChallengeRead]
    history: list[str]


class SchoolScore(ReadModel):
    school_id: int
    name: str
    city: str
    students: int
    active_students: int
    points: int
    average: float
    attendance_count: int
    rank: int


class SchoolFilters(Pagination):
    order: Literal["points", "average"] = "points"


class TeamFilters(Pagination):
    search: str | None = Field(default=None, max_length=100)


class TicketRead(ReadModel):
    token: str
    image: str
    expires_at: datetime
    event_title: str
    name: str


class ScanWrite(InputModel):
    token: str = Field(min_length=20, max_length=2000)


class ScanRead(AttendanceRead):
    name: str
