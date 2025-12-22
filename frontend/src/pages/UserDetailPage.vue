<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" @click="$router.back()" class="q-mr-md" />
      <div class="text-h4 col">User Details</div>
      <q-btn
        color="primary"
        label="Edit User"
        icon="edit"
        @click="openEditUserDialog"
      />
    </div>

    <div v-if="loading" class="row justify-center q-mt-xl">
      <q-spinner color="primary" size="3em" />
    </div>

    <div v-else>
      <!-- User Info Card -->
      <q-card class="q-mb-md">
        <q-card-section>
          <div class="text-h6 q-mb-md">User Information</div>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">Name</div>
              <div class="text-body1">{{ user.Name || user.username || `User ${user.user_id}` }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">User ID</div>
              <div class="text-body1">{{ user.user_id }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">Mobile Number</div>
              <div class="text-body1">{{ user.mobile_number || 'N/A' }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">Email</div>
              <div class="text-body1">{{ user.email || 'N/A' }}</div>
            </div>
            <div class="col-12 col-md-6">
              <div class="text-caption text-grey-7">Role</div>
              <div class="text-body1">
                <q-chip :color="getRoleColor(user.role)" text-color="white" dense>
                  {{ user.role }}
                </q-chip>
              </div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Account Summary Card -->
      <q-card class="q-mb-md">
        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-h6">Account Summary</div>
            </div>
            <div class="col-auto">
              <q-btn
                color="primary"
                label="Add Credit"
                icon="add_card"
                @click="showAddCreditDialog = true"
                class="q-mr-sm"
              >
                <q-tooltip>Add prepaid credit for future rentals</q-tooltip>
              </q-btn>
              <q-btn
                v-if="account.total_owed > 0"
                color="orange"
                label="Settle Debt"
                icon="payments"
                @click="showPaymentDialog = true"
              >
                <q-tooltip>Record payment to settle existing charges</q-tooltip>
              </q-btn>
            </div>
          </div>

          <div class="row q-col-gutter-md">
            <!-- Account Credit (Prepaid Balance) -->
            <div class="col-12 col-md-4">
              <q-card flat bordered :class="account.balance > 0 ? 'bg-positive-1' : ''">
                <q-card-section>
                  <div class="row items-center">
                    <div class="col">
                      <div class="text-overline text-grey-7">Account Credit</div>
                      <div class="text-h4 text-positive">
                        {{ currencySymbol }}{{ Math.max(0, account.balance || 0).toFixed(2) }}
                      </div>
                      <div class="text-caption text-grey-6">Prepaid balance</div>
                    </div>
                    <div class="col-auto">
                      <q-icon name="account_balance_wallet" size="48px" :color="account.balance > 0 ? 'positive' : 'grey'" />
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <!-- Amount Owed (Debt) -->
            <div class="col-12 col-md-4">
              <q-card flat bordered :class="account.total_owed > 0 ? 'bg-negative-1' : ''">
                <q-card-section>
                  <div class="row items-center">
                    <div class="col">
                      <div class="text-overline text-grey-7">Amount Owed</div>
                      <div class="text-h4 text-negative">
                        {{ currencySymbol }}{{ account.total_owed?.toFixed(2) || '0.00' }}
                      </div>
                      <div class="text-caption text-grey-6">Unpaid charges</div>
                    </div>
                    <div class="col-auto">
                      <q-icon name="receipt_long" size="48px" :color="account.total_owed > 0 ? 'negative' : 'grey'" />
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <!-- Net Balance -->
            <div class="col-12 col-md-4">
              <q-card flat bordered :class="netBalance > 0 ? 'bg-positive-1' : netBalance < 0 ? 'bg-negative-1' : ''">
                <q-card-section>
                  <div class="row items-center">
                    <div class="col">
                      <div class="text-overline text-grey-7">Net Balance</div>
                      <div class="text-h4" :class="netBalance >= 0 ? 'text-positive' : 'text-negative'">
                        {{ netBalance >= 0 ? '' : '-' }}{{ currencySymbol }}{{ Math.abs(netBalance).toFixed(2) }}
                      </div>
                      <div class="text-caption" :class="netBalance >= 0 ? 'text-positive' : 'text-negative'">
                        {{ netBalance > 0 ? 'Credit available' : netBalance < 0 ? 'Payment due' : 'Account settled' }}
                      </div>
                    </div>
                    <div class="col-auto">
                      <q-icon name="account_balance" size="48px" :color="netBalance >= 0 ? 'positive' : 'negative'" />
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>

          <!-- Total Spent (Lifetime) - Secondary Metric -->
          <div class="row q-mt-sm">
            <div class="col-12">
              <q-card flat bordered>
                <q-card-section class="q-pa-sm">
                  <div class="row items-center">
                    <div class="col">
                      <div class="text-caption text-grey-7">Total Lifetime Spending</div>
                    </div>
                    <div class="col-auto">
                      <div class="text-body2 text-weight-medium">
                        {{ currencySymbol }}{{ account.total_spent?.toFixed(2) || '0.00' }}
                      </div>
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Subscriptions Card -->
      <q-card class="q-mb-md">
        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-h6">Subscriptions</div>
            </div>
            <div class="col-auto">
              <q-btn
                color="primary"
                label="Assign Subscription"
                icon="add"
                @click="openAssignSubscriptionDialog"
              />
            </div>
          </div>

          <div v-if="subscriptionsLoading" class="row justify-center q-pa-md">
            <q-spinner color="primary" size="2em" />
          </div>

          <div v-else-if="userSubscriptions.length === 0" class="text-grey-7 q-pa-md text-center">
            <q-icon name="subscriptions" size="48px" class="q-mb-sm" />
            <div>No active subscriptions</div>
          </div>

          <q-list v-else bordered separator>
            <q-item v-for="sub in userSubscriptions" :key="sub.subscription_id">
              <q-item-section>
                <q-item-label>{{ sub.package_name }}</q-item-label>
                <q-item-label caption>
                  {{ sub.description }}
                </q-item-label>
                <q-item-label caption class="q-mt-xs">
                  <q-chip dense size="sm" :color="getSubscriptionStatusColor(sub.status)" text-color="white">
                    {{ sub.status }}
                  </q-chip>
                  <span class="q-ml-sm">
                    Billing: {{ sub.billing_period }} | Next: {{ formatDate(sub.next_billing_date) }}
                  </span>
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="text-h6 text-primary">{{ currencySymbol }}{{ sub.price?.toFixed(2) }}</div>
                <div class="text-caption text-grey-7">per {{ sub.billing_period }}</div>
              </q-item-section>
              <q-item-section side>
                <div class="row q-gutter-xs">
                  <q-btn
                    flat
                    dense
                    round
                    icon="edit"
                    color="primary"
                    @click="editSubscription(sub)"
                  >
                    <q-tooltip>Edit Subscription</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    round
                    icon="pause"
                    color="warning"
                    @click="pauseSubscription(sub)"
                    v-if="sub.status === 'active'"
                  >
                    <q-tooltip>Pause Subscription</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    round
                    icon="play_arrow"
                    color="positive"
                    @click="resumeSubscription(sub)"
                    v-if="sub.status === 'paused'"
                  >
                    <q-tooltip>Resume Subscription</q-tooltip>
                  </q-btn>
                  <q-btn
                    flat
                    dense
                    round
                    icon="delete"
                    color="negative"
                    @click="cancelSubscription(sub)"
                  >
                    <q-tooltip>Cancel Subscription</q-tooltip>
                  </q-btn>
                </div>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>

      <!-- Current Rentals -->
      <q-card class="q-mb-md">
        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-h6">Current Rentals</div>
            </div>
            <div class="col-auto">
              <q-btn flat label="Refresh" icon="refresh" @click="loadCurrentRentals" />
            </div>
          </div>

          <div v-if="rentalsLoading" class="row justify-center q-pa-md">
            <q-spinner color="primary" size="2em" />
          </div>

          <div v-else-if="currentRentals.length === 0" class="text-grey-7 q-pa-md text-center">
            <q-icon name="inbox" size="48px" class="q-mb-sm" />
            <div>No active rentals</div>
          </div>

          <q-list v-else bordered separator>
            <q-item v-for="rental in currentRentals" :key="rental.rentral_id" class="q-pa-md">
              <q-item-section>
                <q-item-label class="text-weight-medium">
                  Rental #{{ rental.rentral_id }}
                  <q-chip dense size="sm" color="positive" text-color="white" class="q-ml-sm">
                    {{ rental.status }}
                  </q-chip>
                </q-item-label>
                <q-item-label caption class="q-mt-sm">
                  <div class="row q-col-gutter-md">
                    <div class="col-12 col-md-6">
                      <div><strong>Battery:</strong> {{ rental.battery_model || `Battery ID ${rental.battery_id}` }}</div>
                      <div v-if="rental.pue_items && rental.pue_items.length > 0">
                        <strong>PUE Items:</strong>
                        <q-chip v-for="pue in rental.pue_items" :key="pue.pue_id" dense size="sm" class="q-ml-xs">
                          {{ pue.name || `PUE ${pue.pue_id}` }}
                        </q-chip>
                      </div>
                      <div v-if="rental.total_cost">
                        <strong>Total Cost:</strong> {{ currencySymbol }}{{ rental.total_cost.toFixed(2) }}
                      </div>
                    </div>
                    <div class="col-12 col-md-6">
                      <div><strong>Rental Start:</strong> {{ formatTimestamp(rental.timestamp_taken) }}</div>
                      <div><strong>Due Back:</strong> {{ formatTimestamp(rental.due_back) }}</div>
                      <div v-if="rental.payment_status">
                        <strong>Payment:</strong>
                        <q-chip dense size="sm" :color="getPaymentStatusColor(rental.payment_status)">
                          {{ rental.payment_status }}
                        </q-chip>
                      </div>
                    </div>
                  </div>
                </q-item-label>
              </q-item-section>

              <q-item-section side>
                <div class="column q-gutter-sm">
                  <q-btn
                    color="primary"
                    label="Return"
                    icon="assignment_return"
                    dense
                    @click="openReturnDialog(rental)"
                  />
                  <q-btn
                    color="orange"
                    label="Extend"
                    icon="schedule"
                    dense
                    @click="openExtendDialog(rental)"
                  />
                  <q-btn
                    flat
                    dense
                    color="info"
                    label="Details"
                    icon="info"
                    @click="router.push(`/rentals/${rental.rentral_id}`)"
                  />
                </div>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>

      <!-- Transaction History -->
      <q-card>
        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-h6">Transaction History</div>
            </div>
            <div class="col-auto">
              <q-btn flat label="Refresh" icon="refresh" @click="loadTransactions" />
              <q-btn flat label="Export" icon="download" @click="exportTransactions" />
            </div>
          </div>

          <!-- Search Bar -->
          <q-input
            v-model="transactionSearch"
            outlined
            dense
            placeholder="Search transactions by description or type..."
            class="q-mb-md"
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
            <template v-slot:append>
              <q-icon v-if="transactionSearch" name="clear" class="cursor-pointer" @click="transactionSearch = ''" />
            </template>
          </q-input>
        </q-card-section>

        <q-card-section>
          <q-table
            :rows="filteredTransactions"
            :columns="transactionColumns"
            row-key="transaction_id"
            :loading="transactionsLoading"
            :rows-per-page-options="[10, 25, 50, 100]"
            :pagination="pagination"
          >
            <template v-slot:body-cell-timestamp="props">
              <q-td :props="props">
                {{ formatTimestamp(props.row.timestamp) }}
              </q-td>
            </template>

            <template v-slot:body-cell-transaction_type="props">
              <q-td :props="props">
                <q-chip
                  :color="props.row.transaction_type === 'charge' ? 'negative' : 'positive'"
                  text-color="white"
                  dense
                  size="sm"
                >
                  {{ props.row.transaction_type }}
                </q-chip>
              </q-td>
            </template>

            <template v-slot:body-cell-payment_type="props">
              <q-td :props="props">
                <q-badge v-if="props.row.payment_type" color="blue-grey" text-color="white">
                  {{ props.row.payment_type }}
                </q-badge>
                <span v-else class="text-grey-6">-</span>
              </q-td>
            </template>

            <template v-slot:body-cell-amount="props">
              <q-td :props="props">
                <span :class="props.row.transaction_type === 'charge' ? 'text-negative' : 'text-positive'">
                  {{ props.row.transaction_type === 'charge' ? '-' : '+' }}{{ currencySymbol }}{{ Math.abs(props.row.amount)?.toFixed(2) }}
                </span>
              </q-td>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </div>

    <!-- Settle Debt Dialog -->
    <q-dialog v-model="showPaymentDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Settle Debt</div>
          <div class="text-subtitle2">User: {{ user.Name || user.username || `User ${user.user_id}` }}</div>
        </q-card-section>

        <q-card-section>
          <!-- Current Debt Summary -->
          <q-banner class="bg-orange-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="info" color="orange" />
            </template>
            <div class="text-body2">
              <div class="text-weight-medium">Amount Owed: {{ currencySymbol }}{{ account.total_owed?.toFixed(2) }}</div>
            </div>
          </q-banner>

          <!-- Available Credit Option -->
          <div v-if="availableCredit > 0" class="q-mb-md">
            <q-card flat bordered class="bg-positive-1">
              <q-card-section class="q-pa-md">
                <q-checkbox
                  v-model="useAvailableCredit"
                  label="Use available credit"
                  color="positive"
                />
                <div v-if="useAvailableCredit" class="q-mt-sm text-caption">
                  <div class="row justify-between">
                    <span>Available Credit:</span>
                    <span class="text-weight-medium">{{ currencySymbol }}{{ availableCredit.toFixed(2) }}</span>
                  </div>
                  <div class="row justify-between">
                    <span>Credit Applied:</span>
                    <span class="text-weight-medium">-{{ currencySymbol }}{{ creditToApply.toFixed(2) }}</span>
                  </div>
                  <q-separator class="q-my-xs" />
                  <div class="row justify-between text-weight-bold">
                    <span>Remaining to Pay:</span>
                    <span>{{ currencySymbol }}{{ remainingAfterCredit.toFixed(2) }}</span>
                  </div>
                </div>
              </q-card-section>
            </q-card>
          </div>

          <!-- Payment Amount Input -->
          <q-input
            v-model.number="paymentAmount"
            type="number"
            :label="useAvailableCredit ? 'Additional Payment Amount' : 'Payment Amount'"
            :prefix="currencySymbol"
            step="0.01"
            outlined
            :rules="[val => val >= 0 || 'Must be greater than or equal to 0']"
            :hint="paymentOverage > 0 ? `Overpayment of ${currencySymbol}${paymentOverage.toFixed(2)} will be added as credit` : useAvailableCredit ? `To settle: ${currencySymbol}${remainingAfterCredit.toFixed(2)}` : `To settle: ${currencySymbol}${account.total_owed?.toFixed(2)}`"
          />

          <div class="row q-gutter-sm q-mt-xs">
            <q-btn
              flat
              dense
              color="primary"
              label="Pay Exact Amount"
              size="sm"
              @click="paymentAmount = remainingAfterCredit"
            >
              <q-tooltip>Pay exactly what's needed ({{ currencySymbol }}{{ remainingAfterCredit.toFixed(2) }})</q-tooltip>
            </q-btn>
            <q-btn
              v-if="!useAvailableCredit"
              flat
              dense
              color="positive"
              label="Pay + Add Extra Credit"
              size="sm"
              @click="showOverpaymentInput = true"
            >
              <q-tooltip>Pay debt and add extra credit</q-tooltip>
            </q-btn>
          </div>

          <!-- Overpayment Warning/Info -->
          <q-banner v-if="paymentOverage > 0" dense class="bg-positive-1 q-mt-md">
            <template v-slot:avatar>
              <q-icon name="info" color="positive" />
            </template>
            <div class="text-body2">
              <strong>Overpayment:</strong> {{ currencySymbol }}{{ paymentOverage.toFixed(2) }} will be added to account credit
            </div>
          </q-banner>

          <!-- Payment Summary -->
          <q-card flat bordered class="q-mt-md bg-grey-2">
            <q-card-section class="q-pa-sm">
              <div class="text-caption text-weight-medium">Payment Breakdown</div>
              <div class="text-caption q-mt-xs">
                <div v-if="useAvailableCredit && creditToApply > 0" class="row justify-between">
                  <span>Credit Applied:</span>
                  <span>{{ currencySymbol }}{{ creditToApply.toFixed(2) }}</span>
                </div>
                <div class="row justify-between">
                  <span>Cash/Payment Received:</span>
                  <span>{{ currencySymbol }}{{ (paymentAmount || 0).toFixed(2) }}</span>
                </div>
                <q-separator class="q-my-xs" />
                <div class="row justify-between text-weight-bold">
                  <span>Total Payment:</span>
                  <span>{{ currencySymbol }}{{ totalPayment.toFixed(2) }}</span>
                </div>
                <q-separator class="q-my-sm" />
                <div class="row justify-between text-orange">
                  <span>Applied to Debt:</span>
                  <span>-{{ currencySymbol }}{{ amountTowardsDebt.toFixed(2) }}</span>
                </div>
                <div v-if="paymentOverage > 0" class="row justify-between text-positive">
                  <span>Added to Credit:</span>
                  <span>+{{ currencySymbol }}{{ paymentOverage.toFixed(2) }}</span>
                </div>
              </div>
            </q-card-section>
          </q-card>

          <!-- Payment Method Selection -->
          <q-select
            v-model="settlementPaymentType"
            :options="paymentTypeOptions"
            label="Payment Method"
            outlined
            class="q-mt-md"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            :rules="[val => !!val || 'Payment method is required']"
          >
            <template v-slot:prepend>
              <q-icon name="payment" />
            </template>
          </q-select>

          <q-input
            v-model="paymentDescription"
            label="Description / Reference Number"
            outlined
            class="q-mt-md"
            hint="Optional note or transaction reference"
          />

          <!-- Confirmation -->
          <q-separator class="q-mt-md" />
          <div v-if="settlementPaymentType && paymentAmount > 0" class="bg-orange-1 q-pa-md rounded-borders q-mt-md">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="warning" color="orange" class="q-mr-sm" />
              Payment Confirmation Required
            </div>
            <q-checkbox
              v-model="confirmPaymentReceived"
              :label="`I confirm that ${settlementPaymentType} payment of ${currencySymbol}${(paymentAmount || 0).toFixed(2)} has been received`"
              color="positive"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            :label="paymentOverage > 0 ? 'Settle Debt & Add Credit' : 'Record Payment'"
            color="orange"
            @click="submitPayment"
            :disable="totalPayment <= 0 || (paymentAmount > 0 && (!settlementPaymentType || !confirmPaymentReceived))"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Credit Dialog -->
    <q-dialog v-model="showAddCreditDialog">
      <q-card style="min-width: 450px">
        <q-card-section>
          <div class="text-h6">Add Prepaid Credit</div>
          <div class="text-subtitle2">User: {{ user.Name || user.username || `User ${user.user_id}` }}</div>
        </q-card-section>

        <q-card-section>
          <!-- Current Credit Summary -->
          <q-banner class="bg-blue-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="account_balance_wallet" color="primary" />
            </template>
            <div class="text-body2">
              <div class="text-weight-medium">Current Prepaid Credit: {{ currencySymbol }}{{ Math.max(0, account.balance || 0).toFixed(2) }}</div>
              <div class="text-caption">This credit can be used for future rentals</div>
            </div>
          </q-banner>
          <q-input
            v-model.number="creditAmount"
            type="number"
            label="Credit Amount"
            :prefix="currencySymbol"
            step="0.01"
            outlined
            :rules="[val => val > 0 || 'Must be greater than 0']"
          />
          <q-input
            v-model="creditDescription"
            label="Description"
            type="textarea"
            outlined
            rows="2"
            hint="Optional note about the credit"
          />

          <q-select
            v-model="creditPaymentType"
            :options="paymentTypeOptions"
            label="Payment Type"
            outlined
            option-value="value"
            option-label="label"
            emit-value
            map-options
            :rules="[val => !!val || 'Payment type is required']"
          >
            <template v-slot:prepend>
              <q-icon name="payment" />
            </template>
          </q-select>

          <q-separator />

          <div v-if="creditPaymentType" class="bg-orange-1 q-pa-md rounded-borders">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="warning" color="orange" class="q-mr-sm" />
              Payment Confirmation Required
            </div>
            <q-checkbox
              v-model="confirmCashPayment"
              :label="`I confirm that ${creditPaymentType} payment has been received`"
              color="positive"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Add Credit"
            color="primary"
            @click="submitAddCredit"
            :disable="!confirmCashPayment || !creditAmount || creditAmount <= 0"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Assign Subscription Dialog -->
    <q-dialog v-model="showAssignSubscriptionDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Assign Subscription</div>
        </q-card-section>

        <q-card-section>
          <q-select
            v-model="selectedSubscriptionPackage"
            :options="filteredSubscriptionPackages"
            option-value="package_id"
            option-label="package_name"
            emit-value
            map-options
            label="Subscription Package"
            outlined
            use-input
            input-debounce="300"
            @filter="filterSubscriptionPackages"
            :rules="[val => !!val || 'Subscription package is required']"
            @update:model-value="onSubscriptionPackageSelect"
          >
            <template v-slot:prepend>
              <q-icon name="subscriptions" />
            </template>
            <template v-slot:append>
              <q-icon name="search" />
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.package_name }}</q-item-label>
                  <q-item-label caption>
                    {{ currencySymbol }}{{ scope.opt.price?.toFixed(2) }} per {{ scope.opt.billing_period }}
                  </q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No packages match your search
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <div v-if="selectedSubscriptionDetails" class="q-mt-md">
            <q-card flat bordered>
              <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Package Details</div>
                <div class="text-caption text-grey-7 q-mb-md">
                  <div><strong>Billing:</strong> {{ selectedSubscriptionDetails.billing_period }}</div>
                  <div><strong>Price:</strong> {{ currencySymbol }}{{ selectedSubscriptionDetails.price?.toFixed(2) }}</div>
                  <div v-if="selectedSubscriptionDetails.included_kwh">
                    <strong>Included kWh:</strong> {{ selectedSubscriptionDetails.included_kwh }} kWh
                    <span v-if="selectedSubscriptionDetails.overage_rate_kwh">
                      (Overage: {{ currencySymbol }}{{ selectedSubscriptionDetails.overage_rate_kwh }}/kWh)
                    </span>
                  </div>
                  <div v-else>
                    <strong>Included kWh:</strong> Unlimited
                  </div>
                  <div v-if="selectedSubscriptionDetails.max_concurrent_batteries">
                    <strong>Max Concurrent Batteries:</strong> {{ selectedSubscriptionDetails.max_concurrent_batteries }}
                  </div>
                  <div v-if="selectedSubscriptionDetails.max_concurrent_pue">
                    <strong>Max Concurrent PUE:</strong> {{ selectedSubscriptionDetails.max_concurrent_pue }}
                  </div>
                </div>

                <!-- Included Items -->
                <div v-if="selectedSubscriptionDetails.items && selectedSubscriptionDetails.items.length > 0">
                  <q-separator class="q-mb-sm" />
                  <div class="text-subtitle2 q-mb-sm">Included Items</div>
                  <q-list dense>
                    <q-item v-for="(item, idx) in selectedSubscriptionDetails.items" :key="idx" class="q-px-none">
                      <q-item-section avatar>
                        <q-icon :name="item.item_type.includes('battery') ? 'battery_charging_full' : 'devices'" color="primary" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-weight-medium">{{ getItemTypeLabel(item.item_type) }}</q-item-label>
                        <q-item-label caption>
                          {{ getItemReferenceDisplay(item) }}
                          <span v-if="item.quantity_limit"> • Limit: {{ item.quantity_limit }} {{ item.quantity_limit === 1 ? 'unit' : 'units' }}</span>
                        </q-item-label>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </div>
              </q-card-section>
            </q-card>
          </div>

          <q-input
            v-model="subscriptionStartDate"
            type="date"
            label="Start Date"
            outlined
            class="q-mt-md"
            :rules="[val => !!val || 'Start date is required']"
          >
            <template v-slot:prepend>
              <q-icon name="event" />
            </template>
          </q-input>

          <q-toggle
            v-model="subscriptionAutoRenew"
            label="Auto-renew subscription"
            color="primary"
            class="q-mt-md"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Assign Subscription"
            color="primary"
            @click="submitAssignSubscription"
            :disable="!selectedSubscriptionPackage || !subscriptionStartDate"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Edit User Dialog -->
    <q-dialog v-model="showEditUserDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Edit User</div>
          <div class="text-subtitle2">User ID: {{ user.user_id }}</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model="editUserForm.Name"
            label="Name"
            outlined
            :rules="[val => !!val || 'Name is required']"
          />
          <q-input
            v-model="editUserForm.username"
            label="Username"
            outlined
            :rules="[val => !!val || 'Username is required']"
          />
          <q-input
            v-model="editUserForm.mobile_number"
            label="Mobile Number"
            outlined
          />
          <q-input
            v-model="editUserForm.email"
            label="Email"
            type="email"
            outlined
          />
          <q-input
            v-model="editUserForm.address"
            label="Address"
            type="textarea"
            outlined
            rows="2"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Save Changes" color="primary" @click="submitEditUser" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Return Rental Dialog -->
    <q-dialog v-model="showReturnDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Return Rental</div>
          <div class="text-subtitle2">Rental #{{ selectedRental?.rentral_id }}</div>
        </q-card-section>

        <q-card-section>
          <q-banner class="bg-blue-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            <div class="text-body2">
              <div><strong>Battery:</strong> {{ selectedRental?.battery_model || `Battery ID ${selectedRental?.battery_id}` }}</div>
              <div><strong>Due Back:</strong> {{ formatTimestamp(selectedRental?.due_back) }}</div>
            </div>
          </q-banner>

          <q-select
            v-model="returnCondition"
            :options="['good', 'fair', 'poor', 'damaged']"
            label="Battery Condition"
            outlined
            :rules="[val => !!val || 'Condition is required']"
          >
            <template v-slot:prepend>
              <q-icon name="battery_std" />
            </template>
          </q-select>

          <q-input
            v-model="returnNotes"
            label="Return Notes"
            type="textarea"
            outlined
            rows="3"
            class="q-mt-md"
            hint="Optional notes about the condition or any issues"
          />

          <div v-if="selectedRental?.deposit_amount && selectedRental?.deposit_amount > 0 && !selectedRental?.deposit_returned" class="q-mt-md">
            <q-separator class="q-mb-md" />
            <q-checkbox
              v-model="returnDeposit"
              :label="`Return deposit of ${currencySymbol}${selectedRental?.deposit_amount.toFixed(2)} to user`"
              color="positive"
            />
            <div class="text-caption text-grey-7 q-ml-lg">
              Deposit will be added to user's account credit
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Return Rental"
            color="primary"
            icon="assignment_return"
            @click="submitReturnRental"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Extend Rental Dialog -->
    <q-dialog v-model="showExtendDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Extend Rental</div>
          <div class="text-subtitle2">Rental #{{ selectedRental?.rentral_id }}</div>
        </q-card-section>

        <q-card-section>
          <q-banner class="bg-blue-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            <div class="text-body2">
              <div><strong>Current Due Date:</strong> {{ formatTimestamp(selectedRental?.due_back) }}</div>
              <div><strong>Battery:</strong> {{ selectedRental?.battery_model || `Battery ID ${selectedRental?.battery_id}` }}</div>
            </div>
          </q-banner>

          <q-input
            v-model="extendNewDate"
            type="datetime-local"
            label="New Due Date"
            outlined
            :rules="[val => !!val || 'New due date is required']"
          >
            <template v-slot:prepend>
              <q-icon name="event" />
            </template>
          </q-input>

          <q-separator class="q-my-md" />

          <div class="text-subtitle2 q-mb-md">Extension Payment (Optional)</div>

          <q-input
            v-model.number="extendPaymentAmount"
            type="number"
            label="Payment Amount"
            :prefix="currencySymbol"
            step="0.01"
            outlined
            hint="Enter additional payment for extension"
          />

          <q-select
            v-if="extendPaymentAmount > 0"
            v-model="extendPaymentType"
            :options="paymentTypeOptions"
            label="Payment Method"
            outlined
            class="q-mt-md"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            :rules="[val => !!val || 'Payment method is required']"
          >
            <template v-slot:prepend>
              <q-icon name="payment" />
            </template>
          </q-select>

          <div v-if="extendPaymentAmount > 0 && extendPaymentType" class="bg-orange-1 q-pa-md rounded-borders q-mt-md">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="warning" color="orange" class="q-mr-sm" />
              Payment Confirmation Required
            </div>
            <q-checkbox
              v-model="confirmExtendPayment"
              :label="`I confirm that ${extendPaymentType} payment of ${currencySymbol}${extendPaymentAmount.toFixed(2)} has been received`"
              color="positive"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Extend Rental"
            color="orange"
            icon="schedule"
            @click="submitExtendRental"
            :disable="!extendNewDate || (extendPaymentAmount > 0 && (!extendPaymentType || !confirmExtendPayment))"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { usersAPI, accountsAPI, settingsAPI, subscriptionsAPI, rentalsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const authStore = useAuthStore()
const hubSettingsStore = useHubSettingsStore()

const userId = ref(route.params.id)
const loading = ref(false)
const transactionsLoading = ref(false)
const user = ref({})
const account = ref({
  balance: 0,
  total_spent: 0,
  total_owed: 0
})
const transactions = ref([])
const transactionSearch = ref('')
const pagination = ref({
  sortBy: 'timestamp',
  descending: true,
  page: 1,
  rowsPerPage: 25
})

// Use centralized hub settings store for currency
const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

// Net balance = credit (positive balance) - debt (amount owed)
const netBalance = computed(() => {
  const credit = Math.max(0, account.value.balance || 0)
  const owed = account.value.total_owed || 0
  return credit - owed
})

// Payment dialog
const showPaymentDialog = ref(false)
const paymentAmount = ref(0)
const paymentDescription = ref('')
const useAvailableCredit = ref(false)
const settlementPaymentType = ref(null)
const confirmPaymentReceived = ref(false)

// Payment computed properties (rounded to 2 decimal places)
const availableCredit = computed(() => Math.round(Math.max(0, account.value.balance || 0) * 100) / 100)
const creditToApply = computed(() => {
  if (!useAvailableCredit.value) return 0
  return Math.round(Math.min(availableCredit.value, account.value.total_owed || 0) * 100) / 100
})
const remainingAfterCredit = computed(() => {
  return Math.round(Math.max(0, (account.value.total_owed || 0) - creditToApply.value) * 100) / 100
})
const totalPayment = computed(() => {
  return Math.round((creditToApply.value + (paymentAmount.value || 0)) * 100) / 100
})
const paymentOverage = computed(() => {
  const debt = Math.round((account.value.total_owed || 0) * 100) / 100
  const total = totalPayment.value
  return Math.round(Math.max(0, total - debt) * 100) / 100
})
const amountTowardsDebt = computed(() => {
  const debt = Math.round((account.value.total_owed || 0) * 100) / 100
  return Math.round(Math.min(totalPayment.value, debt) * 100) / 100
})

// Add Credit dialog
const showAddCreditDialog = ref(false)
const creditAmount = ref(0)
const creditDescription = ref('')
const creditPaymentType = ref(null)
const confirmCashPayment = ref(false)

// Edit User dialog
const showEditUserDialog = ref(false)
const editUserForm = ref({
  Name: '',
  username: '',
  mobile_number: '',
  email: '',
  address: ''
})

// Subscriptions
const userSubscriptions = ref([])
const subscriptionsLoading = ref(false)
const showAssignSubscriptionDialog = ref(false)
const availableSubscriptionPackages = ref([])
const filteredSubscriptionPackages = ref([])
const selectedSubscriptionPackage = ref(null)
const subscriptionStartDate = ref(new Date().toISOString().split('T')[0])
const subscriptionAutoRenew = ref(true)

const selectedSubscriptionDetails = computed(() => {
  if (!selectedSubscriptionPackage.value) return null
  return availableSubscriptionPackages.value.find(p => p.package_id === selectedSubscriptionPackage.value)
})

// Current Rentals
const currentRentals = ref([])
const rentalsLoading = ref(false)
const showReturnDialog = ref(false)
const showExtendDialog = ref(false)
const selectedRental = ref(null)
const returnCondition = ref('good')
const returnNotes = ref('')
const returnDeposit = ref(false)
const extendNewDate = ref(null)
const extendPaymentAmount = ref(0)
const extendPaymentType = ref(null)
const confirmExtendPayment = ref(false)

// Payment types
const paymentTypeOptions = ref([])

const transactionColumns = [
  { name: 'timestamp', label: 'Date', field: 'timestamp', align: 'left', sortable: true },
  { name: 'transaction_type', label: 'Type', field: 'transaction_type', align: 'center', sortable: true },
  { name: 'payment_type', label: 'Method', field: 'payment_type', align: 'center', sortable: true },
  { name: 'amount', label: 'Amount', field: 'amount', align: 'right', sortable: true },
  { name: 'description', label: 'Description', field: 'description', align: 'left' }
]

const filteredTransactions = computed(() => {
  if (!transactionSearch.value) return transactions.value

  const search = transactionSearch.value.toLowerCase()
  return transactions.value.filter(t =>
    t.description?.toLowerCase().includes(search) ||
    t.transaction_type?.toLowerCase().includes(search)
  )
})

const getRoleColor = (role) => {
  switch (role?.toUpperCase()) {
    case 'SUPERADMIN': return 'red'
    case 'ADMIN': return 'orange'
    case 'USER': return 'blue'
    default: return 'grey'
  }
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString()
}

const loadUser = async () => {
  try {
    loading.value = true
    const response = await usersAPI.get(userId.value)
    user.value = response.data
  } catch (error) {
    console.error('Failed to load user:', error)
    $q.notify({ type: 'negative', message: 'Failed to load user details', position: 'top' })
  } finally {
    loading.value = false
  }
}

const loadAccount = async () => {
  try {
    const response = await accountsAPI.getUserAccount(userId.value)
    account.value = response.data
  } catch (error) {
    console.error('Failed to load account:', error)
    $q.notify({ type: 'negative', message: 'Failed to load account details', position: 'top' })
  }
}

const loadTransactions = async () => {
  try {
    transactionsLoading.value = true
    const response = await accountsAPI.getUserTransactions(userId.value)
    transactions.value = response.data.transactions || []

    // Sort by timestamp descending (newest first)
    transactions.value.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  } catch (error) {
    console.error('Failed to load transactions:', error)
    $q.notify({ type: 'negative', message: 'Failed to load transactions', position: 'top' })
  } finally {
    transactionsLoading.value = false
  }
}

const submitPayment = async () => {
  if (totalPayment.value <= 0) {
    $q.notify({
      type: 'warning',
      message: 'Total payment must be greater than 0',
      position: 'top'
    })
    return
  }

  // Validate payment method and confirmation for cash payments
  if (paymentAmount.value > 0 && !settlementPaymentType.value) {
    $q.notify({
      type: 'warning',
      message: 'Please select a payment method',
      position: 'top'
    })
    return
  }

  if (paymentAmount.value > 0 && !confirmPaymentReceived.value) {
    $q.notify({
      type: 'warning',
      message: 'Please confirm that payment has been received',
      position: 'top'
    })
    return
  }

  try {
    let paymentSummary = []

    // Apply credit if selected
    if (useAvailableCredit.value && creditToApply.value > 0) {
      await accountsAPI.createTransaction(userId.value, {
        transaction_type: 'payment',
        amount: creditToApply.value,
        description: `Credit applied to settle debt${paymentDescription.value ? ` - ${paymentDescription.value}` : ''}`,
        payment_type: 'credit_transfer'
      })
      paymentSummary.push(`Credit: ${currencySymbol.value}${creditToApply.value.toFixed(2)}`)
    }

    // Record cash/payment portion towards debt
    if (paymentAmount.value > 0 && amountTowardsDebt.value > creditToApply.value) {
      const debtPayment = amountTowardsDebt.value - creditToApply.value
      await accountsAPI.createTransaction(userId.value, {
        transaction_type: 'payment',
        amount: debtPayment,
        description: `${settlementPaymentType.value} payment to settle debt${paymentDescription.value ? ` - ${paymentDescription.value}` : ''}`,
        payment_type: settlementPaymentType.value
      })
      paymentSummary.push(`${settlementPaymentType.value}: ${currencySymbol.value}${debtPayment.toFixed(2)}`)
    }

    // Handle overpayment - add to credit
    if (paymentOverage.value > 0) {
      await accountsAPI.createTransaction(userId.value, {
        transaction_type: 'credit',
        amount: paymentOverage.value,
        description: `Overpayment credit from ${settlementPaymentType.value} payment${paymentDescription.value ? ` - ${paymentDescription.value}` : ''}`,
        payment_type: settlementPaymentType.value
      })
      paymentSummary.push(`Overpayment → Credit: ${currencySymbol.value}${paymentOverage.value.toFixed(2)}`)
    }

    const summaryText = paymentSummary.join(' + ')
    $q.notify({
      type: 'positive',
      message: paymentOverage.value > 0
        ? `Payment recorded: ${currencySymbol.value}${amountTowardsDebt.value.toFixed(2)} to debt, ${currencySymbol.value}${paymentOverage.value.toFixed(2)} to credit`
        : `Debt payment recorded: ${currencySymbol.value}${totalPayment.value.toFixed(2)}`,
      position: 'top',
      timeout: 5000
    })

    showPaymentDialog.value = false

    // Reset form
    paymentAmount.value = 0
    paymentDescription.value = ''
    useAvailableCredit.value = false
    settlementPaymentType.value = null
    confirmPaymentReceived.value = false

    // Reload data
    await loadAccount()
    await loadTransactions()
  } catch (error) {
    console.error('Failed to record payment:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to record payment',
      position: 'top'
    })
  }
}

const submitAddCredit = async () => {
  if (!creditPaymentType.value) {
    $q.notify({
      type: 'warning',
      message: 'Please select a payment type',
      position: 'top'
    })
    return
  }

  if (!confirmCashPayment.value) {
    $q.notify({
      type: 'warning',
      message: `Please confirm that ${creditPaymentType.value} payment has been received`,
      position: 'top'
    })
    return
  }

  if (creditAmount.value <= 0) {
    $q.notify({
      type: 'warning',
      message: 'Credit amount must be greater than 0',
      position: 'top'
    })
    return
  }

  try {
    await accountsAPI.createTransaction(userId.value, {
      transaction_type: 'credit',
      amount: creditAmount.value,
      description: creditDescription.value || 'Account credit added by admin',
      payment_type: creditPaymentType.value
    })

    $q.notify({
      type: 'positive',
      message: `Credit of ${currencySymbol.value}${creditAmount.value.toFixed(2)} added successfully`,
      position: 'top'
    })
    showAddCreditDialog.value = false

    // Reset form
    creditAmount.value = 0
    creditDescription.value = ''
    creditPaymentType.value = null
    confirmCashPayment.value = false

    // Reload data
    await loadAccount()
    await loadTransactions()
  } catch (error) {
    console.error('Failed to add credit:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to add credit',
      position: 'top'
    })
  }
}

