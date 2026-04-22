import calendar
import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def calc_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """P, r, n → PMT"""
    if annual_rate == 0:
        return principal / term_months
    r = annual_rate / 100 / 12
    return principal * r * (1 + r) ** term_months / ((1 + r) ** term_months - 1)


def calc_term(principal: float, annual_rate: float, monthly_payment: float) -> int:
    """P, r, PMT → n"""
    if annual_rate == 0:
        return math.ceil(principal / monthly_payment)
    r = annual_rate / 100 / 12
    if monthly_payment <= principal * r:
        raise ValueError("payment_too_low")
    n = -math.log(1 - float(principal) * r / monthly_payment) / math.log(1 + r)
    return math.ceil(n)


def calc_principal(monthly_payment: float, annual_rate: float, term_months: int) -> float:
    """PMT, r, n → P"""
    if annual_rate == 0:
        return monthly_payment * term_months
    r = annual_rate / 100 / 12
    return monthly_payment * ((1 + r) ** term_months - 1) / (r * (1 + r) ** term_months)


def calc_rate_newton(principal: float, monthly_payment: float, term_months: int) -> float:
    """P, PMT, n → annual_rate% via Newton-Raphson"""
    P, PMT, n = float(principal), float(monthly_payment), term_months
    r = PMT / P  # initial guess
    for _ in range(200):
        h = r * 1e-6 if r > 0 else 1e-9
        f = PMT * ((1 + r) ** n - 1) / (r * (1 + r) ** n) - P
        f2 = PMT * ((1 + r + h) ** n - 1) / ((r + h) * (1 + r + h) ** n) - P
        df = (f2 - f) / h
        if abs(df) < 1e-14:
            break
        r_new = r - f / df
        if r_new <= 0:
            r_new = 1e-8
        if abs(r_new - r) < 1e-10:
            r = r_new
            break
        r = r_new
    return round(r * 12 * 100, 6)


def _add_months(d: date, months: int) -> date:
    total_months = d.month - 1 + months
    year = d.year + total_months // 12
    month = total_months % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calc_amortization(
    principal: float,
    annual_rate: float,
    monthly_payment: float,
    term_months: int,
    start_date: date,
    extra_payments: list[dict],
    monthly_extra: float = 0,
) -> list[dict]:
    """
    Calculates full amortization schedule with Sondertilgungen.
    extra_payments: list of {payment_date: date, amount: float, effect: str}
    Returns list of row dicts.
    """
    TWO = Decimal("0.01")
    r = Decimal(str(annual_rate)) / 100 / 12
    balance = Decimal(str(principal))
    base_payment = Decimal(str(monthly_payment))
    m_extra = Decimal(str(monthly_extra))
    current_payment = base_payment + m_extra
    remaining_months = term_months

    sorted_eps = sorted(extra_payments, key=lambda x: x["payment_date"])
    ep_iter = iter(sorted_eps)
    next_ep = next(ep_iter, None)

    rows = []

    for month_num in range(1, term_months + 361):  # safety cap
        if balance <= Decimal("0.005"):
            break

        payment_date = _add_months(start_date, month_num - 1)
        month_extra = Decimal("0")

        # Apply any Sondertilgungen due this month or earlier
        while next_ep and next_ep["payment_date"] <= payment_date:
            amt = Decimal(str(next_ep["amount"]))
            month_extra += amt
            new_bal = balance - month_extra
            if new_bal <= Decimal("0.005"):
                balance = Decimal("0")
                break
            if next_ep["effect"] == "shorten_term" and r > 0:
                remaining_months = math.ceil(
                    -math.log(1 - float(new_bal * r / current_payment))
                    / math.log(1 + float(r))
                )
            elif next_ep["effect"] == "reduce_payment":
                if r > 0 and remaining_months > 0:
                    rp = float(r)
                    current_payment = new_bal * Decimal(str(
                        rp * (1 + rp) ** remaining_months / ((1 + rp) ** remaining_months - 1)
                    ))
                    current_payment = current_payment.quantize(TWO, rounding=ROUND_HALF_UP)
                elif remaining_months > 0:
                    current_payment = new_bal / remaining_months
            next_ep = next(ep_iter, None)

        balance = max(Decimal("0"), balance - month_extra)
        if balance <= Decimal("0.005"):
            break

        interest = (balance * r).quantize(TWO, rounding=ROUND_HALF_UP)
        principal_part = current_payment - interest

        if principal_part <= 0:
            break  # payment doesn't cover interest

        if principal_part >= balance:
            principal_part = balance
            actual_payment = principal_part + interest
        else:
            actual_payment = current_payment

        balance = max(Decimal("0"), balance - principal_part)
        remaining_months = max(0, remaining_months - 1)

        rows.append({
            "month": month_num,
            "date": payment_date.isoformat(),
            "payment": float(actual_payment.quantize(TWO)),
            "interest": float(interest),
            "principal": float(principal_part.quantize(TWO)),
            "extra": float(month_extra.quantize(TWO)),
            "balance": float(balance.quantize(TWO)),
        })

        if balance <= Decimal("0.005"):
            break

    return rows


def calc_stats(
    principal: float,
    annual_rate: float,
    monthly_payment: float,
    term_months: int,
    start_date: date,
    extra_payments: list[dict],
    monthly_extra: float = 0,
) -> dict:
    rows = calc_amortization(
        principal, annual_rate, monthly_payment, term_months,
        start_date, extra_payments, monthly_extra,
    )
    rows_baseline = calc_amortization(
        principal, annual_rate, monthly_payment, term_months,
        start_date, [], 0,
    )

    total_interest = sum(r["interest"] for r in rows)
    total_paid = sum(r["payment"] + r["extra"] for r in rows)
    baseline_interest = sum(r["interest"] for r in rows_baseline)
    interest_saved = baseline_interest - total_interest
    months_saved = len(rows_baseline) - len(rows)
    payoff_date = rows[-1]["date"] if rows else None

    today = date.today()
    current_balance = 0.0
    for row in rows:
        if date.fromisoformat(row["date"]) >= today:
            current_balance = row["balance"]
            break

    return {
        "total_interest": round(total_interest, 2),
        "total_paid": round(total_paid, 2),
        "interest_saved": round(interest_saved, 2),
        "months_saved": months_saved,
        "payoff_date": payoff_date,
        "current_balance": round(current_balance, 2),
        "total_months": len(rows),
    }
