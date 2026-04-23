# 📅 Fixed Costs

Fixed costs are recurring bookings that HELLEDGER automatically creates as transactions every month.

---

## Types

| Type | Description |
|------|-------------|
| **Income** | Regular income (e.g. salary) |
| **Expense** | Recurring expense (e.g. rent, utilities, subscriptions) |
| **Savings Transfer** | Automatic transfer from one account to a savings account |

---

## Intervals

Fixed costs can be configured with different booking intervals:

| Interval | Booking |
|----------|---------|
| Monthly | Every month |
| Quarterly | Jan, Apr, Jul, Oct |
| Semi-annual | Jan, Jul |
| Annual | Once per year |

---

## Reserve Overview

For non-monthly fixed costs (e.g. annual insurance), HELLEDGER automatically calculates the **monthly reserve share**. The reserve overview shows how much should be set aside each month.

---

## Auto-Booking

HELLEDGER books fixed costs automatically when the dashboard loads for the current month. Already-booked months are never double-booked.

---

## Expiry Warning

Fixed costs with an **end date** display a warning in the dashboard when they expire within the next 30 days.

---

## Setting Up a Savings Transfer

1. Select type **Savings Transfer**
2. Choose **source account** (e.g. fixed costs account)
3. Choose **target account** (savings account)
4. Set amount and start date

The savings rate shown in the dashboard and month view is calculated automatically from all active savings transfers.
