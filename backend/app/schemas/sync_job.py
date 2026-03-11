from datetime import datetime

from pydantic import BaseModel


class SyncJobFilters(BaseModel):
    status: str | None = None
    category_id: str | None = None
    brand: str | None = None


class SyncJobCreate(BaseModel):
    channel: str
    filters: SyncJobFilters = SyncJobFilters()
    max_retries: int = 3
    cron_expression: str | None = None


class SyncJobRead(BaseModel):
    id: str
    channel: str
    status: str
    filters: dict = {}
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metrics: dict
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: datetime | None = None
    scheduled: bool = False
    cron_expression: str | None = None
    next_run_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SyncScheduleUpdate(BaseModel):
    cron_expression: str | None = None
    enabled: bool = True

