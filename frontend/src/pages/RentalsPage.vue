<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Rentals</div>
      </div>
      <div class="col-auto row items-center q-gutter-sm">
        <HubFilter v-model="selectedHub" @change="onHubChange" />
        <q-btn
          label="Returns"
          icon="assignment_return"
          color="positive"
          outline
          @click="showQuickReturnsDialog = true"
        />
        <q-btn
          label="Rent a Battery"
          icon="battery_charging_full"
          color="primary"
          @click="openBatteryRentalDialog"
        />
        <q-btn
          label="Rent a PUE"
          icon="devices"
          color="purple"
          @click="openPUERentalDialog"
        />
      </div>
    </div>

    <!-- Rental Type Filter tabs -->
    <q-tabs
      v-model="rentalTypeFilter"
      dense
      class="text-grey"
      active-color="secondary"
      indicator-color="secondary"
      align="left"
      narrow-indicator
      @update:model-value="loadRentals"
    >
      <q-tab name="all" label="All Types" />
      <q-tab name="battery" label="Battery" />
      <q-tab name="pue" label="PUE" />
    </q-tabs>

    <!-- Status Filter tabs -->
    <q-tabs
      v-model="statusFilter"
      dense
      class="text-grey q-mt-sm"
      active-color="primary"
      indicator-color="primary"
      align="justify"
      narrow-indicator
      @update:model-value="loadRentals"
    >
      <q-tab name="all" label="All Rentals" />
      <q-tab name="active" label="Active" />
      <q-tab name="returned" label="Returned" />
      <q-tab name="overdue" label="Overdue" />
    </q-tabs>

    <q-card class="q-mt-md">
      <q-card-section>
        <q-table
          :rows="rentals"
          :columns="columns"
          row-key="rentral_id"
          :loading="loading"
          :filter="filter"
          @row-click="onRowClick"
          class="cursor-pointer"
          :no-data-label="selectedHub ? 'No rentals found for this hub' : 'No rentals available yet - create your first rental!'"
        >
          <template v-slot:top-right>
            <q-input
              v-model="filter"
              outlined
              dense
              debounce="300"
              placeholder="Search"
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </template>

          <template v-slot:body-cell-rental_type="props">
            <q-td :props="props">
              <q-badge
                :color="props.row.rental_type === 'battery' ? 'blue' : 'purple'"
                :label="props.row.rental_type === 'battery' ? 'Battery' : 'PUE'"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge
                :color="getStatusColor(props.row.status || props.row.rental_status)"
                :label="props.row.status || props.row.rental_status"
              >
                <q-tooltip>
                  {{ getStatusTooltip(props.row.status || props.row.rental_status) }}
                </q-tooltip>
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-timestamp_taken="props">
            <q-td :props="props">
              {{ formatDate(props.row.timestamp_taken) }}
            </q-td>
          </template>

          <template v-slot:body-cell-due_back="props">
            <q-td :props="props">
              {{ formatDate(props.row.due_back) }}
            </q-td>
          </template>

          <template v-slot:body-cell-total_cost="props">
            <q-td :props="props">
              {{ currentCurrencySymbol }}{{ props.row.total_cost?.toFixed(2) || '0.00' }}
            </q-td>
          </template>

          <template v-slot:body-cell-user="props">
            <q-td :props="props">
              <div>
                <div>{{ props.row.user?.Name || props.row.user?.username || `User ${props.row.user_id}` }}</div>
                <div v-if="props.row.user?.account_balance !== undefined"
                     class="text-caption"
                     :class="props.row.user.account_balance >= 0 ? 'text-positive' : 'text-negative'">
                  Balance: {{ currentCurrencySymbol }}{{ props.row.user.account_balance?.toFixed(2) }}
                </div>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-subscription="props">
            <q-td :props="props">
              <div v-if="props.row.subscription">
                <q-badge color="blue" :label="props.row.subscription.package_name">
                  <q-tooltip>
                    <div class="q-pa-xs">
                      <div><strong>Package:</strong> {{ props.row.subscription.package_name }}</div>
                      <div><strong>Status:</strong> {{ props.row.subscription.status }}</div>
                      <div v-if="props.row.subscription.kwh_limit">
                        <strong>kWh Limit:</strong> {{ props.row.subscription.kwh_limit }} kWh
                      </div>
                      <div><strong>Billing:</strong> {{ props.row.subscription.billing_cycle }}</div>
                    </div>
                  </q-tooltip>
                </q-badge>
              </div>
              <span v-else class="text-grey-5">-</span>
            </q-td>
          </template>

          <template v-slot:body-cell-payment_status="props">
            <q-td :props="props">
              <q-badge
                :color="getPaymentStatusColor(props.row.payment_status)"
                :label="getPaymentStatusLabel(props.row.payment_status)"
              >
                <q-tooltip>
                  {{ getPaymentStatusDescription(props.row) }}
                </q-tooltip>
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-battery="props">
            <q-td :props="props">
              <div class="row items-center no-wrap">
                <span>{{ props.row.battery?.short_id || `Battery ${props.row.battery_id}` }}</span>
                <q-btn
                  flat
                  round
                  dense
                  size="sm"
                  icon="open_in_new"
                  color="primary"
                  :to="`/batteries/${props.row.battery_id}`"
                  class="q-ml-xs"
                >
                  <q-tooltip>View Battery Details</q-tooltip>
                </q-btn>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                icon="visibility"
                color="primary"
                :to="{ name: 'rental-detail', params: { id: props.row.rentral_id } }"
              />
              <q-btn
                v-if="props.row.status === 'active' || props.row.status === 'overdue'"
                flat
                round
                dense
                icon="assignment_return"
                color="positive"
                @click.stop="returnRental(props.row)"
              >
                <q-tooltip>Return Rental</q-tooltip>
              </q-btn>
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click="editRental(props.row)"
              />
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Create/Edit Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">{{ editingRental ? 'Edit Rental' : 'New Rental' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveRental">
            <!-- Auto-generated Rental ID (read-only display) -->
            <q-input
              v-if="formData.rental_unique_id"
              v-model="formData.rental_unique_id"
              label="Rental ID"
              outlined
              readonly
              hint="Automatically generated unique rental ID"
              bg-color="grey-2"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="tag" />
              </template>
            </q-input>

            <q-select
              v-model="formData.hub_id"
              :options="hubOptions"
              option-value="hub_id"
              option-label="what_three_word_location"
              emit-value
              map-options
              label="Hub"
              outlined
              :rules="[val => !!val || 'Hub is required']"
              @update:model-value="onHubChange"
              class="q-mb-md"
            />

            <q-select
              v-model="formData.user_id"
              :options="filteredUsers"
              option-value="user_id"
              option-label="username"
              emit-value
              map-options
              label="User"
              outlined
              use-input
              input-debounce="0"
              @filter="filterUsers"
              @update:model-value="loadUserAccount"
              :rules="[val => !!val || 'User is required']"
              :disable="!formData.hub_id"
              :hint="!formData.hub_id ? 'Select a hub first' : ''"
              class="q-mb-md"
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.username }} - {{ scope.opt.Name }}</q-item-label>
                    <q-item-label caption>
                      User ID: {{ scope.opt.user_id }}
                      <template v-if="scope.opt.mobile_number"> | Mobile: {{ scope.opt.mobile_number }}</template>
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
              <template v-slot:no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    No users found
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <!-- User Summary (Credit & Subscriptions) -->
            <div v-if="formData.user_id && (userAccount || userSubscriptions.length > 0)" class="q-mb-md">
              <q-banner class="bg-blue-1 text-dark">
                <template v-slot:avatar>
                  <q-icon name="person" color="primary" size="md" />
                </template>
                <div class="text-subtitle1 text-weight-medium q-mb-sm">
                  User Selected: {{ userOptions.find(u => u.user_id === formData.user_id)?.Name || `User ${formData.user_id}` }}
                </div>
                <div class="row q-col-gutter-sm">
                  <div v-if="userAccount" class="col-12 col-md-6">
                    <div class="text-caption text-grey-8">💰 Credit Available:</div>
                    <div class="text-body1 text-weight-bold" :class="userAccount.balance > 0 ? 'text-positive' : 'text-grey'">
                      {{ currentCurrencySymbol }}{{ Math.max(0, userAccount.balance || 0).toFixed(2) }}
                      <span v-if="userAccount.balance > 0" class="text-caption text-grey-7">(apply at return/payment)</span>
                    </div>
                  </div>
                  <div v-if="userSubscriptions.length > 0" class="col-12 col-md-6">
                    <div class="text-caption text-grey-8">📋 Active Subscriptions:</div>
                    <div class="text-body1 text-weight-bold text-positive">
                      {{ userSubscriptions.length }} subscription(s)
                      <span class="text-caption">(select below to auto-fill)</span>
                    </div>
                  </div>
                </div>
              </q-banner>
            </div>

            <!-- User Account Balance Display -->
            <div v-if="userAccount" class="q-mb-md">
              <q-card flat bordered>
                <q-card-section class="q-pa-md">
                  <div class="row items-center q-mb-sm">
                    <q-icon name="account_balance_wallet" size="sm" color="primary" class="q-mr-sm" />
                    <div class="text-subtitle2">Account Balance</div>
                  </div>
                  <div class="row q-col-gutter-md">
                    <div class="col-4">
                      <div class="text-caption text-grey-7">Current Balance</div>
                      <div class="text-h6" :class="userAccount.balance >= 0 ? 'text-positive' : 'text-negative'">
                        {{ currentCurrencySymbol }}{{ userAccount.balance?.toFixed(2) || '0.00' }}
                      </div>
                    </div>
                    <div class="col-4">
                      <div class="text-caption text-grey-7">Total Owed</div>
                      <div class="text-body1 text-negative">
                        {{ currentCurrencySymbol }}{{ userAccount.total_owed?.toFixed(2) || '0.00' }}
                      </div>
                    </div>
                    <div class="col-4">
                      <div class="text-caption text-grey-7">Available Credit</div>
                      <div class="text-body1 text-positive">
                        {{ currentCurrencySymbol }}{{ Math.max(0, userAccount.balance || 0).toFixed(2) }}
                      </div>
                    </div>
                  </div>
                </q-card-section>

                <!-- Apply Credit Option - Only shown when collecting upfront payment -->
                <q-card-section v-if="false" class="q-pt-none">
                  <!-- Credit application is handled in the Payment Collection section below -->
                  <div class="text-caption text-grey-7">
                    💡 Tip: Credit can be applied in the Payment Collection section below
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <!-- User Subscriptions -->
            <div v-if="userSubscriptions.length > 0" class="q-mb-md">
              <q-card flat bordered>
                <q-card-section>
                  <div class="row items-center q-mb-sm">
                    <q-icon name="subscriptions" size="sm" color="primary" class="q-mr-sm" />
                    <div class="text-subtitle2">Active Subscriptions</div>
                  </div>
                  <q-select
                    v-model="selectedSubscription"
                    :options="userSubscriptions"
                    option-value="subscription_id"
                    option-label="package_name"
                    emit-value
                    map-options
                    label="Use Subscription"
                    outlined
                    clearable
                    @update:model-value="onSubscriptionSelect"
                  >
                    <template v-slot:prepend>
                      <q-icon name="subscriptions" />
                    </template>
                    <template v-slot:option="scope">
                      <q-item v-bind="scope.itemProps">
                        <q-item-section>
                          <q-item-label>{{ scope.opt.package_name }}</q-item-label>
                          <q-item-label caption>
                            {{ currentCurrencySymbol }}{{ scope.opt.price?.toFixed(2) }} per {{ scope.opt.billing_period }}
                          </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                          <q-chip dense size="sm" :color="getSubscriptionStatusColor(scope.opt.status)" text-color="white">
                            {{ scope.opt.status }}
                          </q-chip>
                        </q-item-section>
                      </q-item>
                    </template>
                    <template v-slot:hint v-if="selectedSubscription">
                      Using subscription will auto-select compatible batteries and PUE items
                    </template>
                  </q-select>
                </q-card-section>
              </q-card>
            </div>

            <!-- Subscription Coverage Banner -->
            <div v-if="isSubscriptionRental" class="q-mb-md">
              <q-banner class="bg-green-1 text-dark">
                <template v-slot:avatar>
                  <q-icon name="check_circle" color="positive" size="md" />
                </template>
                <div class="text-subtitle1 text-weight-medium q-mb-xs">
                  Subscription Applied: {{ selectedSubscriptionDetails?.package_name }}
                </div>
                <div class="text-body2">
                  This rental is covered by the user's active subscription.
                  The subscription fee of {{ currentCurrencySymbol }}{{ selectedSubscriptionDetails?.price?.toFixed(2) }}
                  per {{ selectedSubscriptionDetails?.billing_period }} will be charged automatically.
                </div>
                <div class="q-mt-sm text-caption text-grey-8">
                  You may still collect an optional deposit or add extra charges below.
                </div>
              </q-banner>
            </div>

            <q-select
              v-model="formData.battery_id"
              :options="filteredBatteries"
              option-value="battery_id"
              option-label="battery_id"
              emit-value
              map-options
              label="Battery"
              outlined
              use-input
              input-debounce="0"
              @filter="filterBatteries"
              @update:model-value="onBatterySelected"
              :rules="[val => !!val || 'Battery is required']"
              :disable="!formData.hub_id"
              :hint="!formData.hub_id ? 'Select a hub first' : availableBatteries.length === 0 ? 'No available batteries in this hub' : ''"
              class="q-mb-md"
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>Battery ID: {{ scope.opt.battery_id }}</q-item-label>
                    <q-item-label caption>
                      {{ scope.opt.battery_capacity_wh ? scope.opt.battery_capacity_wh + 'Wh' : 'Capacity not specified' }} -
                      {{ scope.opt.status }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
              <template v-slot:no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    No batteries available
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <!-- Cost Structure Selector (FIRST) -->
            <q-separator class="q-my-md" />
            <div class="row items-center q-mb-md">
              <div class="text-subtitle2">Pricing & Duration</div>
              <q-space />
              <q-chip
                v-if="costEstimate"
                color="primary"
                text-color="white"
                icon="calculate"
                size="md"
              >
                Total: {{ currentCurrencySymbol }}{{ costEstimate.total.toFixed(2) }}
              </q-chip>
            </div>

            <div class="q-mb-md">
              <q-select
                v-model="selectedCostStructure"
                :options="availableCostStructures"
                option-value="structure_id"
                option-label="name"
                emit-value
                map-options
                label="Cost Structure"
                outlined
                :loading="loadingCostStructures"
                @update:model-value="onCostStructureChange"
                hint="Select a pricing template first"
                clearable
              >
                <template v-slot:prepend>
                  <q-icon name="receipt_long" />
                </template>
                <template v-slot:option="scope">
                  <q-item v-bind="scope.itemProps">
                    <q-item-section>
                      <q-item-label>{{ scope.opt.name }}</q-item-label>
                      <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                      <q-item-label caption class="text-grey-6">
                        {{ scope.opt.components.length }} components
                      </q-item-label>
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>
            </div>

            <!-- Dynamic inputs based on cost structure requirements -->
            <div v-if="selectedCostStructureObject">

              <!-- Rental Start Date (always shown) -->
              <div class="row q-col-gutter-md q-mb-md">
                <div class="col-12">
                  <q-input
                    v-model="formData.timestamp_taken"
                    label="Rental Start Date"
                    type="datetime-local"
                    outlined
                    :rules="[
                      val => !!val || 'Rental date is required',
                      val => new Date(val) >= new Date(new Date().setHours(0, 0, 0, 0)) || 'Cannot select a past date'
                    ]"
                    @update:model-value="onStartDateChange"
                  />
                </div>
              </div>

              <!-- Duration inputs (only if structure uses time-based components) -->
              <div v-if="requiresDuration">
                <div class="row q-col-gutter-md q-mb-md">
                  <div class="col-12">
                    <q-select
                      v-model="selectedDuration"
                      :options="durationOptions"
                      option-value="value"
                      option-label="label"
                      emit-value
                      map-options
                      label="Rental Duration"
                      outlined
                      :loading="loadingDurations"
                      @update:model-value="onDurationChange"
                    >
                      <template v-slot:hint>
                        Required for {{ getTimeBasedComponents() }}
                      </template>
                    </q-select>
                  </div>
                </div>

                <!-- Custom duration inputs (only shown when custom is selected) -->
                <div v-if="isCustomDuration" class="row q-col-gutter-md q-mb-md">
                  <div class="col-6">
                    <q-input
                      v-model.number="customDurationValue"
                      type="number"
                      label="Duration Value"
                      outlined
                      min="1"
                      step="1"
                      hint="Enter number of units"
                      :rules="[
                        val => val !== null && val !== '' || 'Please enter a value',
                        val => val > 0 || 'Must be greater than 0',
                        val => Number.isInteger(Number(val)) || 'Must be a whole number'
                      ]"
                      @update:model-value="onCustomDurationChange"
                    />
                  </div>
                  <div class="col-6">
                    <q-select
                      v-model="customDurationUnit"
                      :options="['hours', 'days', 'weeks', 'months']"
                      label="Duration Unit"
                      outlined
                      hint="Select time unit"
                      @update:model-value="onCustomDurationChange"
                    />
                  </div>
                </div>

                <!-- Due back date -->
                <div class="row q-col-gutter-md q-mb-md">
                  <div class="col-12">
                    <q-input
                      v-model="formData.due_back"
                      label="Due Back Date"
                      type="datetime-local"
                      outlined
                      :rules="[
                        val => !!val || 'Due back date is required',
                        val => new Date(val) > new Date(formData.timestamp_taken) || 'Due date must be after start date'
                      ]"
                      :readonly="!isCustomDuration"
                      :bg-color="!isCustomDuration ? 'grey-2' : 'white'"
                      :hint="isCustomDuration ? 'Manually adjust if needed' : 'Automatically calculated from duration'"
                    />
                  </div>
                </div>
              </div>

              <!-- Due back date only (for fixed/kwh only structures) -->
              <div v-if="!requiresDuration" class="row q-col-gutter-md q-mb-md">
                <div class="col-12">
                  <q-input
                    v-model="formData.due_back"
                    label="Expected Return Date"
                    type="datetime-local"
                    outlined
                    :rules="[
                      val => !!val || 'Return date is required',
                      val => new Date(val) > new Date(formData.timestamp_taken) || 'Return date must be after start date'
                    ]"
                  >
                    <template v-slot:hint>
                      <span class="text-grey-6">Duration not needed for this pricing structure</span>
                    </template>
                  </q-input>
                </div>
              </div>

              <!-- kWh Estimate (only if structure uses per_kwh component) -->
              <div v-if="requiresKwhEstimate" class="row q-col-gutter-md q-mb-md">
                <div class="col-12">
                  <q-input
                    v-model.number="estimatedKwh"
                    label="Estimated kWh Usage"
                    type="number"
                    step="0.1"
                    outlined
                    prefix="kWh"
                    :hint="kwhEstimateHint"
                    @update:model-value="onKwhChange"
                  >
                    <template v-slot:prepend>
                      <q-icon name="battery_charging_full" />
                    </template>
                  </q-input>
                  <div v-if="selectedBatteryCapacity" class="q-mt-xs q-ml-sm">
                    <q-chip size="sm" color="blue-1" text-color="blue-9" icon="info">
                      Battery Capacity: {{ (selectedBatteryCapacity / 1000).toFixed(2) }} kWh
                    </q-chip>
                    <q-chip size="sm" color="green-1" text-color="green-9" icon="tips_and_updates">
                      Typical usage: {{ typicalUsageEstimate }} kWh
                    </q-chip>
                  </div>
                </div>
              </div>
            </div>

            <!-- Cost Breakdown Display -->
            <div v-if="costEstimate" class="q-pa-md bg-grey-1 rounded-borders q-mb-md">
              <div class="text-caption text-grey-7 q-mb-sm">Cost Breakdown:</div>

              <div v-for="(item, idx) in costEstimate.breakdown" :key="idx" class="row items-center q-mb-xs">
                <div class="col">
                  <span class="text-body2">{{ item.component_name }}</span>
                  <span class="text-caption text-grey-6">
                    ({{ item.quantity }} × {{ currentCurrencySymbol }}{{ item.rate }})
                  </span>
                  <q-badge v-if="item.is_calculated_on_return" color="orange" class="q-ml-xs">
                    Calculated on return
                  </q-badge>
                </div>
                <div class="col-auto text-weight-medium">
                  {{ currentCurrencySymbol }}{{ item.amount.toFixed(2) }}
                </div>
              </div>

              <q-separator class="q-my-sm" />

              <div class="row items-center q-mb-xs">
                <div class="col text-body2">Subtotal:</div>
                <div class="col-auto text-weight-medium">{{ currentCurrencySymbol }}{{ costEstimate.subtotal.toFixed(2) }}</div>
              </div>

              <div class="row items-center q-mb-xs">
                <div class="col text-body2">
                  VAT ({{ costEstimate.vat_percentage }}%):
                </div>
                <div class="col-auto text-weight-medium">{{ currentCurrencySymbol }}{{ costEstimate.vat_amount.toFixed(2) }}</div>
              </div>

              <q-separator class="q-my-sm" />

              <div class="row items-center">
                <div class="col text-h6 text-primary">Total:</div>
                <div class="col-auto text-h6 text-primary">{{ currentCurrencySymbol }}{{ costEstimate.total.toFixed(2) }}</div>
              </div>

              <!-- Deposit Information (if applicable) -->
              <div v-if="costEstimate.deposit_amount && costEstimate.deposit_amount > 0" class="q-mt-md">
                <q-separator class="q-my-sm" />
                <div class="bg-orange-1 q-pa-sm rounded-borders">
                  <div class="row items-center">
                    <q-icon name="info" color="orange" class="q-mr-sm" />
                    <div class="col text-body2">
                      <span class="text-weight-medium">Deposit Required:</span>
                      {{ currentCurrencySymbol }}{{ costEstimate.deposit_amount.toFixed(2) }}
                    </div>
                  </div>
                  <div class="text-caption text-grey-7 q-mt-xs">
                    This deposit is required for this rental type
                  </div>
                </div>
              </div>

            </div>

            <!-- Payment Method -->
            <q-separator class="q-my-md" />
            <div v-if="!isSubscriptionRental">
              <div class="text-subtitle2 q-mb-md">Payment Options</div>
              <div class="row q-col-gutter-md q-mb-md">
                <div class="col-12">
                  <q-select
                    v-model="formData.payment_method"
                    :options="paymentMethodOptions"
                    label="Payment Method"
                    outlined
                    emit-value
                    map-options
                    hint="How will the customer pay?"
                  >
                    <template v-slot:prepend>
                      <q-icon name="payment" />
                    </template>
                  </q-select>
                </div>
              </div>

              <!-- Account Credit Available - Only for upfront/partial payments -->
              <div v-if="userAccount && userAccount.balance > 0 && (formData.payment_method === 'upfront' || formData.payment_method === 'partial')" class="q-mb-md">
                <div class="bg-green-1 q-pa-md rounded-borders">
                  <div class="row items-center q-mb-sm">
                    <q-icon name="account_balance_wallet" color="positive" size="sm" class="q-mr-sm" />
                    <div class="col">
                      <div class="text-body2 text-weight-medium">Account Credit Available</div>
                      <div class="text-h6 text-positive">
                        {{ currentCurrencySymbol }}{{ userAccount.balance.toFixed(2) }}
                      </div>
                    </div>
                    <div class="col-auto">
                      <q-btn
                        color="positive"
                        icon="add"
                        label="Apply to Rental"
                        @click="showApplyCreditDialog = true"
                        unelevated
                        no-caps
                      />
                    </div>
                  </div>
                  <div v-if="formData.credit_used && formData.credit_used > 0" class="bg-white q-pa-sm rounded-borders">
                    <div class="row items-center">
                      <div class="col text-caption">Credit Applied:</div>
                      <div class="col-auto text-body2 text-positive text-weight-medium">
                        -{{ currentCurrencySymbol }}{{ formData.credit_used.toFixed(2) }}
                      </div>
                    </div>
                    <div class="row items-center q-mt-xs">
                      <div class="col text-caption">Remaining to Pay:</div>
                      <div class="col-auto text-body1 text-weight-bold">
                        {{ currentCurrencySymbol }}{{ Math.max(0, costEstimate.total - formData.credit_used).toFixed(2) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else>
              <div class="text-subtitle2 q-mb-md">Additional Charges (Optional)</div>
              <div class="q-mb-sm text-caption text-grey-7">
                Rental is covered by subscription. You may optionally collect deposits or add additional charges.
              </div>
            </div>

            <!-- Deposit & Payment Collection -->
            <div class="q-mb-md">
              <div v-if="!isSubscriptionRental" class="text-subtitle2 q-mb-sm">Payment Collection</div>
              <div class="row q-col-gutter-md">
                <!-- Deposit Collection (available for all rentals) -->
                <div class="col-12 col-md-6">
                  <q-card flat bordered>
                    <q-card-section class="row items-center">
                      <div class="col">
                        <div class="text-caption text-grey-7">Deposit Amount</div>
                        <div class="text-h6 text-positive">
                          {{ currentCurrencySymbol }}{{ formData.deposit_amount?.toFixed(2) || '0.00' }}
                        </div>
                        <div v-if="isSubscriptionRental" class="text-caption text-grey-6 q-mt-xs">
                          Optional security deposit
                        </div>
                      </div>
                      <div class="col-auto">
                        <q-btn
                          color="positive"
                          icon="add_circle"
                          :label="isSubscriptionRental ? 'Add Deposit' : 'Collect Deposit'"
                          @click="showDepositDialog = true"
                          flat
                        />
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Payment Collection (show for upfront and partial only for non-subscription rentals) -->
                <div v-if="!isSubscriptionRental && (formData.payment_method === 'upfront' || formData.payment_method === 'partial')" class="col-12 col-md-6">
                  <q-card flat bordered>
                    <q-card-section class="row items-center">
                      <div class="col">
                        <div class="text-caption text-grey-7">Payment Collected</div>
                        <div class="text-h6 text-primary">
                          {{ currentCurrencySymbol }}{{ ((formData.amount_paid || 0) + (formData.credit_used || 0)).toFixed(2) }}
                        </div>
                        <div v-if="(formData.amount_paid || 0) + (formData.credit_used || 0) > 0" class="text-caption text-grey-7 q-mt-xs">
                          Est. remaining at return: {{ currentCurrencySymbol }}{{ Math.max(0, costEstimate.total - (formData.amount_paid || 0) - (formData.credit_used || 0)).toFixed(2) }}
                        </div>
                      </div>
                      <div class="col-auto">
                        <q-btn
                          color="primary"
                          icon="payments"
                          label="Collect Payment"
                          @click="showPaymentCollectionDialog = true"
                          flat
                        />
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Add Credit to Account (for subscription rentals) -->
                <div v-if="isSubscriptionRental" class="col-12 col-md-6">
                  <q-card flat bordered class="bg-blue-1">
                    <q-card-section class="row items-center">
                      <div class="col">
                        <div class="text-caption text-grey-7">Add Credit to User Account</div>
                        <div class="text-body2 q-mt-xs">
                          Add funds to user's account balance
                        </div>
                      </div>
                      <div class="col-auto">
                        <q-btn
                          color="primary"
                          icon="account_balance_wallet"
                          label="Add Credit"
                          @click="showApplyCreditDialog = true"
                          flat
                        />
                      </div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </div>

            <!-- Payment Status (Auto-calculated) - Hide for subscription rentals -->
            <div v-if="!isSubscriptionRental && formData.payment_method !== 'on_return'" class="q-mb-md">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-subtitle2 q-mb-md">Payment Status</div>
                  <div class="row q-col-gutter-md items-center">
                    <div class="col-auto">
                      <q-badge
                        :color="getPaymentStatusColor(computedPaymentStatus)"
                        :label="computedPaymentStatus"
                        size="lg"
                        class="text-capitalize"
                      />
                    </div>
                    <div class="col">
                      <div class="text-caption text-grey-7">
                        {{ getPaymentStatusDescription(computedPaymentStatus) }}
                      </div>
                    </div>
                  </div>
                  <div v-if="costEstimate && costEstimate.has_estimated_component" class="q-mt-sm">
                    <q-banner dense class="bg-orange-1 text-orange-9">
                      <template v-slot:avatar>
                        <q-icon name="info" color="orange" />
                      </template>
                      This rental includes estimated costs. Status will be "partial" until final usage is determined.
                    </q-banner>
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn label="Cancel" flat @click="closeDialog" />
              <q-btn
                label="Save"
                type="submit"
                color="primary"
                :loading="saving"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- PUE Rental Dialog -->
    <q-dialog v-model="showPUERentalDialog" persistent>
      <q-card style="min-width: 700px; max-width: 900px">
        <q-card-section>
          <div class="text-h6">New PUE Rental</div>
        </q-card-section>

        <q-card-section class="q-pt-none" style="max-height: 70vh; overflow-y: auto">
          <q-form @submit="savePUERental">
            <!-- Hub Selection -->
            <q-select
              v-model="pueFormData.hub_id"
              :options="hubOptions"
              option-value="hub_id"
              option-label="what_three_word_location"
              emit-value
              map-options
              label="Hub *"
              outlined
              :rules="[val => !!val || 'Hub is required']"
              @update:model-value="onPUEHubChange"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="store" />
              </template>
            </q-select>

            <!-- User Selection -->
            <q-select
              v-model="pueFormData.user_id"
              :options="filteredUsers"
              option-value="user_id"
              option-label="username"
              emit-value
              map-options
              label="User *"
              outlined
              use-input
              input-debounce="0"
              @filter="filterUsers"
              :rules="[val => !!val || 'User is required']"
              @update:model-value="onPUEUserChange"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="person" />
              </template>
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.username }}</q-item-label>
                    <q-item-label caption>{{ scope.opt.Name }} - {{ scope.opt.Phone_Number }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <!-- User Account Balance Display -->
            <div v-if="pueUserAccount" class="q-mb-md">
              <q-banner dense class="bg-green-1" v-if="pueUserAccount.balance > 0">
                <template v-slot:avatar>
                  <q-icon name="account_balance_wallet" color="positive" />
                </template>
                <div class="text-body2">
                  User Selected: {{ userOptions.find(u => u.user_id === pueFormData.user_id)?.Name || `User ${pueFormData.user_id}` }}
                </div>
                <div class="row q-col-gutter-sm">
                  <div class="col-12 col-md-6">
                    <div class="text-caption text-grey-8">💰 Credit Available:</div>
                    <div class="text-body1 text-weight-bold" :class="pueUserAccount.balance > 0 ? 'text-positive' : 'text-grey'">
                      {{ currentCurrencySymbol }}{{ Math.max(0, pueUserAccount.balance || 0).toFixed(2) }}
                      <span v-if="pueUserAccount.balance > 0" class="text-caption text-grey-7">(apply at return/payment)</span>
                    </div>
                  </div>
                </div>
              </q-banner>
            </div>

            <q-separator class="q-my-md" />

            <!-- PUE Item Selection -->
            <div class="text-subtitle2 q-mb-md">Equipment Selection</div>

            <q-select
              v-model="pueFormData.pue_id"
              :options="filteredPUE"
              option-value="pue_id"
              option-label="name"
              emit-value
              map-options
              label="Select PUE Item *"
              outlined
              use-input
              input-debounce="0"
              @filter="filterPUE"
              :disable="!pueFormData.hub_id"
              :hint="!pueFormData.hub_id ? 'Select a hub first' : ''"
              :rules="[val => !!val || 'PUE item is required']"
              @update:model-value="onPUEItemSelect"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="devices" />
              </template>
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.name }} (ID: {{ scope.opt.pue_id }})</q-item-label>
                    <q-item-label caption>
                      {{ scope.opt.description || 'No description' }} - {{ scope.opt.status }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
              <template v-slot:no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    No equipment available
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <!-- Quantity Selection -->
            <q-input
              v-model.number="pueFormData.quantity"
              type="number"
              label="Quantity *"
              outlined
              min="1"
              :rules="[val => val > 0 || 'Quantity must be greater than 0']"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="numbers" />
              </template>
            </q-input>

            <q-separator class="q-my-md" />

            <!-- Cost Structure Selection -->
            <div class="text-subtitle2 q-mb-md">Pricing & Duration</div>

            <q-select
              v-model="pueFormData.cost_structure_id"
              :options="availablePUECostStructures"
              option-value="structure_id"
              option-label="name"
              emit-value
              map-options
              label="Cost Structure *"
              outlined
              :loading="loadingPUECostStructures"
              @update:model-value="onPUERentalCostStructureChange"
              :disable="!pueFormData.pue_id"
              :hint="!pueFormData.pue_id ? 'Select a PUE item first' : 'Select a pricing template'"
              :rules="[val => !!val || 'Cost structure is required']"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="receipt" />
              </template>
            </q-select>

            <!-- Duration Selection -->
            <q-select
              v-if="pueFormData.cost_structure_id"
              v-model="pueFormData.duration_preset"
              :options="pueDurationOptions"
              option-value="value"
              option-label="label"
              emit-value
              map-options
              label="Duration *"
              outlined
              @update:model-value="onPUERentalDurationChange"
              :rules="[val => !!val || 'Duration is required']"
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="schedule" />
              </template>
            </q-select>

            <!-- Custom Duration Inputs (if custom selected) -->
            <div v-if="isPUECustomDuration" class="row q-col-gutter-md q-mb-md">
              <div class="col-6">
                <q-input
                  v-model.number="pueFormData.custom_duration_value"
                  type="number"
                  label="Duration Value"
                  outlined
                  min="1"
                  @update:model-value="onPUERentalCustomDurationChange"
                />
              </div>
              <div class="col-6">
                <q-select
                  v-model="pueFormData.custom_duration_unit"
                  :options="['hours', 'days', 'weeks', 'months']"
                  label="Duration Unit"
                  outlined
                  @update:model-value="onPUERentalCustomDurationChange"
                />
              </div>
            </div>

            <!-- Rental Dates -->
            <div class="row q-col-gutter-md q-mb-md">
              <div class="col-6">
                <q-input
                  v-model="pueFormData.rental_start_date"
                  type="datetime-local"
                  label="Rental Start"
                  outlined
                  :rules="[val => !!val || 'Start date is required']"
                >
                  <template v-slot:prepend>
                    <q-icon name="event" />
                  </template>
                </q-input>
              </div>
              <div class="col-6">
                <q-input
                  v-model="pueFormData.due_date"
                  type="datetime-local"
                  label="Due Date"
                  outlined
                  readonly
                  bg-color="grey-2"
                  hint="Automatically calculated from duration"
                >
                  <template v-slot:prepend>
                    <q-icon name="event_available" />
                  </template>
                </q-input>
              </div>
            </div>

            <!-- Cost Estimate Display -->
            <div v-if="pueCostEstimate" class="q-mb-md">
              <q-card flat bordered class="bg-blue-1">
                <q-card-section>
                  <div class="text-subtitle2 q-mb-sm">Cost Estimate</div>
                  <div class="row q-col-gutter-sm">
                    <div class="col-6">
                      <div class="text-caption text-grey-7">Subtotal:</div>
                      <div class="text-body1">{{ currentCurrencySymbol }}{{ pueCostEstimate.subtotal?.toFixed(2) || '0.00' }}</div>
                    </div>
                    <div class="col-6">
                      <div class="text-caption text-grey-7">VAT ({{ pueCostEstimate.vat_percentage || 0 }}%):</div>
                      <div class="text-body1">{{ currentCurrencySymbol }}{{ pueCostEstimate.vat_amount?.toFixed(2) || '0.00' }}</div>
                    </div>
                    <div class="col-12">
                      <q-separator class="q-my-xs" />
                      <div class="text-caption text-grey-7">Total:</div>
                      <div class="text-h6 text-primary">{{ currentCurrencySymbol }}{{ pueCostEstimate.total?.toFixed(2) || '0.00' }}</div>
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <q-separator class="q-my-md" />

            <!-- Payment Method -->
            <div class="text-subtitle2 q-mb-md">Payment Options</div>
            <div class="row q-col-gutter-md q-mb-md">
              <div class="col-12">
                <q-select
                  v-model="pueFormData.payment_method"
                  :options="paymentMethodOptions"
                  label="Payment Method *"
                  outlined
                  emit-value
                  map-options
                  hint="How will the customer pay?"
                  :rules="[val => !!val || 'Payment method is required']"
                >
                  <template v-slot:prepend>
                    <q-icon name="payment" />
                  </template>
                </q-select>
              </div>
            </div>

            <!-- Account Credit Available - Only for upfront/partial payments -->
            <div v-if="pueUserAccount && pueUserAccount.balance > 0 && (pueFormData.payment_method === 'upfront' || pueFormData.payment_method === 'partial')" class="q-mb-md">
              <div class="bg-green-1 q-pa-md rounded-borders">
                <div class="row items-center q-mb-sm">
                  <q-icon name="account_balance_wallet" color="positive" size="sm" class="q-mr-sm" />
                  <div class="col">
                    <div class="text-body2 text-weight-medium">Account Credit Available</div>
                    <div class="text-h6 text-positive">
                      {{ currentCurrencySymbol }}{{ pueUserAccount.balance.toFixed(2) }}
                    </div>
                  </div>
                  <div class="col-auto">
                    <q-btn
                      color="positive"
                      icon="add"
                      label="Apply to Rental"
                      @click="showPUEApplyCreditDialog = true"
                      unelevated
                      no-caps
                    />
                  </div>
                </div>
                <div v-if="pueFormData.credit_used && pueFormData.credit_used > 0" class="bg-white q-pa-sm rounded-borders">
                  <div class="row items-center">
                    <div class="col text-caption">Credit Applied:</div>
                    <div class="col-auto text-body2 text-positive text-weight-medium">
                      -{{ currentCurrencySymbol }}{{ pueFormData.credit_used.toFixed(2) }}
                    </div>
                  </div>
                  <div class="row items-center q-mt-xs">
                    <div class="col text-caption">Remaining to Pay:</div>
                    <div class="col-auto text-body1 text-weight-bold">
                      {{ currentCurrencySymbol }}{{ Math.max(0, (pueCostEstimate?.total || 0) - pueFormData.credit_used).toFixed(2) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <q-separator class="q-my-md" />

            <!-- Deposit & Payment Collection -->
            <div class="q-mb-md">
              <div class="text-subtitle2 q-mb-sm">Payment Collection</div>
              <div class="row q-col-gutter-md">
                <!-- Deposit Collection -->
                <div class="col-12 col-md-6">
                  <q-card flat bordered>
                    <q-card-section class="row items-center">
                      <div class="col">
                        <div class="text-caption text-grey-7">Deposit Amount</div>
                        <div class="text-h6 text-positive">
                          {{ currentCurrencySymbol }}{{ pueFormData.deposit_amount?.toFixed(2) || '0.00' }}
                        </div>
                      </div>
                      <div class="col-auto">
                        <q-btn
                          color="positive"
                          icon="add_circle"
                          label="Collect Deposit"
                          @click="showPUEDepositDialog = true"
                          flat
                        />
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Payment Collection (show for upfront and partial only) -->
                <div v-if="pueFormData.payment_method === 'upfront' || pueFormData.payment_method === 'partial'" class="col-12 col-md-6">
                  <q-card flat bordered>
                    <q-card-section class="row items-center">
                      <div class="col">
                        <div class="text-caption text-grey-7">Payment Collected</div>
                        <div class="text-h6 text-primary">
                          {{ currentCurrencySymbol }}{{ ((pueFormData.amount_paid || 0) + (pueFormData.credit_used || 0)).toFixed(2) }}
                        </div>
                        <div v-if="(pueFormData.amount_paid || 0) + (pueFormData.credit_used || 0) > 0" class="text-caption text-grey-7 q-mt-xs">
                          Est. remaining at return: {{ currentCurrencySymbol }}{{ Math.max(0, (pueCostEstimate?.total || 0) - (pueFormData.amount_paid || 0) - (pueFormData.credit_used || 0)).toFixed(2) }}
                        </div>
                      </div>
                      <div class="col-auto">
                        <q-btn
                          color="primary"
                          icon="payments"
                          label="Collect Payment"
                          @click="showPUEPaymentCollectionDialog = true"
                          flat
                        />
                      </div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </div>

            <div class="row justify-end q-gutter-sm q-mt-md">
              <q-btn label="Cancel" flat @click="closeDialog" />
              <q-btn
                label="Create Rental"
                type="submit"
                color="purple"
                :loading="saving"
                :disable="!pueFormData.pue_id || !pueFormData.cost_structure_id"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- PUE Cost Structure Selection Dialog -->
    <q-dialog v-model="showPUECostStructureDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">Add PUE Item</div>
          <div class="text-caption" v-if="selectedPUEItem">
            {{ selectedPUEItem.name }}
          </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <!-- Cost Structure Selection -->
          <q-select
            v-model="selectedPUECostStructure"
            :options="availablePUECostStructures"
            option-value="structure_id"
            option-label="name"
            emit-value
            map-options
            label="Cost Structure *"
            outlined
            :loading="loadingPUECostStructures"
            @update:model-value="onPUECostStructureChange"
            hint="Select a pricing template"
            class="q-mb-md"
          >
            <template v-slot:prepend>
              <q-icon name="receipt_long" />
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.name }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                  <q-item-label caption class="text-grey-6">
                    {{ scope.opt.components.length }} components
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- Duration Selection -->
          <q-select
            v-if="selectedPUECostStructure"
            v-model="selectedPUEDuration"
            :options="pueDurationOptions"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            label="Duration *"
            outlined
            @update:model-value="onPUEDurationChange"
            hint="Select rental duration"
            class="q-mb-md"
          >
            <template v-slot:prepend>
              <q-icon name="schedule" />
            </template>
          </q-select>

          <!-- Quantity -->
          <q-input
            v-model.number="pueQuantity"
            type="number"
            label="Quantity *"
            outlined
            min="1"
            step="1"
            @update:model-value="calculatePUECostEstimate"
            hint="Number of items"
            class="q-mb-md"
          >
            <template v-slot:prepend>
              <q-icon name="inventory_2" />
            </template>
          </q-input>

          <!-- Cost Estimate Display -->
          <div v-if="pueCostEstimate" class="q-pa-md bg-grey-1 rounded-borders">
            <div class="text-caption text-grey-7 q-mb-sm">Cost Breakdown:</div>
            <div v-for="item in pueCostEstimate.breakdown" :key="item.name" class="row items-center q-mb-xs">
              <div class="col">
                {{ item.name }}
                <span class="text-caption text-grey-6">({{ item.quantity }} × {{ currentCurrencySymbol}}{{ item.rate }})</span>
              </div>
              <div class="col-auto text-weight-medium">{{ currentCurrencySymbol}}{{ item.total.toFixed(2) }}</div>
            </div>
            <q-separator class="q-my-sm" />
            <div class="row items-center q-mb-xs">
              <div class="col text-weight-medium">Subtotal</div>
              <div class="col-auto text-weight-medium">{{ currentCurrencySymbol}}{{ pueCostEstimate.subtotal.toFixed(2) }}</div>
            </div>
            <div class="row items-center q-mb-xs" v-if="pueCostEstimate.vat_amount > 0">
              <div class="col">VAT ({{ pueCostEstimate.vat_percentage }}%)</div>
              <div class="col-auto">{{ currentCurrencySymbol}}{{ pueCostEstimate.vat_amount.toFixed(2) }}</div>
            </div>
            <q-separator class="q-my-sm" />
            <div class="row items-center">
              <div class="col text-h6 text-primary">Total</div>
              <div class="col-auto text-h6 text-primary">{{ currentCurrencySymbol}}{{ pueCostEstimate.total.toFixed(2) }}</div>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showPUECostStructureDialog = false" />
          <q-btn
            flat
            label="Add to Rental"
            color="primary"
            @click="confirmAddPUEItem"
            :disable="!selectedPUECostStructure || !selectedPUEDuration"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Unified Rental Return Dialog -->
    <RentalReturnDialog
      v-model="showReturnDialog"
      :rental="returningRental"
      @returned="onRentalReturned"
    />

    <!-- Quick Returns Dialog -->
    <q-dialog v-model="showQuickReturnsDialog">
      <q-card style="min-width: 600px; max-width: 800px">
        <q-card-section>
          <div class="text-h6">Quick Returns</div>
          <div class="text-caption text-grey-7">Select a rental to return</div>
        </q-card-section>

        <q-card-section>
          <q-list bordered separator>
            <q-item
              v-for="rental in activeRentals"
              :key="rental.rentral_id"
              clickable
              @click="quickReturn(rental)"
            >
              <q-item-section avatar>
                <q-avatar color="primary" text-color="white">
                  <q-icon name="battery_charging_full" />
                </q-avatar>
              </q-item-section>

              <q-item-section>
                <q-item-label>{{ rental.user?.Name || rental.user?.username || `User ${rental.user_id}` }}</q-item-label>
                <q-item-label caption>
                  Battery {{ rental.battery_id }} | Rental ID: {{ rental.rentral_id }}
                </q-item-label>
                <q-item-label caption>
                  Due: {{ formatDate(rental.due_back) }}
                </q-item-label>
              </q-item-section>

              <q-item-section side>
                <q-badge
                  :color="getStatusColor(rental.status)"
                  :label="rental.status"
                />
              </q-item-section>

              <q-item-section side>
                <q-btn
                  flat
                  round
                  dense
                  icon="assignment_return"
                  color="positive"
                />
              </q-item-section>
            </q-item>

            <q-item v-if="activeRentals.length === 0">
              <q-item-section>
                <q-item-label class="text-grey text-center">
                  No active rentals to return
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn label="Close" flat v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Deposit Collection Dialog -->
    <q-dialog v-model="showDepositDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Collect Deposit</div>
          <div class="text-caption text-grey-7">Enter deposit amount collected from customer</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model.number="depositAmount"
            type="number"
            label="Deposit Amount"
            :prefix="currentCurrencySymbol"
            step="0.01"
            outlined
            autofocus
            :rules="[val => val > 0 || 'Amount must be greater than 0']"
          />

          <q-select
            v-model="depositPaymentType"
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

          <div v-if="depositPaymentType" class="bg-orange-1 q-pa-md rounded-borders">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="warning" color="orange" class="q-mr-sm" />
              Payment Confirmation Required
            </div>
            <q-checkbox
              v-model="confirmCashDeposit"
              :label="`I confirm that ${depositPaymentType} payment has been received`"
              color="positive"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup @click="resetDepositDialog" />
          <q-btn
            flat
            label="Confirm Deposit"
            color="positive"
            @click="confirmDeposit"
            :disable="!depositAmount || depositAmount <= 0 || !depositPaymentType || !confirmCashDeposit"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Payment Collection Dialog -->
    <q-dialog v-model="showPaymentCollectionDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Collect Payment</div>
          <div class="text-caption text-grey-7">Enter payment amount collected from customer</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model.number="paymentAmount"
            type="number"
            label="Payment Amount"
            :prefix="currentCurrencySymbol"
            step="0.01"
            outlined
            autofocus
            :rules="[val => val > 0 || 'Amount must be greater than 0']"
          />

          <q-select
            v-model="upfrontPaymentType"
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

          <div v-if="upfrontPaymentType" class="bg-orange-1 q-pa-md rounded-borders">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="warning" color="orange" class="q-mr-sm" />
              Payment Confirmation Required
            </div>
            <q-checkbox
              v-model="confirmCashPayment"
              :label="`I confirm that ${upfrontPaymentType} payment has been received`"
              color="positive"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup @click="resetPaymentDialog" />
          <q-btn
            flat
            label="Confirm Payment"
            color="primary"
            @click="confirmPayment"
            :disable="!paymentAmount || paymentAmount <= 0 || !upfrontPaymentType || !confirmCashPayment"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Apply Credit Dialog -->
    <q-dialog v-model="showApplyCreditDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Apply Account Credit</div>
          <div class="text-caption text-grey-7">Apply customer's existing credit to this rental</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <div class="bg-green-1 q-pa-md rounded-borders">
            <div class="row items-center q-mb-sm">
              <div class="col">
                <div class="text-caption text-grey-7">Available Credit</div>
                <div class="text-h6 text-positive">
                  {{ currentCurrencySymbol }}{{ userAccount?.balance?.toFixed(2) || '0.00' }}
                </div>
              </div>
              <div class="col-auto">
                <div class="text-caption text-grey-7">Rental Total</div>
                <div class="text-h6">
                  {{ currentCurrencySymbol }}{{ costEstimate?.total?.toFixed(2) || '0.00' }}
                </div>
              </div>
            </div>
          </div>

          <q-input
            v-model.number="creditAmountToApply"
            type="number"
            label="Amount to Apply"
            :prefix="currentCurrencySymbol"
            step="0.01"
            outlined
            autofocus
            :rules="[
              val => val > 0 || 'Amount must be greater than 0',
              val => val <= (userAccount?.balance || 0) || 'Cannot exceed available credit',
              val => val <= (costEstimate?.total || 0) || 'Cannot exceed rental total'
            ]"
            :hint="`Maximum: ${currentCurrencySymbol}${Math.min(userAccount?.balance || 0, costEstimate?.total || 0).toFixed(2)}`"
          >
            <template v-slot:append>
              <q-btn
                flat
                dense
                label="Max"
                color="primary"
                @click="creditAmountToApply = Math.min(userAccount?.balance || 0, costEstimate?.total || 0)"
              />
            </template>
          </q-input>

          <div class="bg-blue-1 q-pa-md rounded-borders">
            <div class="text-caption text-grey-7 q-mb-xs">After applying credit:</div>
            <div class="row items-center">
              <div class="col">
                <div class="text-caption">Remaining Balance</div>
                <div class="text-body1">{{ currentCurrencySymbol }}{{ ((userAccount?.balance || 0) - (creditAmountToApply || 0)).toFixed(2) }}</div>
              </div>
              <div class="col-auto">
                <div class="text-caption">Amount Still Owed</div>
                <div class="text-body1">{{ currentCurrencySymbol }}{{ Math.max(0, (costEstimate?.total || 0) - (creditAmountToApply || 0)).toFixed(2) }}</div>
              </div>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup @click="creditAmountToApply = 0" />
          <q-btn
            flat
            label="Apply Credit"
            color="positive"
            @click="applyCredit"
            :disable="!creditAmountToApply || creditAmountToApply <= 0"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { rentalsAPI, batteryRentalsAPI, pueRentalsAPI, hubsAPI, usersAPI, batteriesAPI, pueAPI, settingsAPI, accountsAPI, subscriptionsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useQuasar, date } from 'quasar'
import { useRoute, useRouter } from 'vue-router'
import RentalReturnDialog from 'components/RentalReturnDialog.vue'
import HubFilter from 'src/components/HubFilter.vue'

const $q = useQuasar()
const authStore = useAuthStore()
const hubSettingsStore = useHubSettingsStore()
const route = useRoute()
const router = useRouter()

const rentals = ref([])
const hubOptions = ref([])
const userOptions = ref([])
const availableBatteries = ref([])
const availablePUE = ref([])
const filteredUsers = ref([])
const filteredBatteries = ref([])
const filteredPUE = ref([])
const selectedPUE = ref(null)
const loading = ref(false)
const filter = ref('')
const statusFilter = ref('all')
const rentalTypeFilter = ref('all')
const selectedHub = ref(null)
const showCreateDialog = ref(false)
const showPUERentalDialog = ref(false)
const showReturnDialog = ref(false)
const showQuickReturnsDialog = ref(false)
const showDepositDialog = ref(false)
const showPaymentCollectionDialog = ref(false)
const showApplyCreditDialog = ref(false)
const depositAmount = ref(0)
const paymentAmount = ref(0)
const creditAmountToApply = ref(0)
const depositPaymentType = ref(null)
const upfrontPaymentType = ref(null)
const confirmCashDeposit = ref(false)
const confirmCashPayment = ref(false)
const editingRental = ref(null)
const returningRental = ref(null)
const saving = ref(false)
const returnCostCalculation = ref(null)
const loadingReturnCost = ref(false)
const kwhUsageEnd = ref(null)

// Duration presets
const durationPresets = ref([])
const loadingDurations = ref(false)
const selectedDuration = ref(null)
const durationOptions = ref([{ label: 'Custom', value: 'custom' }])
const customDurationValue = ref(1)
const customDurationUnit = ref('days')

// Computed property to check if custom duration is selected
const isCustomDuration = computed(() => {
  if (!selectedDuration.value) return false
  return selectedDuration.value === 'custom' ||
         selectedDuration.value.toString().startsWith('custom-') ||
         durationOptions.value.find(d => d.value === selectedDuration.value)?.is_custom === true
})

// Pricing configs
const pricingConfigs = ref([])
const loadingPricing = ref(false)

// PUE items with quantities (for display and calculation)
const pueItemsWithQuantity = ref([])

// PUE cost structure selection
const showPUECostStructureDialog = ref(false)
const selectedPUEItem = ref(null)
const selectedPUECostStructure = ref(null)
const availablePUECostStructures = ref([])
const loadingPUECostStructures = ref(false)
const selectedPUEDuration = ref(null)
const pueDurationOptions = ref([{ label: 'Custom', value: 'custom' }])
const pueQuantity = ref(1)
const pueCostEstimate = ref(null)

// PUE Rental Form Data (for separate PUE rental flow)
const pueFormData = ref({
  hub_id: null,
  user_id: null,
  pue_id: null,
  quantity: 1,
  cost_structure_id: null,
  duration_preset: null,
  custom_duration_value: 1,
  custom_duration_unit: 'days',
  rental_start_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
  due_date: null,
  payment_method: null,
  deposit_amount: 0,
  amount_paid: 0,
  credit_used: 0
})

const pueUserAccount = ref(null)
const showPUEApplyCreditDialog = ref(false)
const showPUEDepositDialog = ref(false)
const showPUEPaymentCollectionDialog = ref(false)

// Computed property for custom duration check
const isPUECustomDuration = computed(() => {
  if (!pueFormData.value.duration_preset) return false
  return pueFormData.value.duration_preset === 'custom' ||
         pueFormData.value.duration_preset.toString().startsWith('custom-') ||
         pueDurationOptions.value.find(d => d.value === pueFormData.value.duration_preset)?.is_custom === true
})

// Payment method options
const paymentMethodOptions = [
  { label: 'Pay Upfront', value: 'upfront' },
  { label: 'Pay on Return', value: 'on_return' },
  { label: 'Deposit Only', value: 'deposit_only' },
  { label: 'Partial Payment', value: 'partial' }
]

// Payment type options (from settings)
const paymentTypeOptions = ref([])
const loadingPaymentTypes = ref(false)

// User account information
const userAccount = ref(null)
const loadingUserAccount = ref(false)
const applyCreditToRental = ref(false)

// User subscriptions
const userSubscriptions = ref([])
const selectedSubscription = ref(null)

// Subscription limits and allowed items
const subscriptionAllowedPUE = ref([]) // Array of {pue_id, quantity_limit}
const subscriptionAllowedBatteryCapacity = ref(null) // Minimum capacity required
const subscriptionMaxBatteries = ref(1) // How many batteries allowed

// Cost Structures and Estimator
const availableCostStructures = ref([])
const loadingCostStructures = ref(false)
const selectedCostStructure = ref(null)
const costEstimate = ref(null)
const hubVATPercentage = ref(0)
const estimatedKwh = ref(0)

// Computed properties for dynamic form inputs based on cost structure
const selectedCostStructureObject = computed(() => {
  if (!selectedCostStructure.value) return null
  return availableCostStructures.value.find(s => s.structure_id === selectedCostStructure.value)
})

const requiresDuration = computed(() => {
  if (!selectedCostStructureObject.value) return true // Default to showing duration

  // Check if cost structure has duration options configured
  const hasDurationOptions = selectedCostStructureObject.value.duration_options &&
                             selectedCostStructureObject.value.duration_options.length > 0
  if (hasDurationOptions) return true

  // Otherwise check if any component uses time-based units
  const components = selectedCostStructureObject.value.components || []
  return components.some(c => ['per_day', 'per_hour', 'per_week', 'per_month'].includes(c.unit_type))
})

const requiresKwhEstimate = computed(() => {
  if (!selectedCostStructureObject.value) return false
  const components = selectedCostStructureObject.value.components || []
  return components.some(c => c.unit_type === 'per_kwh')
})

const selectedBatteryCapacity = computed(() => {
  if (!formData.value.battery_id) return null
  const battery = availableBatteries.value.find(b => b.battery_id === formData.value.battery_id)
  return battery?.battery_capacity_wh || null
})

const typicalUsageEstimate = computed(() => {
  if (!selectedBatteryCapacity.value) return '0'
  // Estimate typical usage based on battery capacity and rental duration
  const capacityKwh = selectedBatteryCapacity.value / 1000

  // Get rental duration in days (default to 7 if not set)
  let durationDays = 7
  if (formData.value.due_back && formData.value.timestamp_taken) {
    const start = new Date(formData.value.timestamp_taken)
    const end = new Date(formData.value.due_back)
    durationDays = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)))
  }

  // Conservative estimate: assume 70-80% depth of discharge per charge cycle
  // and 1 full cycle per 2 days (moderate usage)
  const cyclesPerDay = 0.5
  const averageDischargePerCycle = capacityKwh * 0.75
  const estimatedUsage = durationDays * cyclesPerDay * averageDischargePerCycle

  return estimatedUsage.toFixed(1)
})