// Subscription functions
const loadUserSubscriptions = async () => {
  try {
    subscriptionsLoading.value = true
    const response = await subscriptionsAPI.getUserSubscriptions(userId.value)
    userSubscriptions.value = response.data.subscriptions || []
  } catch (error) {
    console.error('Failed to load subscriptions:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load subscriptions',
      position: 'top'
    })
  } finally {
    subscriptionsLoading.value = false
  }
}

const loadSubscriptionPackages = async () => {
  if (!user.value || !user.value.hub_id) {
    console.warn('Cannot load subscription packages: user or hub_id not available')
    return
  }

  try {
    const response = await settingsAPI.getSubscriptionPackages(user.value.hub_id, false)
    availableSubscriptionPackages.value = response.data.packages || []
    filteredSubscriptionPackages.value = availableSubscriptionPackages.value
    console.log('Loaded subscription packages:', availableSubscriptionPackages.value)
  } catch (error) {
    console.error('Failed to load subscription packages:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load subscription packages',
      position: 'top'
    })
  }
}

const filterSubscriptionPackages = (val, update) => {
  update(() => {
    if (val === '') {
      filteredSubscriptionPackages.value = availableSubscriptionPackages.value
    } else {
      const needle = val.toLowerCase()
      filteredSubscriptionPackages.value = availableSubscriptionPackages.value.filter(p =>
        p.package_name.toLowerCase().includes(needle) ||
        (p.description && p.description.toLowerCase().includes(needle)) ||
        p.billing_period.toLowerCase().includes(needle) ||
        String(p.price).includes(needle)
      )
    }
  })
}

