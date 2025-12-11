"""
Accounting utilities for hybrid double-entry system
Provides simple interface while maintaining proper accounting underneath
"""
from sqlalchemy.orm import Session
from models import (
    AccountTransaction, LedgerEntry, UserAccount, AccountReconciliation,
    TransactionType, AccountType
)
from typing import List, Dict, Tuple


def create_ledger_entries(
    db: Session,
    transaction_id: int,
    transaction_type: str,
    amount: float,
    description: str = None
) -> List[LedgerEntry]:
    """
    Create double-entry ledger entries for a transaction.
    Every transaction creates equal debits and credits.

    Args:
        db: Database session
        transaction_id: ID of the AccountTransaction
        transaction_type: Type of transaction (from TransactionType)
        amount: Transaction amount
        description: Optional description

    Returns:
        List of created LedgerEntry objects
    """
    entries = []

    # Map transaction types to their double-entry rules
    # Format: (debit_account_type, debit_account_name, credit_account_type, credit_account_name)

    if transaction_type in [TransactionType.RENTAL_CHARGE, 'rental_charge']:
        # Rental charge creates a receivable
        # Debit: Accounts Receivable (Asset increases)
        # Credit: Rental Revenue (Revenue increases)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.ACCOUNTS_RECEIVABLE,
            debit=amount,
            credit=None,
            description=description or 'Rental charge - customer owes money'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='revenue',
            account_name=AccountType.RENTAL_REVENUE,
            debit=None,
            credit=amount,
            description=description or 'Rental revenue earned'
        ))

    elif transaction_type in [TransactionType.PAYMENT_RECEIVED, TransactionType.PAYMENT, 'payment', 'payment_received']:
        # Payment received for outstanding balance
        # Debit: Cash (Asset increases)
        # Credit: Accounts Receivable (Asset decreases)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.CASH,
            debit=amount,
            credit=None,
            description=description or 'Cash payment received'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.ACCOUNTS_RECEIVABLE,
            debit=None,
            credit=amount,
            description=description or 'Receivable paid off'
        ))

    elif transaction_type in [TransactionType.DEPOSIT_COLLECTED, 'deposit_collected']:
        # Deposit collected from customer
        # Debit: Cash (Asset increases)
        # Credit: Deposits Payable (Liability increases - we owe them the deposit back)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.CASH,
            debit=amount,
            credit=None,
            description=description or 'Security deposit collected'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='liability',
            account_name=AccountType.DEPOSITS_PAYABLE,
            debit=None,
            credit=amount,
            description=description or 'Deposit liability - owe customer refund'
        ))

    elif transaction_type in [TransactionType.DEPOSIT_REFUNDED, 'deposit_refunded']:
        # Deposit returned to customer
        # Debit: Deposits Payable (Liability decreases - no longer owe them)
        # Credit: Cash (Asset decreases)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='liability',
            account_name=AccountType.DEPOSITS_PAYABLE,
            debit=amount,
            credit=None,
            description=description or 'Deposit liability settled'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.CASH,
            debit=None,
            credit=amount,
            description=description or 'Cash refunded to customer'
        ))

    elif transaction_type in [TransactionType.CREDIT_ADDED, TransactionType.CREDIT, 'credit', 'credit_added']:
        # Admin adds credit to customer account
        # Debit: Cash (if customer paid) OR Customer Credit Balance (if comp/gift)
        # Credit: Customer Credit Balance (Liability - we owe them value)
        # For simplicity, treat as cash received that goes to credit balance
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.CASH,
            debit=amount,
            credit=None,
            description=description or 'Credit added - cash received'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='liability',
            account_name=AccountType.CUSTOMER_CREDIT_BALANCE,
            debit=None,
            credit=amount,
            description=description or 'Customer credit balance increased'
        ))

    elif transaction_type in [TransactionType.LATE_FEE, 'late_fee']:
        # Late fee charged
        # Debit: Accounts Receivable (Asset increases)
        # Credit: Late Fee Revenue (Revenue increases)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.ACCOUNTS_RECEIVABLE,
            debit=amount,
            credit=None,
            description=description or 'Late fee charged'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='revenue',
            account_name=AccountType.LATE_FEE_REVENUE,
            debit=None,
            credit=amount,
            description=description or 'Late fee revenue'
        ))

    elif transaction_type in [TransactionType.SUBSCRIPTION_FEE, 'subscription_fee']:
        # Subscription fee charged
        # Debit: Accounts Receivable (Asset increases)
        # Credit: Subscription Revenue (Revenue increases)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.ACCOUNTS_RECEIVABLE,
            debit=amount,
            credit=None,
            description=description or 'Subscription fee charged'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='revenue',
            account_name=AccountType.SUBSCRIPTION_REVENUE,
            debit=None,
            credit=amount,
            description=description or 'Subscription revenue'
        ))

    elif transaction_type in [TransactionType.REFUND_ISSUED, TransactionType.REFUND, 'refund', 'refund_issued']:
        # Refund issued to customer
        # Debit: Refunds Expense (Expense increases)
        # Credit: Cash (Asset decreases)
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='expense',
            account_name=AccountType.REFUNDS_EXPENSE,
            debit=amount,
            credit=None,
            description=description or 'Refund issued'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='asset',
            account_name=AccountType.CASH,
            debit=None,
            credit=amount,
            description=description or 'Cash refunded'
        ))

    elif transaction_type in [TransactionType.ADJUSTMENT_CREDIT, 'adjustment_credit']:
        # Adjustment that increases customer balance (credit)
        # Debit: Refunds Expense or Adjustment Expense
        # Credit: Customer Credit Balance
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='expense',
            account_name=AccountType.REFUNDS_EXPENSE,
            debit=amount,
            credit=None,
            description=description or 'Adjustment expense'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='liability',
            account_name=AccountType.CUSTOMER_CREDIT_BALANCE,
            debit=None,
            credit=amount,
            description=description or 'Credit adjustment'
        ))

    elif transaction_type in [TransactionType.ADJUSTMENT_DEBIT, 'adjustment_debit']:
        # Adjustment that decreases customer balance (debit)
        # Debit: Customer Credit Balance
        # Credit: Revenue or adjustment account
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='liability',
            account_name=AccountType.CUSTOMER_CREDIT_BALANCE,
            debit=amount,
            credit=None,
            description=description or 'Debit adjustment'
        ))
        entries.append(LedgerEntry(
            transaction_id=transaction_id,
            account_type='revenue',
            account_name=AccountType.RENTAL_REVENUE,
            debit=None,
            credit=amount,
            description=description or 'Adjustment revenue'
        ))

    # Add all entries to database
    for entry in entries:
        db.add(entry)

    return entries


