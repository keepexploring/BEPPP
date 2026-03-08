import { getCachedResponse } from './offlineDb.js'

/**
 * Calculate return cost locally when offline, mirroring backend logic.
 * Returns the same JSON shape as the server endpoint so templates work unchanged.
 * Returns null if required data (cost structure) is missing from cache.
 *
 * @param {Object} rental - The rental object (from cached list or detail)
 * @param {'battery'|'pue'} rentalType - Type of rental
 * @returns {Object|null} Cost calculation result or null if data unavailable
 */
export async function calculateReturnCostLocally (rental, rentalType) {
  if (!rental) return null

  const hubId = rental.hub_id
  const rentalId = rentalType === 'pue'
    ? rental.pue_rental_id
    : (rental.rental_id || rental.rentral_id || rental.id)

  // Determine start date field (handle multiple field naming conventions)
  const startDateStr = rentalType === 'pue'
    ? (rental.timestamp_taken || rental.start_date || rental.rental_start_date)
    : (rental.start_date || rental.rental_start_date || rental.timestamp_taken)

  if (!startDateStr) return null

  // Parse start date
  let startDate
  try {
    startDate = new Date(typeof startDateStr === 'string'
      ? startDateStr.replace('Z', '+00:00')
      : startDateStr)
  } catch {
    return null
  }

  const returnDate = new Date()

  // Calculate durations
  const durationMs = returnDate.getTime() - startDate.getTime()
  const actualHours = durationMs / (1000 * 3600)
  const actualDays = durationMs / (1000 * 86400)
  const actualWeeks = actualDays / 7
  const actualMonths = actualDays / 30

  // Look up cost structure from cache
  let costStructure = null
  let components = []

  if (rental.cost_structure_id) {
    // Try to get cost structures from cached settings (ignoreExpiry since we're offline)
    const costStructuresEntry = hubId
      ? await getCachedResponse(`GET:/settings/cost-structures?hub_id=${hubId}`, { ignoreExpiry: true })
      : null

    if (costStructuresEntry) {
      // Backend returns { cost_structures: [...] } or possibly a plain array
      const csData = costStructuresEntry.data
      const csList = Array.isArray(csData) ? csData : (csData?.cost_structures || [])
      const csId = rental.cost_structure_id
      costStructure = csList.find(
        cs => cs.structure_id === csId || String(cs.structure_id) === String(csId)
      )
      if (costStructure && Array.isArray(costStructure.components)) {
        components = costStructure.components
      }
    }
  }

  if (!costStructure) return null

  // Get recharges (battery rentals only)
  let totalRecharges = rental.recharges_used || 0
  if (rentalType === 'battery' && costStructure.count_initial_checkout_as_recharge && totalRecharges === 0) {
    totalRecharges = 1
  }

  // Calculate cost breakdown
  const costBreakdown = []
  const calculationSteps = []
  let subtotal = 0

  for (const component of components) {
    let componentCost = 0
    let quantity = 0
    let explanation = ''

    switch (component.unit_type) {
      case 'per_hour':
        quantity = actualHours
        componentCost = component.rate * actualHours
        explanation = `${component.component_name}: ${quantity.toFixed(2)} hours × R${component.rate.toFixed(2)}/hour = R${componentCost.toFixed(2)}`
        break
      case 'per_day':
        quantity = actualDays
        componentCost = component.rate * actualDays
        explanation = `${component.component_name}: ${quantity.toFixed(2)} days × R${component.rate.toFixed(2)}/day = R${componentCost.toFixed(2)}`
        break
      case 'per_week':
        quantity = actualWeeks
        componentCost = component.rate * actualWeeks
        explanation = `${component.component_name}: ${quantity.toFixed(2)} weeks × R${component.rate.toFixed(2)}/week = R${componentCost.toFixed(2)}`
        break
      case 'per_month':
        quantity = actualMonths
        componentCost = component.rate * actualMonths
        explanation = `${component.component_name}: ${quantity.toFixed(2)} months × R${component.rate.toFixed(2)}/month = R${componentCost.toFixed(2)}`
        break
      case 'per_recharge': {
        quantity = totalRecharges
        componentCost = component.rate * totalRecharges
        const rechargeNote = costStructure.count_initial_checkout_as_recharge && totalRecharges >= 1
          ? ' (includes initial checkout)'
          : ''
        explanation = `${component.component_name}: ${quantity} recharge(s)${rechargeNote} × R${component.rate.toFixed(2)}/recharge = R${componentCost.toFixed(2)}`
        break
      }
      case 'per_kwh':
        // Skip — kWh data requires live battery telemetry
        explanation = `${component.component_name}: kWh cost finalized on sync`
        calculationSteps.push(explanation)
        continue
      case 'fixed':
      case 'one_time':
        quantity = 1
        componentCost = component.rate
        explanation = `${component.component_name}: Fixed charge = R${componentCost.toFixed(2)}`
        break
      default:
        // Handle custom unit types (per_kg, per_litre, etc.) - skip for offline
        if (component.unit_type && component.unit_type.startsWith('per_')) {
          explanation = `${component.component_name}: ${component.unit_type} cost finalized on sync`
          calculationSteps.push(explanation)
        }
        continue
    }

    if (quantity > 0 || component.unit_type === 'fixed') {
      costBreakdown.push({
        component_name: component.component_name,
        unit_type: component.unit_type,
        rate: component.rate,
        quantity: Math.round(quantity * 100) / 100,
        amount: Math.round(componentCost * 100) / 100,
        explanation
      })
      if (explanation) calculationSteps.push(explanation)
      subtotal += componentCost
    }
  }

  // Get hub VAT from cache (ignoreExpiry since we're offline)
  let vatPercentage = 15.0
  if (hubId) {
    const hubEntry = await getCachedResponse(`GET:/settings/hub/${hubId}`, { ignoreExpiry: true })
    if (hubEntry && hubEntry.data && hubEntry.data.vat_percentage != null) {
      vatPercentage = hubEntry.data.vat_percentage
    }
  }

  const vatAmount = subtotal * (vatPercentage / 100)
  const total = subtotal + vatAmount

  // Get user account balance from cache (ignoreExpiry since we're offline)
  let accountBalance = 0
  if (rental.user_id) {
    const accountEntry = await getCachedResponse(`GET:/accounts/user/${rental.user_id}`, { ignoreExpiry: true })
    if (accountEntry && accountEntry.data && accountEntry.data.balance != null) {
      accountBalance = accountEntry.data.balance
    }
  }

  // Payment calculations (handle multiple field naming conventions)
  const depositPaid = rental.deposit_amount || rental.deposit_paid || 0
  const amountStillOwed = Math.max(0, total - depositPaid)
  const amountAfterCredit = Math.max(0, amountStillOwed - accountBalance)

  // Check if late (handle multiple field naming conventions)
  let endDateAware = rental.end_date || rental.expected_return_date || rental.rental_end_date || rental.due_back
  let isLate = false
  if (endDateAware) {
    try {
      const endDate = new Date(endDateAware)
      isLate = returnDate > endDate
    } catch {
      // ignore parse errors
    }
  }

  // Build cost structure info
  const costStructureInfo = {
    structure_id: costStructure.structure_id,
    name: costStructure.name,
    description: costStructure.description || 'No description available'
  }

  // Add battery-rental-specific fields
  if (rentalType === 'battery') {
    costStructureInfo.item_type = costStructure.item_type
    costStructureInfo.item_reference = costStructure.item_reference
    costStructureInfo.count_initial_checkout_as_recharge = costStructure.count_initial_checkout_as_recharge
  }

  const result = {
    rental_id: rentalId,
    cost_structure: costStructureInfo,
    calculation_steps: calculationSteps,
    duration: {
      start_date: startDate.toISOString(),
      return_date: returnDate.toISOString(),
      actual_hours: Math.round(actualHours * 100) / 100,
      actual_days: Math.round(actualDays * 100) / 100,
      scheduled_return_date: endDateAware || null,
      is_late: isLate
    },
    kwh_usage: {
      start_reading: null,
      end_reading: null,
      total_used: null
    },
    cost_breakdown: costBreakdown,
    subtotal: Math.round(subtotal * 100) / 100,
    vat_percentage: vatPercentage,
    vat_amount: Math.round(vatAmount * 100) / 100,
    total: Math.round(total * 100) / 100,
    original_estimate: 0,
    cost_difference: Math.round(total * 100) / 100,
    payment_status: {
      amount_paid_so_far: Math.round(depositPaid * 100) / 100,
      amount_still_owed: Math.round(amountStillOwed * 100) / 100,
      user_account_balance: Math.round(accountBalance * 100) / 100,
      amount_after_credit: Math.round(amountAfterCredit * 100) / 100,
      can_pay_with_credit: accountBalance >= amountStillOwed
    },
    subscription: null,
    _offlineEstimate: true
  }

  // Battery rentals include extra fields
  if (rentalType === 'battery') {
    result.rental_unique_id = rentalId
    result.usage_stats = {
      total_recharges: totalRecharges,
      battery_count: rental.items ? rental.items.length : 1
    }
  }

  return result
}
