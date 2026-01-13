# Pay-to-Own Feature Implementation Plan

## Overview
Implement a "Pay to Own" system for PUE items (and potentially batteries) where users can gradually pay off items to own them.

## Requirements

### 1. Cost Structure Level
- Add "Pay to Own" mode (boolean flag)
- Only for single items (not multiple PUE/batteries)
- When pay-to-own enabled:
  - Enter total item cost (target amount)
  - Duration options irrelevant
  - Cost components specify if they:
    - Count towards ownership (equity building)
    - Are rental fees (not towards ownership)
    - Can be percentage of remaining balance

### 2. Rental Behavior
- First rental assigns item to user
- Labeled as "Pay to own" in rentals table
- Can be returned with credit remaining on account
- Payment history tracked
- Can be reassigned to another user after return

### 3. Display Requirements
- **Rental Detail Page**:
  - Highlight pay-to-own status
  - Show payments made towards item
  - Show amount paid vs amount remaining
  - Progress indicator

- **User Detail Page**:
  - Show pay-to-own items
  - Payment progress

- **Accounts Page**:
  - Payment records with ownership tracking

### 4. Payment Tracking
- Track payments against specific item
- Separate ownership payments from rental fees
- Calculate ownership percentage
- Show progress towards full ownership

---

## Database Schema Changes

### 1. CostStructure Table
```python
# New fields
is_pay_to_own: Boolean = False  # Is this a pay-to-own structure
item_total_cost: Decimal(10,2) = None  # Total cost of item (for pay-to-own)
allow_multiple_items: Boolean = True  # False for pay-to-own structures
```

### 2. CostComponent Table
```python
# New fields
contributes_to_ownership: Boolean = True  # Does this payment build equity?
is_percentage_of_remaining: Boolean = False  # Calculate as % of remaining balance
percentage_value: Decimal(5,2) = None  # If percentage-based, what %
```

### 3. PUERental Table
```python
# New fields
is_pay_to_own: Boolean = False
total_item_cost: Decimal(10,2) = None
total_paid_towards_ownership: Decimal(10,2) = 0.00
total_rental_fees_paid: Decimal(10,2) = 0.00
ownership_percentage: Decimal(5,2) = 0.00  # Calculated field
pay_to_own_status: String = None  # 'active', 'completed', 'returned'
ownership_completion_date: DateTime = None
```

### 4. PUERentalPayment Table (New or Enhanced)
```python
payment_id: Integer (PK)
rental_id: Integer (FK)
user_id: Integer (FK)
payment_date: DateTime
total_amount: Decimal(10,2)
amount_towards_ownership: Decimal(10,2)  # Equity building
amount_for_rental_fees: Decimal(10,2)  # Non-equity
payment_type: String  # cash, mobile_money, etc
notes: Text
created_at: DateTime
```

### 5. UserPayToOwnHistory Table (New - for tracking across returns/reassignments)
```python
history_id: Integer (PK)
user_id: Integer (FK)
pue_id: Integer (FK)
rental_id: Integer (FK)
amount_paid_towards_ownership: Decimal(10,2)
ownership_percentage_achieved: Decimal(5,2)
payment_date: DateTime
is_active: Boolean  # False if item returned/reassigned
return_date: DateTime = None
notes: Text
```

---

## Backend API Changes

### New Endpoints

#### 1. Cost Structure Management
```python
# Update existing cost structure endpoints
POST /api/settings/cost-structures
- Add is_pay_to_own field
- Add item_total_cost field
- Validate single item requirement

PUT /api/settings/cost-structures/{structure_id}
- Update pay-to-own fields

# Cost components
POST /api/settings/cost-components
- Add contributes_to_ownership field
- Add is_percentage_of_remaining field
- Add percentage_value field
```

#### 2. PUE Rental Management
```python
POST /api/pue/rentals
- Handle pay-to-own rental creation
- Initialize ownership tracking fields
- Assign item to user

GET /api/pue/rentals/{rental_id}/ownership-status
- Return ownership progress
- Payment breakdown
- Remaining balance

POST /api/pue/rentals/{rental_id}/payments
- Process payments
- Calculate ownership vs rental portions
- Update ownership percentage
- Check if ownership completed
```

#### 3. User Pay-to-Own Tracking
```python
GET /api/users/{user_id}/pay-to-own-items
- List active pay-to-own items
- Ownership progress for each
- Payment history

GET /api/users/{user_id}/pay-to-own-history
- Historical pay-to-own items
- Including returned/completed items
```