def reconcile_account(db: Session, account_id: int, current_user_id: int = None) -> Dict:
    """
    Reconcile a user account by calculating expected balance from transactions
    and comparing with actual balance.

    Args:
        db: Database session
        account_id: Account to reconcile
        current_user_id: ID of user performing reconciliation

    Returns:
        Dictionary with reconciliation results
    """
    account = db.query(UserAccount).filter(UserAccount.account_id == account_id).first()
    if not account:
        return {"error": "Account not found"}

    # Get all transactions for this account
    transactions = db.query(AccountTransaction).filter(
        AccountTransaction.account_id == account_id
    ).order_by(AccountTransaction.created_at.asc()).all()

    # Calculate expected balance
    expected_balance = 0.0
    for trans in transactions:
        if trans.transaction_type in ['payment', 'credit', 'credit_added', 'payment_received', 'deposit_refunded']:
            expected_balance += trans.amount
        elif trans.transaction_type in ['charge', 'rental_charge', 'late_fee', 'subscription_fee', 'deposit_collected']:
            expected_balance -= trans.amount
        elif trans.transaction_type == 'refund':
            expected_balance += trans.amount
        elif trans.transaction_type == 'adjustment_credit':
            expected_balance += trans.amount
        elif trans.transaction_type == 'adjustment_debit':
            expected_balance -= trans.amount

    actual_balance = account.balance
    difference = actual_balance - expected_balance

    result = {
        "account_id": account_id,
        "expected_balance": round(expected_balance, 2),
        "actual_balance": round(actual_balance, 2),
        "difference": round(difference, 2),
        "is_balanced": abs(difference) < 0.01,  # Allow 1 cent rounding difference
        "transaction_count": len(transactions)
    }

    # If there's a discrepancy, create reconciliation record
    if abs(difference) >= 0.01:
        reconciliation = AccountReconciliation(
            account_id=account_id,
            expected_balance=expected_balance,
            actual_balance=actual_balance,
            difference=difference,
            status='pending'
        )
        db.add(reconciliation)
        db.commit()
        result["reconciliation_id"] = reconciliation.reconciliation_id

    return result


