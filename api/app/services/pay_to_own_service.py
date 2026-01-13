"""
Pay-to-Own Service
Handles payment processing and ownership tracking for pay-to-own rentals
"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from models import PUERental, CostComponent, CostStructure


class PayToOwnService:
    """Service for handling pay-to-own payment calculations and tracking"""

    @staticmethod
    def calculate_payment_breakdown(
        rental: PUERental,
        payment_amount: float
    ) -> Dict:
        """
        Calculate how much of the payment goes to ownership vs rental fees
        based on the cost structure components.

        Args:
            rental: PUERental instance
            payment_amount: Total payment amount

        Returns:
            Dict with ownership_amount, rental_fee_amount, and details
        """
        if not rental.is_pay_to_own:
            raise ValueError("This is not a pay-to-own rental")

        if not rental.cost_structure:
            raise ValueError("Rental has no cost structure assigned")

        ownership_amount = Decimal('0.00')
        rental_fee_amount = Decimal('0.00')
        component_breakdown = []

        cost_structure = rental.cost_structure

        for component in cost_structure.components:
            # Calculate component amount
            if component.is_percentage_of_remaining:
                # Calculate based on remaining balance
                remaining = Decimal(str(rental.total_item_cost or 0)) - rental.total_paid_towards_ownership
                component_amount = remaining * (Decimal(str(component.percentage_value or 0)) / Decimal('100'))
            else:
                # Use the component rate directly
                component_amount = Decimal(str(component.rate or 0))

            # Track the component breakdown
            component_info = {
                'component_name': component.component_name,
                'amount': float(component_amount),
                'contributes_to_ownership': component.contributes_to_ownership
            }
            component_breakdown.append(component_info)

            # Allocate to ownership or rental fees
            if component.contributes_to_ownership:
                ownership_amount += component_amount
            else:
                rental_fee_amount += component_amount

        return {
            'ownership_amount': float(ownership_amount),
            'rental_fee_amount': float(rental_fee_amount),
            'total': float(ownership_amount + rental_fee_amount),
            'component_breakdown': component_breakdown
        }

    @staticmethod
    def process_payment(
        db: Session,
        rental: PUERental,
        payment_amount: float,
        payment_type: str = 'cash',
        notes: str = None,
        credit_applied: float = 0
    ) -> Dict:
        """
        Process a pay-to-own payment and update ownership tracking.

        Args:
            db: Database session
            rental: PUERental instance
            payment_amount: Cash/card payment amount
            payment_type: Type of payment (cash, mobile_money, etc)
            notes: Optional payment notes
            credit_applied: Amount of credit applied from user account

        Returns:
            Dict with payment result and updated ownership info
        """
        if not rental.is_pay_to_own:
            raise ValueError("This is not a pay-to-own rental")

        # Calculate the breakdown based on cost structure
        breakdown = PayToOwnService.calculate_payment_breakdown(rental, payment_amount + credit_applied)

        # Update rental totals
        rental.total_paid_towards_ownership = (
            rental.total_paid_towards_ownership + Decimal(str(breakdown['ownership_amount']))
        )
        rental.total_rental_fees_paid = (
            rental.total_rental_fees_paid + Decimal(str(breakdown['rental_fee_amount']))
        )

        # Calculate ownership percentage
        if rental.total_item_cost and rental.total_item_cost > 0:
            rental.ownership_percentage = (
                rental.total_paid_towards_ownership / Decimal(str(rental.total_item_cost)) * Decimal('100')
            )
        else:
            rental.ownership_percentage = Decimal('0.00')

        # Check if fully owned (>= 100%)
        was_completed = rental.pay_to_own_status == 'completed'
        if rental.ownership_percentage >= Decimal('100') and not was_completed:
            rental.pay_to_own_status = 'completed'
            rental.ownership_completion_date = datetime.now()
            ownership_completed = True
        else:
            if not rental.pay_to_own_status:
                rental.pay_to_own_status = 'active'
            ownership_completed = False

        # Commit changes
        db.commit()
        db.refresh(rental)

        # Calculate remaining balance
        remaining_balance = max(
            float(Decimal(str(rental.total_item_cost or 0)) - rental.total_paid_towards_ownership),
            0
        )

        return {
            'payment_processed': True,
            'ownership_amount': breakdown['ownership_amount'],
            'rental_fee_amount': breakdown['rental_fee_amount'],
            'total_payment': payment_amount + credit_applied,
            'cash_payment': payment_amount,
            'credit_applied': credit_applied,
            'total_paid_towards_ownership': float(rental.total_paid_towards_ownership),
            'total_rental_fees_paid': float(rental.total_rental_fees_paid),
            'remaining_balance': remaining_balance,
            'ownership_percentage': float(rental.ownership_percentage),
            'ownership_status': rental.pay_to_own_status,
            'ownership_completed': ownership_completed,
            'completion_date': rental.ownership_completion_date.isoformat() if rental.ownership_completion_date else None,
            'component_breakdown': breakdown['component_breakdown']
        }

    @staticmethod
    def get_ownership_status(rental: PUERental) -> Dict:
        """
        Get current ownership status for a pay-to-own rental.

        Args:
            rental: PUERental instance

        Returns:
            Dict with ownership details
        """
        if not rental.is_pay_to_own:
            return {
                'is_pay_to_own': False,
                'error': 'This is not a pay-to-own rental'
            }

        remaining_balance = max(
            float(Decimal(str(rental.total_item_cost or 0)) - rental.total_paid_towards_ownership),
            0
        )

        return {
            'is_pay_to_own': True,
            'rental_id': rental.pue_rental_id,
            'rental_unique_id': getattr(rental, 'rental_unique_id', None),
            'total_item_cost': float(rental.total_item_cost) if rental.total_item_cost else 0,
            'total_paid_towards_ownership': float(rental.total_paid_towards_ownership),
            'total_rental_fees_paid': float(rental.total_rental_fees_paid),
            'ownership_percentage': float(rental.ownership_percentage),
            'remaining_balance': remaining_balance,
            'pay_to_own_status': rental.pay_to_own_status,
            'ownership_completion_date': rental.ownership_completion_date.isoformat() if rental.ownership_completion_date else None,
            'is_completed': rental.pay_to_own_status == 'completed'
        }

    @staticmethod
    def validate_pay_to_own_cost_structure(cost_structure: CostStructure) -> Tuple[bool, str]:
        """
        Validate that a cost structure is properly configured for pay-to-own.

        Args:
            cost_structure: CostStructure instance

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cost_structure.is_pay_to_own:
            return True, ""  # Not a pay-to-own structure, no special validation needed

        # Must have item_total_cost set
        if not cost_structure.item_total_cost or cost_structure.item_total_cost <= 0:
            return False, "Pay-to-own cost structures must have a valid item_total_cost"

        # Should not allow multiple items
        if cost_structure.allow_multiple_items:
            return False, "Pay-to-own cost structures should not allow multiple items"

        # Should have at least one component that contributes to ownership
        has_ownership_component = any(
            comp.contributes_to_ownership for comp in cost_structure.components
        )
        if not has_ownership_component:
            return False, "Pay-to-own cost structures must have at least one component that contributes to ownership"

        return True, ""