### Payment Processing Logic
```python
def process_pay_to_own_payment(rental, payment_amount):
    """
    Distribute payment between ownership and rental fees
    based on cost component configurations
    """
    ownership_amount = 0
    rental_fee_amount = 0

    # For each cost component in the structure
    for component in rental.cost_structure.components:
        if component.is_percentage_of_remaining:
            remaining = rental.total_item_cost - rental.total_paid_towards_ownership
            component_amount = remaining * (component.percentage_value / 100)
        else:
            # Calculate based on unit_type (per_day, fixed, etc)
            component_amount = calculate_component_amount(component, rental)

        if component.contributes_to_ownership:
            ownership_amount += component_amount
        else:
            rental_fee_amount += component_amount

    # Update rental
    rental.total_paid_towards_ownership += ownership_amount
    rental.total_rental_fees_paid += rental_fee_amount
    rental.ownership_percentage = (
        rental.total_paid_towards_ownership / rental.total_item_cost * 100
    )

    # Check if fully owned
    if rental.ownership_percentage >= 100:
        rental.pay_to_own_status = 'completed'
        rental.ownership_completion_date = datetime.now()
        # Transfer ownership in system
        transfer_item_ownership(rental.pue_id, rental.user_id)

    return {
        'ownership_amount': ownership_amount,
        'rental_fee_amount': rental_fee_amount,
        'total_paid': rental.total_paid_towards_ownership,
        'remaining': rental.total_item_cost - rental.total_paid_towards_ownership,
        'ownership_percentage': rental.ownership_percentage
    }
```

---

## Frontend Changes

### 1. Cost Structure Creation/Edit (Settings Page)

**Add to Cost Structure Form:**
```vue
<!-- Pay to Own Section -->
<q-checkbox
  v-model="costStructureForm.is_pay_to_own"
  label="Pay to Own Item"
  @update:model-value="onPayToOwnToggle"
/>

<q-input
  v-if="costStructureForm.is_pay_to_own"
  v-model.number="costStructureForm.item_total_cost"
  type="number"
  label="Total Item Cost *"
  prefix="MK"
  hint="The full price of the item to be owned"
  :rules="[val => val > 0 || 'Item cost is required for pay-to-own']"
/>

<q-banner v-if="costStructureForm.is_pay_to_own" class="bg-blue-1">
  Pay-to-own structures can only be applied to a single item at a time.
  Duration options are not applicable for pay-to-own items.
</q-banner>
```

**Add to Cost Component Form:**
```vue
<!-- For each cost component -->
<q-card-section v-if="parentStructure.is_pay_to_own">
  <div class="text-subtitle2">Payment Allocation</div>

  <q-checkbox
    v-model="component.contributes_to_ownership"
    label="Counts towards ownership"
    hint="Check if this payment builds equity in the item"
  />

  <q-checkbox
    v-model="component.is_percentage_of_remaining"
    label="Calculate as percentage of remaining balance"
  />

  <q-input
    v-if="component.is_percentage_of_remaining"
    v-model.number="component.percentage_value"
    type="number"
    label="Percentage"
    suffix="%"
    min="0"
    max="100"
  />
</q-card-section>
```

### 2. PUE Rental Form (RentalsPage.vue)

**Show Pay-to-Own Indicator:**
```vue
<!-- After cost structure selection -->
<q-banner
  v-if="selectedCostStructureIsPayToOwn"
  class="bg-purple-1 q-mb-md"
>
  <template v-slot:avatar>
    <q-icon name="account_balance" color="purple" />
  </template>
  <div class="text-h6">Pay to Own</div>
  <div class="text-body2">
    Total Item Cost: {{ currentCurrencySymbol }}{{ payToOwnItemCost.toFixed(2) }}
  </div>
  <div class="text-caption">
    This rental will allow the customer to gradually own this item through payments.
  </div>
</q-banner>
```

### 3. Rentals Table

**Add Badge/Label Column:**
```vue
<template v-slot:body-cell-rental_type="props">
  <q-td :props="props">
    <div class="row items-center q-gutter-xs">
      <q-badge
        :color="props.row.rental_type === 'battery' ? 'blue' : 'purple'"
        :label="props.row.rental_type === 'battery' ? 'Battery' : 'PUE'"
      />
      <q-badge
        v-if="props.row.is_pay_to_own"
        color="purple-10"
        label="Pay to Own"
      />
    </div>
  </q-td>
</template>
```

### 4. Rental Detail Page

