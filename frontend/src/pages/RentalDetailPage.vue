<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h4 q-ml-md">Rental #{{ $route.params.id }}</span>
      </div>
      <div class="col-auto">
        <q-btn
          v-if="canReturn"
          label="Return Rental"
          icon="assignment_return"
          color="positive"
          @click="showReturnDialog = true"
          class="q-mr-sm"
        />
        <q-btn
          v-if="canCollectPayment"
          label="Collect Payment"
          icon="payment"
          color="primary"
          @click="showPaymentDialog = true"
        />
      </div>
    </div>

    <div v-if="loading" class="flex flex-center q-pa-xl">
      <q-spinner-gears size="50px" color="primary" />
    </div>

    <div v-else-if="rental" class="row q-col-gutter-md">
      <div class="col-12">
        <q-banner v-if="rentalData?.status === 'overdue'" class="bg-negative text-white">
          <template v-slot:avatar>
            <q-icon name="warning" />
          </template>
          This rental is overdue!
        </q-banner>
      </div>

      <!-- Rental Info -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">
              Rental Information
              <q-badge v-if="isPayToOwn" color="purple" class="q-ml-sm">
                <q-icon name="account_balance" size="xs" class="q-mr-xs" />
                Pay to Own
              </q-badge>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>ID:</strong> {{ rentalData?.id }}</div>
            <div>
              <strong>User:</strong>
              <q-btn
                flat
                dense
                color="primary"
                :label="getUserDisplayName(userData)"
                icon="person"
                :to="{ name: 'user-detail', params: { id: rentalData?.user_id } }"
                class="q-ml-sm"
              />
            </div>
            <!-- Battery Info -->
            <div v-if="rentalData?.battery_id">
              <strong>Battery:</strong>
              <q-btn
                flat
                dense
                color="primary"
                :label="batteryData?.short_id || `Battery ${rentalData?.battery_id}`"
                icon="battery_charging_full"
                :to="{ name: 'battery-detail', params: { id: rentalData?.battery_id } }"
                class="q-ml-sm"
              />
              <q-badge
                v-if="rentalData?.actual_return_date"
                color="grey"
                class="q-ml-sm"
              >
                Returned
              </q-badge>
              <q-btn
                v-else-if="canReturn"
                flat
                dense
                size="sm"
                label="Return Battery"
                icon="assignment_return"
                color="positive"
                @click="showReturnDialog = true"
                class="q-ml-sm"
              />
            </div>

            <!-- PUE Item Info -->
            <div v-if="pueData">
              <strong>PUE Item:</strong>
              <q-btn
                flat
                dense
                color="primary"
                :label="pueData.name || `PUE #${pueData.pue_id}`"
                icon="devices"
                :to="{ name: 'pue-detail', params: { id: pueData.pue_id } }"
                class="q-ml-sm"
              />
              <q-badge
                v-if="rentalData?.actual_return_date"
                color="grey"
                class="q-ml-sm"
              >
                Returned
              </q-badge>
              <q-btn
                v-else-if="canReturn"
                flat
                dense
                size="sm"
                label="Return PUE"
                icon="assignment_return"
                color="positive"
                @click="showReturnDialog = true"
                class="q-ml-sm"
              />
            </div>
            <div>
              <strong>Status:</strong>
              <q-badge :color="getStatusColor(rentalData?.status)" class="q-ml-sm" text-color="white">
                {{ rentalData?.status }}
              </q-badge>
            </div>
            <div><strong>Rental Date:</strong> {{ formatDate(rentalData?.rental_date) }}</div>
            <div v-if="!isPayToOwn"><strong>Expected Return:</strong> {{ formatDate(rentalData?.expected_return_date) }}</div>
            <div v-if="rentalData?.actual_return_date">
              <strong>Actual Return:</strong> {{ formatDate(rentalData?.actual_return_date) }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Cost Structure & Breakdown -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Cost Breakdown</div>
            <div v-if="costStructureInfo" class="text-subtitle2 text-grey-7">
              {{ costStructureInfo.name }}
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <!-- Cost Structure Components -->
            <div v-if="costStructureInfo?.components && costStructureInfo.components.length > 0" class="q-mb-md">
              <div class="text-weight-medium q-mb-xs">Pricing:</div>
              <div v-for="(component, idx) in costStructureInfo.components" :key="idx" class="q-ml-sm">
                <div class="row items-center">
                  <div class="col">{{ component.component_name }}</div>
                  <div class="col-auto">
                    {{ currencySymbol }}{{ component.rate.toFixed(2) }} {{ formatUnitType(component.unit_type) }}
                  </div>
                </div>
                <div v-if="component.late_fee_rate && component.late_fee_action" class="text-caption text-grey-7 q-ml-sm">
                  Late fee: {{ currencySymbol }}{{ component.late_fee_rate.toFixed(2) }} {{ formatUnitType(component.unit_type) }}
                  <span v-if="component.late_fee_grace_days"> (after {{ component.late_fee_grace_days }} days grace)</span>
                </div>
              </div>
            </div>

            <q-separator v-if="costStructureInfo?.components && costStructureInfo.components.length > 0" />

            <!-- Rental Duration Info -->
            <div v-if="rentalData?.rental_date" class="q-my-sm">
              <div class="row items-center">
                <div class="col"><strong>Days Rented:</strong></div>
                <div class="col-auto">{{ calculateDays(rentalData) }} days</div>
              </div>
              <div v-if="!rentalData?.actual_return_date && rentalData?.expected_return_date" class="row items-center">
                <div class="col"><strong>Days Remaining:</strong></div>
                <div class="col-auto" :class="daysRemaining < 0 ? 'text-negative' : ''">
                  {{ Math.abs(daysRemaining) }} days {{ daysRemaining < 0 ? 'overdue' : 'left' }}
                </div>
              </div>
            </div>

            <q-separator />

            <!-- Financial Summary -->
            <div class="q-my-sm">
              <div v-if="rentalData?.deposit_amount" class="row items-center">
                <div class="col"><strong>Deposit Paid:</strong></div>
                <div class="col-auto">{{ currencySymbol }}{{ Number(rentalData.deposit_amount).toFixed(2) }}</div>
              </div>
              <div v-if="amountPaid > 0" class="row items-center">
                <div class="col"><strong>Amount Paid:</strong></div>
                <div class="col-auto text-positive">{{ currencySymbol }}{{ amountPaid.toFixed(2) }}</div>
              </div>
              <div class="row items-center text-h6 text-primary q-mt-sm">
                <div class="col"><strong>Total Cost:</strong></div>
                <div class="col-auto">
                  {{ currencySymbol }}{{ totalCost.toFixed(2) }}
                  <q-btn
                    v-if="totalCost === 0 && rentalData?.actual_return_date"
                    flat
                    dense
                    size="sm"
                    color="orange"
                    icon="refresh"
                    @click="recalculateCost"
                    class="q-ml-sm"
                  >
                    <q-tooltip>Recalculate cost for this returned rental</q-tooltip>
                  </q-btn>
                </div>
              </div>
              <div v-if="balanceDue !== 0" class="row items-center q-mt-xs">
                <div class="col"><strong>Balance Due:</strong></div>
                <div class="col-auto" :class="balanceDue > 0 ? 'text-negative' : 'text-positive'">
                  {{ currencySymbol }}{{ Math.abs(balanceDue).toFixed(2) }}
                  <span v-if="balanceDue < 0" class="text-caption">(credit)</span>
                </div>
              </div>

              <q-separator class="q-my-md" />

              <!-- Payment Status -->
              <div class="row items-center">
                <div class="col"><strong>Payment Status:</strong></div>
                <div class="col-auto">
                  <q-chip
                    :color="totalCost > 0 ? (balanceDue <= 0 ? 'positive' : 'negative') : 'grey'"
                    text-color="white"
                    dense
                  >
                    {{ totalCost > 0 ? (balanceDue <= 0 ? 'PAID' : 'STILL OWED') : 'PENDING' }}
                  </q-chip>
                  <q-btn
                    v-if="canCollectPayment"
                    flat
                    dense
                    size="sm"
                    label="Collect Payment"
                    icon="payment"
                    color="primary"
                    @click="showPaymentDialog = true"
                    class="q-ml-sm"
                  />
                </div>
              </div>
              <div v-if="balanceDue > 0 && userData" class="row items-center q-mt-xs">
                <div class="col"><strong>Owed By:</strong></div>
                <div class="col-auto">{{ userData.Name || userData.username || `User #${userData.user_id}` }}</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Pay-to-Own Ownership Progress -->
      <div class="col-12" v-if="isPayToOwn">
        <q-card>
          <q-card-section class="bg-purple-1">
            <div class="text-h6">
              <q-icon name="account_balance" color="purple" class="q-mr-sm" />
              Ownership Progress
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section v-if="loadingOwnership" class="flex flex-center q-pa-xl">
            <q-spinner color="purple" size="40px" />
          </q-card-section>
          <q-card-section v-else-if="ownershipStatus">
            <!-- Progress Bar -->
            <div class="q-mb-md">
              <div class="row items-center q-mb-sm">
                <div class="col text-weight-medium">Ownership Progress</div>
                <div class="col-auto text-h6 text-purple">
                  {{ ownershipStatus.ownership_percentage?.toFixed(1) || 0 }}%
                </div>
              </div>
              <q-linear-progress
                :value="(ownershipStatus.ownership_percentage || 0) / 100"
                size="20px"
                color="purple"
                class="rounded-borders"
              >
                <div class="absolute-full flex flex-center">
                  <q-badge
                    color="white"
                    text-color="purple"
                    :label="`${ownershipStatus.ownership_percentage?.toFixed(1) || 0}% Owned`"
                  />
                </div>
              </q-linear-progress>
            </div>

            <q-separator class="q-my-md" />

            <!-- Financial Breakdown -->
            <div class="row q-col-gutter-md">
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat bordered class="bg-blue-1">
                  <q-card-section class="q-pa-md">
                    <div class="text-caption text-grey-7">Total Item Cost</div>
                    <div class="text-h6 text-primary">
                      {{ currencySymbol }}{{ ownershipStatus.total_item_cost?.toFixed(2) || '0.00' }}
                    </div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat bordered class="bg-positive-1">
                  <q-card-section class="q-pa-md">
                    <div class="text-caption text-grey-7">Paid Towards Ownership</div>
                    <div class="text-h6 text-positive">
                      {{ currencySymbol }}{{ ownershipStatus.total_paid_towards_ownership?.toFixed(2) || '0.00' }}
                    </div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat bordered class="bg-orange-1">
                  <q-card-section class="q-pa-md">
                    <div class="text-caption text-grey-7">Rental Fees Paid</div>
                    <div class="text-h6 text-orange">
                      {{ currencySymbol }}{{ ownershipStatus.total_rental_fees_paid?.toFixed(2) || '0.00' }}
                    </div>
                  </q-card-section>
                </q-card>
              </div>
              <div class="col-12 col-sm-6 col-md-3">
                <q-card flat bordered class="bg-purple-1">
                  <q-card-section class="q-pa-md">
                    <div class="text-caption text-grey-7">Remaining Balance</div>
                    <div class="text-h6 text-purple">
                      {{ currencySymbol }}{{ ownershipStatus.remaining_balance?.toFixed(2) || '0.00' }}
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>

            <!-- Ownership Status Banner -->
            <q-banner
              v-if="ownershipStatus.ownership_percentage >= 100"
              class="bg-positive text-white q-mt-md"
              rounded
            >
              <template v-slot:avatar>
                <q-icon name="check_circle" />
              </template>
              <div class="text-weight-medium">Ownership Complete!</div>
              <div class="text-caption">
                This item is now fully owned by the customer.
                <span v-if="ownershipStatus.ownership_completion_date">
                  Completed on {{ formatDate(ownershipStatus.ownership_completion_date) }}
                </span>
              </div>
            </q-banner>
            <q-banner
              v-else-if="ownershipStatus.remaining_balance > 0"
              class="bg-info text-white q-mt-md"
              rounded
            >
              <template v-slot:avatar>
                <q-icon name="info" />
              </template>
              <div class="text-caption">
                The customer still needs to pay
                <strong>{{ currencySymbol }}{{ ownershipStatus.remaining_balance?.toFixed(2) }}</strong>
                to fully own this item.
              </div>
            </q-banner>
          </q-card-section>
        </q-card>
      </div>

      <!-- PUE Items -->
      <div class="col-12" v-if="rental.pue_items && rental.pue_items.length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6">Equipment (PUE) Items</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list separator>
              <q-item v-for="item in rental.pue_items" :key="item.id">
                <q-item-section avatar>
                  <q-icon name="devices" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ item.pue?.name || `PUE #${item.pue_id}` }}</q-item-label>
                  <q-item-label caption>
                    Rented: {{ formatDate(item.added_at || item.rental_date) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="row items-center q-gutter-sm">
                    <q-badge v-if="item.returned_date" color="grey">
                      Returned: {{ formatDate(item.returned_date) }}
                    </q-badge>
                    <q-badge v-else color="positive">Active</q-badge>
                    <q-btn
                      v-if="!item.returned_date"
                      flat
                      dense
                      round
                      size="sm"
                      icon="assignment_return"
                      color="positive"
                      @click="returnPUEItem(item)"
                    >
                      <q-tooltip>Return this item</q-tooltip>
                    </q-btn>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- Payment History -->
      <div class="col-12" v-if="paymentHistory.length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6">Payment History</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list separator>
              <q-item v-for="(payment, idx) in paymentHistory" :key="idx">
                <q-item-section avatar>
                  <q-icon name="payment" color="positive" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ currencySymbol }}{{ payment.amount.toFixed(2) }}</q-item-label>
                  <q-item-label caption>
                    {{ payment.payment_type || 'Cash' }}
                  </q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label caption>{{ formatDate(payment.created_at) }}</q-item-label>
                  <q-item-label caption v-if="payment.description">{{ payment.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- Notes -->
      <div class="col-12" v-if="rental.rental?.return_notes">
        <q-card>
          <q-card-section>
            <div class="text-h6">Return Notes</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            {{ rental.rental?.return_notes }}
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Unified Rental Return Dialog -->
    <RentalReturnDialog
      v-model="showReturnDialog"
      :rental="rentalData"
      @returned="onRentalReturned"
    />

    <!-- Return PUE Item Dialog -->
    <q-dialog v-model="showPUEReturnDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Return PUE Item</div>
          <div class="text-subtitle2">{{ selectedPUEItem?.pue?.name || `PUE #${selectedPUEItem?.pue_id}` }}</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model="pueReturnNotes"
            type="textarea"
            label="Return Notes"
            hint="Optional notes about the item condition"
            rows="3"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Confirm Return" color="positive" @click="confirmPUEReturn" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Take Payment Dialog -->
    <q-dialog v-model="showPaymentDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Take Payment</div>
          <div class="text-subtitle2">Rental #{{ $route.params.id }}</div>
        </q-card-section>

        <q-card-section>
          <!-- Payment Summary -->
          <q-banner class="bg-blue-1 q-mb-md">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            <div class="text-body2">
              <div class="text-weight-medium">Amount Owed: {{ currencySymbol }}{{ balanceDue.toFixed(2) }}</div>
              <div v-if="userAccountBalance > 0" class="text-caption text-positive q-mt-xs">
                Available Credit: {{ currencySymbol }}{{ userAccountBalance.toFixed(2) }}
              </div>
            </div>
          </q-banner>

          <!-- Credit Application (always show, but disabled if no credit) -->
          <div class="q-mb-md">
            <q-input
              v-model.number="creditApplied"
              type="number"
              label="Apply Credit from Account"
              :prefix="currencySymbol"
              step="0.01"
              outlined
              :max="maxCreditAvailable"
              :disable="userAccountBalance <= 0"
              :hint="userAccountBalance > 0 ? `Available credit: ${currencySymbol}${userAccountBalance.toFixed(2)}` : 'User has no account credit'"
              :rules="[
                val => val >= 0 || 'Credit cannot be negative',
                val => val <= userAccountBalance || `Cannot exceed available credit (${currencySymbol}${userAccountBalance.toFixed(2)})`,
                val => val <= balanceDue || 'Credit applied cannot exceed amount owed'
              ]"
            >
              <template v-slot:prepend>
                <q-icon name="account_balance_wallet" :color="userAccountBalance > 0 ? 'positive' : 'grey'" />
              </template>
              <template v-slot:append>
                <q-btn
                  flat
                  dense
                  color="positive"
                  label="Use Max"
                  size="sm"
                  @click="creditApplied = maxCreditAvailable"
                  :disable="userAccountBalance <= 0"
                />
              </template>
            </q-input>
          </div>
          <q-input
            v-model.number="paymentAmount"
            type="number"
            label="Payment Amount"
            :prefix="currencySymbol"
            step="0.01"
            outlined
            autofocus
            :rules="[val => ((val || 0) + (creditApplied || 0)) > 0 || 'Total payment (cash + credit) must be greater than 0']"
          >
            <template v-slot:append>
              <q-btn
                flat
                dense
                color="primary"
                label="Full Amount"
                size="sm"
                @click="paymentAmount = balanceDue"
                v-if="balanceDue > 0"
              />
            </template>
          </q-input>

          <!-- Payment Method Selection -->
          <q-select
            v-model="paymentType"
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
            v-model="paymentNotes"
            label="Notes (Optional)"
            outlined
            class="q-mt-md"
            hint="Add any notes or reference number"
          />

          <!-- Confirmation -->
          <q-separator class="q-mt-md" />
          <!-- Show confirmation checkbox only when actual payment is being collected -->
          <div v-if="paymentAmount > 0 && paymentType" class="bg-positive-1 q-pa-md rounded-borders q-mt-md">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="check_circle" color="positive" class="q-mr-sm" />
              Payment Confirmation
            </div>
            <q-checkbox
              v-model="confirmPaymentReceived"
              color="positive"
            >
              <template v-slot:default>
                <div class="text-body2">
                  I confirm that <strong>{{ paymentType }}</strong> payment of
                  <strong>{{ currencySymbol }}{{ (paymentAmount || 0).toFixed(2) }}</strong> has been received<span v-if="creditApplied > 0">, and <strong>{{ currencySymbol }}{{ creditApplied.toFixed(2) }}</strong> will be taken from the user's account credit</span>
                </div>
              </template>
            </q-checkbox>
          </div>
          <!-- When only credit is used, show informational message -->
          <div v-else-if="creditApplied > 0 && paymentAmount === 0" class="bg-positive-1 q-pa-md rounded-borders q-mt-md">
            <div class="text-weight-medium q-mb-sm">
              <q-icon name="account_balance_wallet" color="positive" class="q-mr-sm" />
              Credit Payment
            </div>
            <div class="text-body2">
              <strong>{{ currencySymbol }}{{ creditApplied.toFixed(2) }}</strong> will be taken from the user's account credit to cover this payment.
            </div>
          </div>

          <!-- Payment Summary Preview -->
          <q-card flat bordered class="q-mt-md bg-grey-2">
            <q-card-section class="q-pa-sm">
              <div class="text-caption text-weight-medium q-mb-xs">Payment Summary</div>
              <div class="text-caption">
                <div class="row justify-between">
                  <span>Cash/Card Payment:</span>
                  <span class="text-weight-bold">{{ currencySymbol }}{{ (paymentAmount || 0).toFixed(2) }}</span>
                </div>
                <div v-if="creditApplied > 0" class="row justify-between text-positive">
                  <span>Credit Applied:</span>
                  <span class="text-weight-bold">{{ currencySymbol }}{{ creditApplied.toFixed(2) }}</span>
                </div>
                <div class="row justify-between text-grey-7">
                  <span>Amount Owed:</span>
                  <span>{{ currencySymbol }}{{ balanceDue.toFixed(2) }}</span>
                </div>
                <q-separator class="q-my-xs" />
                <div class="row justify-between text-weight-bold" :class="remainingAfterPayment < 0 ? 'text-positive' : remainingAfterPayment > 0 ? 'text-orange' : ''">
                  <span>Remaining After Payment:</span>
                  <span>{{ currencySymbol }}{{ Math.max(0, remainingAfterPayment).toFixed(2) }}</span>
                </div>
                <div v-if="remainingAfterPayment < 0" class="row justify-between text-positive text-caption q-mt-xs">
                  <span>Overpayment (will be added as credit):</span>
                  <span>{{ currencySymbol }}{{ Math.abs(remainingAfterPayment).toFixed(2) }}</span>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            :label="paymentAmount > 0 ? 'Confirm Payment Received' : 'Apply Credit Payment'"
            color="positive"
            icon="check"
            @click="collectPayment"
            :disable="((paymentAmount || 0) + (creditApplied || 0)) <= 0 || !paymentType || (paymentAmount > 0 && !confirmPaymentReceived)"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { rentalsAPI, batteryRentalsAPI, pueRentalsAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'
import RentalReturnDialog from 'components/RentalReturnDialog.vue'
import { useHubSettingsStore } from 'stores/hubSettings'

const $q = useQuasar()
const route = useRoute()
const router = useRouter()
const hubSettingsStore = useHubSettingsStore()

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const rental = ref(null)
const loading = ref(true)
const paymentHistory = ref([])
const ownershipStatus = ref(null)
const loadingOwnership = ref(false)
const fullUserData = ref(null)

// Computed properties to normalize data structure across rental types
const rentalData = computed(() => {
  if (!rental.value) return null

  // For new battery rental system
  if (route.name === 'battery-rental-detail') {
    return {
      id: rental.value.rental_id || rental.value.rentral_id,
      user_id: rental.value.user_id,
      battery_id: rental.value.batteries?.[0]?.battery_id,
      status: rental.value.rental_status || rental.value.status,
      rental_date: rental.value.rental_start_date,
      expected_return_date: rental.value.rental_end_date,
      actual_return_date: rental.value.actual_return_date,
      deposit_amount: rental.value.deposit_amount || rental.value.deposit_paid,
      total_cost: rental.value.total_cost_calculated || rental.value.final_cost_total || rental.value.estimated_cost_total
    }
  }

  // For new PUE rental system
  if (route.name === 'pue-rental-detail') {
    return {
      id: rental.value.pue_rental_id,
      user_id: rental.value.user_id,
      pue_id: rental.value.pue_id,
      status: rental.value.status || 'active',
      rental_date: rental.value.timestamp_taken,
      expected_return_date: rental.value.due_back,
      actual_return_date: rental.value.date_returned,
      rental_cost: rental.value.rental_cost,
      deposit_amount: rental.value.deposit_amount
    }
  }

  // For legacy rental system
  return rental.value.rental
})

const userData = computed(() => {
  if (!rental.value) return null
  if (route.name === 'battery-rental-detail' || route.name === 'pue-rental-detail') {
    // New system - return fetched user data or fallback to user_id only
    return fullUserData.value || { user_id: rental.value.user_id }
  }
  return rental.value.user
})

const batteryData = computed(() => {
  if (!rental.value) return null
  if (route.name === 'battery-rental-detail') {
    return rental.value.batteries?.[0]
  }
  return rental.value.battery
})

const pueData = computed(() => {
  if (!rental.value) return null
  if (route.name === 'pue-rental-detail') {
    return {
      pue_id: rental.value.pue_id,
      name: rental.value.pue_name
    }
  }
  return null
})

// Computed property for cost structure information
const costStructureInfo = computed(() => {
  if (!rental.value) return null
  if (route.name === 'battery-rental-detail') {
    return rental.value.cost_structure
  }
  if (route.name === 'pue-rental-detail') {
    return rental.value.cost_structure
  }
  return null
})

// Computed property for days remaining
const daysRemaining = computed(() => {
  if (!rentalData.value || !rentalData.value.expected_return_date) return 0

  const now = new Date()
  const expectedReturn = new Date(rentalData.value.expected_return_date)
  const diffTime = expectedReturn - now
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  return diffDays
})

// Computed property for amount paid
const amountPaid = computed(() => {
  if (!rental.value) return 0
  if (route.name === 'battery-rental-detail') {
    return rental.value.amount_paid || 0
  }
  return rentalData.value?.amount_paid || 0
})

// Computed property for total cost
const totalCost = computed(() => {
  if (!rentalData.value) return 0
  return rentalData.value.total_cost || rentalData.value.rental_cost || 0
})

// Computed property for balance due
const balanceDue = computed(() => {
  const balance = totalCost.value - amountPaid.value
  return Math.round(balance * 100) / 100
})

// Computed property to check if rental can be returned
const canReturn = computed(() => {
  if (!rentalData.value) return false

  // Check status and return date from normalized data
  const status = rentalData.value.status
  const isActive = status === 'active' || status === 'overdue'
  const notReturned = !rentalData.value.actual_return_date &&
                       !rentalData.value.date_returned

  return isActive && notReturned
})

const canCollectPayment = computed(() => {
  if (!rentalData.value) return false

  // Can collect payment if:
  // 1. Rental is returned (has actual_return_date)
  // 2. There's a balance due (balanceDue > 0)
  // 3. Total cost is calculated (totalCost > 0)
  const isReturned = rentalData.value.actual_return_date || rentalData.value.date_returned
  const hasBalance = balanceDue.value > 0
  const hasCost = totalCost.value > 0

  return isReturned && hasBalance && hasCost
})

// Computed property to check if this is a pay-to-own rental
const isPayToOwn = computed(() => {
  if (!rental.value) return false
  if (route.name === 'pue-rental-detail') {
    return rental.value.is_pay_to_own || false
  }
  return false
})

const showReturnDialog = ref(false)
const showPaymentDialog = ref(false)
const paymentAmount = ref(0)
const paymentType = ref('cash')
const paymentNotes = ref('')
const confirmPaymentReceived = ref(false)
const creditApplied = ref(0)
const userAccountBalance = ref(0)
const paymentTypeOptions = [
  { label: 'Cash', value: 'cash' },
  { label: 'Mobile Money', value: 'mobile_money' },
  { label: 'Bank Transfer', value: 'bank_transfer' },
  { label: 'Card', value: 'card' }
]

const remainingAfterPayment = computed(() => {
  const totalPayment = (paymentAmount.value || 0) + (creditApplied.value || 0)
  return Math.round((balanceDue.value - totalPayment) * 100) / 100
})

const maxCreditAvailable = computed(() => {
  return Math.min(userAccountBalance.value, balanceDue.value)
})
const returnNotes = ref('')
const showBatteryReturnDialog = ref(false)
const showPUEReturnDialog = ref(false)
const selectedPUEItem = ref(null)
const batteryCondition = ref('good')
const pueReturnNotes = ref('')

// Full return dialog state
const fullReturnCondition = ref('good')
const fullReturnNotes = ref('')
const returnDeposit = ref(true)
const returnPaymentAmount = ref(0)
const returnPaymentType = ref(null)
const confirmReturnPayment = ref(false)
const needsPayment = ref(false)
const kwhEndReading = ref(null)
const calculatedCost = ref(null)
const calculatingCost = ref(false)

const getStatusColor = (status) => {
  const colors = {
    active: 'positive',
    returned: 'grey',
    overdue: 'negative',
    cancelled: 'warning'
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm') + ' UTC'
}

const getUserDisplayName = (user) => {
  if (!user) return 'Unknown User'

  // Try different field combinations
  if (user.Name) return user.Name
  if (user.first_name && user.last_name) return `${user.first_name} ${user.last_name}`
  if (user.first_name) return user.first_name
  if (user.username) return user.username
  if (user.user_id) return `User ${user.user_id}`

  return 'Unknown User'
}

const calculateDays = (rentalInfo) => {
  if (!rentalInfo || !rentalInfo.rental_date || !rentalInfo.expected_return_date) return 0

  const start = new Date(rentalInfo.rental_date)
  const end = rentalInfo.actual_return_date
    ? new Date(rentalInfo.actual_return_date)
    : new Date(rentalInfo.expected_return_date)

  return Math.ceil((end - start) / (1000 * 60 * 60 * 24))
}

const formatUnitType = (unitType) => {
  const unitTypeMap = {
    'per_day': '/day',
    'per_hour': '/hour',
    'per_kwh': '/kWh',
    'per_week': '/week',
    'per_month': '/month',
    'per_year': '/year',
    'flat': '(one-time)',
    'per_charge': '/charge',
    'per_recharge': '/recharge'
  }
  return unitTypeMap[unitType] || ''
}

const loadRentalDetails = async () => {
  loading.value = true

  try {
    const rentalId = route.params.id
    console.log('Loading rental details:', {
      rentalId,
      routeName: route.name,
      fullRoute: route.fullPath
    })
    let response

    // Determine which API to use based on route
    if (route.name === 'battery-rental-detail') {
      // New battery rental system
      console.log('Using battery rentals API for ID:', rentalId)
      response = await batteryRentalsAPI.get(rentalId)
    } else if (route.name === 'pue-rental-detail') {
      // New PUE rental system
      console.log('Using PUE rentals API for ID:', rentalId)
      response = await pueRentalsAPI.get(rentalId)
    } else {
      // Legacy rental system
      console.log('Using legacy rentals API for ID:', rentalId)
      response = await rentalsAPI.get(rentalId)
    }

    rental.value = response.data

    // Fetch full user data for new rental systems
    if ((route.name === 'battery-rental-detail' || route.name === 'pue-rental-detail') && response.data.user_id) {
      try {
        const userResponse = await usersAPI.get(response.data.user_id)
        fullUserData.value = userResponse.data
      } catch (error) {
        console.error('Failed to load user data:', error)
        // Continue without user data
      }
    }

    // If this is a pay-to-own rental, load ownership status
    if (response.data.is_pay_to_own) {
      await loadOwnershipStatus()
    }
  } catch (error) {
    console.error('Failed to load rental:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load rental details',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const loadOwnershipStatus = async () => {
  if (!isPayToOwn.value) return

  loadingOwnership.value = true
  try {
    const rentalId = route.params.id
    const response = await api.get(`/pue-rentals/${rentalId}/ownership-status`)
    ownershipStatus.value = response.data
  } catch (error) {
    console.error('Failed to load ownership status:', error)
  } finally {
    loadingOwnership.value = false
  }
}

const confirmBatteryReturn = async () => {
  try {
    await rentalsAPI.return(route.params.id, {
      return_battery: true,
      return_pue_items: [],  // Don't return PUE items
      battery_condition: batteryCondition.value,
      return_notes: returnNotes.value || ''
    })

    $q.notify({
      type: 'positive',
      message: 'Battery returned successfully',
      position: 'top'
    })

    showBatteryReturnDialog.value = false
    returnNotes.value = ''
    batteryCondition.value = 'good'
    // Reload rental details to show updated status
    await loadRentalDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return battery',
      position: 'top'
    })
  }
}

const returnPUEItem = (item) => {
  selectedPUEItem.value = item
  pueReturnNotes.value = ''
  showPUEReturnDialog.value = true
}

const confirmPUEReturn = async () => {
  try {
    await rentalsAPI.return(route.params.id, {
      return_battery: false,
      return_pue_items: [selectedPUEItem.value.id],
      return_notes: pueReturnNotes.value || ''
    })

    $q.notify({
      type: 'positive',
      message: 'PUE item returned successfully',
      position: 'top'
    })

    showPUEReturnDialog.value = false
    pueReturnNotes.value = ''
    selectedPUEItem.value = null
    // Reload rental details to show updated status
    await loadRentalDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return PUE item',
      position: 'top'
    })
  }
}

const calculateReturnCost = async () => {
  calculatingCost.value = true
  try {
    const params = {}
    if (kwhEndReading.value) {
      params.kwh_usage = kwhEndReading.value
    }

    const response = await rentalsAPI.calculateReturnCost(route.params.id, params)
    calculatedCost.value = response.data

    // Update the needsPayment flag
    if (calculatedCost.value.payment_status?.amount_still_owed > 0) {
      needsPayment.value = true
    }

    $q.notify({
      type: 'positive',
      message: 'Cost calculated successfully',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to calculate cost',
      position: 'top'
    })
  } finally {
    calculatingCost.value = false
  }
}

const confirmFullReturn = async () => {
  try {
    const returnData = {
      battery_return_condition: fullReturnCondition.value,
      battery_return_notes: fullReturnNotes.value,
      return_deposit: returnDeposit.value
    }

    // Add kWh reading if provided
    if (kwhEndReading.value) {
      returnData.kwh_end_reading = kwhEndReading.value
    }

    // If cost was recalculated, update the rental total
    if (calculatedCost.value) {
      returnData.final_cost = calculatedCost.value.total
    }

    // If payment is being collected, add payment info
    if (returnPaymentAmount.value > 0 && returnPaymentType.value) {
      returnData.payment_amount = returnPaymentAmount.value
      returnData.payment_type = returnPaymentType.value
    }

    await rentalsAPI.returnBattery(route.params.id, returnData)

    $q.notify({
      type: 'positive',
      message: 'Rental returned successfully',
      position: 'top'
    })

    showReturnDialog.value = false
    fullReturnCondition.value = 'good'
    fullReturnNotes.value = ''
    returnDeposit.value = true
    returnPaymentAmount.value = 0
    returnPaymentType.value = null
    confirmReturnPayment.value = false
    kwhEndReading.value = null
    calculatedCost.value = null

    // Reload rental details to show updated status
    await loadRentalDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return rental',
      position: 'top'
    })
  }
}

