from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, String, Numeric, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"))
    snapshot_date: Mapped[date] = mapped_column(Date)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    net_worth: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
