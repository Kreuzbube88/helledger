# 🏦 Loans

Under **Loans**, manage consumer loans and mortgages with full amortization schedules.

---

## Loan Types

| Type | Description |
|------|-------------|
| **Consumer Loan** | Standard installment loan |
| **Mortgage** | Home loan with purchase price, equity, and land charge |

---

## Creating a Loan

HELLEDGER automatically calculates the missing value when you fill in **3 of 4** fields:

- Loan amount
- Annual interest rate
- Monthly payment
- Term (months)

---

## Amortization Schedule

The **amortization** tab shows monthly details:

| Column | Description |
|--------|-------------|
| Month / Date | Booking date |
| Payment | Total monthly payment |
| Interest | Interest portion |
| Principal | Principal repayment |
| Extra | Extra payment amount |
| Balance | Remaining balance after booking |

The schedule can be exported as **CSV**.

---

## Extra Payments

Under the **Extra Payments** tab, add additional payments:

- **One-time** — on a specific date
- **Recurring** — with interval and optional end date

**Effects:**
- **Shorten term** — payment stays the same, term decreases
- **Reduce payment** — term stays the same, monthly payment decreases

---

## KPIs

| KPI | Description |
|-----|-------------|
| Total Interest | Total interest cost over the full term |
| Total Paid | Sum of all payments |
| Interest Saved | Savings from extra payments |
| Months Saved | Reduction in loan term |
| Current Balance | Today's remaining balance |
| Estimated Payoff | Projected payoff date |

---

## Automatic Fixed Cost Link

When a loan is created, a fixed cost category is automatically set up. The monthly payment is booked via fixed costs. When marked as "paid off", the category is archived.