const kwhEstimateHint = computed(() => {
  if (!selectedBatteryCapacity.value) {
    return 'Estimate for cost calculation (actual usage calculated on return)'
  }
  return `Enter estimated kWh usage. Actual usage will be calculated on return based on meter readings.`
})

const getTimeBasedComponents = () => {
  if (!selectedCostStructureObject.value) return ''
  const components = selectedCostStructureObject.value.components || []
  const timeComponents = components.filter(c =>
    ['per_day', 'per_hour', 'per_week', 'per_month'].includes(c.unit_type)
  )
  return timeComponents.map(c => c.component_name).join(', ')
}

// Computed property for active rentals
const activeRentals = computed(() => {
  return rentals.value.filter(r => r.status === 'active' || r.status === 'overdue')
})

// Use centralized currency symbol from hub settings store
const currentCurrencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

// Computed property for automatic payment status
const computedPaymentStatus = computed(() => {
  const totalCost = costEstimate.value?.total || formData.value.total_cost || 0
  const amountPaid = (formData.value.amount_paid || 0) + (formData.value.deposit_amount || 0)
  const hasEstimatedComponent = costEstimate.value?.has_estimated_component || false

  // If there's an estimated component, it's always partial
  if (hasEstimatedComponent) {
    return 'partial'
  }

  // If nothing paid
  if (amountPaid === 0) {
    return 'unpaid'
  }

  // If paid in full (or more)
  if (amountPaid >= totalCost) {
    return 'paid'
  }

  // Otherwise partial
  return 'partial'
})

