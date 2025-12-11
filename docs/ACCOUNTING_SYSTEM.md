# Hybrid Double-Entry Accounting System

## Overview

The system now implements a **hybrid accounting approach** that combines the simplicity of single-entry bookkeeping for day-to-day operations with the rigor of double-entry accounting for financial reporting and auditing.

## Key Benefits

✅ **Simple Interface** - Users see simple transactions (payment, charge, credit)
✅ **Proper Accounting** - Double-entry ledger maintained underneath
✅ **Audit Trail** - Complete financial tracking and reconciliation
✅ **Financial Reports** - Generate balance sheets and income statements
✅ **Future-Proof** - Ready for complex financial requirements
✅ **Reconciliation** - Automatic detection of balance discrepancies

## Architecture

### Two-Layer System

1. **User-Facing Layer** (`AccountTransaction`):
   - Simple transaction types
   - Running balance tracking
   - Easy to understand

2. **Accounting Layer** (`LedgerEntry`):
   - Double-entry bookkeeping
   - Debits and Credits
   - Account categorization (Assets, Liabilities, Revenue, Expenses)

## Enhanced Transaction Types

### Specific Transaction Categories

| Transaction Type | Description | Use Case |
|-----------------|-------------|-----------|
| `rental_charge` | Charge for rental service | When customer rents a battery |
| `deposit_collected` | Security deposit received | When collecting upfront deposit |
| `deposit_refunded` | Deposit returned | When customer returns battery in good condition |
| `payment_received` | Payment for outstanding balance | When customer pays their bill |
| `credit_added` | Admin adds credit | Top-up or compensation |
| `late_fee` | Late return penalty | Overdue rental charges |
| `subscription_fee` | Monthly subscription charge | Recurring subscription billing |
| `refund_issued` | Refund to customer | Service credit or overpayment return |
| `adjustment_debit` | Correction (decrease balance) | Fix accounting errors |
| `adjustment_credit` | Correction (increase balance) | Fix accounting errors |

### Legacy Support

The system still supports old transaction types for backward compatibility:
- `payment` → `payment_received`
- `credit` → `credit_added`
- `charge` → `rental_charge`
- `refund` → `refund_issued`

## Chart of Accounts

### Assets (What the Business Owns)
- **Cash** - Money received from customers
- **Accounts Receivable** - Money owed by customers
- **Customer Deposits** - Deposits held (offset by liability)

### Liabilities (What the Business Owes)
- **Customer Credit Balance** - Prepaid credit customers have
- **Deposits Payable** - Deposits that must be refunded

### Revenue (Income)
- **Rental Revenue** - Income from battery rentals
- **Late Fee Revenue** - Income from late fees
- **Subscription Revenue** - Recurring subscription income

### Expenses (Costs)
- **Refunds Expense** - Cost of refunds issued

## How It Works

### Example: Customer Rents a Battery

When a rental charge is created:

1. **User sees**: Simple transaction
   ```
   Transaction: rental_charge
   Amount: $50
   Balance After: -$50
   ```

2. **System creates**: Two ledger entries
   ```
   Debit: Accounts Receivable (Asset)     +$50
   Credit: Rental Revenue (Revenue)       +$50
   ```

### Example: Customer Pays Their Bill

When payment is received:

1. **User sees**: Simple transaction
   ```
   Transaction: payment_received
   Amount: $50
   Balance After: $0
   ```

2. **System creates**: Two ledger entries
   ```
   Debit: Cash (Asset)                    +$50
   Credit: Accounts Receivable (Asset)    -$50
   ```

## New API Endpoints

### 1. Account Reconciliation

**POST** `/accounts/{account_id}/reconcile`

Checks if the account balance matches the sum of all transactions.

**Response:**
```json
{
  "account_id": 123,
  "expected_balance": 100.00,
  "actual_balance": 100.00,
  "difference": 0.00,
  "is_balanced": true,
  "transaction_count": 45
}
```

If discrepancy found, creates a reconciliation record for admin review.

### 2. Account Summary

**GET** `/accounts/{account_id}/summary`

Comprehensive financial summary for an account.

**Response:**
```json
{
  "account_id": 123,
  "current_balance": 100.00,
  "total_credits": 500.00,
  "total_debits": 400.00,
  "net_balance": 100.00,
  "total_spent": 400.00,
  "total_owed": 50.00,
  "available_credit": 50.00,
  "deposits_held": 0.00,
  "transaction_count": 45
}
```

### 3. Financial Report

**GET** `/accounts/financial-report?start_date=2024-01-01&end_date=2024-12-31`

Generates complete financial report using double-entry accounting.