def get_account_summary(db: Session, account_id: int) -> Dict:
    """
    Get comprehensive account summary with all financial metrics.

    Args:
        db: Database session
        account_id: Account ID

    Returns:
        Dictionary with account summary
    """
    account = db.query(UserAccount).filter(UserAccount.account_id == account_id).first()
    if not account:
        return {"error": "Account not found"}

    transactions = db.query(AccountTransaction).filter(
        AccountTransaction.account_id == account_id
    ).all()

    # Calculate summaries
    total_credits = sum(
        t.amount for t in transactions
        if t.transaction_type in ['payment', 'credit', 'credit_added', 'payment_received', 'adjustment_credit']
    )

    total_debits = sum(
        t.amount for t in transactions
        if t.transaction_type in ['charge', 'rental_charge', 'late_fee', 'subscription_fee', 'adjustment_debit']
    )

    total_deposits_collected = sum(
        t.amount for t in transactions
        if t.transaction_type == 'deposit_collected'
    )

    total_deposits_refunded = sum(
        t.amount for t in transactions
        if t.transaction_type == 'deposit_refunded'
    )

    return {
        "account_id": account_id,
        "current_balance": round(account.balance, 2),
        "total_credits": round(total_credits, 2),
        "total_debits": round(total_debits, 2),
        "net_balance": round(total_credits - total_debits, 2),
        "total_spent": round(account.total_spent, 2),
        "total_owed": round(account.total_owed, 2),
        "available_credit": round(account.balance - account.total_owed, 2),
        "deposits_held": round(total_deposits_collected - total_deposits_refunded, 2),
        "transaction_count": len(transactions)
    }


def get_financial_report(db: Session, hub_id: int = None, start_date=None, end_date=None) -> Dict:
    """
    Generate financial report using double-entry ledger.

    Args:
        db: Database session
        hub_id: Optional hub filter
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Financial report with assets, liabilities, revenue, expenses
    """
    query = db.query(LedgerEntry)

    if start_date:
        query = query.filter(LedgerEntry.created_at >= start_date)
    if end_date:
        query = query.filter(LedgerEntry.created_at <= end_date)

    entries = query.all()

    # Aggregate by account type and name
    accounts = {}
    for entry in entries:
        key = f"{entry.account_type}:{entry.account_name}"
        if key not in accounts:
            accounts[key] = {
                "account_type": entry.account_type,
                "account_name": entry.account_name,
                "total_debits": 0.0,
                "total_credits": 0.0,
                "balance": 0.0
            }

        if entry.debit:
            accounts[key]["total_debits"] += entry.debit
        if entry.credit:
            accounts[key]["total_credits"] += entry.credit

        # Calculate balance based on account type
        # Assets & Expenses: Debit increases, Credit decreases
        # Liabilities & Revenue: Credit increases, Debit decreases
        if entry.account_type in ['asset', 'expense']:
            accounts[key]["balance"] = accounts[key]["total_debits"] - accounts[key]["total_credits"]
        else:  # liability, revenue
            accounts[key]["balance"] = accounts[key]["total_credits"] - accounts[key]["total_debits"]

    # Organize by category
    report = {
        "assets": {},
        "liabilities": {},
        "revenue": {},
        "expenses": {},
        "totals": {
            "total_assets": 0.0,
            "total_liabilities": 0.0,
            "total_revenue": 0.0,
            "total_expenses": 0.0,
            "net_income": 0.0,
            "is_balanced": True
        }
    }

    for key, data in accounts.items():
        acc_type = data["account_type"]
        if acc_type == 'asset':
            report["assets"][data["account_name"]] = round(data["balance"], 2)
            report["totals"]["total_assets"] += data["balance"]
        elif acc_type == 'liability':
            report["liabilities"][data["account_name"]] = round(data["balance"], 2)
            report["totals"]["total_liabilities"] += data["balance"]
        elif acc_type == 'revenue':
            report["revenue"][data["account_name"]] = round(data["balance"], 2)
            report["totals"]["total_revenue"] += data["balance"]
        elif acc_type == 'expense':
            report["expenses"][data["account_name"]] = round(data["balance"], 2)
            report["totals"]["total_expenses"] += data["balance"]

    # Round totals
    report["totals"]["total_assets"] = round(report["totals"]["total_assets"], 2)
    report["totals"]["total_liabilities"] = round(report["totals"]["total_liabilities"], 2)
    report["totals"]["total_revenue"] = round(report["totals"]["total_revenue"], 2)
    report["totals"]["total_expenses"] = round(report["totals"]["total_expenses"], 2)

    # Calculate net income
    report["totals"]["net_income"] = round(
        report["totals"]["total_revenue"] - report["totals"]["total_expenses"],
        2
    )

    # Check if books balance (Assets = Liabilities + Equity)
    # Equity = Revenue - Expenses = Net Income
    left_side = report["totals"]["total_assets"]
    right_side = report["totals"]["total_liabilities"] + report["totals"]["net_income"]
    report["totals"]["is_balanced"] = abs(left_side - right_side) < 0.01

    return report