const openAssignSubscriptionDialog = async () => {
  // Reload packages when opening dialog
  await loadSubscriptionPackages()
  showAssignSubscriptionDialog.value = true
}

const onSubscriptionPackageSelect = () => {
  // selectedSubscriptionDetails is computed, no action needed
}

const getSubscriptionStatusColor = (status) => {
  const colors = {
    active: 'positive',
    paused: 'warning',
    cancelled: 'negative',
    expired: 'grey'
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString()
}

const getPaymentStatusColor = (status) => {
  const colors = {
    'paid': 'positive',
    'partial': 'orange',
    'unpaid': 'negative',
    'deposit_only': 'blue',
    'pending_kwh': 'orange'
  }
  return colors[status] || 'grey'
}

const getItemTypeLabel = (itemType) => {
  const labels = {
    'battery': 'All Batteries',
    'battery_capacity': 'Battery Capacity',
    'battery_item': 'Specific Battery',
    'pue': 'All PUE Items',
    'pue_type': 'PUE Type',
    'pue_item': 'Specific PUE Item'
  }
  return labels[itemType] || itemType
}

const getItemReferenceDisplay = (item) => {
  if (item.item_reference === 'all') {
    return 'All items'
  }
  if (item.item_type === 'battery_capacity') {
    return `${item.item_reference} Wh capacity`
  }
  if (item.item_type === 'battery_item') {
    return `Battery ID: ${item.item_reference}`
  }
  if (item.item_type === 'pue_item') {
    return `PUE ID: ${item.item_reference}`
  }
  if (item.item_type === 'pue_type') {
    return item.item_reference
  }
  return item.item_reference
}

const submitAssignSubscription = async () => {
  try {
    await subscriptionsAPI.assignSubscription(userId.value, {
      package_id: selectedSubscriptionPackage.value,
      start_date: subscriptionStartDate.value,
      auto_renew: subscriptionAutoRenew.value,
      status: 'active'
    })

    $q.notify({
      type: 'positive',
      message: 'Subscription assigned successfully',
      position: 'top'
    })

    showAssignSubscriptionDialog.value = false

    // Reset form
    selectedSubscriptionPackage.value = null
    subscriptionStartDate.value = new Date().toISOString().split('T')[0]
    subscriptionAutoRenew.value = true

    // Reload subscriptions
    await loadUserSubscriptions()
  } catch (error) {
    console.error('Failed to assign subscription:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to assign subscription',
      position: 'top'
    })
  }
}

