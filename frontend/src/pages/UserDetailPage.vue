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
                color="positive"
                label="Take Payment"
                icon="payments"
                @click="openTakePaymentDialog"
              >
                <q-tooltip>Record a payment from this user</q-tooltip>
              </q-btn>
              <q-btn
                v-if="account.total_owed > 0"
                color="orange"
                label="Settle Debt"
                icon="account_balance"
                @click="showPaymentDialog = true"
                class="q-ml-sm"
              >
                <q-tooltip>Advanced: Settle debt with credit options</q-tooltip>
              </q-btn>
              <q-btn
                color="grey-7"
                label="Manual Adjustment"
                icon="edit"
                @click="showManualAdjustmentDialog = true"
                class="q-ml-sm"
                outline
              >
                <q-tooltip>Make a manual journal entry to adjust balance</q-tooltip>
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

      <!-- Rentals (Tabbed View) -->
      <q-card class="q-mb-md">
        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-h6">Rentals</div>
            </div>
            <div class="col-auto">
              <q-btn-dropdown color="primary" label="Create Rental" icon="add" class="q-mr-sm">
                <q-list>
                  <q-item clickable v-close-popup @click="router.push(`/rentals/battery/create?user_id=${userId}`)">
                    <q-item-section avatar>
                      <q-icon name="battery_charging_full" color="primary" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label>New Battery Rental</q-item-label>
                      <q-item-label caption>Rent batteries to this user</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item clickable v-close-popup @click="router.push(`/rentals/pue/create?user_id=${userId}`)">
                    <q-item-section avatar>
                      <q-icon name="devices_other" color="primary" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label>New PUE Rental</q-item-label>
                      <q-item-label caption>Rent productive use equipment</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-btn-dropdown>
              <q-btn flat label="Refresh" icon="refresh" @click="refreshAllRentals" />
            </div>
          </div>

          <q-tabs
            v-model="rentalTab"
            dense
            class="text-grey"
            active-color="primary"
            indicator-color="primary"
            align="left"
          >
            <q-tab name="battery" label="Active Battery Rentals" />
            <q-tab name="pue" label="Active PUE Rentals" />
            <q-tab name="battery-history" label="Battery History" />
            <q-tab name="pue-history" label="PUE History" />
          </q-tabs>

          <q-separator />

          <q-tab-panels v-model="rentalTab" animated>
            <!-- Battery Rentals Tab -->
            <q-tab-panel name="battery">
              <div v-if="batteryRentalsLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="batteryRentals.length === 0" class="text-grey-7 q-pa-md text-center">
                <q-icon name="battery_charging_full" size="48px" class="q-mb-sm" />
                <div>No active battery rentals</div>
                <q-btn
                  flat
                  color="primary"
                  label="Create Battery Rental"
                  icon="add"
                  @click="router.push(`/rentals/battery/create?user_id=${userId}`)"
                  class="q-mt-md"
                />
              </div>

              <q-list v-else bordered separator>
                <q-item v-for="rental in batteryRentals" :key="rental.rental_id" class="q-pa-md">
                  <q-item-section>
                    <q-item-label class="text-weight-medium">
                      Battery Rental #{{ rental.rental_id }}
                      <q-chip dense size="sm" color="positive" text-color="white" class="q-ml-sm">
                        Active
                      </q-chip>
                    </q-item-label>
                    <q-item-label caption class="q-mt-sm">
                      <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-6">
                          <div><strong>Batteries:</strong> {{ rental.battery_count || rental.items?.length || 0 }} item(s)</div>
                          <div v-if="rental.recharge_count !== undefined">
                            <strong>Recharges:</strong> {{ rental.recharge_count }}
                          </div>
                          <div v-if="rental.deposit_amount">
                            <strong>Deposit:</strong> {{ currencySymbol }}{{ rental.deposit_amount.toFixed(2) }}
                          </div>
                        </div>
                        <div class="col-12 col-md-6">
                          <div><strong>Start Date:</strong> {{ formatTimestamp(rental.rental_start_date) }}</div>
                          <div v-if="rental.due_date"><strong>Due Date:</strong> {{ formatTimestamp(rental.due_date) }}</div>
                          <div v-if="rental.cost_structure_name">
                            <strong>Cost Structure:</strong> {{ rental.cost_structure_name }}
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
                        @click="openReturnDialog(rental, 'battery')"
                      />
                      <q-btn
                        color="orange"
                        label="Recharge"
                        icon="bolt"
                        dense
                        @click="openRechargeDialog(rental)"
                      />
                      <q-btn
                        flat
                        dense
                        color="info"
                        label="Details"
                        icon="info"
                        @click="router.push(`/rentals/battery/${rental.rental_id}`)"
                      />
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-tab-panel>

            <!-- PUE Rentals Tab -->
            <q-tab-panel name="pue">
              <div v-if="pueRentalsLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="pueRentals.length === 0" class="text-grey-7 q-pa-md text-center">
                <q-icon name="devices_other" size="48px" class="q-mb-sm" />
                <div>No active PUE rentals</div>
                <q-btn
                  flat
                  color="primary"
                  label="Create PUE Rental"
                  icon="add"
                  @click="router.push(`/rentals/pue/create?user_id=${userId}`)"
                  class="q-mt-md"
                />
              </div>

              <q-list v-else bordered separator>
                <q-item v-for="rental in pueRentals" :key="rental.rental_id" class="q-pa-md">
                  <q-item-section>
                    <q-item-label class="text-weight-medium">
                      PUE Rental #{{ rental.rental_id }}
                      <q-chip dense size="sm" color="positive" text-color="white" class="q-ml-sm">
                        Active
                      </q-chip>
                      <q-chip
                        v-if="rental.is_pay_to_own"
                        dense
                        size="sm"
                        color="purple"
                        text-color="white"
                        class="q-ml-sm"
                      >
                        Pay-to-Own
                      </q-chip>
                    </q-item-label>
                    <q-item-label caption class="q-mt-sm">
                      <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-6">
                          <div><strong>PUE:</strong> {{ rental.pue_name || `PUE ID ${rental.pue_id}` }}</div>
                          <div v-if="rental.is_pay_to_own && rental.pay_to_own_price">
                            <strong>Total Price:</strong> {{ currencySymbol }}{{ rental.pay_to_own_price.toFixed(2) }}
                          </div>
                          <div v-if="rental.is_pay_to_own && rental.amount_paid !== undefined">
                            <strong>Paid:</strong> {{ currencySymbol }}{{ rental.amount_paid.toFixed(2) }}
                            <q-linear-progress
                              :value="rental.pay_to_own_price > 0 ? rental.amount_paid / rental.pay_to_own_price : 0"
                              color="purple"
                              class="q-mt-xs"
                            />
                          </div>
                        </div>
                        <div class="col-12 col-md-6">
                          <div><strong>Start Date:</strong> {{ formatTimestamp(rental.rental_start_date) }}</div>
                          <div v-if="rental.cost_structure_name">
                            <strong>Cost Structure:</strong> {{ rental.cost_structure_name }}
                          </div>
                        </div>
                      </div>
                    </q-item-label>
                  </q-item-section>

                  <q-item-section side>
                    <div class="column q-gutter-sm">
                      <q-btn
                        v-if="rental.is_pay_to_own"
                        color="purple"
                        label="Payment"
                        icon="payment"
                        dense
                        @click="openPaymentDialog(rental)"
                      />
                      <q-btn
                        v-else
                        color="primary"
                        label="Return"
                        icon="assignment_return"
                        dense
                        @click="openReturnDialog(rental, 'pue')"
                      />
                      <q-btn
                        flat
                        dense
                        color="info"
                        label="Details"
                        icon="info"
                        @click="router.push(`/rentals/pue/${rental.rental_id}`)"
                      />
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-tab-panel>

            <!-- Battery Rental History Tab -->
            <q-tab-panel name="battery-history">
              <div v-if="batteryHistoryLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="batteryHistory.length === 0" class="text-grey-7 q-pa-md text-center">
                <q-icon name="history" size="48px" class="q-mb-sm" />
                <div>No battery rental history found</div>
              </div>

              <q-list v-else bordered separator>
                <q-item v-for="rental in batteryHistory" :key="rental.rental_id" class="q-pa-md">
                  <q-item-section>
                    <q-item-label class="text-weight-medium">
                      Battery Rental #{{ rental.rental_id }}
                      <q-chip dense size="sm" :color="getRentalStatusColor(rental.status)" text-color="white" class="q-ml-sm">
                        {{ rental.status }}
                      </q-chip>
                    </q-item-label>
                    <q-item-label caption class="q-mt-sm">
                      <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-4">
                          <div><strong>Batteries:</strong> {{ rental.battery_count || rental.items?.length || 0 }} item(s)</div>
                          <div v-if="rental.recharge_count !== undefined">
                            <strong>Recharges:</strong> {{ rental.recharge_count }}
                          </div>
                          <div v-if="rental.cost_structure_name">
                            <strong>Cost Structure:</strong> {{ rental.cost_structure_name }}
                          </div>
                        </div>
                        <div class="col-12 col-md-4">
                          <div><strong>Start Date:</strong> {{ formatTimestamp(rental.rental_start_date) }}</div>
                          <div v-if="rental.due_date"><strong>Due Date:</strong> {{ formatTimestamp(rental.due_date) }}</div>
                          <div v-if="rental.actual_return_date"><strong>Returned:</strong> {{ formatTimestamp(rental.actual_return_date) }}</div>
                        </div>
                        <div class="col-12 col-md-4">
                          <div v-if="rental.deposit_amount">
                            <strong>Deposit:</strong> {{ currencySymbol }}{{ rental.deposit_amount.toFixed(2) }}
                          </div>
                          <div v-if="rental.total_cost !== undefined && rental.total_cost !== null">
                            <strong>Total Cost:</strong> {{ currencySymbol }}{{ rental.total_cost.toFixed(2) }}
                          </div>
                        </div>
                      </div>
                    </q-item-label>
                  </q-item-section>

                  <q-item-section side>
                    <q-btn
                      flat
                      dense
                      color="info"
                      label="Details"
                      icon="info"
                      @click="router.push(`/rentals/battery/${rental.rental_id}`)"
                    />
                  </q-item-section>
                </q-item>
              </q-list>
            </q-tab-panel>

            <!-- PUE Rental History Tab -->
            <q-tab-panel name="pue-history">
              <div v-if="pueHistoryLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="pueHistory.length === 0" class="text-grey-7 q-pa-md text-center">
                <q-icon name="history" size="48px" class="q-mb-sm" />
                <div>No PUE rental history found</div>
              </div>

              <q-list v-else bordered separator>
                <q-item v-for="rental in pueHistory" :key="rental.rental_id" class="q-pa-md">
                  <q-item-section>
                    <q-item-label class="text-weight-medium">
                      PUE Rental #{{ rental.rental_id }}
                      <q-chip dense size="sm" :color="getRentalStatusColor(rental.status)" text-color="white" class="q-ml-sm">
                        {{ rental.status }}
                      </q-chip>
                      <q-chip
                        v-if="rental.is_pay_to_own"
                        dense
                        size="sm"
                        color="purple"
                        text-color="white"
                        class="q-ml-sm"
                      >
                        Pay-to-Own
                      </q-chip>
                    </q-item-label>
                    <q-item-label caption class="q-mt-sm">
                      <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-4">
                          <div><strong>PUE:</strong> {{ rental.pue_name || `PUE ID ${rental.pue_id}` }}</div>
                          <div v-if="rental.is_pay_to_own && rental.pay_to_own_price">
                            <strong>Total Price:</strong> {{ currencySymbol }}{{ rental.pay_to_own_price.toFixed(2) }}
                          </div>
                          <div v-if="rental.is_pay_to_own && rental.amount_paid !== undefined">
                            <strong>Paid:</strong> {{ currencySymbol }}{{ rental.amount_paid.toFixed(2) }}
                            <q-linear-progress
                              :value="rental.pay_to_own_price > 0 ? rental.amount_paid / rental.pay_to_own_price : 0"
                              color="purple"
                              class="q-mt-xs"
                            />
                          </div>
                          <div v-if="rental.cost_structure_name">
                            <strong>Cost Structure:</strong> {{ rental.cost_structure_name }}
                          </div>
                        </div>
                        <div class="col-12 col-md-4">
                          <div><strong>Start Date:</strong> {{ formatTimestamp(rental.rental_start_date) }}</div>
                          <div v-if="rental.actual_return_date"><strong>Returned:</strong> {{ formatTimestamp(rental.actual_return_date) }}</div>
                          <div v-if="rental.ownership_transferred_date"><strong>Ownership Transferred:</strong> {{ formatTimestamp(rental.ownership_transferred_date) }}</div>
                        </div>
                        <div class="col-12 col-md-4">
                          <div v-if="rental.total_cost !== undefined && rental.total_cost !== null">
                            <strong>Total Cost:</strong> {{ currencySymbol }}{{ rental.total_cost.toFixed(2) }}
                          </div>
                        </div>
                      </div>
                    </q-item-label>
                  </q-item-section>

                  <q-item-section side>
                    <q-btn
                      flat
                      dense
                      color="info"
                      label="Details"
                      icon="info"
                      @click="router.push(`/rentals/pue/${rental.rental_id}`)"
                    />
                  </q-item-section>
                </q-item>
              </q-list>
            </q-tab-panel>
          </q-tab-panels>
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

    <!-- Take Payment Dialog -->
    <q-dialog v-model="showTakePaymentDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Take Payment</div>
          <div class="text-subtitle2">User: {{ user.Name || user.username || `User ${user.user_id}` }}</div>
        </q-card-section>

        <q-card-section>
          <!-- Payment Summary -->
          <q-banner class="bg-blue-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            <div class="text-body2">
              <div class="text-weight-medium">Amount Owed: {{ currencySymbol }}{{ (account.total_owed || 0).toFixed(2) }}</div>
              <div v-if="account.balance > 0" class="text-caption text-positive">
                Available Credit: {{ currencySymbol }}{{ account.balance.toFixed(2) }}
              </div>
            </div>
          </q-banner>

          <!-- Rental Selection (if user has unpaid/partial rentals) -->
          <q-select
            v-model="selectedRentalForPayment"
            :options="rentalPaymentOptions"
            label="Apply Payment To"
            outlined
            class="q-mb-md"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            hint="Select which rental to apply this payment to, or choose General Payment"
          >
            <template v-slot:prepend>
              <q-icon name="receipt" />
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.label }}</q-item-label>
                  <q-item-label caption v-if="scope.opt.caption">{{ scope.opt.caption }}</q-item-label>
                </q-item-section>
                <q-item-section side v-if="scope.opt.amount_owed">
                  <q-badge :color="scope.opt.payment_status === 'unpaid' ? 'negative' : 'warning'">
                    {{ currencySymbol }}{{ scope.opt.amount_owed.toFixed(2) }}
                  </q-badge>
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- Credit Application (show when paying to rental, disabled if no credit) -->
          <div v-if="selectedRentalForPayment" class="q-mb-md">
            <q-input
              v-model.number="takePaymentCreditApplied"
              type="number"
              label="Apply Credit from Account"
              :prefix="currencySymbol"
              step="0.01"
              outlined
              :max="account.balance"
              :disable="account.balance <= 0"
              :hint="account.balance > 0 ? `Available credit: ${currencySymbol}${account.balance.toFixed(2)}` : 'User has no account credit'"
              :rules="[
                val => val >= 0 || 'Credit cannot be negative',
                val => val <= account.balance || `Cannot exceed available credit (${currencySymbol}${account.balance.toFixed(2)})`
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="account_balance_wallet" :color="account.balance > 0 ? 'positive' : 'grey'" />
              </template>
              <template v-slot:append>
                <q-btn
                  flat
                  dense
                  color="positive"
                  label="Use Max"
                  size="sm"
                  @click="takePaymentCreditApplied = Math.min(account.balance, selectedRentalForPayment?.amount_owed || 0)"
                  :disable="account.balance <= 0"
                />
              </template>
            </q-input>
          </div>

          <!-- Payment Amount Input -->
          <q-input
            v-model.number="takePaymentAmount"
            type="number"
            label="Payment Amount"
            :prefix="currencySymbol"
            step="0.01"
            outlined
            autofocus
            :rules="[val => ((val || 0) + (takePaymentCreditApplied || 0)) > 0 || 'Total payment (cash + credit) must be greater than 0']"
          >
            <template v-slot:append>
              <q-btn
                flat
                dense
                color="primary"
                label="Full Amount"
                size="sm"
                @click="takePaymentAmount = account.total_owed || 0"
                v-if="account.total_owed > 0"
              />
            </template>
          </q-input>

          <!-- Payment Method Selection -->
          <q-select
            v-model="takePaymentType"
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

          <!-- Optional Description -->
          <q-input
            v-model="takePaymentDescription"
            label="Notes (Optional)"
            outlined
            class="q-mt-md"
            hint="Add any notes or reference number"
          />

          <!-- Confirmation -->
          <q-separator class="q-mt-md" />
          <!-- Show confirmation checkbox only when actual payment is being collected -->
          <div v-if="takePaymentAmount > 0 && takePaymentType" class="bg-positive-1 q-pa-md rounded-borders q-mt-md">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="check_circle" color="positive" class="q-mr-sm" />
              Payment Confirmation
            </div>
            <q-checkbox
              v-model="confirmTakePaymentReceived"
              color="positive"
            >
              <template v-slot:default>
                <div class="text-body2">
                  I confirm that <strong>{{ takePaymentType }}</strong> payment of
                  <strong>{{ currencySymbol }}{{ (takePaymentAmount || 0).toFixed(2) }}</strong> has been received<span v-if="takePaymentCreditApplied > 0 && selectedRentalForPayment">, and <strong>{{ currencySymbol }}{{ takePaymentCreditApplied.toFixed(2) }}</strong> will be taken from the user's account credit</span>
                </div>
              </template>
            </q-checkbox>
          </div>
          <!-- When only credit is used, show informational message -->
          <div v-else-if="takePaymentCreditApplied > 0 && takePaymentAmount === 0 && selectedRentalForPayment" class="bg-positive-1 q-pa-md rounded-borders q-mt-md">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="account_balance_wallet" color="positive" class="q-mr-sm" />
              Credit Payment
            </div>
            <div class="text-body2">
              <strong>{{ currencySymbol }}{{ takePaymentCreditApplied.toFixed(2) }}</strong> will be taken from the user's account credit to cover this payment.
            </div>
          </div>

          <!-- Payment Summary Preview -->
          <q-card flat bordered class="q-mt-md bg-grey-2">
            <q-card-section class="q-pa-sm">
              <div class="text-caption text-weight-medium q-mb-xs">Payment Summary</div>
              <div class="text-caption">
                <div class="row justify-between">
                  <span>Payment Amount:</span>
                  <span class="text-weight-bold">{{ currencySymbol }}{{ (takePaymentAmount || 0).toFixed(2) }}</span>
                </div>
                <div class="row justify-between text-grey-7">
                  <span>Current Debt:</span>
                  <span>{{ currencySymbol }}{{ (account.total_owed || 0).toFixed(2) }}</span>
                </div>
                <q-separator class="q-my-xs" />
                <div class="row justify-between text-weight-bold" :class="remainingDebt < 0 ? 'text-positive' : remainingDebt > 0 ? 'text-orange' : ''">
                  <span>Remaining After Payment:</span>
                  <span>{{ currencySymbol }}{{ Math.max(0, remainingDebt).toFixed(2) }}</span>
                </div>
                <div v-if="remainingDebt < 0" class="row justify-between text-positive q-mt-xs">
                  <span>Overpayment (Added to Credit):</span>
                  <span>+{{ currencySymbol }}{{ Math.abs(remainingDebt).toFixed(2) }}</span>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            :label="takePaymentAmount > 0 ? 'Confirm Payment Received' : 'Apply Credit Payment'"
            color="positive"
            icon="check"
            @click="submitTakePayment"
            :disable="((takePaymentAmount || 0) + (takePaymentCreditApplied || 0)) <= 0 || !takePaymentType || (takePaymentAmount > 0 && !confirmTakePaymentReceived)"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Manual Adjustment Dialog -->
    <q-dialog v-model="showManualAdjustmentDialog">
      <q-card style="min-width: 500px">
        <q-card-section class="bg-warning text-white">
          <div class="text-h6">
            <q-icon name="warning" class="q-mr-sm" />
            Manual Balance Adjustment
          </div>
          <div class="text-subtitle2">User: {{ user.Name || user.username || `User ${user.user_id}` }}</div>
        </q-card-section>

        <q-card-section>
          <!-- Warning Banner -->
          <q-banner class="bg-orange-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="info" color="warning" />
            </template>
            <div class="text-body2">
              <div class="text-weight-medium">Admin Action Required</div>
              <div class="text-caption">This will create a manual journal entry in the accounting system.</div>
            </div>
          </q-banner>

          <!-- Current Balance Display -->
          <q-card flat bordered class="q-mb-md bg-grey-2">
            <q-card-section class="q-pa-sm">
              <div class="text-caption text-weight-medium q-mb-xs">Current Account Status</div>
              <div class="text-caption">
                <div class="row justify-between">
                  <span>Current Balance:</span>
                  <span class="text-weight-bold" :class="account.balance >= 0 ? 'text-positive' : 'text-negative'">
                    {{ currencySymbol }}{{ (account.balance || 0).toFixed(2) }}
                  </span>
                </div>
                <div class="row justify-between">
                  <span>Amount Owed:</span>
                  <span>{{ currencySymbol }}{{ (account.total_owed || 0).toFixed(2) }}</span>
                </div>
              </div>
            </q-card-section>
          </q-card>

          <!-- Adjustment Amount Input -->
          <q-input
            v-model.number="manualAdjustmentAmount"
            type="number"
            label="Adjustment Amount"
            :prefix="currencySymbol"
            step="0.01"
            outlined
            autofocus
            :rules="[val => val !== 0 || 'Adjustment amount cannot be zero']"
            hint="Positive = increases balance (credit), Negative = decreases balance (debit)"
          >
            <template v-slot:prepend>
              <q-icon name="edit" />
            </template>
          </q-input>

          <!-- Reason Input -->
          <q-input
            v-model="manualAdjustmentReason"
            label="Reason for Adjustment *"
            outlined
            class="q-mt-md"
            type="textarea"
            rows="3"
            :rules="[val => !!val || 'Reason is required for audit trail']"
            hint="Detailed explanation for this adjustment (required for compliance)"
          />

          <!-- Preview Card -->
          <q-card flat bordered class="q-mt-md" :class="manualAdjustmentAmount >= 0 ? 'bg-positive-1' : 'bg-negative-1'">
            <q-card-section class="q-pa-sm">
              <div class="text-caption text-weight-medium q-mb-xs">Preview</div>
              <div class="text-caption">
                <div class="row justify-between">
                  <span>Adjustment Type:</span>
                  <span class="text-weight-bold">
                    {{ manualAdjustmentAmount >= 0 ? 'Credit (+)' : 'Debit (-)' }}
                  </span>
                </div>
                <div class="row justify-between">
                  <span>Current Balance:</span>
                  <span>{{ currencySymbol }}{{ (account.balance || 0).toFixed(2) }}</span>
                </div>
                <div class="row justify-between text-weight-bold" :class="(account.balance + (manualAdjustmentAmount || 0)) >= 0 ? 'text-positive' : 'text-negative'">
                  <span>New Balance:</span>
                  <span>{{ currencySymbol }}{{ ((account.balance || 0) + (manualAdjustmentAmount || 0)).toFixed(2) }}</span>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Apply Adjustment"
            color="warning"
            icon="check"
            @click="submitManualAdjustment"
            :disable="!manualAdjustmentAmount || manualAdjustmentAmount === 0 || !manualAdjustmentReason"
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

    <!-- Unified Rental Return Dialog -->
    <RentalReturnDialog
      v-model="showReturnDialog"
      :rental="selectedRental"
      @returned="onRentalReturned"
    />

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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { usersAPI, accountsAPI, settingsAPI, subscriptionsAPI, rentalsAPI, batteryRentalsAPI, pueRentalsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'
import RentalReturnDialog from 'components/RentalReturnDialog.vue'

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

// Take Payment dialog (simplified)
const showTakePaymentDialog = ref(false)
const takePaymentAmount = ref(0)
const takePaymentType = ref(null)
const takePaymentDescription = ref('')
const confirmTakePaymentReceived = ref(false)
const takePaymentCreditApplied = ref(0)
const selectedRentalForPayment = ref(null) // null = general payment, or rental_id
const userRentals = ref([])
const rentalPaymentOptions = ref([])

const remainingDebt = computed(() => {
  return Math.round(((account.value.total_owed || 0) - (takePaymentAmount.value || 0)) * 100) / 100
})

// Manual Adjustment Dialog
const showManualAdjustmentDialog = ref(false)
const manualAdjustmentAmount = ref(0)
const manualAdjustmentReason = ref('')

const openTakePaymentDialog = async () => {
  // Load user's rentals to show outstanding payments
  try {
    const [batteryRentalsResponse, pueRentalsResponse] = await Promise.all([
      batteryRentalsAPI.list({ user_id: userId.value }),
      pueRentalsAPI.list({ user_id: userId.value })
    ])

    const allRentals = [
      ...(batteryRentalsResponse.data || []).map(r => ({ ...r, rental_type: 'battery' })),
      ...(pueRentalsResponse.data || []).map(r => ({ ...r, rental_type: 'pue' }))
    ]

    // Filter for rentals with outstanding payments (unpaid or partial)
    const unpaidRentals = allRentals.filter(r =>
      r.payment_status && ['unpaid', 'partial'].includes(r.payment_status) && r.amount_owed > 0
    )

    userRentals.value = unpaidRentals

    // Build payment options
    const options = [
      {
        label: 'General Payment (Account Credit)',
        value: null,
        caption: 'Add to account balance, not specific to any rental'
      }
    ]

    unpaidRentals.forEach(rental => {
      const rentalLabel = rental.rental_type === 'battery'
        ? `Battery Rental #${rental.rental_id}`
        : `PUE Rental #${rental.rental_id}`
      const statusLabel = rental.payment_status === 'unpaid' ? 'Unpaid' : 'Partial Payment'

      options.push({
        label: `${rentalLabel} - ${statusLabel}`,
        value: {rental_id: rental.rental_id, rental_type: rental.rental_type},
        caption: `Owed: ${currencySymbol.value}${rental.amount_owed.toFixed(2)}`,
        amount_owed: rental.amount_owed,
        payment_status: rental.payment_status
      })
    })

    rentalPaymentOptions.value = options
    selectedRentalForPayment.value = null // Default to general payment
  } catch (error) {
    console.error('Failed to load rentals:', error)
    // Still allow payment even if rentals fail to load
    rentalPaymentOptions.value = [{
      label: 'General Payment (Account Credit)',
      value: null,
      caption: 'Add to account balance'
    }]
    selectedRentalForPayment.value = null
  }

  // Default to full amount owed
  takePaymentAmount.value = account.value.total_owed || 0
  takePaymentType.value = null
  takePaymentDescription.value = ''
  confirmTakePaymentReceived.value = false
  takePaymentCreditApplied.value = 0
  showTakePaymentDialog.value = true
}

const submitTakePayment = async () => {
  const totalPayment = (takePaymentAmount.value || 0) + (takePaymentCreditApplied.value || 0)
  if (totalPayment <= 0) {
    $q.notify({
      type: 'warning',
      message: 'Total payment (cash + credit) must be greater than 0',
      position: 'top'
    })
    return
  }

  if (!takePaymentType.value) {
    $q.notify({
      type: 'warning',
      message: 'Please select a payment method',
      position: 'top'
    })
    return
  }

  // Only require confirmation checkbox if actual cash/card payment is being collected
  if (takePaymentAmount.value > 0 && !confirmTakePaymentReceived.value) {
    $q.notify({
      type: 'warning',
      message: 'Please confirm that payment has been received',
      position: 'top'
    })
    return
  }

  try {
    let response

    if (selectedRentalForPayment.value && selectedRentalForPayment.value.rental_id) {
      // Payment for specific rental
      const rental = selectedRentalForPayment.value
      const paymentData = {
        payment_amount: takePaymentAmount.value,
        payment_type: takePaymentType.value,
        payment_notes: takePaymentDescription.value || null,
        credit_applied: takePaymentCreditApplied.value || 0
      }

      if (rental.rental_type === 'battery') {
        response = await batteryRentalsAPI.recordPayment(rental.rental_id, paymentData)
      } else {
        response = await pueRentalsAPI.recordPayment(rental.rental_id, paymentData)
      }

      const totalPayment = (takePaymentAmount.value || 0) + (takePaymentCreditApplied.value || 0)
      $q.notify({
        type: 'positive',
        message: `Payment of ${currencySymbol.value}${totalPayment.toFixed(2)} recorded for ${rental.rental_type} rental #${rental.rental_id}${takePaymentCreditApplied.value > 0 ? ` (including ${currencySymbol.value}${takePaymentCreditApplied.value.toFixed(2)} credit)` : ''}`,
        position: 'top',
        timeout: 5000
      })
    } else {
      // General payment to account
      response = await accountsAPI.recordPayment(userId.value, {
        amount: takePaymentAmount.value,
        payment_type: takePaymentType.value,
        description: takePaymentDescription.value || null
      })

      $q.notify({
        type: 'positive',
        message: `Payment of ${currencySymbol.value}${takePaymentAmount.value.toFixed(2)} recorded successfully. Received by ${response.data.received_by}`,
        position: 'top',
        timeout: 5000
      })
    }

    showTakePaymentDialog.value = false

    // Reset form
    takePaymentAmount.value = 0
    takePaymentType.value = null
    takePaymentDescription.value = ''
    confirmTakePaymentReceived.value = false
    takePaymentCreditApplied.value = 0
    selectedRentalForPayment.value = null

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

const submitManualAdjustment = async () => {
  if (!manualAdjustmentAmount.value || manualAdjustmentAmount.value === 0) {
    $q.notify({
      type: 'warning',
      message: 'Adjustment amount cannot be zero',
      position: 'top'
    })
    return
  }

  if (!manualAdjustmentReason.value) {
    $q.notify({
      type: 'warning',
      message: 'Please provide a reason for this adjustment',
      position: 'top'
    })
    return
  }

  try {
    const response = await accountsAPI.createManualAdjustment(userId.value, {
      amount: manualAdjustmentAmount.value,
      reason: manualAdjustmentReason.value
    })

    $q.notify({
      type: 'positive',
      message: `Manual adjustment of ${currencySymbol.value}${Math.abs(manualAdjustmentAmount.value).toFixed(2)} applied successfully. ${response.data.adjustment_type} by ${response.data.created_by}`,
      position: 'top',
      timeout: 5000
    })

    showManualAdjustmentDialog.value = false

    // Reset form
    manualAdjustmentAmount.value = 0
    manualAdjustmentReason.value = ''

    // Reload data
    await loadAccount()
    await loadTransactions()
  } catch (error) {
    console.error('Failed to create manual adjustment:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create manual adjustment',
      position: 'top'
    })
  }
}

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

// Current Rentals (Legacy)
const currentRentals = ref([])
const rentalsLoading = ref(false)

// Battery Rentals
const batteryRentals = ref([])
const batteryRentalsLoading = ref(false)

// PUE Rentals
const pueRentals = ref([])
const pueRentalsLoading = ref(false)

// Rental tab
const rentalTab = ref('battery')

// Rental History
const batteryHistory = ref([])
const batteryHistoryLoading = ref(false)
const pueHistory = ref([])
const pueHistoryLoading = ref(false)

// Rental dialogs
const showReturnDialog = ref(false)
const showExtendDialog = ref(false)
const selectedRental = ref(null)
const selectedRentalType = ref(null) // 'battery' or 'pue'
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

const getRentalStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'active': return 'positive'
    case 'returned': return 'grey'
    case 'completed': return 'blue'
    case 'overdue': return 'negative'
    case 'ownership_transferred': return 'purple'
    default: return 'grey-7'
  }
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString() + ' UTC'
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
const openReturnDialog = (rental, type = 'legacy') => {
  selectedRental.value = rental
  selectedRentalType.value = type
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

const openRechargeDialog = (rental) => {
  // TODO: Implement recharge dialog for battery rentals
  $q.notify({
    type: 'info',
    message: 'Recharge functionality coming soon',
    position: 'top'
  })
  console.log('Open recharge dialog for rental:', rental)
}

const openPaymentDialog = (rental) => {
  // TODO: Implement payment dialog for pay-to-own PUE rentals
  $q.notify({
    type: 'info',
    message: 'Payment functionality coming soon',
    position: 'top'
  })
  console.log('Open payment dialog for rental:', rental)
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

// Load current rentals for this user (Legacy)
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

// Load battery rentals for this user
const loadBatteryRentals = async () => {
  try {
    batteryRentalsLoading.value = true
    const response = await batteryRentalsAPI.list({ user_id: userId.value, status: 'active' })
    batteryRentals.value = response.data || []
  } catch (error) {
    console.error('Failed to load battery rentals:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load battery rentals',
      position: 'top'
    })
  } finally {
    batteryRentalsLoading.value = false
  }
}

// Load PUE rentals for this user
const loadPueRentals = async () => {
  try {
    pueRentalsLoading.value = true
    const response = await pueRentalsAPI.list({ user_id: userId.value, status: 'active' })
    pueRentals.value = response.data || []
  } catch (error) {
    console.error('Failed to load PUE rentals:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load PUE rentals',
      position: 'top'
    })
  } finally {
    pueRentalsLoading.value = false
  }
}

// Load battery rental history for this user (all statuses)
const loadBatteryHistory = async () => {
  try {
    batteryHistoryLoading.value = true
    // Fetch all battery rentals without status filter
    const response = await batteryRentalsAPI.list({ user_id: userId.value })
    batteryHistory.value = response.data || []
  } catch (error) {
    console.error('Failed to load battery rental history:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load battery rental history',
      position: 'top'
    })
  } finally {
    batteryHistoryLoading.value = false
  }
}