const onRentalReturned = async () => {
  // Reload rental details after successful return
  await loadRentalDetails()
}

const recalculateCost = async () => {
  const rentalId = route.params.id
  if (!rentalId) return

  try {
    $q.loading.show({ message: 'Recalculating cost...' })

    const response = await api.post(`/admin/battery-rentals/${rentalId}/recalculate-cost`)

    $q.notify({
      type: 'positive',
      message: `Cost recalculated: ${currencySymbol.value}${response.data.total.toFixed(2)}`,
      position: 'top'
    })

    // Reload rental details to show updated cost
    await loadRentalDetails()
  } catch (error) {
    console.error('Failed to recalculate cost:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to recalculate cost',
      position: 'top'
    })
  } finally {
    $q.loading.hide()
  }
}

const collectPayment = async () => {
  const totalPayment = (paymentAmount.value || 0) + (creditApplied.value || 0)

  if (totalPayment <= 0) {
    $q.notify({
      type: 'warning',
      message: 'Total payment (cash + credit) must be greater than 0',
      position: 'top'
    })
    return
  }

  if (!paymentType.value) {
    $q.notify({
      type: 'warning',
      message: 'Please select a payment method',
      position: 'top'
    })
    return
  }

  // Only require confirmation checkbox if actual cash/card payment is being collected
  if (paymentAmount.value > 0 && !confirmPaymentReceived.value) {
    $q.notify({
      type: 'warning',
      message: 'Please confirm that payment has been received',
      position: 'top'
    })
    return
  }

  try {
    $q.loading.show({ message: 'Recording payment...' })

    const rentalId = route.params.id
    if (!rentalId) {
      throw new Error('Rental ID not found')
    }

    // Use batteryRentalsAPI to record payment (updates both account and rental payment status)
    // Backend will auto-calculate cost if not yet calculated
    await batteryRentalsAPI.recordPayment(rentalId, {
      payment_amount: paymentAmount.value,
      payment_type: paymentType.value,
      payment_notes: paymentNotes.value || null,
      credit_applied: creditApplied.value || 0
    })

    const totalPayment = (paymentAmount.value || 0) + (creditApplied.value || 0)
    $q.notify({
      type: 'positive',
      message: `Payment of ${currencySymbol.value}${totalPayment.toFixed(2)} recorded successfully${creditApplied.value > 0 ? ` (including ${currencySymbol.value}${creditApplied.value.toFixed(2)} credit)` : ''}`,
      position: 'top',
      timeout: 5000
    })

    // Reset form
    showPaymentDialog.value = false
    paymentAmount.value = 0
    paymentType.value = 'cash'
    paymentNotes.value = ''
    confirmPaymentReceived.value = false
    creditApplied.value = 0
    userAccountBalance.value = 0

    // Reload rental details to show updated payment status
    await loadRentalDetails()
  } catch (error) {
    console.error('Failed to record payment:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to record payment',
      position: 'top'
    })
  } finally {
    $q.loading.hide()
  }
}

onMounted(() => {
  loadRentalDetails()
})

// Watch for when payment dialog opens to pre-fill amount and fetch account balance
watch(() => showPaymentDialog.value, async (isOpen) => {
  if (isOpen && balanceDue.value > 0) {
    paymentAmount.value = balanceDue.value
    paymentType.value = paymentTypeOptions[0].value
    confirmPaymentReceived.value = false
    creditApplied.value = 0

    // Fetch user's account balance
    try {
      const userId = rentalData.value?.user_id
      if (userId) {
        const { accountsAPI } = await import('src/services/api')
        const response = await accountsAPI.getUserAccount(userId)
        userAccountBalance.value = response.data?.balance || 0
        console.log('Fetched user account balance:', userAccountBalance.value, 'for user:', userId)
      }
    } catch (error) {
      console.error('Failed to fetch user account balance:', error)
      userAccountBalance.value = 0
    }
  }
})

// Watch credit applied to auto-adjust payment amount
watch(() => creditApplied.value, (newCredit) => {
  if (showPaymentDialog.value) {
    const remaining = balanceDue.value - (newCredit || 0)
    paymentAmount.value = Math.max(0, remaining)
  }
})
</script>
