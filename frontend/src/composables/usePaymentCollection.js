import { ref, computed } from 'vue'
import { accountsAPI } from 'src/services/api'

/**
 * Composable for payment collection with credit support
 * Handles common payment logic across different pages/components
 */
export function usePaymentCollection() {
  // Payment form state
  const paymentAmount = ref(0)
  const creditApplied = ref(0)
  const paymentType = ref(null)
  const paymentNotes = ref('')
  const confirmPaymentReceived = ref(false)
  const userAccountBalance = ref(0)
  const userId = ref(null)

  // Computed properties
  const maxCreditAvailable = computed(() => {
    return userAccountBalance.value
  })

  const totalPayment = computed(() => {
    return (paymentAmount.value || 0) + (creditApplied.value || 0)
  })

  const remainingAfterPayment = computed(() => {
    return (amountOwed) => {
      return Math.round((amountOwed - totalPayment.value) * 100) / 100
    }
  })

  /**
   * Fetch user's account balance
   * @param {number} userIdValue - User ID
   * @returns {Promise<number>} Account balance
   */
  const fetchUserAccountBalance = async (userIdValue) => {
    try {
      userId.value = userIdValue
      if (!userIdValue) {
        userAccountBalance.value = 0
        return 0
      }

      const response = await accountsAPI.getUserAccount(userIdValue)
      const balance = response.data?.balance || 0
      userAccountBalance.value = balance
      return balance
    } catch (error) {
      console.error('Failed to fetch user account balance:', error)
      userAccountBalance.value = 0
      return 0
    }
  }

  /**
   * Validate credit amount
   * @param {number} amount - Credit amount to validate
   * @param {number} amountOwed - Total amount owed
   * @returns {Object} Validation result { valid: boolean, error: string }
   */
  const validateCreditAmount = (amount, amountOwed) => {
    if (amount < 0) {
      return { valid: false, error: 'Credit cannot be negative' }
    }
    if (amount > userAccountBalance.value) {
      return {
        valid: false,
        error: `Cannot exceed available credit (${userAccountBalance.value.toFixed(2)})`
      }
    }
    if (amount > amountOwed) {
      return { valid: false, error: 'Credit applied cannot exceed amount owed' }
    }
    return { valid: true }
  }

  /**
   * Initialize payment form with default values
   * @param {number} defaultAmount - Default payment amount
   * @param {string} defaultPaymentType - Default payment type
   */
  const initializePaymentForm = async (defaultAmount = 0, defaultPaymentType = 'cash', userIdValue = null) => {
    paymentAmount.value = defaultAmount
    paymentType.value = defaultPaymentType
    paymentNotes.value = ''
    confirmPaymentReceived.value = false
    creditApplied.value = 0

    // Fetch account balance if userId provided
    if (userIdValue) {
      await fetchUserAccountBalance(userIdValue)
    }
  }

  /**
   * Reset payment form
   */
  const resetPaymentForm = () => {
    paymentAmount.value = 0
    creditApplied.value = 0
    paymentType.value = null
    paymentNotes.value = ''
    confirmPaymentReceived.value = false
    userAccountBalance.value = 0
    userId.value = null
  }

  /**
   * Build payment data object for API call
   * @returns {Object} Payment data
   */
  const buildPaymentData = () => {
    return {
      payment_amount: paymentAmount.value,
      payment_type: paymentType.value,
      payment_notes: paymentNotes.value || null,
      credit_applied: creditApplied.value || 0
    }
  }

  /**
   * Format success message with credit details
   * @param {string} currencySymbol - Currency symbol
   * @param {string} additionalInfo - Additional info to append
   * @returns {string} Formatted message
   */
  const formatSuccessMessage = (currencySymbol, additionalInfo = '') => {
    const total = totalPayment.value
    let message = `Payment of ${currencySymbol}${total.toFixed(2)} recorded successfully`

    if (creditApplied.value > 0) {
      message += ` (including ${currencySymbol}${creditApplied.value.toFixed(2)} credit)`
    }

    if (additionalInfo) {
      message += ` ${additionalInfo}`
    }

    return message
  }

  return {
    // State
    paymentAmount,
    creditApplied,
    paymentType,
    paymentNotes,
    confirmPaymentReceived,
    userAccountBalance,
    userId,

    // Computed
    maxCreditAvailable,
    totalPayment,
    remainingAfterPayment,

    // Methods
    fetchUserAccountBalance,
    validateCreditAmount,
    initializePaymentForm,
    resetPaymentForm,
    buildPaymentData,
    formatSuccessMessage
  }
}
