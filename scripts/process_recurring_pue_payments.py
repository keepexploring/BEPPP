#!/usr/bin/env python3
"""
Recurring PUE Payment Processor

This script processes recurring payments for PUE rentals (especially pay-to-own items).
It should be run periodically (e.g., daily via cron job) to charge users for their recurring payments.

Usage:
    python process_recurring_pue_payments.py [--dry-run]

Options:
    --dry-run    Show what would be charged without actually charging
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import argparse
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    PUERental,
    CostStructure,
    CostComponent,
    UserAccount,
    AccountTransaction,
    User
)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://beppp:changeme@localhost:5434/beppp')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def calculate_next_payment_date(current_date, frequency):
    """Calculate the next payment date based on the frequency"""
    if frequency == 'daily':
        return current_date + timedelta(days=1)
    elif frequency == 'weekly':
        return current_date + timedelta(weeks=1)
    elif frequency == 'monthly':
        return current_date + timedelta(days=30)
    else:
        return current_date + timedelta(days=30)  # Default to monthly


def calculate_payment_breakdown(rental, cost_structure, only_recurring=False):
    """Calculate how much should be charged based on the cost structure

    Args:
        rental: The PUERental object
        cost_structure: The CostStructure object
        only_recurring: If True, only include components with is_recurring_payment=True
    """
    ownership_amount = Decimal('0.00')
    rental_fee_amount = Decimal('0.00')

    for component in cost_structure.components:
        # Skip non-recurring components if only_recurring is True
        if only_recurring and not component.is_recurring_payment:
            continue

        # Skip recurring components if only_recurring is False (rental-level payment mode)
        if not only_recurring and component.is_recurring_payment:
            continue

        # Calculate component amount
        if component.is_percentage_of_remaining:
            remaining = Decimal(str(rental.total_item_cost or 0)) - rental.total_paid_towards_ownership
            component_amount = remaining * (Decimal(str(component.percentage_value or 0)) / Decimal('100'))
        else:
            component_amount = Decimal(str(component.rate or 0))

        # Allocate to ownership or rental fees
        if component.contributes_to_ownership:
            ownership_amount += component_amount
        else:
            rental_fee_amount += component_amount

    return float(ownership_amount), float(rental_fee_amount)


def calculate_days_for_interval(interval, unit_type):
    """Convert interval and unit_type to days"""
    unit_to_days = {
        'per_day': 1,
        'per_week': 7,
        'per_month': 30,
        'per_hour': 1/24  # Will be multiplied by interval
    }
    base_days = unit_to_days.get(unit_type, 30)  # Default to 30 days
    return interval * base_days


def get_recurring_components_due(rental, cost_structure, now):
    """Check which recurring components are due for charge

    Returns a list of components that should be charged now
    """
    due_components = []

    for component in cost_structure.components:
        if not component.is_recurring_payment or not component.recurring_interval:
            continue

        # Calculate interval in days
        interval_days = calculate_days_for_interval(
            float(component.recurring_interval),
            component.unit_type
        )

        # Calculate time since checkout
        checkout_date = rental.date_checked_out
        days_since_checkout = (now - checkout_date).total_seconds() / 86400

        # Calculate how many full intervals have passed
        intervals_passed = int(days_since_checkout / interval_days)

        # Calculate when the next charge should occur
        next_charge_days = (intervals_passed + 1) * interval_days

        # Check if we're past the next charge point
        if days_since_checkout >= next_charge_days:
            due_components.append(component)

    return due_components


def process_recurring_pue_payments(dry_run=False):
    """Process recurring payments for all PUE rentals that are due

    This script handles:
    1. Rental-level recurring payments (has_recurring_payment=True)
       - Charges all non-recurring components at the rental's frequency
    2. Component-level recurring payments (component.is_recurring_payment=True)
       - TODO: Requires additional tracking mechanism to charge components
         at their custom intervals without duplicates. For now, recurring
         components should be used within rental-level recurring payment structure.
    """
    db = SessionLocal()

    try:
        today = datetime.utcnow().date()
        now = datetime.utcnow()

        # Get all active PUE rentals with recurring payments that are due
        due_rentals = db.query(PUERental).filter(
            PUERental.has_recurring_payment == True,
            PUERental.is_active == True,
            PUERental.date_returned.is_(None),  # Not returned
            PUERental.next_payment_due_date <= now
        ).all()

        print(f"\n{'='*60}")
        print(f"Recurring PUE Payment Processor")
        print(f"Date: {today}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"{'='*60}\n")
        print(f"Found {len(due_rentals)} rental(s) due for payment\n")

        total_charged = 0
        success_count = 0
        error_count = 0

        for rental in due_rentals:
            try:
                # Get cost structure details
                cost_structure = db.query(CostStructure).filter(
                    CostStructure.structure_id == rental.cost_structure_id
                ).first()

                if not cost_structure:
                    print(f"⚠️  Rental {rental.pue_rental_id}: Cost structure not found")
                    error_count += 1
                    continue

                # Get user details
                user = db.query(User).filter(User.user_id == rental.user_id).first()
                if not user:
                    print(f"⚠️  Rental {rental.pue_rental_id}: User not found")
                    error_count += 1
                    continue

                # Get or create user account
                user_account = db.query(UserAccount).filter(
                    UserAccount.user_id == rental.user_id
                ).first()

                if not user_account:
                    if not dry_run:
                        user_account = UserAccount(
                            user_id=rental.user_id,
                            balance=0,
                            total_spent=0,
                            total_owed=0
                        )
                        db.add(user_account)
                        db.flush()
                    else:
                        print(f"  [DRY RUN] Would create account for user {user.Name}")

                # Calculate payment amounts
                ownership_amount, rental_fee_amount = calculate_payment_breakdown(rental, cost_structure)
                total_amount = ownership_amount + rental_fee_amount

                print(f"📋 PUE Rental {rental.pue_rental_id}:")
                print(f"   User: {user.Name} (ID: {user.user_id})")
                print(f"   Cost Structure: {cost_structure.name}")
                print(f"   Frequency: {rental.recurring_payment_frequency}")
                print(f"   Due Date: {rental.next_payment_due_date}")
                print(f"   Amount: ${total_amount:.2f}")
                print(f"     - Towards Ownership: ${ownership_amount:.2f}")
                print(f"     - Rental Fees: ${rental_fee_amount:.2f}")

                if rental.is_pay_to_own:
                    remaining = float(rental.total_item_cost or 0) - float(rental.total_paid_towards_ownership)
                    print(f"   Remaining to Own: ${remaining:.2f}")

                if not dry_run:
                    # Update account balances
                    user_account.balance -= total_amount  # Debit
                    user_account.total_spent += total_amount
                    user_account.total_owed += total_amount

                    # Create transaction record
                    description = f'Recurring payment: {cost_structure.name}'
                    if rental.is_pay_to_own:
                        description += f' (Pay-to-Own: ${ownership_amount:.2f} towards ownership)'

                    transaction = AccountTransaction(
                        account_id=user_account.account_id,
                        transaction_type='recurring_pue_payment',
                        amount=-total_amount,  # Negative for charges
                        balance_after=user_account.balance,
                        description=description,
                        payment_method='recurring',
                        created_at=now
                    )
                    db.add(transaction)

                    # Update rental payment tracking
                    if rental.is_pay_to_own:
                        rental.total_paid_towards_ownership += Decimal(str(ownership_amount))
                        rental.total_rental_fees_paid += Decimal(str(rental_fee_amount))

                        # Calculate ownership percentage
                        if rental.total_item_cost and rental.total_item_cost > 0:
                            rental.ownership_percentage = (
                                rental.total_paid_towards_ownership / rental.total_item_cost * Decimal('100')
                            )

                        # Check if fully owned
                        if rental.ownership_percentage >= Decimal('100'):
                            rental.pay_to_own_status = 'completed'
                            rental.ownership_completion_date = now
                            rental.has_recurring_payment = False  # Stop recurring payments
                            print(f"   🎉 OWNERSHIP COMPLETE!")

                    # Update payment dates
                    rental.last_payment_date = now
                    rental.next_payment_due_date = calculate_next_payment_date(
                        rental.next_payment_due_date,
                        rental.recurring_payment_frequency
                    )

                    print(f"   ✅ Charged successfully")
                    if rental.has_recurring_payment:
                        print(f"   Next payment: {rental.next_payment_due_date}")
                else:
                    next_payment = calculate_next_payment_date(
                        rental.next_payment_due_date,
                        rental.recurring_payment_frequency
                    )
                    print(f"   [DRY RUN] Would charge ${total_amount:.2f}")
                    print(f"   [DRY RUN] Would set next payment to: {next_payment}")

                print()

                total_charged += total_amount
                success_count += 1

            except Exception as e:
                print(f"   ❌ Error: {e}")
                error_count += 1
                import traceback
                traceback.print_exc()

        if not dry_run:
            db.commit()
            print(f"\n{'='*60}")
            print(f"✅ Payment processing complete")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"ℹ️  DRY RUN - No changes made")
            print(f"{'='*60}")

        print(f"\nSummary:")
        print(f"  Success: {success_count}")
        print(f"  Errors: {error_count}")
        print(f"  Total Amount: ${total_charged:.2f}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n❌ Fatal error during payment processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process recurring PUE payments')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be charged without actually charging')

    args = parser.parse_args()

    process_recurring_pue_payments(dry_run=args.dry_run)
