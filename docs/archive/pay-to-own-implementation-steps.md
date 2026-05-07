# Pay-to-Own Implementation Steps

## Phase 1: Database Schema & Backend API (Current Phase)

### Step 1.1: Create Database Migration
**File:** `alembic/versions/[timestamp]_add_pay_to_own_fields.py`

```python
"""Add pay-to-own fields

Revision ID: [auto-generated]
Create Date: [auto-generated]
"""

def upgrade():
    # CostStructure table
    op.add_column('cost_structure', sa.Column('is_pay_to_own', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('cost_structure', sa.Column('item_total_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('cost_structure', sa.Column('allow_multiple_items', sa.Boolean(), nullable=False, server_default='true'))

    # CostComponent table
    op.add_column('cost_component', sa.Column('contributes_to_ownership', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('cost_component', sa.Column('is_percentage_of_remaining', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('cost_component', sa.Column('percentage_value', sa.Numeric(5, 2), nullable=True))

    # PUERental table
    op.add_column('pue_rental', sa.Column('is_pay_to_own', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('pue_rental', sa.Column('total_item_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('pue_rental', sa.Column('total_paid_towards_ownership', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
    op.add_column('pue_rental', sa.Column('total_rental_fees_paid', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
    op.add_column('pue_rental', sa.Column('ownership_percentage', sa.Numeric(5, 2), nullable=False, server_default='0.00'))
    op.add_column('pue_rental', sa.Column('pay_to_own_status', sa.String(20), nullable=True))
    op.add_column('pue_rental', sa.Column('ownership_completion_date', sa.DateTime(), nullable=True))

def downgrade():
    # Reverse all changes
    op.drop_column('pue_rental', 'ownership_completion_date')
    op.drop_column('pue_rental', 'pay_to_own_status')
    op.drop_column('pue_rental', 'ownership_percentage')
    op.drop_column('pue_rental', 'total_rental_fees_paid')
    op.drop_column('pue_rental', 'total_paid_towards_ownership')
    op.drop_column('pue_rental', 'total_item_cost')
    op.drop_column('pue_rental', 'is_pay_to_own')

    op.drop_column('cost_component', 'percentage_value')
    op.drop_column('cost_component', 'is_percentage_of_remaining')
    op.drop_column('cost_component', 'contributes_to_ownership')

    op.drop_column('cost_structure', 'allow_multiple_items')
    op.drop_column('cost_structure', 'item_total_cost')
    op.drop_column('cost_structure', 'is_pay_to_own')
```

### Step 1.2: Update Models
**File:** `models.py`

Update `CostStructure` model:
```python
class CostStructure(Base):
    # ... existing fields ...
    is_pay_to_own = Column(Boolean, default=False, nullable=False)
    item_total_cost = Column(Numeric(10, 2), nullable=True)
    allow_multiple_items = Column(Boolean, default=True, nullable=False)
```

Update `CostComponent` model:
```python
class CostComponent(Base):
    # ... existing fields ...
    contributes_to_ownership = Column(Boolean, default=True, nullable=False)
    is_percentage_of_remaining = Column(Boolean, default=False, nullable=False)
    percentage_value = Column(Numeric(5, 2), nullable=True)
```

Update `PUERental` model:
```python
class PUERental(Base):
    # ... existing fields ...
    is_pay_to_own = Column(Boolean, default=False, nullable=False)
    total_item_cost = Column(Numeric(10, 2), nullable=True)
    total_paid_towards_ownership = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_rental_fees_paid = Column(Numeric(10, 2), default=0.00, nullable=False)
    ownership_percentage = Column(Numeric(5, 2), default=0.00, nullable=False)
    pay_to_own_status = Column(String(20), nullable=True)  # 'active', 'completed', 'returned'
    ownership_completion_date = Column(DateTime, nullable=True)
```

### Step 1.3: Update Pydantic Schemas
**File:** `api/app/main.py` or separate schemas file

```python
class CostStructureCreate(BaseModel):
    # ... existing fields ...
    is_pay_to_own: bool = False
    item_total_cost: Optional[float] = None
    allow_multiple_items: bool = True

class CostComponentCreate(BaseModel):
    # ... existing fields ...
    contributes_to_ownership: bool = True
    is_percentage_of_remaining: bool = False
    percentage_value: Optional[float] = None

class PUERentalCreate(BaseModel):
    # ... existing fields ...
    is_pay_to_own: bool = False

class PUERentalResponse(BaseModel):
    # ... existing fields ...
    is_pay_to_own: bool
    total_item_cost: Optional[float]
    total_paid_towards_ownership: float
    total_rental_fees_paid: float
    ownership_percentage: float
    pay_to_own_status: Optional[str]
    ownership_completion_date: Optional[datetime]
```

### Step 1.4: Add Payment Processing Logic
**File:** `api/app/services/pay_to_own_service.py` (new file)