const editSubscription = (subscription) => {
  $q.notify({
    type: 'info',
    message: 'Edit subscription functionality coming soon',
    position: 'top'
  })
}

const pauseSubscription = async (subscription) => {
  try {
    await subscriptionsAPI.updateUserSubscription(userId.value, subscription.subscription_id, {
      status: 'paused'
    })

    $q.notify({
      type: 'positive',
      message: 'Subscription paused successfully',
      position: 'top'
    })

    await loadUserSubscriptions()
  } catch (error) {
    console.error('Failed to pause subscription:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to pause subscription',
      position: 'top'
    })
  }
}

const resumeSubscription = async (subscription) => {
  try {
    await subscriptionsAPI.updateUserSubscription(userId.value, subscription.subscription_id, {
      status: 'active'
    })

    $q.notify({
      type: 'positive',
      message: 'Subscription resumed successfully',
      position: 'top'
    })

    await loadUserSubscriptions()
  } catch (error) {
    console.error('Failed to resume subscription:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to resume subscription',
      position: 'top'
    })
  }
}

const cancelSubscription = async (subscription) => {
  $q.dialog({
    title: 'Confirm Cancellation',
    message: `Are you sure you want to cancel "${subscription.package_name}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await subscriptionsAPI.cancelUserSubscription(userId.value, subscription.subscription_id)

      $q.notify({
        type: 'positive',
        message: 'Subscription cancelled successfully',
        position: 'top'
      })

      await loadUserSubscriptions()
    } catch (error) {
      console.error('Failed to cancel subscription:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to cancel subscription',
        position: 'top'
      })
    }
  })
}

const exportTransactions = () => {
  if (transactions.value.length === 0) {
    $q.notify({ type: 'warning', message: 'No transactions to export', position: 'top' })
    return
  }

  // Generate CSV
  const headers = ['Date', 'Type', 'Payment Method', 'Amount', 'Description']
  const rows = transactions.value.map(t => [
    formatTimestamp(t.timestamp),
    t.transaction_type,
    t.payment_type || 'N/A',
    t.amount.toFixed(2),
    t.description || ''
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  // Download file
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `user_${userId.value}_transactions_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)

  $q.notify({ type: 'positive', message: 'Transactions exported successfully', position: 'top' })
}

// Edit User functions
const openEditUserDialog = () => {
  editUserForm.value = {
    Name: user.value.Name || '',
    username: user.value.username || '',
    mobile_number: user.value.mobile_number || '',
    email: user.value.email || '',
    address: user.value.address || ''
  }
  showEditUserDialog.value = true
}

const submitEditUser = async () => {
  try {
    await usersAPI.update(userId.value, editUserForm.value)

    $q.notify({
      type: 'positive',
      message: 'User updated successfully',
      position: 'top'
    })

    showEditUserDialog.value = false

    // Reload user data
    await loadUser()
  } catch (error) {
    console.error('Failed to update user:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to update user',
      position: 'top'
    })
  }
}

