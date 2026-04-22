from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Numeric, String, Date, DateTime, Boolean, Integer, ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped
from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    loan_type: Mapped[str] = mapped_column(String(20))  # 'consumer' | 'mortgage'
    lender: Mapped[str | None] = mapped_column(String(100), nullable=True)
    principal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4))
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    term_months: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    is_existing: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_extra: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active' | 'paid_off'
    paid_off_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, default=True)
    # Mortgage-only fields
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    equity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    property_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    fixed_rate_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    land_charge: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class LoanExtraPayment(Base):
    __tablename__ = "loan_extra_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), index=True)
    payment_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    effect: Mapped[str] = mapped_column(String(20))  # 'shorten_term' | 'reduce_payment'
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interval_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