// Load PUE rental history for this user (all statuses)
const loadPueHistory = async () => {
  try {
    pueHistoryLoading.value = true
    // Fetch all PUE rentals without status filter
    const response = await pueRentalsAPI.list({ user_id: userId.value })
    pueHistory.value = response.data || []
  } catch (error) {
    console.error('Failed to load PUE rental history:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load PUE rental history',
      position: 'top'
    })
  } finally {
    pueHistoryLoading.value = false
  }
}

// Refresh all rentals (active and history)
const refreshAllRentals = async () => {
  await Promise.all([
    loadBatteryRentals(),
    loadPueRentals(),
    loadBatteryHistory(),
    loadPueHistory()
  ])
}

// Watch credit applied to auto-adjust payment amount
watch(() => takePaymentCreditApplied.value, (newCredit) => {
  if (showTakePaymentDialog.value && selectedRentalForPayment.value) {
    const amountOwed = selectedRentalForPayment.value.amount_owed || 0
    const remaining = amountOwed - (newCredit || 0)
    takePaymentAmount.value = Math.max(0, remaining)
  }
})

// Watch rental selection to adjust payment amount
watch(() => selectedRentalForPayment.value, (newRental) => {
  if (showTakePaymentDialog.value) {
    if (newRental && newRental.amount_owed) {
      // Specific rental selected - set amount to what's owed minus any credit
      const creditAmount = takePaymentCreditApplied.value || 0
      takePaymentAmount.value = Math.max(0, newRental.amount_owed - creditAmount)
    } else {
      // General payment - reset to account total owed
      takePaymentAmount.value = account.value.total_owed || 0
      takePaymentCreditApplied.value = 0 // Reset credit for general payment
    }
  }
})

onMounted(async () => {
  loadHubSettings()
  await loadUser()
  loadPaymentTypes()
  loadAccount()
  loadTransactions()
  loadUserSubscriptions()
  loadSubscriptionPackages()
  // Load new rental system data
  refreshAllRentals()
})
</script>