// Check if rental is covered by subscription
const isSubscriptionRental = computed(() => {
  return selectedSubscription.value !== null && selectedSubscription.value !== undefined
})

// Get selected subscription details
const selectedSubscriptionDetails = computed(() => {
  if (!isSubscriptionRental.value) return null
  return userSubscriptions.value.find(s => s.subscription_id === selectedSubscription.value)
})

// Subscription hint for PUE selection
const subscriptionHint = computed(() => {
  if (isSubscriptionRental.value && subscriptionAllowedPUE.value.length > 0) {
    return 'Only subscription items can be added'
  }
  return ''
})

const formData = ref({
  rentral_id: null,
  rental_unique_id: null,
  hub_id: null,
  user_id: null,
  battery_id: null,
  timestamp_taken: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
  due_back: date.formatDate(
    date.addToDate(new Date(), { days: 7 }),
    'YYYY-MM-DDTHH:mm'
  ),
  battery_cost: 0,
  pue_cost: 0,
  total_cost: 0,
  deposit_amount: 0,
  payment_method: 'on_return',  // Default to pay on return
  payment_type: null,  // Cash, mobile money, etc.
  payment_status: 'unpaid',
  amount_paid: 0,
  amount_owed: 0,
  pue_item_ids: []
})

const returnData = ref({
  actual_return_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
  return_notes: '',
  collectPayment: false,
  payment_amount: 0,
  payment_notes: ''
})