```python
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from models import PUERental, CostComponent, PUERentalPayment

class PayToOwnService:
    @staticmethod
    def calculate_payment_breakdown(rental: PUERental, payment_amount: float) -> dict:
        """
        Calculate how much of the payment goes to ownership vs rental fees
        """
        ownership_amount = Decimal('0.00')
        rental_fee_amount = Decimal('0.00')

        # Get cost structure and components
        cost_structure = rental.cost_structure

        for component in cost_structure.components:
            # Calculate component amount
            if component.is_percentage_of_remaining:
                remaining = Decimal(str(rental.total_item_cost)) - rental.total_paid_towards_ownership
                component_amount = remaining * (Decimal(str(component.percentage_value)) / Decimal('100'))
            else:
                # Use standard calculation based on unit_type
                component_amount = PayToOwnService._calculate_component_amount(component, rental)

            # Allocate to ownership or rental fees
            if component.contributes_to_ownership:
                ownership_amount += component_amount
            else:
                rental_fee_amount += component_amount

        return {
            'ownership_amount': float(ownership_amount),
            'rental_fee_amount': float(rental_fee_amount),
            'total': float(ownership_amount + rental_fee_amount)
        }

    @staticmethod
    def process_payment(
        db: Session,
        rental: PUERental,
        payment_amount: float,
        payment_type: str,
        notes: str = None
    ) -> dict:
        """
        Process a pay-to-own payment
        """
        breakdown = PayToOwnService.calculate_payment_breakdown(rental, payment_amount)

        # Update rental totals
        rental.total_paid_towards_ownership += Decimal(str(breakdown['ownership_amount']))
        rental.total_rental_fees_paid += Decimal(str(breakdown['rental_fee_amount']))

        # Calculate ownership percentage
        if rental.total_item_cost and rental.total_item_cost > 0:
            rental.ownership_percentage = (
                rental.total_paid_towards_ownership / Decimal(str(rental.total_item_cost)) * Decimal('100')
            )

        # Check if fully owned
        if rental.ownership_percentage >= Decimal('100'):
            rental.pay_to_own_status = 'completed'
            rental.ownership_completion_date = datetime.now()
            # TODO: Transfer item ownership

        # Create payment record
        payment_record = PUERentalPayment(
            rental_id=rental.rental_id,
            user_id=rental.user_id,
            payment_date=datetime.now(),
            total_amount=Decimal(str(payment_amount)),
            amount_towards_ownership=Decimal(str(breakdown['ownership_amount'])),
            amount_for_rental_fees=Decimal(str(breakdown['rental_fee_amount'])),
            payment_type=payment_type,
            notes=notes
        )

        db.add(payment_record)
        db.commit()
        db.refresh(rental)

        return {
            'ownership_amount': breakdown['ownership_amount'],
            'rental_fee_amount': breakdown['rental_fee_amount'],
            'total_paid_towards_ownership': float(rental.total_paid_towards_ownership),
            'remaining_balance': float(Decimal(str(rental.total_item_cost)) - rental.total_paid_towards_ownership),
            'ownership_percentage': float(rental.ownership_percentage),
            'is_completed': rental.pay_to_own_status == 'completed'
        }

    @staticmethod
    def _calculate_component_amount(component: CostComponent, rental: PUERental) -> Decimal:
        """Calculate amount for a cost component"""
        # Implementation depends on unit_type
        # This is a simplified version
        return Decimal(str(component.base_amount or 0))
```

### Step 1.5: Add API Endpoints
**File:** `api/app/main.py`

```python
# Get ownership status
@app.get("/api/pue/rentals/{rental_id}/ownership-status")
async def get_ownership_status(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    rental = db.query(PUERental).filter(PUERental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    if not rental.is_pay_to_own:
        raise HTTPException(status_code=400, detail="This is not a pay-to-own rental")

    remaining = float(Decimal(str(rental.total_item_cost)) - rental.total_paid_towards_ownership)

    return {
        "rental_id": rental.rental_id,
        "is_pay_to_own": rental.is_pay_to_own,
        "total_item_cost": float(rental.total_item_cost),
        "total_paid_towards_ownership": float(rental.total_paid_towards_ownership),
        "total_rental_fees_paid": float(rental.total_rental_fees_paid),
        "ownership_percentage": float(rental.ownership_percentage),
        "remaining_balance": remaining,
        "pay_to_own_status": rental.pay_to_own_status,
        "ownership_completion_date": rental.ownership_completion_date
    }

# Process pay-to-own payment
@app.post("/api/pue/rentals/{rental_id}/pay-to-own-payment")
async def process_pay_to_own_payment(
    rental_id: int,
    payment_data: PayToOwnPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    rental = db.query(PUERental).filter(PUERental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    if not rental.is_pay_to_own:
        raise HTTPException(status_code=400, detail="This is not a pay-to-own rental")

    result = PayToOwnService.process_payment(
        db=db,
        rental=rental,
        payment_amount=payment_data.payment_amount,
        payment_type=payment_data.payment_type,
        notes=payment_data.notes
    )

    return result

# Get user's pay-to-own items
@app.get("/api/users/{user_id}/pay-to-own-items")
async def get_user_pay_to_own_items(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    rentals = db.query(PUERental).filter(
        PUERental.user_id == user_id,
        PUERental.is_pay_to_own == True,
        PUERental.pay_to_own_status.in_(['active', None])
    ).all()

    items = []
    for rental in rentals:
        items.append({
            "rental_id": rental.rental_id,
            "rental_unique_id": rental.rental_unique_id,
            "pue_id": rental.pue_item_id,
            "pue_name": rental.pue_item.name if rental.pue_item else "Unknown",
            "total_item_cost": float(rental.total_item_cost),
            "total_paid_towards_ownership": float(rental.total_paid_towards_ownership),
            "ownership_percentage": float(rental.ownership_percentage),
            "remaining_balance": float(Decimal(str(rental.total_item_cost)) - rental.total_paid_towards_ownership)
        })

    return items
```

