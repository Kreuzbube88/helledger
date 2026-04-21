from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class NetWorthCreate(BaseModel):
    snapshot_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    notes: str | None = None


class NetWorthOut(BaseModel):
    id: int
    household_id: int
    snapshot_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