const loadHubSettings = async () => {
  const hubId = user.value?.hub_id || authStore.user?.hub_id
  if (!hubId) return
  // Load hub settings into the store (includes currency)
  await hubSettingsStore.loadHubSettings(hubId)
}

const loadPaymentTypes = async () => {
  const hubId = user.value.hub_id || authStore.user?.hub_id
  if (!hubId) return

  try {
    const response = await settingsAPI.getPaymentTypes({ hub_id: hubId, is_active: true })
    paymentTypeOptions.value = response.data.payment_types.map(pt => ({
      label: pt.type_name,
      value: pt.type_name
    }))
  } catch (error) {
    console.error('Failed to load payment types:', error)
  }
}

// Rental actions
const openReturnDialog = (rental) => {
  selectedRental.value = rental
  returnCondition.value = 'good'
  returnNotes.value = ''
  returnDeposit.value = rental.deposit_amount && rental.deposit_amount > 0 && !rental.deposit_returned
  showReturnDialog.value = true
}

const openExtendDialog = (rental) => {
  selectedRental.value = rental
  extendNewDate.value = null
  extendPaymentAmount.value = 0
  extendPaymentType.value = null
  confirmExtendPayment.value = false
  showExtendDialog.value = true
}

const submitReturnRental = async () => {
  if (!selectedRental.value) return

  try {
    const returnData = {
      battery_return_condition: returnCondition.value,
      battery_return_notes: returnNotes.value,
      return_deposit: returnDeposit.value
    }

    await rentalsAPI.returnBattery(selectedRental.value.rentral_id, returnData)

    $q.notify({
      type: 'positive',
      message: 'Rental returned successfully',
      position: 'top'
    })

    showReturnDialog.value = false

    // Reload data
    await loadCurrentRentals()
    await loadAccount()
    await loadTransactions()
  } catch (error) {
    console.error('Failed to return rental:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return rental',
      position: 'top'
    })
  }
}

