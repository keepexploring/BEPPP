#!/usr/bin/env python3
"""
Subscription Billing Processor

This script processes recurring subscription billing for active subscriptions.
It should be run periodically (e.g., daily via cron job) to charge users for their subscriptions.

Usage:
    python process_subscription_billing.py [--dry-run]

Options:
    --dry-run    Show what would be charged without actually charging
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    UserSubscription,
    SubscriptionPackage,
    UserAccount,
    AccountTransaction,
    User
)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://beppp:changeme@localhost:5434/beppp')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def calculate_next_billing_date(current_date, billing_period):
    """Calculate the next billing date based on the billing period"""
    if billing_period == 'daily':
        return current_date + timedelta(days=1)
    elif billing_period == 'weekly':
        return current_date + timedelta(weeks=1)
    elif billing_period == 'monthly':
        # Add approximately 30 days for monthly
        return current_date + timedelta(days=30)
    elif billing_period == 'yearly':
        return current_date + timedelta(days=365)
    else:
        return current_date + timedelta(days=30)  # Default to monthly


def process_subscription_billing(dry_run=False):
    """Process billing for all active subscriptions that are due"""
    db = SessionLocal()

    try:
        today = datetime.utcnow().date()

        # Get all active subscriptions that are due for billing
        due_subscriptions = db.query(UserSubscription).join(
            SubscriptionPackage
        ).filter(
            UserSubscription.status == 'active',
            UserSubscription.next_billing_date <= datetime.utcnow()
        ).all()

        print(f"\n{'='*60}")
        print(f"Subscription Billing Processor")
        print(f"Date: {today}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"{'='*60}\n")
        print(f"Found {len(due_subscriptions)} subscription(s) due for billing\n")

        total_charged = 0
        success_count = 0
        error_count = 0

        for user_sub in due_subscriptions:
            try:
                # Get subscription package details
                package = db.query(SubscriptionPackage).filter(
                    SubscriptionPackage.package_id == user_sub.package_id
                ).first()

                if not package:
                    print(f"⚠️  Subscription {user_sub.subscription_id}: Package not found")
                    error_count += 1
                    continue

                # Get user details
                user = db.query(User).filter(User.user_id == user_sub.user_id).first()
                if not user:
                    print(f"⚠️  Subscription {user_sub.subscription_id}: User not found")
                    error_count += 1
                    continue

                # Get or create user account
                user_account = db.query(UserAccount).filter(
                    UserAccount.user_id == user_sub.user_id
                ).first()

                if not user_account:
                    if not dry_run:
                        user_account = UserAccount(
                            user_id=user_sub.user_id,
                            balance=0,
                            total_spent=0,
                            total_owed=0
                        )
                        db.add(user_account)
                        db.flush()
                    else:
                        print(f"  [DRY RUN] Would create account for user {user.Name}")

                charge_amount = package.price

                print(f"📋 Subscription {user_sub.subscription_id}:")
                print(f"   User: {user.Name} (ID: {user.user_id})")
                print(f"   Package: {package.package_name}")
                print(f"   Amount: ${charge_amount:.2f}")
                print(f"   Period: {package.billing_period}")
                print(f"   Due Date: {user_sub.next_billing_date}")

                if not dry_run:
                    # Update account balances
                    user_account.balance -= charge_amount  # Debit
                    user_account.total_spent += charge_amount
                    user_account.total_owed += charge_amount

                    # Create transaction record
                    transaction = AccountTransaction(
                        account_id=user_account.account_id,
                        transaction_type='subscription_charge',
                        amount=-charge_amount,  # Negative for charges
                        balance_after=user_account.balance,
                        description=f'Subscription charge: {package.package_name} ({package.billing_period})',
                        payment_method='subscription',
                        created_at=datetime.utcnow()
                    )
                    db.add(transaction)

                    # Update subscription next billing date
                    user_sub.next_billing_date = calculate_next_billing_date(
                        user_sub.next_billing_date,
                        package.billing_period
                    )
                    user_sub.period_start_date = datetime.utcnow()
                    user_sub.kwh_used_current_period = 0  # Reset kWh usage for new period

                    print(f"   ✅ Charged successfully")
                    print(f"   Next billing: {user_sub.next_billing_date}")
                else:
                    next_billing = calculate_next_billing_date(
                        user_sub.next_billing_date,
                        package.billing_period
                    )
                    print(f"   [DRY RUN] Would charge ${charge_amount:.2f}")
                    print(f"   [DRY RUN] Would set next billing to: {next_billing}")

                print()

                total_charged += charge_amount
                success_count += 1

            except Exception as e:
                print(f"   ❌ Error: {e}")
                error_count += 1
                import traceback
                traceback.print_exc()

        if not dry_run:
            db.commit()
            print(f"\n{'='*60}")
            print(f"✅ Billing processing complete")
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
        print(f"\n❌ Fatal error during billing processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process subscription billing')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be charged without actually charging')

    args = parser.parse_args()

    process_subscription_billing(dry_run=args.dry_run)