---

## Phase 2: Cost Structure UI Updates

### Step 2.1: Update Cost Structure Form
**File:** `frontend/src/pages/SettingsPage.vue` (or relevant settings component)

- Add checkbox for "Pay to Own"
- Add input for "Item Total Cost"
- Add validation to ensure single item when pay-to-own
- Hide duration options when pay-to-own is enabled

### Step 2.2: Update Cost Component Form
- Add checkbox "Contributes to Ownership"
- Add checkbox "Calculate as percentage of remaining"
- Add percentage input (only shown when percentage checkbox is checked)

---

## Phase 3: PUE Rental Form Updates

### Step 3.1: Update Rental Creation Form
**File:** `frontend/src/pages/RentalsPage.vue`

- Fetch cost structure details to check if pay-to-own
- Show pay-to-own banner when cost structure is pay-to-own
- Display total item cost
- Validate quantity = 1 for pay-to-own
- Set `is_pay_to_own` flag when creating rental

### Step 3.2: Update API Call
- Include `is_pay_to_own` in rental creation request
- Copy `item_total_cost` from cost structure to rental

---

## Phase 4: Display Updates

### Step 4.1: Update Rentals Table
**File:** `frontend/src/pages/RentalsPage.vue`

- Add "Pay to Own" badge for pay-to-own rentals
- Update columns to show ownership progress (optional)

### Step 4.2: Update Rental Detail Page
**File:** `frontend/src/pages/RentalDetailPage.vue`

Major additions:
- Pay-to-Own status card with progress bar
- Financial summary (total cost, paid, remaining, fees)
- Payment history table showing ownership vs rental fees breakdown
- Ownership completion indicator

API calls needed:
- Fetch ownership status: `GET /api/pue/rentals/{id}/ownership-status`
- Fetch payment history: Enhance existing payment endpoint

### Step 4.3: Update User Detail Page
**File:** `frontend/src/pages/UserDetailPage.vue`

- Add "Pay-to-Own Items" section
- Show circular progress for each item
- Display paid amount and remaining balance
- Link to rental detail page

API call needed:
- `GET /api/users/{id}/pay-to-own-items`

### Step 4.4: Update Accounts Page
**File:** `frontend/src/pages/AccountsPage.vue`

- Add filter for pay-to-own transactions
- Show payment breakdown in transaction list
- Display ownership contribution vs rental fees

---

## Phase 5: Payment Processing UI

### Step 5.1: Update Payment Collection Dialog
- Detect if rental is pay-to-own
- Show payment breakdown preview before confirmation
- Display how much goes to ownership vs fees
- Update confirmation message to reflect breakdown

### Step 5.2: Add Payment Success Feedback
- Show ownership percentage after payment
- Display remaining balance
- Show completion message if 100% reached

---

## Phase 6: Return & Reassignment Logic

### Step 6.1: Update Return Process
- Allow return even with partial payment
- Update pay_to_own_status to 'returned'
- Keep payment history
- Allow credit to remain on account

### Step 6.2: Add Reassignment Support
- Allow assigning same item to new user
- Track previous ownership history
- Start new pay-to-own cycle

---

## Testing Checklist

- [ ] Create pay-to-own cost structure
- [ ] Add components with mixed ownership flags
- [ ] Add percentage-based component
- [ ] Create pay-to-own rental
- [ ] Verify single item constraint
- [ ] Make first payment
- [ ] Verify payment breakdown
- [ ] Check ownership percentage update
- [ ] View on rental detail page
- [ ] View on user detail page
- [ ] Make additional payments
- [ ] Reach 100% ownership
- [ ] Verify completion status
- [ ] Test return with partial payment
- [ ] Test reassignment
- [ ] Check payment history across pages

---

## Current Status

✅ Phase 1, Step 1: Planning complete
⏳ Phase 1, Step 1.1: Ready to create migration

Next action: Create the database migration file