const submitExtendRental = async () => {
  if (!selectedRental.value || !extendNewDate.value) return

  if (extendPaymentAmount.value > 0 && !extendPaymentType.value) {
    $q.notify({
      type: 'warning',
      message: 'Please select a payment method',
      position: 'top'
    })
    return
  }

  if (extendPaymentAmount.value > 0 && !confirmExtendPayment.value) {
    $q.notify({
      type: 'warning',
      message: 'Please confirm that payment has been received',
      position: 'top'
    })
    return
  }

  try {
    await rentalsAPI.update(selectedRental.value.rentral_id, { due_back: extendNewDate.value })

    // If payment received, record it
    if (extendPaymentAmount.value > 0) {
      await accountsAPI.createTransaction(userId.value, {
        transaction_type: 'payment',
        amount: extendPaymentAmount.value,
        description: `Payment for rental extension - Rental #${selectedRental.value.rentral_id}`,
        payment_type: extendPaymentType.value
      })
    }

    $q.notify({
      type: 'positive',
      message: `Rental extended to ${formatDate(extendNewDate.value)}`,
      position: 'top'
    })

    showExtendDialog.value = false

    // Reload data
    await loadCurrentRentals()
    await loadAccount()
    await loadTransactions()
  } catch (error) {
    console.error('Failed to extend rental:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to extend rental',
      position: 'top'
    })
  }
}

// Load current rentals for this user
const loadCurrentRentals = async () => {
  try {
    rentalsLoading.value = true
    const response = await rentalsAPI.list({ user_id: userId.value, status: 'active' })
    currentRentals.value = response.data || []
  } catch (error) {
    console.error('Failed to load current rentals:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load current rentals',
      position: 'top'
    })
  } finally {
    rentalsLoading.value = false
  }
}

onMounted(async () => {
  loadHubSettings()
  await loadUser()
  loadPaymentTypes()
  loadAccount()
  loadTransactions()
  loadUserSubscriptions()
  loadSubscriptionPackages()
  loadCurrentRentals()
})
</script>
