import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class NewDocument(StrictModel):
    title: str = Field(min_length=1, max_length=250)
    kind: Literal['lesson', 'plan', 'personal_report']
    period_id: str = Field(min_length=1, max_length=80)
    content: dict

    @field_validator('content')
    @classmethod
    def size_limit(cls, value):
        if len(json.dumps(value)) > 250000 or value.get('type') != 'doc':
            raise ValueError('Nội dung cần là doc, tối đa 250 KB JSON.')
        return value


class SaveDocument(NewDocument):
    # kind/period are excluded from save by the route, ensuring immutable assignment.
    expected_revision: int = Field(ge=1)


class Revision(StrictModel):
    expected_revision: int = Field(ge=1)


class Decision(Revision):
    decision: Literal['approve', 'request_changes']
    reason: str = Field(min_length=1, max_length=2000)


class Override(Revision):
    user_id: str = Field(min_length=1, max_length=80)
    allowed_until: datetime
    reason: str = Field(min_length=1, max_length=1000)

    @field_validator('allowed_until')
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError('Cần thời gian có múi giờ.')
        return value


class TeacherReport(StrictModel):
    assigned: int | None = Field(default=None, ge=0, le=10000)
    completed: int | None = Field(default=None, ge=0, le=10000)
    activity_codes: list[Literal['A1', 'A2', 'A3']] = Field(default_factory=list, max_length=3)
    achievements: str = Field(default='', max_length=4000)
    difficulties: str = Field(default='', max_length=4000)
    proposals: str = Field(default='', max_length=4000)

    @model_validator(mode='after')
    def consistent(self):
        if (self.assigned is None) != (self.completed is None):
            raise ValueError('Điền cả hai số hoặc để cả hai không áp dụng.')
        if self.assigned is not None and self.completed > self.assigned:
            raise ValueError('Số hoàn thành không vượt số được giao.')
        if len(set(self.activity_codes)) != len(self.activity_codes):
            raise ValueError('Mã hoạt động không được lặp.')
        return self


class DraftRequest(StrictModel):
    kind: Literal['lesson', 'plan', 'personal_report']
    instructions: str = Field(min_length=10, max_length=6000)
    source_ids: list[str] = Field(default_factory=list, max_length=8)