**Add Ownership Progress Section:**
```vue
<!-- Pay to Own Status Section -->
<q-card v-if="rental.is_pay_to_own" flat bordered class="q-mb-md">
  <q-card-section class="bg-purple-1">
    <div class="row items-center q-mb-md">
      <q-icon name="account_balance" size="md" color="purple" class="q-mr-md" />
      <div class="col">
        <div class="text-h6">Pay to Own Progress</div>
        <div class="text-caption">Customer is working towards owning this item</div>
      </div>
      <div class="col-auto">
        <q-chip color="purple" text-color="white" size="lg">
          {{ rental.ownership_percentage.toFixed(1) }}% Owned
        </q-chip>
      </div>
    </div>

    <!-- Progress Bar -->
    <q-linear-progress
      :value="rental.ownership_percentage / 100"
      size="20px"
      color="purple"
      class="q-mb-md"
    />

    <!-- Financial Summary -->
    <div class="row q-col-gutter-md">
      <div class="col-6 col-md-3">
        <div class="text-caption text-grey-7">Total Item Cost</div>
        <div class="text-h6">{{ currentCurrencySymbol }}{{ rental.total_item_cost.toFixed(2) }}</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="text-caption text-grey-7">Paid Towards Ownership</div>
        <div class="text-h6 text-positive">{{ currentCurrencySymbol }}{{ rental.total_paid_towards_ownership.toFixed(2) }}</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="text-caption text-grey-7">Remaining Balance</div>
        <div class="text-h6 text-negative">{{ currentCurrencySymbol }}{{ (rental.total_item_cost - rental.total_paid_towards_ownership).toFixed(2) }}</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="text-caption text-grey-7">Rental Fees Paid</div>
        <div class="text-body1">{{ currentCurrencySymbol }}{{ rental.total_rental_fees_paid.toFixed(2) }}</div>
      </div>
    </div>
  </q-card-section>

  <!-- Payment History -->
  <q-card-section>
    <div class="text-subtitle2 q-mb-md">Payment History</div>
    <q-list bordered separator>
      <q-item v-for="payment in payToOwnPayments" :key="payment.payment_id">
        <q-item-section>
          <q-item-label>{{ formatDate(payment.payment_date) }}</q-item-label>
          <q-item-label caption>{{ payment.payment_type }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="text-caption text-grey-7">Towards Ownership</div>
          <div class="text-body2 text-positive">
            {{ currentCurrencySymbol }}{{ payment.amount_towards_ownership.toFixed(2) }}
          </div>
        </q-item-section>
        <q-item-section side>
          <div class="text-caption text-grey-7">Rental Fees</div>
          <div class="text-body2">
            {{ currentCurrencySymbol }}{{ payment.amount_for_rental_fees.toFixed(2) }}
          </div>
        </q-item-section>
        <q-item-section side>
          <div class="text-caption text-grey-7">Total</div>
          <div class="text-body2 text-weight-bold">
            {{ currentCurrencySymbol }}{{ payment.total_amount.toFixed(2) }}
          </div>
        </q-item-section>
      </q-item>
    </q-list>
  </q-card-section>
</q-card>
```

### 5. User Detail Page

**Add Pay-to-Own Items Section:**
```vue
<q-card flat bordered>
  <q-card-section>
    <div class="text-h6">Pay-to-Own Items</div>
  </q-card-section>

  <q-card-section v-if="userPayToOwnItems.length > 0">
    <q-list bordered separator>
      <q-item v-for="item in userPayToOwnItems" :key="item.rental_id" clickable @click="viewRental(item.rental_id)">
        <q-item-section>
          <q-item-label>{{ item.pue_name }}</q-item-label>
          <q-item-label caption>Rental #{{ item.rental_unique_id }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-circular-progress
            :value="item.ownership_percentage"
            size="50px"
            :thickness="0.2"
            color="purple"
            track-color="grey-3"
            class="q-ma-md"
          >
            {{ item.ownership_percentage.toFixed(0) }}%
          </q-circular-progress>
        </q-item-section>
        <q-item-section side>
          <div class="text-caption">Paid</div>
          <div class="text-body2">{{ currentCurrencySymbol }}{{ item.total_paid_towards_ownership.toFixed(2) }}</div>
          <div class="text-caption q-mt-xs">Remaining</div>
          <div class="text-body2">{{ currentCurrencySymbol }}{{ (item.total_item_cost - item.total_paid_towards_ownership).toFixed(2) }}</div>
        </q-item-section>
      </q-item>
    </q-list>
  </q-card-section>

  <q-card-section v-else>
    <div class="text-center text-grey-7">
      No active pay-to-own items
    </div>
  </q-card-section>
</q-card>
```

---

## Implementation Order

1. **Phase 1: Database & Backend** (Start here)
   - Create migration for new fields
   - Update models
   - Add/update API endpoints
   - Implement payment processing logic

2. **Phase 2: Cost Structure UI**
   - Update settings page for pay-to-own options
   - Add validation for single item requirement

3. **Phase 3: Rental Creation**
   - Update PUE rental form
   - Show pay-to-own indicators
   - Handle pay-to-own rental creation

4. **Phase 4: Display & Tracking**
   - Update rentals table
   - Add ownership progress to rental detail page
   - Add pay-to-own section to user detail page
   - Update accounts page

5. **Phase 5: Payment Processing**
   - Update payment collection to split ownership/fees
   - Add payment history display
   - Implement ownership completion logic

6. **Phase 6: Return & Reassignment**
   - Handle return with credit retention
   - Track ownership history
   - Allow reassignment to new users

---

## Testing Scenarios

1. Create pay-to-own cost structure with mixed components
2. Create pay-to-own rental
3. Make partial payments
4. Verify ownership percentage updates
5. Complete ownership (100% paid)
6. Return item before completion
7. Reassign to new user
8. View payment history across all pages
9. Test percentage-based components
10. Test with different payment types

---

## Notes

- Duration is irrelevant for pay-to-own but rental still tracks start/end dates
- Item can be "returned" even when partially paid (credit remains)
- Ownership transfer happens at 100% payment
- Multiple users can have ownership history for same item (sequential)
- Payment breakdown must be clear on every display
- Consider refund scenarios if needed