**Response:**
```json
{
  "assets": {
    "cash": 10000.00,
    "accounts_receivable": 5000.00,
    "customer_deposits": 2000.00
  },
  "liabilities": {
    "customer_credit_balance": 3000.00,
    "deposits_payable": 2000.00
  },
  "revenue": {
    "rental_revenue": 25000.00,
    "late_fee_revenue": 1000.00,
    "subscription_revenue": 5000.00
  },
  "expenses": {
    "refunds_expense": 500.00
  },
  "totals": {
    "total_assets": 17000.00,
    "total_liabilities": 5000.00,
    "total_revenue": 31000.00,
    "total_expenses": 500.00,
    "net_income": 30500.00,
    "is_balanced": true
  }
}
```

The `is_balanced` field verifies: **Assets = Liabilities + Net Income**

## Database Tables

### `ledger_entries`

| Column | Type | Description |
|--------|------|-------------|
| entry_id | Integer | Primary key |
| transaction_id | Integer | Links to AccountTransaction |
| account_type | String | 'asset', 'liability', 'revenue', 'expense' |
| account_name | String | Specific account (e.g., 'cash', 'rental_revenue') |
| debit | Float | Debit amount (or NULL) |
| credit | Float | Credit amount (or NULL) |
| description | Text | Entry description |
| created_at | DateTime | When entry was created |

**Rule**: Every transaction creates **exactly 2 ledger entries** with equal debits and credits.

### `account_reconciliations`

| Column | Type | Description |
|--------|------|-------------|
| reconciliation_id | Integer | Primary key |
| account_id | Integer | Account being reconciled |
| expected_balance | Float | Calculated from transactions |
| actual_balance | Float | Current account balance |
| difference | Float | Discrepancy amount |
| status | String | 'pending', 'resolved', 'ignored' |
| resolution_notes | Text | Admin notes |
| resolved_by | Integer | User who resolved it |
| reconciliation_date | DateTime | When reconciliation was run |
| resolved_at | DateTime | When issue was resolved |

## Usage Examples

### Creating a Transaction (Automatic Ledger Entries)

```python
# Old way - still works
POST /accounts/user/123/transaction?transaction_type=payment&amount=50

# New way - more specific
POST /accounts/user/123/transaction?transaction_type=payment_received&amount=50

# System automatically creates:
# 1. AccountTransaction record
# 2. Two LedgerEntry records (debit cash, credit accounts receivable)
```

### Reconciling Accounts

```python
# Run reconciliation for account 123
POST /accounts/123/reconcile

# Returns balance check and creates reconciliation record if discrepancy found
```

### Generating Financial Reports

```python
# Get financial report for hub 1 for Q1 2024
GET /accounts/financial-report?hub_id=1&start_date=2024-01-01&end_date=2024-03-31

# Returns complete financial statement with all accounts
```

## Migration Notes

### Existing Data

- All existing `AccountTransaction` records work as before
- No changes needed to existing code using transactions
- Ledger entries are created going forward

### Backward Compatibility

- Old transaction types (`payment`, `credit`, `charge`, `refund`) still work
- System maps them to new specific types internally
- No breaking changes to existing API calls

## Best Practices

### For Developers

1. **Use specific transaction types** for new code:
   ```python
   # ✅ Good
   transaction_type = 'payment_received'

   # ❌ Old way (still works but less specific)
   transaction_type = 'payment'
   ```

2. **Always include descriptions** for audit trail:
   ```python
   description = 'Payment for rental #1234 - customer John Doe'
   ```

3. **Run reconciliation periodically**:
   ```python
   # Good practice: reconcile accounts monthly
   POST /accounts/{account_id}/reconcile
   ```

### For Admins

1. **Review reconciliation reports** to catch discrepancies early
2. **Use financial reports** for business insights
3. **Check `is_balanced`** flag in financial reports
4. **Investigate any reconciliation with status='pending'**

## Future Enhancements

The system is now ready for:

✅ Complex financial reporting
✅ Multi-currency support
✅ Tax reporting
✅ Audit compliance
✅ Integration with accounting software (QuickBooks, Xero, etc.)
✅ Payroll tracking
✅ Inventory cost tracking
✅ Budget vs. Actual reports

## Technical Details

### Double-Entry Rules

| Transaction Type | Debit Account | Credit Account |
|-----------------|---------------|----------------|
| Rental Charge | Accounts Receivable | Rental Revenue |
| Payment Received | Cash | Accounts Receivable |
| Deposit Collected | Cash | Deposits Payable |
| Deposit Refunded | Deposits Payable | Cash |
| Credit Added | Cash | Customer Credit Balance |
| Late Fee | Accounts Receivable | Late Fee Revenue |
| Refund Issued | Refunds Expense | Cash |

### Accounting Equation

**Assets = Liabilities + Equity**

Where Equity = Revenue - Expenses = Net Income

The system validates this equation in the financial report.

## Support

For questions or issues with the accounting system:
1. Check `/accounts/{account_id}/summary` for account details
2. Run `/accounts/{account_id}/reconcile` to check for discrepancies
3. Review ledger entries in the database if needed
4. Contact system administrator for reconciliation support

---

*Last Updated: 2025-12-08*
*Version: 1.0.0*