const columns = [
  { name: 'rentral_id', label: 'ID', field: 'rentral_id', align: 'left', sortable: true },
  { name: 'rental_type', label: 'Type', field: 'rental_type', align: 'center', sortable: true },
  { name: 'hub', label: 'Hub', field: row => row.hub?.what_three_word_location || `Hub ${row.hub?.hub_id || '-'}`, align: 'left', sortable: true },
  { name: 'user', label: 'User', field: row => row.user?.Name || row.user?.username || `User ${row.user_id}`, align: 'left', sortable: true },
  { name: 'battery', label: 'Battery', field: row => row.battery?.short_id || `Battery ${row.battery_id}`, align: 'left' },
  { name: 'subscription', label: 'Subscription', field: row => row.subscription?.package_name || '-', align: 'left', sortable: true },
  { name: 'timestamp_taken', label: 'Rental Date', field: 'timestamp_taken', align: 'left', sortable: true },
  { name: 'due_back', label: 'Due Back', field: 'due_back', align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'total_cost', label: 'Total Cost', field: 'total_cost', align: 'left', sortable: true },
  { name: 'payment_status', label: 'Payment', field: 'payment_status', align: 'center', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const getStatusColor = (status) => {
  const colors = {
    active: 'positive',
    returned: 'grey',
    overdue: 'negative',
    cancelled: 'warning'
  }
  return colors[status] || 'grey'
}

const getStatusTooltip = (status) => {
  const tooltips = {
    active: 'Rental is currently active',
    returned: 'All items have been returned',
    overdue: 'Rental is past due date',
    cancelled: 'Rental was cancelled'
  }
  return tooltips[status] || status
}

const getPaymentStatusColor = (status) => {
  if (status === null || status === undefined) return 'grey'
  const colors = {
    paid: 'positive',
    partial: 'warning',
    deposit_only: 'info',
    unpaid: 'negative',
    pending_kwh: 'orange'
  }
  return colors[status] || 'grey'
}

const getPaymentStatusLabel = (status) => {
  if (status === null || status === undefined) return 'Pending'
  const labels = {
    paid: 'Paid in Full',
    partial: 'Partial',
    deposit_only: 'Deposit Only',
    unpaid: 'Unpaid',
    pending_kwh: 'Pending kWh'
  }
  return labels[status] || status || 'Unknown'
}

const getPaymentStatusDescription = (rental) => {
  if (!rental) return ''

  const status = rental.payment_status

  // For active rentals without calculated cost
  if (status === null || status === undefined) {
    return 'Cost will be calculated when rental is returned'
  }

  const amountPaid = rental.amount_paid || 0
  const amountOwed = rental.amount_owed || 0
  const totalCost = rental.total_cost || 0

  if (status === 'paid') {
    return `Paid in full: ${currentCurrencySymbol.value}${amountPaid.toFixed(2)}`
  } else if (status === 'partial') {
    return `Paid: ${currentCurrencySymbol.value}${amountPaid.toFixed(2)} | Owed: ${currentCurrencySymbol.value}${amountOwed.toFixed(2)}`
  } else if (status === 'deposit_only') {
    return `Deposit collected: ${currentCurrencySymbol.value}${(rental.deposit_amount || 0).toFixed(2)}`
  } else if (status === 'unpaid') {
    return `Amount due: ${currentCurrencySymbol.value}${totalCost.toFixed(2)}`
  } else if (status === 'pending_kwh') {
    return `Pending kWh calculation. Partial: ${currentCurrencySymbol.value}${amountPaid.toFixed(2)}`
  }
  return ''
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm') + ' UTC'
}

const onRowClick = (evt, row) => {
  if (row.rental_type === 'battery') {
    router.push(`/rentals/battery/${row.rentral_id}`)
  } else if (row.rental_type === 'pue') {
    router.push(`/rentals/pue/${row.rentral_id}`)
  } else {
    // Fallback for legacy rentals
    router.push({ name: 'rental-detail', params: { id: row.rentral_id } })
  }
}

const loadRentals = async () => {
  loading.value = true
  try {
    const params = {}

    // Map status filter to API parameter
    if (statusFilter.value !== 'all') {
      params.status = statusFilter.value
    }

    // Add hub filter if selected
    if (selectedHub.value) {
      params.hub_id = selectedHub.value
    }

    let allRentals = []

    // Load rentals based on rental type filter
    if (rentalTypeFilter.value === 'all') {
      // Load both battery and PUE rentals
      const [batteryResponse, pueResponse] = await Promise.all([
        batteryRentalsAPI.list(params),
        pueRentalsAPI.list(params)
      ])

      // Add rental_type field to each item
      const batteryRentals = (batteryResponse.data || []).map(rental => ({
        ...rental,
        rental_type: 'battery'
      }))

      const pueRentals = (pueResponse.data || []).map(rental => ({
        ...rental,
        rental_type: 'pue'
      }))

      allRentals = [...batteryRentals, ...pueRentals]
    } else if (rentalTypeFilter.value === 'battery') {
      // Load only battery rentals
      const response = await batteryRentalsAPI.list(params)
      allRentals = (response.data || []).map(rental => ({
        ...rental,
        rental_type: 'battery'
      }))
    } else if (rentalTypeFilter.value === 'pue') {
      // Load only PUE rentals
      const response = await pueRentalsAPI.list(params)
      allRentals = (response.data || []).map(rental => ({
        ...rental,
        rental_type: 'pue'
      }))
    }

    rentals.value = allRentals
  } catch (error) {
    console.error('Failed to load rentals:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to load rentals',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const buildDurationOptionsFromStructure = (structureDurationOptions) => {
  durationOptions.value = []

  structureDurationOptions.forEach((option, index) => {
    if (option.input_type === 'dropdown' && option.dropdown_options) {
      // Parse dropdown_options JSON
      let choices = []
      try {
        choices = typeof option.dropdown_options === 'string'
          ? JSON.parse(option.dropdown_options)
          : option.dropdown_options
      } catch (e) {
        console.error('Failed to parse dropdown_options:', e)
        return
      }

      // Add each choice as a selectable option
      choices.forEach((choice, choiceIndex) => {
        durationOptions.value.push({
          label: choice.label,
          value: `${option.option_id}-${choiceIndex}`,
          duration_value: choice.value,
          duration_unit: choice.unit,
          option_id: option.option_id
        })
      })
    } else if (option.input_type === 'custom') {
      // For custom input, show the range as a custom option
      durationOptions.value.push({
        label: `Custom (${option.min_value || 1}-${option.max_value || 99} ${option.custom_unit || 'days'})`,
        value: `custom-${option.option_id}`,
        is_custom: true,
        custom_unit: option.custom_unit,
        min_value: option.min_value,
        max_value: option.max_value,
        default_value: option.default_value,
        option_id: option.option_id
      })
    }
  })

  // Always add a "Custom" option at the end to allow manual entry
  durationOptions.value.push({
    label: 'Custom',
    value: 'custom',
    is_custom: true
  })
}

const loadDurationPresets = async () => {
  // This function is now deprecated - duration options come from cost structures
  // Keeping it for backward compatibility if no cost structure is selected
  if (!formData.value.hub_id) return

  try {
    loadingDurations.value = true
    const response = await settingsAPI.getDurationPresets(formData.value.hub_id)
    durationPresets.value = response.data.presets

    // Build duration options
    durationOptions.value = response.data.presets.map(p => ({
      label: p.label,
      value: p.preset_id,
      duration_value: p.duration_value,
      duration_unit: p.duration_unit
    }))

    // Add custom option at the end
    durationOptions.value.push({ label: 'Custom', value: 'custom' })
  } catch (error) {
    console.error('Failed to load duration presets:', error)
  } finally {
    loadingDurations.value = false
  }
}

const onStartDateChange = () => {
  // When start date changes, recalculate due date if a preset is selected
  if (selectedDuration.value && selectedDuration.value !== 'custom') {
    onDurationChange(selectedDuration.value)
  }
}

const onDurationChange = async (selectedValue) => {
  if (!selectedValue) return

  // Find the selected duration option
  const duration = durationOptions.value.find(d => d.value === selectedValue)
  if (!duration) return

  // If it's a custom duration option, just return (custom inputs will handle it)
  if (duration.is_custom) {
    // Set default values for custom inputs
    if (duration.custom_unit) {
      customDurationUnit.value = duration.custom_unit
    }
    if (duration.default_value) {
      customDurationValue.value = duration.default_value
    }
    // Trigger custom duration calculation
    await onCustomDurationChange()
    return
  }

  // For dropdown options, use the duration_value and duration_unit
  const durationValue = duration.duration_value
  const durationUnit = duration.duration_unit

  if (!durationValue || !durationUnit) return

  // Calculate due date based on duration
  const startDate = new Date(formData.value.timestamp_taken)
  let dueDate

  switch (durationUnit) {
    case 'hours':
      dueDate = date.addToDate(startDate, { hours: durationValue })
      break
    case 'days':
      const nextDay = date.addToDate(startDate, { days: 1 })
      const startOfNextDay = new Date(nextDay.setHours(0, 0, 0, 0))
      dueDate = date.addToDate(startOfNextDay, { days: durationValue - 1 })
      dueDate.setHours(23, 59, 0, 0)
      break
    case 'weeks':
      const nextDayForWeek = date.addToDate(startDate, { days: 1 })
      const startOfNextDayForWeek = new Date(nextDayForWeek.setHours(0, 0, 0, 0))
      dueDate = date.addToDate(startOfNextDayForWeek, { days: (durationValue * 7) - 1 })
      dueDate.setHours(23, 59, 0, 0)
      break
    case 'months':
      const nextDayForMonth = date.addToDate(startDate, { days: 1 })
      const startOfNextDayForMonth = new Date(nextDayForMonth.setHours(0, 0, 0, 0))
      dueDate = date.addToDate(startOfNextDayForMonth, { months: durationValue })
      dueDate = date.addToDate(dueDate, { days: -1 })
      dueDate.setHours(23, 59, 0, 0)
      break
    default:
      const nextDayDefault = date.addToDate(startDate, { days: 1 })
      const startOfNextDayDefault = new Date(nextDayDefault.setHours(0, 0, 0, 0))
      dueDate = date.addToDate(startOfNextDayDefault, { days: durationValue - 1 })
      dueDate.setHours(23, 59, 0, 0)
  }

  formData.value.due_back = date.formatDate(dueDate, 'YYYY-MM-DDTHH:mm')

  // Fetch cost estimate for this duration
  if (selectedCostStructure.value) {
    try {
      const params = {
        duration_value: durationValue,
        duration_unit: durationUnit,
        vat_percentage: hubVATPercentage.value
      }

      const response = await settingsAPI.estimateCost(selectedCostStructure.value, params)
      costEstimate.value = response.data

      // Update formData with estimated costs
      formData.value.estimated_cost_before_vat = response.data.subtotal
      formData.value.estimated_vat = response.data.vat_amount
      formData.value.estimated_cost_total = response.data.total
      formData.value.cost_structure_id = selectedCostStructure.value
      formData.value.total_cost = response.data.total

    } catch (error) {
      console.error('Failed to estimate cost:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to calculate cost estimate',
        position: 'top'
      })
    }
  }

  // Recalculate PUE cost based on new duration
  if (pueItemsWithQuantity.value.length > 0) {
    pueItemsWithQuantity.value.forEach(item => {
      const pueItem = availablePUE.value.find(p => p.pue_id === item.pue_id)
      if (!pueItem) return

      let pricing = pricingConfigs.value.find(p =>
        p.item_type === 'pue_item' &&
        p.item_reference === String(item.pue_id) &&
        p.is_active
      )

      if (!pricing && pueItem.pue_type) {
        pricing = pricingConfigs.value.find(p =>
          p.item_type === 'pue_type' &&
          p.item_reference === pueItem.pue_type &&
          p.is_active
        )
      }

      if (pricing) {
        item.pricePerUnit = calculateCostByUnit(pricing)
        item.unitType = pricing.unit_type
      }
    })

    calculatePUECostFromQuantities()
  }
}

const onCustomDurationChange = async () => {
  if (!customDurationValue.value || customDurationValue.value < 1) {
    customDurationValue.value = 1
  }

  if (!customDurationUnit.value) {
    customDurationUnit.value = 'days'
  }

  // Calculate due back date based on custom duration
  const now = new Date()
  const dueDate = new Date(now)

  switch (customDurationUnit.value) {
    case 'hours':
      dueDate.setHours(dueDate.getHours() + customDurationValue.value)
      break
    case 'days':
      dueDate.setDate(dueDate.getDate() + customDurationValue.value)
      break
    case 'weeks':
      dueDate.setDate(dueDate.getDate() + (customDurationValue.value * 7))
      break
    case 'months':
      dueDate.setMonth(dueDate.getMonth() + customDurationValue.value)
      break
  }

  formData.value.due_back = date.formatDate(dueDate, 'YYYY-MM-DDTHH:mm')

  // Fetch cost estimate with custom duration
  if (selectedCostStructure.value) {
    try {
      const params = {
        duration_value: customDurationValue.value,
        duration_unit: customDurationUnit.value,
        vat_percentage: hubVATPercentage.value
      }

      const response = await settingsAPI.estimateCost(selectedCostStructure.value, params)
      costEstimate.value = response.data

      // Update formData with estimated costs
      formData.value.estimated_cost_before_vat = response.data.subtotal
      formData.value.estimated_vat = response.data.vat_amount
      formData.value.estimated_cost_total = response.data.total
      formData.value.cost_structure_id = selectedCostStructure.value
      formData.value.total_cost = response.data.total

    } catch (error) {
      console.error('Failed to estimate cost with custom duration:', error)
      $q.notify({
        type: 'negative',
        message: 'Failed to calculate cost estimate',
        position: 'top'
      })
    }
  }

  // Recalculate PUE cost based on new duration
  if (pueItemsWithQuantity.value.length > 0) {
    pueItemsWithQuantity.value.forEach(item => {
      const pueItem = availablePUE.value.find(p => p.pue_id === item.pue_id)
      if (!pueItem) return

      let pricing = pricingConfigs.value.find(p =>
        p.item_type === 'pue_item' &&
        p.item_reference === String(item.pue_id) &&
        p.is_active
      )

      if (!pricing && pueItem.pue_type) {
        pricing = pricingConfigs.value.find(p =>
          p.item_type === 'pue_type' &&
          p.item_reference === pueItem.pue_type &&
          p.is_active
        )
      }

      if (pricing) {
        item.pricePerUnit = calculateCostByUnit(pricing)
        item.unitType = pricing.unit_type
      }
    })

    calculatePUECostFromQuantities()
  }
}

const onKwhChange = async () => {
  // Recalculate cost estimate when kWh value changes
  if (!selectedCostStructure.value || !estimatedKwh.value) return

  try {
    const params = {
      vat_percentage: hubVATPercentage.value
    }

    // Add duration if available
    if (formData.value.due_back && formData.value.timestamp_taken) {
      const start = new Date(formData.value.timestamp_taken)
      const end = new Date(formData.value.due_back)
      const durationHours = (end - start) / (1000 * 60 * 60)
      params.duration_value = durationHours
      params.duration_unit = 'hours'
    }

    // Add kWh estimate
    params.estimated_kwh = estimatedKwh.value

    const response = await settingsAPI.estimateCost(selectedCostStructure.value, params)
    costEstimate.value = response.data

    // Update formData with estimated costs
    formData.value.estimated_cost_before_vat = response.data.subtotal
    formData.value.estimated_vat = response.data.vat_amount
    formData.value.estimated_cost_total = response.data.total
    formData.value.cost_structure_id = selectedCostStructure.value
    formData.value.battery_cost = response.data.total
    formData.value.total_cost = response.data.total

  } catch (error) {
    console.error('Failed to recalculate cost with kWh:', error)
  }
}

const calculateTotalCost = () => {
  const batteryCost = parseFloat(formData.value.battery_cost) || 0
  const pueCost = parseFloat(formData.value.pue_cost) || 0
  formData.value.total_cost = batteryCost + pueCost
  calculateAmountOwed()
}

const calculateAmountOwed = () => {
  const totalCost = parseFloat(formData.value.total_cost) || 0
  const amountPaid = parseFloat(formData.value.amount_paid) || 0
  formData.value.amount_owed = Math.max(0, totalCost - amountPaid)
}

const onHubChange = async (hubId) => {
  selectedHub.value = hubId

  // Reload rentals list with the new hub filter
  await loadRentals()

  if (!hubId) return

  try {
    // Load available batteries for this hub
    const batteriesResponse = await hubsAPI.getBatteries(hubId)
    availableBatteries.value = batteriesResponse.data.filter(
      b => b.status === 'available'
    )
    filteredBatteries.value = availableBatteries.value

    // Load available PUE for this hub
    const pueResponse = await hubsAPI.getPUE(hubId)
    availablePUE.value = pueResponse.data.filter(
      p => p.status === 'available'
    )
    filteredPUE.value = availablePUE.value

    // Load users for this hub
    const usersResponse = await hubsAPI.getUsers(hubId)
    userOptions.value = usersResponse.data
    filteredUsers.value = userOptions.value

    // Load duration presets for this hub
    await loadDurationPresets()

    // Load pricing configs for this hub
    await loadPricingConfigs(hubId)

    // Load payment types for this hub
    await loadPaymentTypes(hubId)
  } catch (error) {
    console.error('Failed to load hub data:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load hub data',
      position: 'top'
    })
  }
}

const loadPricingConfigs = async (hubId) => {
  try {
    loadingPricing.value = true
    const response = await settingsAPI.getPricingConfigs({ hub_id: hubId })
    pricingConfigs.value = response.data.filter(p => p.is_active)
  } catch (error) {
    console.error('Failed to load pricing configs:', error)
  } finally {
    loadingPricing.value = false
  }
}

const loadPaymentTypes = async (hubId) => {
  try {
    loadingPaymentTypes.value = true
    const response = await settingsAPI.getPaymentTypes({ hub_id: hubId, is_active: true })
    paymentTypeOptions.value = response.data.payment_types.map(pt => ({
      label: pt.type_name,
      value: pt.type_name
    }))
  } catch (error) {
    console.error('Failed to load payment types:', error)
  } finally {
    loadingPaymentTypes.value = false
  }
}

const loadUserAccount = async (userId) => {
  if (!userId) {
    userAccount.value = null
    applyCreditToRental.value = false
    userSubscriptions.value = []
    selectedSubscription.value = null
    return
  }

  try {
    loadingUserAccount.value = true
    const response = await accountsAPI.getUserAccount(userId)
    userAccount.value = response.data
    // Reset apply credit when user changes
    applyCreditToRental.value = false

    // Load user subscriptions
    await loadUserSubscriptions(userId)
  } catch (error) {
    console.error('Failed to load user account:', error)
    userAccount.value = null
    applyCreditToRental.value = false
    userSubscriptions.value = []
  } finally {
    loadingUserAccount.value = false
  }
}

const loadUserSubscriptions = async (userId) => {
  if (!userId) return

  try {
    const response = await subscriptionsAPI.getUserSubscriptions(userId)
    userSubscriptions.value = (response.data.subscriptions || []).filter(s => s.status === 'active')
  } catch (error) {
    console.error('Failed to load user subscriptions:', error)
    userSubscriptions.value = []
  }
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

const onSubscriptionSelect = async () => {
  if (!selectedSubscription.value) {
    // Subscription cleared, reset payment method to default and clear limits
    formData.value.payment_method = 'on_return'
    subscriptionAllowedPUE.value = []
    subscriptionAllowedBatteryCapacity.value = null
    subscriptionMaxBatteries.value = 1
    return
  }

  try {
    // Get the subscription details - items are already included from the API
    const subscription = userSubscriptions.value.find(s => s.subscription_id === selectedSubscription.value)
    if (!subscription) {
      console.warn('Subscription not found:', selectedSubscription.value)
      return
    }

    // Set payment method to 'subscription' when subscription is applied
    formData.value.payment_method = 'subscription'

    // Reset subscription limits
    subscriptionAllowedPUE.value = []
    subscriptionAllowedBatteryCapacity.value = null
    subscriptionMaxBatteries.value = 1

    $q.notify({
      type: 'info',
      message: `Loading items from "${subscription.package_name}"...`,
      position: 'top'
    })

    // Process subscription items and set limits
    if (subscription.items && subscription.items.length > 0) {
      for (const item of subscription.items) {
        if (item.item_type === 'battery_capacity') {
          // Store battery capacity requirement and quantity limit
          const requiredCapacity = parseInt(item.item_reference)
          subscriptionAllowedBatteryCapacity.value = requiredCapacity
          subscriptionMaxBatteries.value = item.quantity_limit || 1

          // Find batteries matching the capacity requirement
          const compatibleBattery = availableBatteries.value.find(b =>
            b.battery_capacity_wh >= requiredCapacity
          )

          if (compatibleBattery) {
            formData.value.battery_id = compatibleBattery.battery_id
            await onBatterySelected()
          } else {
            console.warn('No compatible battery found for capacity:', requiredCapacity)
          }
        } else if (item.item_type === 'pue_item') {
          // Store allowed PUE items with their quantity limits
          const pueId = parseInt(item.item_reference)
          subscriptionAllowedPUE.value.push({
            pue_id: pueId,
            quantity_limit: item.quantity_limit || 1
          })

          // Auto-add PUE items from subscription (up to quantity limit)
          if (pueId && !formData.value.pue_item_ids.includes(pueId)) {
            formData.value.pue_item_ids.push(pueId)
          }
        }
      }

      $q.notify({
        type: 'positive',
        message: 'Subscription items loaded successfully',
        position: 'top'
      })
    } else {
      $q.notify({
        type: 'warning',
        message: 'No items found in subscription package',
        position: 'top'
      })
    }
  } catch (error) {
    console.error('Failed to load subscription items:', error)
    $q.notify({
      type: 'negative',
      message: `Failed to load subscription items: ${error.message}`,
      position: 'top'
    })
  }
}

const onApplyCreditChange = () => {
  if (!applyCreditToRental.value) {
    // Credit unchecked - recalculate without credit
    calculateTotalCost()
    return
  }

  // Credit checked - apply credit to reduce amount owed
  if (userAccount.value && userAccount.value.balance > 0) {
    const creditToApply = Math.min(userAccount.value.balance, formData.value.total_cost || 0)
    formData.value.amount_paid = (formData.value.amount_paid || 0) + creditToApply
    formData.value.amount_owed = Math.max(0, (formData.value.total_cost || 0) - formData.value.amount_paid)

    // Update payment status
    if (formData.value.amount_owed === 0) {
      formData.value.payment_status = 'paid'
    } else if (formData.value.amount_paid > 0) {
      formData.value.payment_status = 'partial'
    }
  }
}

const loadCostStructures = async (hubId, batteryCapacity) => {
  if (!hubId) return

  try {
    loadingCostStructures.value = true

    // Load cost structures that match this battery's capacity
    const capacityResponse = batteryCapacity ? await settingsAPI.getCostStructures({
      hub_id: hubId,
      item_type: 'battery_capacity',
      item_reference: String(batteryCapacity),
      is_active: true
    }) : { data: { cost_structures: [] } }

    // Load cost structures that apply to "all batteries"
    const allBatteriesResponse = await settingsAPI.getCostStructures({
      hub_id: hubId,
      item_type: 'battery',
      item_reference: 'all',
      is_active: true
    })

    // Combine both sets of cost structures
    const capacityStructures = capacityResponse.data.cost_structures || []
    const allBatteriesStructures = allBatteriesResponse.data.cost_structures || []
    availableCostStructures.value = [...capacityStructures, ...allBatteriesStructures]

  } catch (error) {
    console.error('Failed to load cost structures:', error)
    availableCostStructures.value = []
  } finally {
    loadingCostStructures.value = false
  }
}

const loadHubVAT = async (hubId) => {
  try {
    const response = await settingsAPI.getHubSettings(hubId)
    hubVATPercentage.value = response.data.vat_percentage || 0
    // Currency is now handled by hubSettingsStore
  } catch (error) {
    console.error('Failed to load hub settings:', error)
    hubVATPercentage.value = 0
  }
}

const onCostStructureChange = async (structureId) => {
  costEstimate.value = null

  if (!structureId) {
    durationOptions.value = [{ label: 'Custom', value: 'custom' }]
    selectedDuration.value = null
    return
  }

  // Load duration options from the selected cost structure
  const structure = availableCostStructures.value.find(s => s.structure_id === structureId)

  if (structure && structure.duration_options && structure.duration_options.length > 0) {
    buildDurationOptionsFromStructure(structure.duration_options)
  } else {
    // Fallback to custom only
    durationOptions.value = [{ label: 'Custom', value: 'custom' }]
  }

  // Only calculate estimate if duration is already selected
  if (!selectedDuration.value) {
    return
  }

  try {
    const duration = durationOptions.value.find(d => d.value === selectedDuration.value)
    if (!duration) return

    const params = {
      duration_value: duration.duration_value,
      duration_unit: duration.duration_unit,
      vat_percentage: hubVATPercentage.value
    }

    const response = await settingsAPI.estimateCost(structureId, params)
    costEstimate.value = response.data

    // Update formData with estimated costs
    formData.value.estimated_cost_before_vat = response.data.subtotal
    formData.value.estimated_vat = response.data.vat_amount
    formData.value.estimated_cost_total = response.data.total
    formData.value.cost_structure_id = structureId
    formData.value.total_cost = response.data.total

  } catch (error) {
    console.error('Failed to estimate cost:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to calculate cost estimate',
      position: 'top'
    })
  }
}

const onBatterySelected = async (batteryId) => {
  if (!batteryId) return

  // Find selected battery
  const battery = availableBatteries.value.find(b => b.battery_id === batteryId)
  if (!battery) return

  // Load cost structures for this battery capacity
  if (battery.battery_capacity_wh && formData.value.hub_id) {
    await loadCostStructures(formData.value.hub_id, battery.battery_capacity_wh)
    await loadHubVAT(formData.value.hub_id)
  }

  // Calculate cost based on pricing configs and rental duration
  const cost = calculateBatteryCost(battery)
  if (cost > 0) {
    formData.value.battery_cost = cost
    calculateTotalCost()
  }
}

const calculateBatteryCost = (battery) => {
  if (!battery.battery_capacity_wh) return 0

  // Find matching pricing config for battery capacity
  const capacityStr = String(battery.battery_capacity_wh)
  const pricing = pricingConfigs.value.find(p =>
    p.item_type === 'battery_capacity' &&
    p.item_reference === capacityStr &&
    p.is_active
  )

  if (!pricing) return 0

  // Calculate cost based on unit type and rental duration
  return calculateCostByUnit(pricing)
}

const calculateCostByUnit = (pricing) => {
  const unitType = pricing.unit_type
  const price = parseFloat(pricing.price)

  if (!formData.value.timestamp_taken || !formData.value.due_back) {
    // Default to base price if no dates set
    return price
  }

  const startDate = new Date(formData.value.timestamp_taken)
  const endDate = new Date(formData.value.due_back)
  const durationMs = endDate - startDate
  const durationHours = durationMs / (1000 * 60 * 60)
  const durationDays = durationHours / 24

  switch (unitType) {
    case 'per_hour':
      return price * Math.ceil(durationHours)
    case 'per_day':
      return price * Math.ceil(durationDays)
    case 'per_week':
      return price * Math.ceil(durationDays / 7)
    case 'per_month':
      return price * Math.ceil(durationDays / 30)
    case 'per_kwh':
      // For kWh, we can't calculate without usage data, so return base price
      return price
    default:
      return price
  }
}

// Calculate total PUE cost based on pricing configs or PUE item rental_cost (legacy method)
const calculatePUECost = () => {
  if (!formData.value.pue_item_ids || formData.value.pue_item_ids.length === 0) {
    formData.value.pue_cost = 0
    calculateTotalCost()
    return
  }

  let totalPUECost = 0

  formData.value.pue_item_ids.forEach(pueId => {
    const pueItem = availablePUE.value.find(p => p.pue_id === pueId)
    if (!pueItem) return

    // Try to find pricing config for this specific PUE item
    let pricing = pricingConfigs.value.find(p =>
      p.item_type === 'pue_item' &&
      p.item_reference === String(pueId) &&
      p.is_active
    )

    // If no specific pricing, try to find pricing for the PUE type
    if (!pricing && pueItem.pue_type) {
      pricing = pricingConfigs.value.find(p =>
        p.item_type === 'pue_type' &&
        p.item_reference === pueItem.pue_type &&
        p.is_active
      )
    }

    // If pricing config exists, calculate cost based on unit type
    if (pricing) {
      totalPUECost += calculateCostByUnit(pricing)
    } else if (pueItem.rental_cost) {
      // Fallback to PUE item's rental_cost field
      totalPUECost += parseFloat(pueItem.rental_cost)
    }
  })

  formData.value.pue_cost = totalPUECost
  calculateTotalCost()
}

// Calculate total PUE cost based on quantities
const calculatePUECostFromQuantities = () => {
  let totalPUECost = 0

  pueItemsWithQuantity.value.forEach(item => {
    totalPUECost += item.pricePerUnit * item.quantity
  })

  formData.value.pue_cost = totalPUECost

  // Update pue_item_ids for backend (repeat IDs based on quantity)
  formData.value.pue_item_ids = []
  pueItemsWithQuantity.value.forEach(item => {
    for (let i = 0; i < item.quantity; i++) {
      formData.value.pue_item_ids.push(item.pue_id)
    }
  })

  calculateTotalCost()
}

// Handler for when PUE quantity changes
const onPUEQuantityChange = () => {
  calculatePUECostFromQuantities()
}

const filterUsers = (val, update) => {
  update(() => {
    if (val === '') {
      filteredUsers.value = userOptions.value
    } else {
      const needle = val.toLowerCase()
      filteredUsers.value = userOptions.value.filter(u =>
        String(u.user_id).toLowerCase().includes(needle) ||
        (u.username && u.username.toLowerCase().includes(needle)) ||
        (u.Name && u.Name.toLowerCase().includes(needle)) ||
        (u.mobile_number && u.mobile_number.toLowerCase().includes(needle))
      )
    }
  })
}

const filterBatteries = (val, update) => {
  update(() => {
    if (val === '') {
      filteredBatteries.value = availableBatteries.value
    } else {
      const needle = val.toLowerCase()
      filteredBatteries.value = availableBatteries.value.filter(b =>
        String(b.battery_id).toLowerCase().includes(needle) ||
        (b.battery_capacity_wh && String(b.battery_capacity_wh).toLowerCase().includes(needle))
      )
    }
  })
}

const filterPUE = (val, update) => {
  update(() => {
    // Start with all available PUE
    let pueList = availablePUE.value

    // If subscription is active, filter to only allowed items
    if (isSubscriptionRental.value && subscriptionAllowedPUE.value.length > 0) {
      const allowedIds = subscriptionAllowedPUE.value.map(a => a.pue_id)
      pueList = pueList.filter(p => allowedIds.includes(p.pue_id))
    }

    // Apply search filter
    if (val === '') {
      filteredPUE.value = pueList
    } else {
      const needle = val.toLowerCase()
      filteredPUE.value = pueList.filter(p =>
        String(p.pue_id).toLowerCase().includes(needle) ||
        p.name.toLowerCase().includes(needle) ||
        (p.description && p.description.toLowerCase().includes(needle))
      )
    }
  })
}

const addPUEToRental = async (pue) => {
  if (!pue) return

  // Check subscription limits if subscription is active
  if (isSubscriptionRental.value && subscriptionAllowedPUE.value.length > 0) {
    // Check if this PUE item is allowed by subscription
    const allowedPUE = subscriptionAllowedPUE.value.find(a => a.pue_id === pue.pue_id)

    if (!allowedPUE) {
      $q.notify({
        type: 'negative',
        message: `${pue.name} is not included in your subscription`,
        position: 'top'
      })
      selectedPUE.value = null
      return
    }

    // Check if quantity limit would be exceeded
    const currentCount = pueItemsWithQuantity.value
      .filter(item => item.pue_id === pue.pue_id)
      .reduce((sum, item) => sum + (item.quantity || 1), 0)

    if (currentCount >= allowedPUE.quantity_limit) {
      $q.notify({
        type: 'negative',
        message: `Maximum ${allowedPUE.quantity_limit} ${pue.name} allowed by subscription`,
        position: 'top'
      })
      selectedPUE.value = null
      return
    }
  }

  // Store the selected PUE item and open cost structure dialog
  selectedPUEItem.value = pue
  pueQuantity.value = 1
  selectedPUECostStructure.value = null
  selectedPUEDuration.value = null
  pueCostEstimate.value = null

  // Load cost structures for this PUE item
  await loadPUECostStructures(pue.pue_id, pue.pue_type_id)

  showPUECostStructureDialog.value = true
  selectedPUE.value = null // Clear selection
}

const loadPUECostStructures = async (pueId, pueTypeId) => {
  if (!formData.value.hub_id) return

  try {
    loadingPUECostStructures.value = true

    // Load cost structures for specific PUE item
    const itemResponse = await settingsAPI.getCostStructures({
      hub_id: formData.value.hub_id,
      item_type: 'pue_item',
      item_reference: String(pueId),
      is_active: true
    })

    // Load cost structures for PUE type
    const typeResponse = pueTypeId ? await settingsAPI.getCostStructures({
      hub_id: formData.value.hub_id,
      item_type: 'pue_type',
      item_reference: String(pueTypeId),
      is_active: true
    }) : { data: { cost_structures: [] } }

    // Load cost structures that apply to "all PUE items"
    const allPUEResponse = await settingsAPI.getCostStructures({
      hub_id: formData.value.hub_id,
      item_type: 'pue',
      item_reference: 'all',
      is_active: true
    })

    // Combine all cost structures
    const itemStructures = itemResponse.data.cost_structures || []
    const typeStructures = typeResponse.data.cost_structures || []
    const allPUEStructures = allPUEResponse.data.cost_structures || []
    availablePUECostStructures.value = [...itemStructures, ...typeStructures, ...allPUEStructures]

  } catch (error) {
    console.error('Failed to load PUE cost structures:', error)
    availablePUECostStructures.value = []
  } finally {
    loadingPUECostStructures.value = false
  }
}

const onPUECostStructureChange = async (structureId) => {
  pueCostEstimate.value = null

  if (!structureId) {
    pueDurationOptions.value = [{ label: 'Custom', value: 'custom' }]
    selectedPUEDuration.value = null
    return
  }

  // Load duration options from the selected cost structure
  const structure = availablePUECostStructures.value.find(s => s.structure_id === structureId)
  console.log('Selected PUE cost structure:', structure)
  console.log('PUE Duration options from structure:', structure?.duration_options)

  if (structure && structure.duration_options && structure.duration_options.length > 0) {
    buildPUEDurationOptionsFromStructure(structure.duration_options)
    console.log('Built PUE duration options:', pueDurationOptions.value)
  } else {
    // Fallback to custom only
    pueDurationOptions.value = [{ label: 'Custom', value: 'custom' }]
    console.log('No PUE duration options found, using custom only')
  }

  // Only calculate estimate if duration is already selected
  if (!selectedPUEDuration.value) {
    return
  }

  await calculatePUECostEstimate()
}

const onPUEDurationChange = async () => {
  await calculatePUECostEstimate()
}

const calculatePUECostEstimate = async () => {
  if (!selectedPUECostStructure.value || !selectedPUEDuration.value) return

  try {
    const duration = pueDurationOptions.value.find(d => d.value === selectedPUEDuration.value)
    if (!duration || !duration.duration_value) return

    const params = {
      duration_value: duration.duration_value,
      duration_unit: duration.duration_unit,
      vat_percentage: hubVATPercentage.value,
      quantity: pueQuantity.value
    }

    const response = await settingsAPI.estimateCost(selectedPUECostStructure.value, params)
    pueCostEstimate.value = response.data

  } catch (error) {
    console.error('Failed to estimate PUE cost:', error)
  }
}

const confirmAddPUEItem = () => {
  if (!selectedPUEItem.value || !selectedPUECostStructure.value || !selectedPUEDuration.value) {
    $q.notify({ type: 'warning', message: 'Please select cost structure and duration', position: 'top' })
    return
  }

  const duration = pueDurationOptions.value.find(d => d.value === selectedPUEDuration.value)
  if (!duration) return

  // Add PUE item with cost structure info
  pueItemsWithQuantity.value.push({
    pue_id: selectedPUEItem.value.pue_id,
    name: selectedPUEItem.value.name,
    quantity: pueQuantity.value,
    cost_structure_id: selectedPUECostStructure.value,
    duration_value: duration.duration_value,
    duration_unit: duration.duration_unit,
    pricePerUnit: pueCostEstimate.value ? pueCostEstimate.value.total / pueQuantity.value : 0,
    totalCost: pueCostEstimate.value ? pueCostEstimate.value.total : 0,
    unitType: `${duration.duration_value} ${duration.duration_unit}`
  })

  // Update total PUE cost
  onPUEQuantityChange()

  // Close dialog
  showPUECostStructureDialog.value = false
}

// OLD CODE - keeping for reference but will be replaced
const OLD_addPUEToRental = (pue) => {
  if (!pue) return

  // Check if this PUE item is already added
  const existing = pueItemsWithQuantity.value.find(item => item.pue_id === pue.pue_id)
  if (existing) {
    // If already added, just increment quantity
    existing.quantity += 1
  } else {
    // Calculate price per unit for this PUE item
    let pricePerUnit = 0
    let unitType = ''

    // Try to find pricing config for this specific PUE item
    let pricing = pricingConfigs.value.find(p =>
      p.item_type === 'pue_item' &&
      p.item_reference === String(pue.pue_id) &&
      p.is_active
    )

    // If no specific pricing, try to find pricing for the PUE type
    if (!pricing && pue.pue_type) {
      pricing = pricingConfigs.value.find(p =>
        p.item_type === 'pue_type' &&
        p.item_reference === pue.pue_type &&
        p.is_active
      )
    }

    // If pricing config exists, calculate cost based on unit type
    if (pricing) {
      pricePerUnit = calculateCostByUnit(pricing)
      unitType = pricing.unit_type
    } else if (pue.rental_cost) {
      // Fallback to PUE item's rental_cost field
      pricePerUnit = parseFloat(pue.rental_cost)
    }

    // Add to pueItemsWithQuantity
    pueItemsWithQuantity.value.push({
      pue_id: pue.pue_id,
      name: pue.name || `PUE ${pue.pue_id}`,
      quantity: 1,
      pricePerUnit: pricePerUnit,
      unitType: unitType
    })
  }

  // Recalculate total PUE cost
  calculatePUECostFromQuantities()

  // Clear the selection after adding
  selectedPUE.value = null
}

const removePUEItem = (index) => {
  pueItemsWithQuantity.value.splice(index, 1)

  // Recalculate total PUE cost
  calculatePUECostFromQuantities()
}

const getPUEName = (pueId) => {
  const pue = availablePUE.value.find(p => p.pue_id === pueId)
  return pue?.name || `PUE ${pueId}`
}

const editRental = (rental) => {
  editingRental.value = rental
  formData.value = {
    ...rental,
    timestamp_taken: date.formatDate(rental.timestamp_taken, 'YYYY-MM-DDTHH:mm'),
    due_back: date.formatDate(rental.due_back, 'YYYY-MM-DDTHH:mm')
  }
  showCreateDialog.value = true
}

// Deposit dialog handlers
const confirmDeposit = () => {
  formData.value.deposit_amount = depositAmount.value
  formData.value.payment_type = depositPaymentType.value
  showDepositDialog.value = false

  $q.notify({
    type: 'positive',
    message: `Deposit of ${currentCurrencySymbol.value}${depositAmount.value.toFixed(2)} recorded`,
    position: 'top'
  })
}

const resetDepositDialog = () => {
  depositAmount.value = 0
  depositPaymentType.value = null
  confirmCashDeposit.value = false
}

// Payment dialog handlers
const confirmPayment = () => {
  formData.value.amount_paid = paymentAmount.value
  formData.value.payment_type = upfrontPaymentType.value
  showPaymentCollectionDialog.value = false

  $q.notify({
    type: 'positive',
    message: `Payment of ${currentCurrencySymbol.value}${paymentAmount.value.toFixed(2)} recorded`,
    position: 'top'
  })
}

const applyCredit = () => {
  if (!creditAmountToApply.value || creditAmountToApply.value <= 0) return

  // Add credit amount to the amount paid
  formData.value.amount_paid = (formData.value.amount_paid || 0) + creditAmountToApply.value

  // Mark that credit was used (for transaction tracking)
  if (!formData.value.credit_used) {
    formData.value.credit_used = creditAmountToApply.value
  } else {
    formData.value.credit_used += creditAmountToApply.value
  }

  showApplyCreditDialog.value = false

  $q.notify({
    type: 'positive',
    message: `Credit of ${currentCurrencySymbol.value}${creditAmountToApply.value.toFixed(2)} applied to rental`,
    position: 'top',
    caption: `Remaining credit: ${currentCurrencySymbol.value}${((userAccount.value?.balance || 0) - creditAmountToApply.value).toFixed(2)}`
  })

  creditAmountToApply.value = 0
}

const resetPaymentDialog = () => {
  paymentAmount.value = 0
  upfrontPaymentType.value = null
  confirmCashPayment.value = false
}

const saveRental = async () => {
  // Check if there's cash deposit or payment to confirm
  const hasDeposit = formData.value.deposit_amount && formData.value.deposit_amount > 0
  const hasPayment = formData.value.amount_paid && formData.value.amount_paid > 0
  const isCashPayment = formData.value.payment_method === 'cash'

  if ((hasDeposit || hasPayment) && isCashPayment) {
    // Show confirmation dialog
    $q.dialog({
      title: 'Confirm Cash Payment',
      message: `
        <div class="q-gutter-sm">
          <p><strong>Please confirm cash has been received:</strong></p>
          ${hasDeposit ? `<p>• Deposit: ${currentCurrencySymbol.value}${formData.value.deposit_amount.toFixed(2)}</p>` : ''}
          ${hasPayment ? `<p>• Payment: ${currentCurrencySymbol.value}${formData.value.amount_paid.toFixed(2)}</p>` : ''}
          <p class="text-weight-bold text-orange-9 q-mt-md">⚠️ This action will record the cash transaction in the system.</p>
        </div>
      `,
      html: true,
      cancel: true,
      persistent: true,
      ok: {
        label: 'Confirm Cash Received',
        color: 'positive',
        icon: 'check_circle'
      },
      cancel: {
        label: 'Cancel',
        color: 'grey',
        flat: true
      }
    }).onOk(async () => {
      await processSaveRental()
    })
  } else {
    // No cash payment, proceed directly
    await processSaveRental()
  }
}

const processSaveRental = async () => {
  saving.value = true
  try {
    if (editingRental.value) {
      // Keep old update functionality for now (editing legacy rentals)
      const rentalData = {
        ...formData.value,
        timestamp_taken: new Date(formData.value.timestamp_taken).toISOString(),
        due_back: new Date(formData.value.due_back).toISOString(),
        payment_status: computedPaymentStatus.value
      }
      await rentalsAPI.update(editingRental.value.rentral_id, rentalData)
      $q.notify({
        type: 'positive',
        message: 'Rental updated successfully',
        position: 'top'
      })
    } else {
      // NEW RENTAL CREATION - Use new battery rentals API
      if (!formData.value.battery_id) {
        throw new Error('Battery selection is required')
      }

      if (!selectedCostStructure.value) {
        throw new Error('Cost structure is required')
      }

      // Transform data to match BatteryRentalCreate schema
      const batteryRentalData = {
        user_id: formData.value.user_id,
        battery_ids: [formData.value.battery_id], // Convert single battery to array
        cost_structure_id: selectedCostStructure.value,
        rental_start_date: new Date(formData.value.timestamp_taken).toISOString(),
        due_date: new Date(formData.value.due_back).toISOString(),
        deposit_amount: formData.value.deposit_paid || 0,
        notes: formData.value.notes ? [formData.value.notes] : []
      }

      await batteryRentalsAPI.create(batteryRentalData)
      $q.notify({
        type: 'positive',
        message: 'Battery rental created successfully',
        position: 'top'
      })
    }

    closeDialog()
    loadRentals()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || error.message || 'Failed to save rental',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const fetchReturnCostCalculation = async () => {
  if (!returningRental.value) return

  loadingReturnCost.value = true
  try {
    const params = {
      actual_return_date: returnData.value.actual_return_date
    }
    if (kwhUsageEnd.value !== null) {
      params.kwh_usage = kwhUsageEnd.value
    }

    const response = await api.get(`/rentals/${returningRental.value.rentral_id}/calculate-return-cost`, { params })
    returnCostCalculation.value = response.data

    // Update payment amounts based on calculation
    const totalOwed = response.data.payment_status.amount_still_owed
    const accountBalance = response.data.payment_status.user_account_balance

    if (returnData.value.useAccountCredit) {
      const creditToUse = Math.min(totalOwed, accountBalance)
      returnData.value.creditAmount = creditToUse
      returnData.value.cashAmount = totalOwed - creditToUse
      returnData.value.payment_amount = returnData.value.cashAmount
    } else {
      returnData.value.creditAmount = 0
      returnData.value.cashAmount = totalOwed
      returnData.value.payment_amount = totalOwed
    }

  } catch (error) {
    console.error('Failed to fetch return cost calculation:', error)
    $q.notify({
      type: 'warning',
      message: 'Could not calculate final cost. Using estimate.',
      position: 'top'
    })
  } finally {
    loadingReturnCost.value = false
  }
}

const returnRental = async (rental) => {
  // Prevent opening return dialog for already-returned rentals
  if (rental.status === 'returned' || rental.actual_return_date) {
    $q.notify({
      type: 'warning',
      message: 'This rental has already been returned',
      position: 'top'
    })
    return
  }

  returningRental.value = rental
  showReturnDialog.value = true
  // RentalReturnDialog component handles its own cost calculation
}

const quickReturn = async (rental) => {
  showQuickReturnsDialog.value = false
  await returnRental(rental)
}

const onRentalReturned = async () => {
  // Reload rentals list after successful return
  await loadRentals()
}

const confirmReturn = async () => {
  saving.value = true
  try {
    const returnPayload = {
      actual_return_date: new Date(returnData.value.actual_return_date).toISOString(),
      return_notes: returnData.value.return_notes
    }

    // Add kWh usage if provided
    if (kwhUsageEnd.value !== null) {
      returnPayload.kwh_usage_end = kwhUsageEnd.value
    }

    // Add payment data if collecting payment
    if (returnData.value.collectPayment && returnData.value.payment_amount > 0) {
      returnPayload.payment_amount = returnData.value.payment_amount
      returnPayload.payment_notes = returnData.value.payment_notes
    }

    await rentalsAPI.returnBattery(returningRental.value.rentral_id, returnPayload)

    // Build success message
    let message = 'Rental returned successfully'
    if (returnData.value.collectPayment) {
      if (returnData.value.useAccountCredit && returnData.value.creditAmount > 0) {
        message += `. Credit applied: $${returnData.value.creditAmount.toFixed(2)}`
        if (returnData.value.cashAmount > 0) {
          message += `, Cash collected: $${returnData.value.cashAmount.toFixed(2)}`
        }
      } else if (returnData.value.payment_amount > 0) {
        message += `. Payment of $${returnData.value.payment_amount.toFixed(2)} recorded`
      }
    }

    $q.notify({
      type: 'positive',
      message,
      position: 'top'
    })

    showReturnDialog.value = false
    loadRentals()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return rental',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const openBatteryRentalDialog = () => {
  resetForm()
  showCreateDialog.value = true
}

const openPUERentalDialog = () => {
  resetPUEForm()
  showPUERentalDialog.value = true
}

// PUE Rental Form Handlers
const resetPUEForm = () => {
  pueFormData.value = {
    hub_id: null,
    user_id: null,
    pue_id: null,
    quantity: 1,
    cost_structure_id: null,
    duration_preset: null,
    custom_duration_value: 1,
    custom_duration_unit: 'days',
    rental_start_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
    due_date: null,
    payment_method: null,
    deposit_amount: 0,
    amount_paid: 0,
    credit_used: 0
  }
  pueUserAccount.value = null
  pueCostEstimate.value = null
  availablePUECostStructures.value = []
  pueDurationOptions.value = [{ label: 'Custom', value: 'custom' }]
}

const onPUEHubChange = async (hubId) => {
  // Reset dependent fields when hub changes
  pueFormData.value.user_id = null
  pueFormData.value.pue_id = null
  pueFormData.value.cost_structure_id = null
  pueUserAccount.value = null

  if (!hubId) return

  try {
    // Load available PUE for this hub
    const pueResponse = await hubsAPI.getPUE(hubId)
    availablePUE.value = pueResponse.data.filter(
      p => p.status === 'available'
    )
    filteredPUE.value = availablePUE.value

    // Load users for this hub
    const usersResponse = await hubsAPI.getUsers(hubId)
    userOptions.value = usersResponse.data
    filteredUsers.value = userOptions.value

  } catch (error) {
    console.error('Failed to load hub data:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load hub data for PUE rental',
      position: 'top'
    })
  }
}

const onPUEUserChange = async (userId) => {
  if (!userId) {
    pueUserAccount.value = null
    return
  }

  try {
    const response = await accountsAPI.getUserAccount(userId)
    pueUserAccount.value = response.data
  } catch (error) {
    console.error('Failed to load user account:', error)
    pueUserAccount.value = null
  }
}

const onPUEItemSelect = async (pueId) => {
  if (!pueId) {
    pueFormData.value.cost_structure_id = null
    availablePUECostStructures.value = []
    return
  }

  const pueItem = availablePUE.value.find(p => p.pue_id === pueId)
  if (!pueItem) return

  // Load cost structures for this PUE item
  await loadPUECostStructuresForRental(pueId, pueItem.pue_type_id)
}

const loadPUECostStructuresForRental = async (pueId, pueTypeId) => {
  if (!pueFormData.value.hub_id) return

  try {
    loadingPUECostStructures.value = true

    // Load cost structures for specific PUE item
    const itemResponse = await settingsAPI.getCostStructures({
      hub_id: pueFormData.value.hub_id,
      item_type: 'pue_item',
      specific_item_id: pueId
    })

    // Load cost structures for PUE type
    const typeResponse = pueTypeId ? await settingsAPI.getCostStructures({
      hub_id: pueFormData.value.hub_id,
      item_type: 'pue_type',
      specific_item_id: pueTypeId
    }) : { data: { cost_structures: [] } }

    // Load cost structures that apply to "all PUE items"
    const allPUEResponse = await settingsAPI.getCostStructures({
      hub_id: pueFormData.value.hub_id,
      item_type: 'pue',
      is_active: true
    })

    const itemStructures = itemResponse.data.cost_structures || []
    const typeStructures = typeResponse.data.cost_structures || []
    const allPUEStructures = allPUEResponse.data.cost_structures || []
    availablePUECostStructures.value = [...itemStructures, ...typeStructures, ...allPUEStructures]

  } catch (error) {
    console.error('Failed to load PUE cost structures:', error)
    availablePUECostStructures.value = []
  } finally {
    loadingPUECostStructures.value = false
  }
}

const onPUERentalCostStructureChange = async (structureId) => {
  pueCostEstimate.value = null
  pueFormData.value.duration_preset = null
  pueFormData.value.due_date = null

  if (!structureId) {
    pueDurationOptions.value = [{ label: 'Custom', value: 'custom', is_custom: true }]
    return
  }

  // Load duration options from the selected cost structure
  const structure = availablePUECostStructures.value.find(s => s.structure_id === structureId)

  if (structure && structure.duration_options && structure.duration_options.length > 0) {
    buildPUEDurationOptionsFromStructure(structure.duration_options)
  } else {
    // Fallback to custom only
    pueDurationOptions.value = [{ label: 'Custom', value: 'custom', is_custom: true }]
  }
}

const buildPUEDurationOptionsFromStructure = (structureDurationOptions) => {
  pueDurationOptions.value = []

  structureDurationOptions.forEach((option, index) => {
    if (option.input_type === 'dropdown' && option.dropdown_options) {
      // Parse dropdown_options JSON
      let choices = []
      try {
        choices = typeof option.dropdown_options === 'string'
          ? JSON.parse(option.dropdown_options)
          : option.dropdown_options
      } catch (e) {
        console.error('Failed to parse dropdown_options:', e)
        return
      }

      // Add each choice as a selectable option
      choices.forEach((choice, choiceIndex) => {
        const durationValue = choice.value || choice.duration_value
        const durationUnit = choice.unit || choice.duration_unit || 'days'

        pueDurationOptions.value.push({
          label: choice.label || `${durationValue} ${durationUnit}${durationValue > 1 ? 's' : ''}`,
          value: `${option.option_id}-${choiceIndex}`,
          duration_value: durationValue,
          duration_unit: durationUnit,
          option_id: option.option_id
        })
      })
    } else if (option.input_type === 'custom') {
      // For custom input, show the range as a custom option
      pueDurationOptions.value.push({
        label: `Custom (${option.min_value || 1}-${option.max_value || 99} ${option.custom_unit || 'days'})`,
        value: `custom-${option.option_id}`,
        is_custom: true,
        custom_unit: option.custom_unit || 'days',
        min_value: option.min_value,
        max_value: option.max_value,
        default_value: option.default_value,
        option_id: option.option_id
      })
    }
  })

  // Always add a "Custom" option at the end to allow manual entry
  pueDurationOptions.value.push({
    label: 'Custom',
    value: 'custom',
    is_custom: true
  })
}

const onPUERentalDurationChange = async (durationValue) => {
  if (!durationValue || !pueFormData.value.cost_structure_id) return

  let durationInDays = 0
  let durationValueNum = 0
  let durationUnit = ''

  // Check if it's a custom duration
  const selected = pueDurationOptions.value.find(d => d.value === durationValue)

  if (!selected) return

  if (selected.is_custom) {
    // Use the custom values entered by user
    durationValueNum = pueFormData.value.custom_duration_value
    durationUnit = pueFormData.value.custom_duration_unit || selected.custom_unit || 'days'
  } else {
    // Use the preset values from the dropdown
    durationValueNum = selected.duration_value
    durationUnit = selected.duration_unit
  }

  if (!durationValueNum || !durationUnit) return

  // Calculate duration in days
  switch (durationUnit) {
    case 'hours':
      durationInDays = durationValueNum / 24
      break
    case 'days':
      durationInDays = durationValueNum
      break
    case 'weeks':
      durationInDays = durationValueNum * 7
      break
    case 'months':
      durationInDays = durationValueNum * 30
      break
    default:
      durationInDays = durationValueNum
  }

  // Calculate due date
  const startDate = new Date(pueFormData.value.rental_start_date)
  const dueDate = date.addToDate(startDate, { days: durationInDays })
  pueFormData.value.due_date = date.formatDate(dueDate, 'YYYY-MM-DDTHH:mm')

  // Fetch cost estimate
  await calculatePUERentalCostEstimate(durationValueNum, durationUnit)
}

const onPUERentalCustomDurationChange = async () => {
  if (!pueFormData.value.custom_duration_value || !pueFormData.value.custom_duration_unit) return
  await onPUERentalDurationChange('custom')
}

const calculatePUERentalCostEstimate = async (durationValue, durationUnit) => {
  if (!pueFormData.value.cost_structure_id || !durationValue || !durationUnit) return

  try {
    const params = {
      duration_value: durationValue,
      duration_unit: durationUnit,
      quantity: pueFormData.value.quantity || 1
    }

    const response = await settingsAPI.estimateCost(pueFormData.value.cost_structure_id, params)
    pueCostEstimate.value = response.data

  } catch (error) {
    console.error('Failed to calculate PUE cost estimate:', error)
    $q.notify({ type: 'negative', message: 'Failed to calculate cost estimate', position: 'top' })
  }
}

const savePUERental = async () => {
  try {
    saving.value = true

    // Validate required fields
    if (!pueFormData.value.hub_id || !pueFormData.value.user_id || !pueFormData.value.pue_id) {
      throw new Error('Hub, User, and PUE item are required')
    }

    if (!pueFormData.value.cost_structure_id) {
      throw new Error('Cost structure is required')
    }

    // Get duration info
    let durationValue = 0
    let durationUnit = ''

    if (pueFormData.value.duration_preset === 'custom') {
      durationValue = pueFormData.value.custom_duration_value
      durationUnit = pueFormData.value.custom_duration_unit
    } else {
      const selected = pueDurationOptions.value.find(d => d.value === pueFormData.value.duration_preset)
      if (selected) {
        durationValue = selected.duration_value
        durationUnit = selected.duration_unit
      }
    }

    // Prepare rental data
    const rentalData = {
      hub_id: pueFormData.value.hub_id,
      user_id: pueFormData.value.user_id,
      pue_item_ids: [pueFormData.value.pue_id],
      pue_quantities: { [pueFormData.value.pue_id]: pueFormData.value.quantity },
      cost_structure_id: pueFormData.value.cost_structure_id,
      rental_start_date: new Date(pueFormData.value.rental_start_date).toISOString(),
      due_date: new Date(pueFormData.value.due_date).toISOString(),
      duration_value: durationValue,
      duration_unit: durationUnit,
      payment_method: pueFormData.value.payment_method,
      deposit_amount: pueFormData.value.deposit_amount || 0,
      amount_paid: pueFormData.value.amount_paid || 0,
      credit_applied: pueFormData.value.credit_used || 0
    }

    // Create the PUE rental
    const response = await pueAPI.createPUERental(rentalData)

    $q.notify({
      type: 'positive',
      message: 'PUE rental created successfully!',
      position: 'top'
    })

    closeDialog()
    await loadRentals()

  } catch (error) {
    console.error('Failed to create PUE rental:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || error.message || 'Failed to create PUE rental',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  showPUERentalDialog.value = false
  selectedPUE.value = null
  resetForm()
}

const resetForm = () => {
  formData.value = {
    rentral_id: null,
    rental_unique_id: null,
    hub_id: null,
    user_id: null,
    battery_id: null,
    timestamp_taken: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
    due_back: date.formatDate(
      date.addToDate(new Date(), { days: 7 }),
      'YYYY-MM-DDTHH:mm'
    ),
    battery_cost: 0,
    pue_cost: 0,
    total_cost: 0,
    deposit_amount: 0,
    payment_status: 'unpaid',
    amount_paid: 0,
    amount_owed: 0,
    pue_item_ids: []
  }
  pueItemsWithQuantity.value = []
  selectedDuration.value = null
  editingRental.value = null
}

onMounted(() => {
  loadRentals()
  loadHubs()

  // Check if we should open the quick returns dialog
  if (route.query.action === 'returns') {
    showQuickReturnsDialog.value = true
  }
})
</script>
