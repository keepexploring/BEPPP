# Accounting System - Quick Start Guide

## What Changed?

Your battery rental system now has **professional-grade accounting** built in while keeping the simple interface you're used to!

## For Daily Operations (Nothing Changes!)

Everything works exactly as before:
- ✅ Create rentals
- ✅ Collect payments
- ✅ Add credit to accounts
- ✅ Process refunds

**The difference**: Behind the scenes, proper accounting entries are automatically created.

## New Capabilities

### 1. Check Account Balance

```bash
GET /accounts/{account_id}/summary
```

**What you get:**
- Current balance
- Total credits (money in)
- Total debits (money out)
- Total spent
- Amount owed
- Available credit

### 2. Verify Account is Correct

```bash
POST /accounts/{account_id}/reconcile
```

**What it does:**
- Calculates what the balance SHOULD be from all transactions
- Compares with actual balance
- Tells you if there's a discrepancy

**When to use**: Monthly, or if an account balance looks wrong

### 3. Financial Reports

```bash
GET /accounts/financial-report
```

**What you get:**
- All assets (cash, receivables)
- All liabilities (credits owed, deposits)
- Total revenue
- Total expenses
- Net income (profit)

**When to use**: Monthly/quarterly/yearly reporting

## Transaction Types - Now More Specific!

### Old Way (Still Works)
```
payment, credit, charge, refund
```

### New Way (Better Detail)
```
rental_charge       - Customer rented a battery
payment_received    - Customer paid their bill
deposit_collected   - Collected security deposit
deposit_refunded    - Returned security deposit
credit_added        - Added credit to account
late_fee           - Charged late fee
subscription_fee    - Monthly subscription
refund_issued      - Issued refund
```

## Example Workflows

### Scenario 1: Customer Rents Battery

**What happens:**
```
User sees: "Rental charge $50"
System creates:
  - AccountTransaction: rental_charge, $50
  - LedgerEntry 1: Debit Accounts Receivable $50
  - LedgerEntry 2: Credit Rental Revenue $50
```

### Scenario 2: Customer Pays

**What happens:**
```
User sees: "Payment received $50"
System creates:
  - AccountTransaction: payment_received, $50
  - LedgerEntry 1: Debit Cash $50
  - LedgerEntry 2: Credit Accounts Receivable $50
```

### Scenario 3: Monthly Financial Report

**Request:**
```bash
GET /accounts/financial-report?start_date=2024-01-01&end_date=2024-01-31
```

**Response:**
```json
{
  "assets": {
    "cash": 10000,
    "accounts_receivable": 5000
  },
  "liabilities": {
    "customer_credit_balance": 2000,
    "deposits_payable": 1000
  },
  "revenue": {
    "rental_revenue": 15000,
    "late_fee_revenue": 500
  },
  "expenses": {
    "refunds_expense": 200
  },
  "totals": {
    "total_revenue": 15500,
    "total_expenses": 200,
    "net_income": 15300,
    "is_balanced": true
  }
}
```

## Troubleshooting

### "Account balance looks wrong"

1. Run reconciliation:
   ```bash
   POST /accounts/{account_id}/reconcile
   ```

2. Check the response:
   ```json
   {
     "expected_balance": 100.00,
     "actual_balance": 95.00,
     "difference": -5.00,
     "is_balanced": false
   }
   ```

3. If there's a difference, check:
   - Recent transactions
   - Database for manual changes
   - Contact admin if needed

### "Need to see all transactions for an account"

```bash
GET /accounts/user/{user_id}/transactions
```

### "Need financial data for specific period"

```bash
GET /accounts/financial-report?start_date=2024-01-01&end_date=2024-12-31
```

## Best Practices

### Daily
- ✅ Record all transactions as they happen
- ✅ Use specific transaction types
- ✅ Add descriptions to transactions

### Weekly
- ✅ Check reconciliation for high-value accounts
- ✅ Review accounts receivable

### Monthly
- ✅ Run full reconciliation on all accounts
- ✅ Generate financial report
- ✅ Review revenue and expenses

### Quarterly/Yearly
- ✅ Full financial audit
- ✅ Export reports for accounting
- ✅ Review net income trends

## Accounting Basics (Simplified)

### Assets = What You Own
- Cash (money in bank)
- Accounts Receivable (customers owe you)

### Liabilities = What You Owe
- Customer Credit Balance (prepaid by customers)
- Deposits Payable (must return to customers)

### Revenue = Income
- Rental fees
- Late fees
- Subscriptions

### Expenses = Costs
- Refunds
- Operating costs

### Net Income = Profit
```
Net Income = Revenue - Expenses
```

## Quick Reference

| I Want To... | Endpoint | Method |
|--------------|----------|--------|
| See account summary | `/accounts/{id}/summary` | GET |
| Check if account is correct | `/accounts/{id}/reconcile` | POST |
| Get financial report | `/accounts/financial-report` | GET |
| See all transactions | `/accounts/user/{id}/transactions` | GET |
| Record a transaction | `/accounts/user/{id}/transaction` | POST |

## Need Help?

1. Read the full documentation: `docs/ACCOUNTING_SYSTEM.md`
2. Check API documentation: `/docs` (Swagger UI)
3. Review reconciliation reports
4. Contact system administrator

---

**Remember**: The system is doing all the complex accounting automatically. You just need to record transactions as you always have!
