<template>
  <q-page class="q-pa-md">
    <div class="text-h4 q-mb-md">Settings</div>

    <!-- Hub Selector for Superadmins -->
    <q-card v-if="authStore.isSuperAdmin" flat bordered class="q-mb-md">
      <q-card-section>
        <div class="row items-center q-gutter-md">
          <div class="col-auto text-subtitle2">Managing Hub:</div>
          <div class="col-auto" style="min-width: 300px">
            <q-select
              v-model="selectedHubId"
              :options="hubOptions"
              option-value="hub_id"
              option-label="what_three_word_location"
              emit-value
              map-options
              outlined
              dense
              label="Select Hub"
              @update:model-value="onHubChange"
            >
              <template v-slot:prepend>
                <q-icon name="location_on" />
              </template>
            </q-select>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <q-tabs
      v-model="tab"
      dense
      class="text-grey"
      active-color="primary"
      indicator-color="primary"
      align="left"
    >
      <q-tab name="pue-types" label="PUE Types" />
      <q-tab name="payment-types" label="Payment Types" />
      <q-tab name="customer-data" label="Customer Data" />
      <q-tab name="return-surveys" label="Return Surveys" />
      <q-tab name="cost-structures" label="Cost Structures" />
      <q-tab name="hub" label="Hub Settings" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="tab" animated>
      <!-- PUE Types Tab -->
      <q-tab-panel name="pue-types">
        <div class="row justify-between q-mb-md">
          <div class="text-h6">PUE Equipment Types</div>
          <q-btn color="primary" label="Add Type" @click="showAddTypeDialog = true" />
        </div>

        <q-table
          :rows="pueTypes"
          :columns="typeColumns"
          row-key="type_id"
          :loading="loading"
        >
          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat round dense icon="edit" color="primary" @click="editType(props.row)" />
              <q-btn flat round dense icon="delete" color="negative" @click="deleteType(props.row)" />
            </q-td>
          </template>
        </q-table>
      </q-tab-panel>

      <!-- Payment Types Tab -->
      <q-tab-panel name="payment-types">
        <div class="row justify-between q-mb-md">
          <div class="text-h6">Payment Types</div>
          <q-btn color="primary" label="Add Payment Type" icon="add" @click="showAddPaymentTypeDialog = true" />
        </div>

        <div class="text-caption text-grey-7 q-mb-md">
          Configure payment methods available for transactions (rentals, deposits, credit top-ups).
        </div>

        <q-table
          :rows="paymentTypes"
          :columns="paymentTypeColumns"
          row-key="type_id"
          :loading="loadingPaymentTypes"
        >
          <template v-slot:body-cell-is_active="props">
            <q-td :props="props">
              <q-badge :color="props.row.is_active ? 'positive' : 'grey'" :label="props.row.is_active ? 'Active' : 'Inactive'" />
            </q-td>
          </template>
          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                :icon="props.row.is_active ? 'block' : 'check_circle'"
                :color="props.row.is_active ? 'negative' : 'positive'"
                @click="togglePaymentType(props.row)"
              >
                <q-tooltip>{{ props.row.is_active ? 'Deactivate' : 'Activate' }}</q-tooltip>
              </q-btn>
              <q-btn flat round dense icon="delete" color="negative" @click="deletePaymentType(props.row)" />
            </q-td>
          </template>
        </q-table>
      </q-tab-panel>

      <!-- Customer Data Tab -->
      <q-tab-panel name="customer-data">
        <div class="text-h6 q-mb-md">Customer Data Configuration</div>

        <div class="text-caption text-grey-7 q-mb-lg">
          Configure dropdown options for customer demographic and business information fields.
        </div>

        <!-- GESI Status Section -->
        <div class="q-mb-xl">
          <div class="row justify-between items-center q-mb-md">
            <div class="text-subtitle1 text-weight-medium">GESI Status Options</div>
            <q-btn
              color="primary"
              label="Add Option"
              icon="add"
              size="sm"
              @click="openAddCustomerOptionDialog('gesi_status')"
            />
          </div>
          <div class="text-caption text-grey-7 q-mb-sm">
            Gender Equality & Social Inclusion categories (e.g., Youth, Older adults, People with disabilities)
          </div>
          <q-table
            :rows="gesiOptions"
            :columns="customerFieldOptionColumns"
            row-key="option_id"
            :loading="loadingCustomerOptions"
            dense
            flat
            bordered
          >
            <template v-slot:body-cell-is_active="props">
              <q-td :props="props">
                <q-badge :color="props.row.is_active ? 'positive' : 'grey'" :label="props.row.is_active ? 'Active' : 'Inactive'" />
              </q-td>
            </template>
            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense icon="edit" color="primary" @click="editCustomerOption(props.row)" />
                <q-btn flat round dense icon="delete" color="negative" @click="deleteCustomerOption(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>

        <!-- Business Category Section -->
        <div class="q-mb-xl">
          <div class="row justify-between items-center q-mb-md">
            <div class="text-subtitle1 text-weight-medium">Business Category Options</div>
            <q-btn
              color="primary"
              label="Add Option"
              icon="add"
              size="sm"
              @click="openAddCustomerOptionDialog('business_category')"
            />
          </div>
          <div class="text-caption text-grey-7 q-mb-sm">
            Business size categories (e.g., Micro, Small, Medium, Large)
          </div>
          <q-table
            :rows="businessCategoryOptions"
            :columns="customerFieldOptionColumns"
            row-key="option_id"
            :loading="loadingCustomerOptions"
            dense
            flat
            bordered
          >
            <template v-slot:body-cell-is_active="props">
              <q-td :props="props">
                <q-badge :color="props.row.is_active ? 'positive' : 'grey'" :label="props.row.is_active ? 'Active' : 'Inactive'" />
              </q-td>
            </template>
            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense icon="edit" color="primary" @click="editCustomerOption(props.row)" />
                <q-btn flat round dense icon="delete" color="negative" @click="deleteCustomerOption(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>

        <!-- Signup Reason Section -->
        <div class="q-mb-xl">
          <div class="row justify-between items-center q-mb-md">
            <div class="text-subtitle1 text-weight-medium">Main Reason for Signing Up Options</div>
            <q-btn
              color="primary"
              label="Add Option"
              icon="add"
              size="sm"
              @click="openAddCustomerOptionDialog('main_reason_for_signup')"
            />
          </div>
          <div class="text-caption text-grey-7 q-mb-sm">
            Main motivations for customers (e.g., Reduce costs, Reliable power, Business operations)
          </div>
          <q-table
            :rows="signupReasonOptions"
            :columns="customerFieldOptionColumns"
            row-key="option_id"
            :loading="loadingCustomerOptions"
            dense
            flat
            bordered
          >
            <template v-slot:body-cell-is_active="props">
              <q-td :props="props">
                <q-badge :color="props.row.is_active ? 'positive' : 'grey'" :label="props.row.is_active ? 'Active' : 'Inactive'" />
              </q-td>
            </template>
            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense icon="edit" color="primary" @click="editCustomerOption(props.row)" />
                <q-btn flat round dense icon="delete" color="negative" @click="deleteCustomerOption(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>
      </q-tab-panel>

      <!-- Return Surveys Tab -->
      <q-tab-panel name="return-surveys">
        <div class="row justify-between q-mb-md">
          <div class="text-h6">Return Survey Builder</div>
          <div class="q-gutter-sm">
            <q-btn color="secondary" label="Export Responses" icon="download" @click="exportSurveyResponses" outline />
            <q-btn color="primary" label="Add Question" icon="add" @click="resetSurveyQuestionForm(); editingSurveyQuestion = null; showAddSurveyQuestionDialog = true" />
          </div>
        </div>

        <div class="text-caption text-grey-7 q-mb-md">
          Configure survey questions that will be presented to customers when they return batteries or PUE items.
          Questions support conditional logic and can be applied to specific rental types.
        </div>

        <!-- Survey Requirement Setting -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle2">Survey Requirement</div>
                <div class="text-caption text-grey-7">
                  Choose whether customers must complete the survey or can skip it when returning items
                </div>
              </div>
              <div class="col-auto">
                <q-toggle
                  v-model="returnSurveyRequired"
                  @update:model-value="updateReturnSurveyRequired"
                  :label="returnSurveyRequired ? 'Required' : 'Optional'"
                  color="primary"
                  size="lg"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Filter -->
        <div class="row q-gutter-md q-mb-md">
          <q-select
            v-model="surveyFilterType"
            :options="[
              { label: 'All Questions', value: 'all' },
              { label: 'Battery Only', value: 'battery' },
              { label: 'PUE Only', value: 'pue' },
              { label: 'Both Types', value: 'both' }
            ]"
            emit-value
            map-options
            outlined
            dense
            label="Filter by Type"
            style="min-width: 200px"
            @update:model-value="loadSurveyQuestions"
          />
          <q-toggle
            v-model="surveyShowInactive"
            label="Show Inactive"
            @update:model-value="loadSurveyQuestions"
          />
        </div>

        <!-- Questions Table -->
        <q-table
          :rows="surveyQuestions"
          :columns="surveyQuestionColumns"
          row-key="question_id"
          :loading="loadingSurveyQuestions"
          :pagination="{ rowsPerPage: 20 }"
        >
          <template v-slot:body-cell-question_text="props">
            <q-td :props="props">
              <div>{{ props.row.question_text }}</div>
              <div v-if="props.row.help_text" class="text-caption text-grey-7">{{ props.row.help_text }}</div>
            </q-td>
          </template>

          <template v-slot:body-cell-question_type="props">
            <q-td :props="props">
              <q-badge :color="getQuestionTypeColor(props.row.question_type)">
                {{ formatQuestionType(props.row.question_type) }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-applies_to="props">
            <q-td :props="props">
              <div class="q-gutter-xs">
                <q-badge v-if="props.row.applies_to_battery" color="blue">Battery</q-badge>
                <q-badge v-if="props.row.applies_to_pue" color="purple">PUE</q-badge>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-conditional="props">
            <q-td :props="props">
              <q-icon
                v-if="props.row.parent_question_id"
                name="call_split"
                color="orange"
                size="sm"
              >
                <q-tooltip>
                  Conditional: Shows when parent question answered with {{ props.row.show_if_parent_answer }}
                </q-tooltip>
              </q-icon>
            </q-td>
          </template>

          <template v-slot:body-cell-is_required="props">
            <q-td :props="props">
              <q-badge :color="props.row.is_required ? 'positive' : 'grey'">
                {{ props.row.is_required ? 'Required' : 'Optional' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-is_active="props">
            <q-td :props="props">
              <q-badge :color="props.row.is_active ? 'positive' : 'grey'">
                {{ props.row.is_active ? 'Active' : 'Inactive' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-options="props">
            <q-td :props="props">
              <q-btn
                flat
                dense
                size="sm"
                :label="`${props.row.options?.length || 0} options`"
                color="primary"
                @click="viewQuestionOptions(props.row)"
                v-if="['multiple_choice', 'multiple_select', 'rating', 'yes_no'].includes(props.row.question_type)"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat round dense icon="edit" color="primary" @click="editSurveyQuestion(props.row)" />
              <q-btn flat round dense icon="delete" color="negative" @click="deleteSurveyQuestion(props.row)" />
            </q-td>
          </template>
        </q-table>
      </q-tab-panel>

      <!-- Cost Structures Tab -->
      <q-tab-panel name="cost-structures">
        <div class="row justify-between q-mb-md">
          <div class="text-h6">Cost Structures</div>
          <q-btn color="primary" label="Create Structure" icon="add" @click="showAddStructureDialog = true" />
        </div>

        <div class="text-caption text-grey-7 q-mb-md">
          Cost structures are named pricing templates that can combine multiple cost components (e.g., daily rate + kWh usage + admin fee).
          Create reusable structures for different battery capacities or PUE types.
        </div>

        <!-- Search Input -->
        <q-input
          v-model="costStructureSearch"
          outlined
          dense
          placeholder="Search by name, component, or item type..."
          class="q-mb-md"
          clearable
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>

        <q-table
          :rows="filteredCostStructures"
          :columns="structureColumns"
          row-key="structure_id"
          :loading="loading"
        >
          <template v-slot:body-cell-components="props">
            <q-td :props="props">
              <div class="text-caption">
                <div v-for="(comp, idx) in props.row.components" :key="idx">
                  {{ comp.component_name }}: {{ currentCurrencySymbol}}{{ comp.rate }} ({{ comp.unit_type }})
                </div>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-is_active="props">
            <q-td :props="props">
              <q-badge :color="props.row.is_active ? 'positive' : 'grey'">
                {{ props.row.is_active ? 'Active' : 'Inactive' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat round dense icon="edit" color="primary" @click="editStructure(props.row)" />
              <q-btn
                flat
                round
                dense
                :icon="props.row.is_active ? 'visibility_off' : 'visibility'"
                :color="props.row.is_active ? 'orange' : 'positive'"
                @click="toggleStructureActive(props.row)"
              />
              <q-btn flat round dense icon="delete" color="negative" @click="deleteStructure(props.row)" />
            </q-td>
          </template>
        </q-table>
      </q-tab-panel>

      <!-- Hub Settings Tab -->
      <q-tab-panel name="hub">
        <div class="text-h6 q-mb-md">Hub Settings</div>

        <q-form @submit="saveHubSettings" class="q-gutter-md" style="max-width: 600px">
          <q-input
            v-model.number="hubSettings.debt_notification_threshold"
            type="number"
            label="Debt Notification Threshold"
            :hint="`Alert when user balance goes below this amount (in ${hubSettings.default_currency || 'USD'})`"
            :prefix="currentCurrencySymbol"
            :rules="[val => val !== null || 'Required']"
          />

          <q-input
            v-model.number="hubSettings.overdue_notification_hours"
            type="number"
            label="Overdue Rental Notification (Hours)"
            hint="Send notification when rental is overdue by this many hours"
            suffix="hours"
            :rules="[val => val > 0 || 'Must be greater than 0']"
          />

          <q-input
            v-model.number="hubSettings.default_table_rows_per_page"
            type="number"
            label="Default Table Rows Per Page"
            hint="Number of items to show per page in tables (e.g., batteries, users, rentals)"
            suffix="rows"
            :rules="[val => val > 0 || 'Must be greater than 0', val => val <= 500 || 'Maximum 500 rows']"
          />

          <!-- VAT/Tax Configuration -->
          <q-input
            v-model.number="hubSettings.vat_percentage"
            type="number"
            label="VAT/Tax Percentage"
            hint="VAT or sales tax percentage (e.g., 15 for 15%)"
            suffix="%"
            step="0.01"
            :rules="[val => val >= 0 || 'Must be 0 or greater']"
          />

          <!-- Timezone Configuration -->
          <q-select
            v-model="hubSettings.timezone"
            :options="timezoneOptions"
            label="Timezone"
            outlined
            use-input
            input-debounce="300"
            @filter="filterTimezones"
            hint="Timezone for displaying dates and times (e.g., Africa/Nairobi, UTC)"
          >
            <template v-slot:prepend>
              <q-icon name="schedule" />
            </template>
          </q-select>

          <!-- Battery Status Thresholds -->
          <div class="q-mt-md">
            <div class="text-subtitle2 q-mb-sm">Battery Status Indicators</div>
            <div class="text-caption text-grey-7 q-mb-md">
              Configure how long since last data received before battery status changes color on the batteries page.
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input
                  v-model.number="hubSettings.battery_status_green_hours"
                  type="number"
                  label="Green Status Threshold"
                  hint="Hours for recent data (green indicator)"
                  suffix="hours"
                  :rules="[val => val > 0 || 'Must be greater than 0']"
                >
                  <template v-slot:prepend>
                    <q-icon name="circle" color="positive" />
                  </template>
                </q-input>
              </div>
              <div class="col-6">
                <q-input
                  v-model.number="hubSettings.battery_status_orange_hours"
                  type="number"
                  label="Orange Status Threshold"
                  hint="Hours for aging data (orange indicator)"
                  suffix="hours"
                  :rules="[val => val > hubSettings.battery_status_green_hours || 'Must be greater than green threshold']"
                >
                  <template v-slot:prepend>
                    <q-icon name="circle" color="orange" />
                  </template>
                </q-input>
              </div>
            </div>
            <div class="text-caption text-grey-7 q-mt-sm">
              <q-icon name="circle" color="positive" size="xs" /> Green: Data received within {{ hubSettings.battery_status_green_hours || 3 }} hours<br />
              <q-icon name="circle" color="orange" size="xs" /> Orange: Data received between {{ hubSettings.battery_status_green_hours || 3 }} and {{ hubSettings.battery_status_orange_hours || 8 }} hours<br />
              <q-icon name="circle" color="negative" size="xs" /> Red: No data for over {{ hubSettings.battery_status_orange_hours || 8 }} hours
            </div>
          </div>

          <!-- Currency Setting - Superadmin Only -->
          <div class="q-mb-md q-pa-md bg-orange-1 rounded-borders">
            <div class="text-subtitle2 text-weight-bold q-mb-sm">
              <q-icon name="warning" color="orange" size="sm" /> Currency Configuration - Critical Setting
            </div>
            <div class="text-caption text-grey-8 q-mb-md">
              The currency should be configured during initial setup and <strong>must not be changed</strong> once the hub is in use.
              Changing currency will NOT convert existing amounts, prices, or transaction histories, which will cause serious financial discrepancies.
              <span v-if="!authStore.isSuperAdmin" class="text-negative text-weight-bold"> Only superadmins can modify this setting.</span>
            </div>
            <q-select
              v-model="hubSettings.default_currency"
              :options="currencyOptions"
              label="Default Currency"
              outlined
              :disable="!authStore.isSuperAdmin"
              :hint="authStore.isSuperAdmin ? 'Select the currency for this hub' : 'Contact a superadmin to change this setting'"
            />

            <q-input
              v-model="hubSettings.currency_symbol"
              label="Currency Symbol"
              outlined
              :disable="!authStore.isSuperAdmin"
              hint="Custom symbol for this currency (e.g., $, £, MK, KSh)"
              class="q-mt-md"
            />
          </div>

          <div>
            <q-btn label="Save Settings" type="submit" color="primary" />
          </div>
        </q-form>
      </q-tab-panel>

    </q-tab-panels>

    <!-- Add/Edit Duration Dialog -->
    <q-dialog v-model="showAddDurationDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">{{ editingDuration ? 'Edit' : 'Add' }} Rental Duration Preset</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input v-model="newDuration.label" label="Label" hint="e.g., '1 Day', '2 Weeks'" />
          <q-input v-model.number="newDuration.duration_value" type="number" label="Duration Value" />
          <q-select
            v-model="newDuration.duration_unit"
            :options="['hours', 'days', 'weeks']"
            label="Duration Unit"
          />
          <q-input v-model.number="newDuration.sort_order" type="number" label="Sort Order" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat :label="editingDuration ? 'Update' : 'Add'" color="primary" @click="saveDuration" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add/Edit PUE Type Dialog -->
    <q-dialog v-model="showAddTypeDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">{{ editingType ? 'Edit' : 'Add' }} PUE Type</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input v-model="newType.type_name" label="Type Name" />
          <q-input v-model="newType.description" label="Description" type="textarea" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat :label="editingType ? 'Update' : 'Add'" color="primary" @click="saveType" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Payment Type Dialog -->
    <q-dialog v-model="showAddPaymentTypeDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Add Payment Type</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model="newPaymentType.type_name"
            label="Payment Type Name *"
            outlined
            :rules="[val => !!val || 'Name is required']"
            hint="e.g., Cash, Mobile Money, Bank Transfer"
          />
          <q-input
            v-model="newPaymentType.description"
            label="Description"
            type="textarea"
            outlined
            rows="2"
            hint="Optional description"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Add" color="primary" @click="savePaymentType" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add/Edit Survey Question Dialog -->
    <q-dialog v-model="showAddSurveyQuestionDialog" persistent>
      <q-card style="min-width: 600px; max-width: 800px">
        <q-card-section>
          <div class="text-h6">{{ editingSurveyQuestion ? 'Edit' : 'Add' }} Survey Question</div>
        </q-card-section>

        <q-card-section class="q-gutter-md" style="max-height: 60vh; overflow-y: auto;">
          <!-- Question Text -->
          <q-input
            v-model="newSurveyQuestion.question_text"
            label="Question Text *"
            type="textarea"
            outlined
            rows="2"
            :rules="[val => !!val || 'Question text is required']"
            hint="The question to ask the customer"
          />

          <!-- Help Text -->
          <q-input
            v-model="newSurveyQuestion.help_text"
            label="Help Text (Optional)"
            type="textarea"
            outlined
            rows="2"
            hint="Additional explanation or context for the question"
          />

          <!-- Question Type -->
          <q-select
            v-model="newSurveyQuestion.question_type"
            :options="questionTypeOptions"
            emit-value
            map-options
            outlined
            label="Question Type *"
            hint="How the user will answer this question"
          />

          <!-- Applies To -->
          <div>
            <div class="text-subtitle2 q-mb-sm">Applies To *</div>
            <div class="row q-gutter-md">
              <q-checkbox v-model="newSurveyQuestion.applies_to_battery" label="Battery Rentals" />
              <q-checkbox v-model="newSurveyQuestion.applies_to_pue" label="PUE Rentals" />
            </div>
          </div>

          <!-- Required -->
          <q-checkbox
            v-model="newSurveyQuestion.is_required"
            label="This question is required"
          />

          <!-- Active -->
          <q-checkbox
            v-model="newSurveyQuestion.is_active"
            label="Question is active"
          />

          <!-- Sort Order -->
          <q-input
            v-model.number="newSurveyQuestion.sort_order"
            type="number"
            label="Sort Order"
            outlined
            hint="Controls the display order (lower numbers appear first)"
          />

          <!-- Rating Scale Fields (only for rating type) -->
          <div v-if="newSurveyQuestion.question_type === 'rating'">
            <q-separator class="q-my-md" />
            <div class="text-subtitle2 q-mb-sm">Rating Scale Configuration</div>
            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input
                  v-model.number="newSurveyQuestion.rating_min"
                  type="number"
                  label="Minimum Value *"
                  outlined
                  :rules="[val => val !== null && val !== undefined || 'Required']"
                  hint="E.g., 1"
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model.number="newSurveyQuestion.rating_max"
                  type="number"
                  label="Maximum Value *"
                  outlined
                  :rules="[val => val !== null && val !== undefined || 'Required']"
                  hint="E.g., 10"
                />
              </div>
            </div>
            <div class="row q-col-gutter-md q-mt-xs">
              <div class="col-6">
                <q-input
                  v-model="newSurveyQuestion.rating_min_label"
                  label="Minimum Label *"
                  outlined
                  :rules="[val => !!val || 'Required']"
                  hint="E.g., 'Very Dissatisfied'"
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model="newSurveyQuestion.rating_max_label"
                  label="Maximum Label *"
                  outlined
                  :rules="[val => !!val || 'Required']"
                  hint="E.g., 'Very Satisfied'"
                />
              </div>
            </div>
          </div>

          <!-- Answer Options (for multiple choice, select, yes/no - NOT rating) -->
          <div v-if="['multiple_choice', 'multiple_select', 'yes_no'].includes(newSurveyQuestion.question_type)">
            <q-separator class="q-my-md" />
            <div class="text-subtitle2 q-mb-sm">
              Answer Options *
              <span v-if="newSurveyQuestion.question_type === 'yes_no'" class="text-caption text-grey-7">
                (Yes/No options will be created automatically)
              </span>
            </div>
            <div v-if="newSurveyQuestion.question_type === 'yes_no'" class="text-caption text-grey-7 q-mb-md">
              No need to add options - Yes/No will be created automatically when you save.
            </div>
            <div v-else class="text-caption text-grey-7 q-mb-md">
              Define the choices available for this question
            </div>

            <!-- Options List (only show for non-yes_no types) -->
            <q-list v-if="newSurveyQuestion.question_type !== 'yes_no'" bordered separator class="q-mb-md">
              <q-item v-for="(option, index) in currentQuestionOptions" :key="index">
                <q-item-section>
                  <q-item-label>{{ option.option_text }}</q-item-label>
                  <q-item-label caption>Value: {{ option.option_value }}</q-item-label>
                  <q-item-label caption v-if="option.is_open_text_trigger">
                    <q-badge color="blue" label="Triggers text input" />
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="row q-gutter-xs">
                    <q-btn flat dense round icon="edit" size="sm" @click="editOptionInList(index)" />
                    <q-btn flat dense round icon="delete" size="sm" color="negative" @click="removeOptionFromList(index)" />
                  </div>
                </q-item-section>
              </q-item>
              <q-item v-if="currentQuestionOptions.length === 0">
                <q-item-section class="text-grey-7 text-center">
                  No options added yet. Click "Add Option" below.
                </q-item-section>
              </q-item>
            </q-list>

            <!-- Add/Edit Option Form (only for non-yes_no types) -->
            <q-card v-if="newSurveyQuestion.question_type !== 'yes_no'" flat bordered class="q-pa-md">
              <div class="q-gutter-sm">
                <q-input
                  v-model="newQuestionOption.option_text"
                  label="Option Text *"
                  outlined
                  dense
                  hint="The text shown to the user"
                />
                <q-input
                  v-model="newQuestionOption.option_value"
                  label="Option Value *"
                  outlined
                  dense
                  hint="The value stored in the database (e.g., 'yes', '1', '2')"
                />
                <q-input
                  v-model.number="newQuestionOption.sort_order"
                  type="number"
                  label="Sort Order"
                  outlined
                  dense
                  hint="Controls display order"
                />
                <q-checkbox
                  v-model="newQuestionOption.is_open_text_trigger"
                  label="Trigger additional text input"
                  dense
                >
                  <template v-slot:default>
                    <div>
                      <div>Trigger additional text input</div>
                      <div class="text-caption text-grey-7">
                        When this option is selected by a user, an additional text field will appear asking them to provide more details. Useful for "Other" options or when you want elaboration.
                      </div>
                    </div>
                  </template>
                </q-checkbox>
                <div class="row q-gutter-sm justify-end">
                  <q-btn
                    v-if="editingOptionIndex !== null"
                    flat
                    label="Cancel Edit"
                    size="sm"
                    @click="cancelEditOption"
                  />
                  <q-btn
                    flat
                    :label="editingOptionIndex !== null ? 'Update Option' : 'Add Option'"
                    color="primary"
                    size="sm"
                    icon="add"
                    @click="addOptionToList"
                  />
                </div>
              </div>
            </q-card>
          </div>

          <!-- Conditional Logic -->
          <q-expansion-item
            label="Conditional Logic (Advanced)"
            icon="call_split"
            caption="Show this question only when a previous question is answered in a specific way"
          >
            <q-card flat bordered class="q-mt-sm">
              <q-card-section class="q-gutter-md">
                <q-select
                  v-model="newSurveyQuestion.parent_question_id"
                  :options="surveyQuestions.filter(q => q.question_id !== editingSurveyQuestion?.question_id)"
                  option-value="question_id"
                  option-label="question_text"
                  emit-value
                  map-options
                  outlined
                  clearable
                  label="Parent Question"
                  hint="The question that determines if this question should be shown"
                />

                <q-input
                  v-if="newSurveyQuestion.parent_question_id"
                  v-model="newSurveyQuestion.show_if_parent_answer"
                  label="Show if parent answer is"
                  outlined
                  hint='Enter answer values as JSON array, e.g., ["yes"] or ["2", "3"]'
                  placeholder='["answer_value"]'
                />
              </q-card-section>
            </q-card>
          </q-expansion-item>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showAddSurveyQuestionDialog = false; editingSurveyQuestion = null; resetSurveyQuestionForm()" />
          <q-btn flat label="Save Question" color="primary" @click="saveSurveyQuestion" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- View Question Options Dialog -->
    <q-dialog v-model="showQuestionOptionsDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Question Options</div>
          <div class="text-caption text-grey-7">{{ viewingQuestionOptions?.question_text }}</div>
        </q-card-section>

        <q-card-section>
          <q-list bordered separator>
            <q-item v-for="option in viewingQuestionOptions?.options" :key="option.option_id">
              <q-item-section>
                <q-item-label>{{ option.option_text }}</q-item-label>
                <q-item-label caption>Value: {{ option.option_value }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="q-gutter-xs">
                  <q-badge v-if="option.is_open_text_trigger" color="orange" label="Text Input" />
                  <q-badge color="grey" :label="`Order: ${option.sort_order}`" />
                </div>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add/Edit Cost Structure Dialog -->
    <q-dialog v-model="showAddStructureDialog" persistent>
      <q-card style="min-width: 700px; max-width: 900px; max-height: 90vh">
        <q-card-section>
          <div class="text-h6">{{ editingStructure ? 'Edit' : 'Create' }} Cost Structure</div>
        </q-card-section>

        <!-- Tabs for Basic Setup and Late Fee Configuration -->
        <q-tabs
          v-model="structureTab"
          dense
          class="text-grey"
          active-color="primary"
          indicator-color="primary"
          align="justify"
        >
          <q-tab name="basic" label="Basic Setup" icon="settings" />
          <q-tab name="latefees" label="Late Fee Configuration" icon="schedule" :disable="newStructure.components.length === 0" />
        </q-tabs>

        <q-separator />

        <q-tab-panels v-model="structureTab" animated style="max-height: 60vh; overflow-y: auto">
          <!-- Basic Setup Tab -->
          <q-tab-panel name="basic">
            <div class="q-gutter-md">
              <!-- Structure Name -->
          <q-input
            v-model="newStructure.name"
            label="Structure Name"
            hint="e.g., 'Standard Battery Rental', 'Premium with kWh'"
            outlined
            :rules="[val => !!val || 'Name is required']"
          />

          <!-- Description -->
          <q-input
            v-model="newStructure.description"
            label="Description"
            type="textarea"
            rows="2"
            outlined
            hint="Optional description of what this cost structure includes"
          />

          <!-- Item Type -->
          <q-select
            v-model="newStructure.item_type"
            :options="[
              {label: 'All Batteries', value: 'battery', description: 'Applies to all batteries regardless of capacity'},
              {label: 'Specific Battery Capacity', value: 'battery_capacity', description: 'Applies to batteries of a specific capacity'},
              {label: 'Specific Battery', value: 'battery_item', description: 'Applies to one specific battery'},
              {label: 'All PUE Items', value: 'pue', description: 'Applies to all PUE equipment'},
              {label: 'Specific PUE Type', value: 'pue_type', description: 'Applies to specific type of PUE equipment'},
              {label: 'Specific PUE Item', value: 'pue_item', description: 'Applies to one specific PUE item'}
            ]"
            option-label="label"
            option-value="value"
            emit-value
            map-options
            label="Item Type"
            outlined
            @update:model-value="onStructureItemTypeChange"
            hint="What type of item does this structure apply to?"
          >
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.label }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- Item Reference - Changes based on item_type -->
          <q-input
            v-if="newStructure.item_type === 'battery'"
            v-model="newStructure.item_reference"
            label="Reference"
            outlined
            readonly
            hint="This structure applies to all batteries"
          />

          <q-select
            v-else-if="newStructure.item_type === 'battery_capacity'"
            v-model="newStructure.item_reference"
            :options="batteryCapacityOptions"
            label="Battery Capacity"
            outlined
            use-input
            input-debounce="0"
            @filter="filterBatteryCapacities"
            hint="Select battery capacity (Wh)"
          />

          <q-select
            v-else-if="newStructure.item_type === 'battery_item'"
            v-model="newStructure.item_reference"
            :options="filteredBatteries"
            option-value="battery_id"
            option-label="label"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterBatteriesForCostStructure"
            label="Battery"
            outlined
            hint="Type to search by model or ID"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No batteries found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-input
            v-else-if="newStructure.item_type === 'pue'"
            v-model="newStructure.item_reference"
            label="Reference"
            outlined
            readonly
            hint="This structure applies to all PUE items"
          />

          <q-select
            v-else-if="newStructure.item_type === 'pue_type'"
            v-model="newStructure.item_reference"
            :options="filteredPUETypes"
            option-value="type_name"
            option-label="type_name"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterPUETypesForPricing"
            label="PUE Type"
            outlined
            hint="Type to search PUE equipment type"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No PUE types found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-select
            v-else-if="newStructure.item_type === 'pue_item'"
            v-model="newStructure.item_reference"
            :options="filteredPUEItems"
            option-value="pue_id"
            :option-label="(item) => item ? `${item.pue_id} - ${item.name}` : ''"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterPUEItemsForPricing"
            label="PUE Item"
            outlined
            hint="Type to search by ID or name"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No PUE items found
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.pue_id }} - {{ scope.opt.name }}</q-item-label>
                  <q-item-label caption v-if="scope.opt.description">{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-separator class="q-my-md" />

          <!-- Pay to Own Section -->
          <div class="text-subtitle2 q-mt-md">Pay-to-Own Options</div>
          <div class="text-caption text-grey-7 q-mb-sm">
            Configure if this cost structure supports gradual ownership
          </div>

          <q-checkbox
            v-model="newStructure.is_pay_to_own"
            label="Enable Pay-to-Own"
            dense
            :disable="!['pue_item', 'battery_item'].includes(newStructure.item_type)"
            @update:model-value="onPayToOwnToggle"
          >
            <q-tooltip>
              {{['pue_item', 'battery_item'].includes(newStructure.item_type)
                ? 'When enabled, customers can gradually pay off the item to own it'
                : 'Only available for Specific PUE Item or Specific Battery'}}
            </q-tooltip>
          </q-checkbox>

          <q-input
            v-if="newStructure.is_pay_to_own"
            v-model.number="newStructure.item_total_cost"
            type="number"
            label="Total Item Cost *"
            :prefix="currentCurrencySymbol"
            step="0.01"
            outlined
            class="q-mt-md"
            hint="The full price of the item to be owned"
            :rules="[val => newStructure.is_pay_to_own ? (val > 0 || 'Item cost is required for pay-to-own') : true]"
          />

          <q-banner v-if="newStructure.is_pay_to_own" class="bg-purple-1 q-mt-md" rounded>
            <template v-slot:avatar>
              <q-icon name="info" color="purple" />
            </template>
            <div class="text-body2">
              <strong>Pay-to-Own Constraints:</strong>
              <ul class="q-ma-none q-pl-md">
                <li>Only applies to single items (quantity = 1)</li>
                <li>Duration options are not applicable</li>
                <li>Cost components can contribute to ownership or be rental fees</li>
              </ul>
            </div>
          </q-banner>

          <q-separator />

          <!-- Cost Components Section -->
          <div class="text-subtitle2 q-mt-md">Cost Components</div>
          <div class="text-caption text-grey-7 q-mb-sm">
            Add multiple cost components to build your pricing structure
          </div>

          <!-- Component List -->
          <div v-for="(component, index) in newStructure.components" :key="index" class="q-pa-md bg-grey-1 rounded-borders q-mb-sm">
            <div class="row q-gutter-md items-start">
              <!-- Unit Type First -->
              <div class="col-2">
                <q-select
                  v-model="component.unit_type"
                  :options="[
                    {label: 'Per Day', value: 'per_day'},
                    {label: 'Per Week', value: 'per_week'},
                    {label: 'Per Month', value: 'per_month'},
                    {label: 'Per Hour', value: 'per_hour'},
                    {label: 'Per kWh', value: 'per_kwh'},
                    {label: 'Per Kg', value: 'per_kg'},
                    {label: 'Per Recharge', value: 'per_recharge'},
                    {label: 'One Time', value: 'one_time'},
                    {label: 'Fixed Fee', value: 'fixed'}
                  ]"
                  option-label="label"
                  option-value="value"
                  emit-value
                  map-options
                  label="Unit Type"
                  dense
                  outlined
                  @update:model-value="onUnitTypeChange(component)"
                />
              </div>

              <!-- Component Name Second (auto-populated but editable) -->
              <div class="col-3">
                <q-input
                  v-model="component.component_name"
                  label="Component Name"
                  dense
                  outlined
                  hint="Auto-filled, but editable"
                />
              </div>

              <div class="col-2">
                <q-input
                  v-model.number="component.rate"
                  type="number"
                  label="Rate"
                  dense
                  outlined
                  :prefix="currentCurrencySymbol"
                  step="0.01"
                />
              </div>

              <div class="col-3">
                <div class="text-caption text-grey-7 q-mb-xs">Charge Type</div>
                <q-option-group
                  :model-value="getComponentChargeType(component)"
                  @update:model-value="(val) => setComponentChargeType(component, val)"
                  :options="[
                    { label: 'Upfront', value: 'upfront' },
                    { label: 'On Return', value: 'on_return' },
                    { label: 'Recurring', value: 'recurring' }
                  ]"
                  dense
                  inline
                />

                <!-- Recurring Interval Input -->
                <div v-if="getComponentChargeType(component) === 'recurring'" class="row items-center q-mt-xs q-gutter-xs">
                  <q-input
                    v-model.number="component.recurring_interval"
                    type="number"
                    label="Every"
                    dense
                    outlined
                    step="0.5"
                    min="0.5"
                    style="width: 80px"
                  />
                  <span class="text-caption">{{ getIntervalUnit(component.unit_type) }}</span>
                </div>
              </div>

              <div class="col-1">
                <q-btn
                  flat
                  round
                  dense
                  icon="delete"
                  color="negative"
                  @click="removeComponent(index)"
                />
              </div>
            </div>

            <!-- Pay-to-Own Options (only shown when pay-to-own is enabled) -->
            <div v-if="newStructure.is_pay_to_own" class="row q-gutter-md items-start q-mt-sm">
              <div class="col-12">
                <div class="text-caption text-purple-8 q-mb-xs">
                  <q-icon name="account_balance" size="xs" /> Pay-to-Own Settings
                </div>
              </div>

              <div class="col-3">
                <q-checkbox
                  v-model="component.contributes_to_ownership"
                  label="Contributes to Ownership"
                  dense
                  color="purple"
                >
                  <q-tooltip>
                    When checked, this payment builds equity toward ownership
                  </q-tooltip>
                </q-checkbox>
              </div>

              <div class="col-3">
                <q-checkbox
                  v-model="component.is_percentage_of_remaining"
                  label="% of Remaining Balance"
                  dense
                  color="purple"
                  :disable="!component.contributes_to_ownership"
                >
                  <q-tooltip>
                    Calculate as percentage of remaining balance instead of fixed amount
                  </q-tooltip>
                </q-checkbox>
              </div>

              <div class="col-2" v-if="component.is_percentage_of_remaining">
                <q-input
                  v-model.number="component.percentage_value"
                  type="number"
                  label="Percentage"
                  suffix="%"
                  dense
                  outlined
                  min="0"
                  max="100"
                  step="0.1"
                />
              </div>
            </div>
          </div>

          <!-- Add Component Button -->
          <q-btn
            flat
            icon="add"
            label="Add Component"
            color="primary"
            @click="addComponent"
          />

          <!-- Recharge Settings (only shown if per_recharge component exists) -->
          <template v-if="hasPerRechargeComponent">
            <q-separator class="q-my-md" />
            <div class="text-subtitle2 q-mt-md">Recharge Settings</div>
            <div class="text-caption text-grey-7 q-mb-sm">
              Configure how initial checkout is counted for recharge-based pricing
            </div>
            <q-checkbox
              v-model="newStructure.count_initial_checkout_as_recharge"
              label="Count initial checkout as first recharge"
              dense
            >
              <q-tooltip>
                When enabled, rentals start with recharges_used=1. Useful when you want to charge for the initial battery checkout as the first recharge.
              </q-tooltip>
            </q-checkbox>
          </template>

          <!-- Duration Options Section (hidden for pay-to-own) -->
          <template v-if="!newStructure.is_pay_to_own">
            <q-separator class="q-my-md" />

            <!-- Allow Custom Duration Control -->
            <q-checkbox
              v-model="newStructure.allow_custom_duration"
              label="Allow Custom Duration Input"
              dense
              class="q-mb-md"
            >
              <q-tooltip>
                When enabled, users can enter custom rental durations. When disabled, users can only select from predefined duration options.
              </q-tooltip>
            </q-checkbox>

            <div class="text-subtitle2 q-mt-md">Duration Options</div>
            <div class="text-caption text-grey-7 q-mb-sm">
              Define how users will select rental duration (e.g., dropdown with 1, 2, 5 days or custom input)
            </div>

          <!-- Duration Option List -->
          <div v-for="(option, index) in newStructure.duration_options" :key="'dur-' + index" class="q-pa-md bg-grey-1 rounded-borders q-mb-sm">
            <div class="row q-gutter-md items-start q-mb-md">
              <div class="col-3">
                <q-select
                  v-model="option.input_type"
                  :options="[
                    {label: 'Custom Input', value: 'custom'},
                    {label: 'Dropdown Choices', value: 'dropdown'}
                  ]"
                  option-label="label"
                  option-value="value"
                  emit-value
                  map-options
                  label="Input Type"
                  dense
                  outlined
                />
              </div>

              <div class="col-3">
                <q-input
                  v-model="option.label"
                  label="Label"
                  dense
                  outlined
                  hint="e.g., 'Rental Duration'"
                />
              </div>

              <!-- For custom input type -->
              <template v-if="option.input_type === 'custom'">
                <div class="col-2">
                  <q-select
                    v-model="option.custom_unit"
                    :options="[
                      {label: 'Hours', value: 'hours'},
                      {label: 'Days', value: 'days'},
                      {label: 'Weeks', value: 'weeks'},
                      {label: 'Months', value: 'months'}
                    ]"
                    option-label="label"
                    option-value="value"
                    emit-value
                    map-options
                    label="Unit"
                    dense
                    outlined
                  />
                </div>
                <div class="col-1">
                  <q-input
                    v-model.number="option.default_value"
                    type="number"
                    label="Default"
                    dense
                    outlined
                  />
                </div>
                <div class="col-1">
                  <q-input
                    v-model.number="option.min_value"
                    type="number"
                    label="Min"
                    dense
                    outlined
                  />
                </div>
                <div class="col-1">
                  <q-input
                    v-model.number="option.max_value"
                    type="number"
                    label="Max"
                    dense
                    outlined
                  />
                </div>
              </template>

              <div class="col-1">
                <q-btn
                  flat
                  round
                  dense
                  icon="delete"
                  color="negative"
                  @click="removeDurationOption(index)"
                />
              </div>
            </div>

            <!-- For dropdown type - show list of choices -->
            <template v-if="option.input_type === 'dropdown'">
              <div class="q-ml-md">
                <div class="text-caption q-mb-sm">Dropdown Choices:</div>
                <div v-for="(choice, choiceIndex) in option.dropdown_choices" :key="'choice-' + choiceIndex" class="row q-gutter-sm q-mb-xs items-center">
                  <q-input
                    v-model.number="choice.value"
                    type="number"
                    label="Value"
                    dense
                    outlined
                    style="width: 80px"
                  />
                  <q-select
                    v-model="choice.unit"
                    :options="[
                      {label: 'Hours', value: 'hours'},
                      {label: 'Days', value: 'days'},
                      {label: 'Weeks', value: 'weeks'},
                      {label: 'Months', value: 'months'}
                    ]"
                    option-label="label"
                    option-value="value"
                    emit-value
                    map-options
                    label="Unit"
                    dense
                    outlined
                    style="width: 120px"
                  />
                  <q-input
                    v-model="choice.label"
                    label="Label"
                    dense
                    outlined
                    hint="e.g., '1 Day', '2 Weeks'"
                    style="width: 150px"
                  />
                  <q-btn
                    flat
                    round
                    dense
                    size="sm"
                    icon="delete"
                    color="negative"
                    @click="removeDropdownChoice(index, choiceIndex)"
                  />
                </div>
                <q-btn
                  flat
                  size="sm"
                  icon="add"
                  label="Add Choice"
                  color="primary"
                  @click="addDropdownChoice(index)"
                />
              </div>
            </template>
          </div>

          <!-- Add Duration Option Button -->
          <q-btn
            flat
            icon="add"
            label="Add Duration Option"
            color="primary"
            @click="addDurationOption"
          />
          </template>
            </div>
          </q-tab-panel>

          <!-- Late Fee Configuration Tab -->
          <q-tab-panel name="latefees">
            <div class="text-caption text-grey-7 q-mb-md">
              Configure what happens to each cost component when a rental becomes overdue. You can set grace periods and penalty fees per component.
            </div>

            <div v-if="newStructure.components.length === 0" class="text-center q-pa-lg text-grey-7">
              <q-icon name="info" size="lg" class="q-mb-sm" />
              <div>No components added yet. Add components in the Basic Setup tab first.</div>
            </div>

            <!-- Late Fee Configuration for Each Component -->
            <div v-for="(component, index) in newStructure.components" :key="'latefee-' + index" class="q-mb-md">
              <q-card flat bordered>
                <q-card-section class="bg-blue-grey-1">
                  <div class="row items-center">
                    <q-icon name="attach_money" class="q-mr-sm" />
                    <div class="text-weight-medium">{{ component.component_name }}</div>
                    <q-chip dense size="sm" class="q-ml-sm">{{ component.unit_type }}</q-chip>
                  </div>
                </q-card-section>

                <q-card-section>
                  <div class="q-gutter-md">
                    <!-- Late Fee Action -->
                    <q-select
                      v-model="component.late_fee_action"
                      :options="[
                        {label: 'Continue Billing (Default)', value: 'continue', description: 'Keep billing this component after due date'},
                        {label: 'Stop Billing', value: 'stop', description: 'Stop billing this component after due date (e.g., for per_kwh)'},
                        {label: 'Add Daily Fine', value: 'daily_fine', description: 'Add a daily penalty fee after grace period'},
                        {label: 'Add Weekly Fine', value: 'weekly_fine', description: 'Add a weekly penalty fee after grace period'}
                      ]"
                      option-label="label"
                      option-value="value"
                      emit-value
                      map-options
                      label="Late Fee Action"
                      outlined
                      dense
                    >
                      <template v-slot:option="scope">
                        <q-item v-bind="scope.itemProps">
                          <q-item-section>
                            <q-item-label>{{ scope.opt.label }}</q-item-label>
                            <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                          </q-item-section>
                        </q-item>
                      </template>
                    </q-select>

                    <!-- Grace Period -->
                    <q-input
                      v-model.number="component.late_fee_grace_days"
                      type="number"
                      label="Grace Period (Days)"
                      outlined
                      dense
                      min="0"
                      hint="Number of days after due date before late fees apply"
                    />

                    <!-- Fine Rate (only show for daily_fine and weekly_fine) -->
                    <q-input
                      v-if="component.late_fee_action === 'daily_fine' || component.late_fee_action === 'weekly_fine'"
                      v-model.number="component.late_fee_rate"
                      type="number"
                      :label="component.late_fee_action === 'daily_fine' ? 'Fine per Day' : 'Fine per Week'"
                      outlined
                      dense
                      :prefix="currentCurrencySymbol"
                      step="0.01"
                      hint="Amount to charge for each late period"
                    />

                    <!-- Example Calculation -->
                    <q-banner dense class="bg-amber-1 text-grey-8" v-if="component.late_fee_action !== 'continue'">
                      <template v-slot:avatar>
                        <q-icon name="info" color="amber-8" />
                      </template>
                      <div class="text-caption">
                        <strong>Example:</strong>
                        <span v-if="component.late_fee_action === 'stop'">
                          After {{ component.late_fee_grace_days }} days past due date, "{{ component.component_name }}" will stop being charged.
                        </span>
                        <span v-else-if="component.late_fee_action === 'daily_fine'">
                          After {{ component.late_fee_grace_days }} days past due date, a fine of {{ currentCurrencySymbol }}{{ component.late_fee_rate || 0 }}/day will be added.
                        </span>
                        <span v-else-if="component.late_fee_action === 'weekly_fine'">
                          After {{ component.late_fee_grace_days }} days past due date, a fine of {{ currentCurrencySymbol }}{{ component.late_fee_rate || 0 }}/week will be added.
                        </span>
                      </div>
                    </q-banner>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </q-tab-panel>
        </q-tab-panels>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup @click="cancelStructureEdit" />
          <q-btn
            flat
            :label="editingStructure ? 'Update' : 'Create'"
            color="primary"
            @click="saveStructure"
            :disable="!isStructureValid"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Pricing Dialog -->
    <q-dialog v-model="showAddPricingDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Add Pricing Configuration</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <!-- Display current hub being managed -->
          <div v-if="activeHubId.value" class="text-caption text-grey-7 q-mb-sm">
            Managing pricing for: {{ hubOptions.find(h => h.hub_id === activeHubId.value)?.what_three_word_location || 'Current Hub' }}
          </div>

          <!-- Hub Selection (for superadmin) -->
          <q-select
            v-if="authStore.isSuperAdmin"
            v-model="newPricing.hub_id"
            :options="hubOptions"
            option-value="hub_id"
            option-label="what_three_word_location"
            emit-value
            map-options
            label="Hub (Override)"
            outlined
            clearable
            hint="Defaults to selected hub, or leave empty for global pricing"
            @update:model-value="onPricingHubChange"
          />

          <!-- Item Type Selection -->
          <q-select
            v-model="newPricing.item_type"
            :options="[
              {label: 'Battery Capacity', value: 'battery_capacity'},
              {label: 'PUE Item', value: 'pue_item'},
              {label: 'PUE Type', value: 'pue_type'}
            ]"
            option-label="label"
            option-value="value"
            emit-value
            map-options
            label="Item Type"
            outlined
            @update:model-value="onItemTypeChange"
          />

          <!-- Item Reference - Changes based on item_type -->
          <q-select
            v-if="newPricing.item_type === 'battery_capacity'"
            v-model="newPricing.item_reference"
            :options="batteryCapacityOptions"
            label="Battery Capacity"
            outlined
            use-input
            input-debounce="0"
            @filter="filterBatteryCapacities"
            hint="Select battery capacity (Wh)"
            :disable="!newPricing.hub_id && authStore.isSuperAdmin"
            :hint="!newPricing.hub_id && authStore.isSuperAdmin ? 'Select a hub first' : 'Select battery capacity (Wh)'"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No battery capacities found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-select
            v-else-if="newPricing.item_type === 'pue_type'"
            v-model="newPricing.item_reference"
            :options="filteredPUETypes"
            option-value="type_name"
            option-label="type_name"
            emit-value
            map-options
            label="PUE Type"
            outlined
            use-input
            input-debounce="0"
            @filter="filterPUETypesForPricing"
            :disable="!newPricing.hub_id && authStore.isSuperAdmin"
            :hint="!newPricing.hub_id && authStore.isSuperAdmin ? 'Select a hub first' : 'Select PUE equipment type'"
          >
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.type_name }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No PUE types found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-select
            v-else-if="newPricing.item_type === 'pue_item'"
            v-model="newPricing.item_reference"
            :options="filteredPUEItems"
            option-value="pue_id"
            :option-label="(item) => item ? `${item.pue_id} - ${item.name}` : ''"
            emit-value
            map-options
            label="PUE Item"
            outlined
            use-input
            input-debounce="0"
            @filter="filterPUEItemsForPricing"
            :disable="!newPricing.hub_id && authStore.isSuperAdmin"
            :hint="!newPricing.hub_id && authStore.isSuperAdmin ? 'Select a hub first' : 'Type to search by ID or name'"
          >
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.pue_id }} - {{ scope.opt.name }}</q-item-label>
                  <q-item-label caption v-if="scope.opt.description">{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No PUE items found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- Unit Type Selection -->
          <q-select
            v-model="newPricing.unit_type"
            :options="[
              {label: 'Per Day', value: 'per_day'},
              {label: 'Per Week', value: 'per_week'},
              {label: 'Per Month', value: 'per_month'},
              {label: 'Per Hour', value: 'per_hour'},
              {label: 'Per kWh', value: 'per_kwh'},
              {label: 'Per Kg', value: 'per_kg'},
              {label: 'Per Recharge', value: 'per_recharge'},
              {label: 'One Time', value: 'one_time'},
              {label: 'Fixed Fee', value: 'fixed'}
            ]"
            option-label="label"
            option-value="value"
            emit-value
            map-options
            label="Unit Type"
            outlined
          />

          <!-- Price Input -->
          <q-input
            v-model.number="newPricing.price"
            type="number"
            label="Price"
            :prefix="currentCurrencySymbol"
            step="0.01"
            outlined
            :hint="`Price in ${hubSettings.default_currency || 'USD'}`"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Add" color="primary" @click="addPricing" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add GESI Status Option Dialog -->
    <q-dialog v-model="showAddGesiDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Add GESI Status Option</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="newCustomerOption.option_value"
            label="Option Value *"
            outlined
            hint="e.g., Youth (<18), Older (>55)"
          />
          <q-input
            v-model="newCustomerOption.description"
            label="Description"
            type="textarea"
            outlined
            rows="2"
            class="q-mt-md"
            hint="Optional description"
          />
          <q-input
            v-model.number="newCustomerOption.sort_order"
            label="Sort Order"
            type="number"
            outlined
            class="q-mt-md"
            hint="Lower numbers appear first"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Add" color="primary" @click="saveCustomerOption('gesi_status')" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Business Category Option Dialog -->
    <q-dialog v-model="showAddBusinessCategoryDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Add Business Category Option</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="newCustomerOption.option_value"
            label="Option Value *"
            outlined
            hint="e.g., Micro Business, Small Business"
          />
          <q-input
            v-model="newCustomerOption.description"
            label="Description"
            type="textarea"
            outlined
            rows="2"
            class="q-mt-md"
            hint="Optional description"
          />
          <q-input
            v-model.number="newCustomerOption.sort_order"
            label="Sort Order"
            type="number"
            outlined
            class="q-mt-md"
            hint="Lower numbers appear first"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Add" color="primary" @click="saveCustomerOption('business_category')" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Signup Reason Option Dialog -->
    <q-dialog v-model="showAddSignupReasonDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Add Signup Reason Option</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="newCustomerOption.option_value"
            label="Option Value *"
            outlined
            hint="e.g., Reduce Energy Costs, Reliable Power"
          />
          <q-input
            v-model="newCustomerOption.description"
            label="Description"
            type="textarea"
            outlined
            rows="2"
            class="q-mt-md"
            hint="Optional description"
          />
          <q-input
            v-model.number="newCustomerOption.sort_order"
            label="Sort Order"
            type="number"
            outlined
            class="q-mt-md"
            hint="Lower numbers appear first"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Add" color="primary" @click="saveCustomerOption('main_reason_for_signup')" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { settingsAPI, hubsAPI, pueAPI, surveyAPI } from 'src/services/api'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'stores/auth'

const $q = useQuasar()
const authStore = useAuthStore()
const defaultHubId = authStore.user?.hub_id

const tab = ref('pue-types')
const loading = ref(false)

// Hub selection - use selectedHubId for superadmins, defaultHubId for regular users
const selectedHubId = ref(defaultHubId)
const hubOptions = ref([])

// Computed property to get the active hub ID
const activeHubId = computed(() => {
  return authStore.isSuperAdmin ? selectedHubId.value : defaultHubId
})

// Pricing form data sources
const batteryCapacitiesAtHub = ref([])
const batteryCapacityOptions = ref([])
const batteriesAtHub = ref([])
const filteredBatteries = ref([])
const pueTypesAtHub = ref([])
const filteredPUETypes = ref([])
const pueItemsAtHub = ref([])
const filteredPUEItems = ref([])

// Duration Presets
const durationPresets = ref([])
const showAddDurationDialog = ref(false)
const editingDuration = ref(null)
const newDuration = ref({
  label: '',
  duration_value: 1,
  duration_unit: 'days',
  sort_order: 0
})

const durationColumns = [
  { name: 'label', label: 'Label', field: 'label', align: 'left' },
  { name: 'duration_value', label: 'Value', field: 'duration_value', align: 'center' },
  { name: 'duration_unit', label: 'Unit', field: 'duration_unit', align: 'center' },
  { name: 'is_global', label: 'Global', field: row => row.is_global ? 'Yes' : 'No', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

// PUE Types
const pueTypes = ref([])
const showAddTypeDialog = ref(false)
const editingType = ref(null)
const newType = ref({
  type_name: '',
  description: ''
})

// Payment Types
const paymentTypes = ref([])
const loadingPaymentTypes = ref(false)
const showAddPaymentTypeDialog = ref(false)
const newPaymentType = ref({
  type_name: '',
  description: ''
})

const paymentTypeColumns = [
  { name: 'type_name', label: 'Payment Type', field: 'type_name', align: 'left' },
  { name: 'description', label: 'Description', field: 'description', align: 'left' },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const typeColumns = [
  { name: 'type_name', label: 'Type Name', field: 'type_name', align: 'left' },
  { name: 'description', label: 'Description', field: 'description', align: 'left' },
  { name: 'is_global', label: 'Global', field: row => row.is_global ? 'Yes' : 'No', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

// Customer Field Options (GESI, Business Category, Signup Reasons)
const gesiOptions = ref([])
const businessCategoryOptions = ref([])
const signupReasonOptions = ref([])
const loadingCustomerOptions = ref(false)
const showAddGesiDialog = ref(false)
const showAddBusinessCategoryDialog = ref(false)
const showAddSignupReasonDialog = ref(false)
const showEditCustomerOptionDialog = ref(false)
const editingCustomerOption = ref(null)
const newCustomerOption = ref({
  field_name: '',
  option_value: '',
  description: '',
  sort_order: 0
})

const customerFieldOptionColumns = [
  { name: 'option_value', label: 'Option', field: 'option_value', align: 'left', sortable: true },
  { name: 'description', label: 'Description', field: 'description', align: 'left' },
  { name: 'sort_order', label: 'Order', field: 'sort_order', align: 'center', sortable: true },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

// Return Survey System
const surveyQuestions = ref([])
const loadingSurveyQuestions = ref(false)
const surveyFilterType = ref('all')
const surveyShowInactive = ref(false)
const returnSurveyRequired = ref(false)
const showAddSurveyQuestionDialog = ref(false)
const showEditSurveyQuestionDialog = ref(false)
const showQuestionOptionsDialog = ref(false)
const editingSurveyQuestion = ref(null)
const viewingQuestionOptions = ref(null)
const newSurveyQuestion = ref({
  question_text: '',
  question_type: 'open_text',
  help_text: '',
  applies_to_battery: true,
  applies_to_pue: true,
  parent_question_id: null,
  show_if_parent_answer: '',
  rating_min: 1,
  rating_max: 10,
  rating_min_label: '',
  rating_max_label: '',
  is_required: true,
  is_active: true,
  sort_order: 0
})
const newQuestionOption = ref({
  option_text: '',
  option_value: '',
  is_open_text_trigger: false,
  sort_order: 0
})
const currentQuestionOptions = ref([]) // Options for the question being created/edited
const editingOptionIndex = ref(null) // Track which option is being edited

const surveyQuestionColumns = [
  { name: 'sort_order', label: 'Order', field: 'sort_order', align: 'center', sortable: true },
  { name: 'question_text', label: 'Question', field: 'question_text', align: 'left', sortable: true },
  { name: 'question_type', label: 'Type', field: 'question_type', align: 'center' },
  { name: 'applies_to', label: 'Applies To', align: 'center' },
  { name: 'conditional', label: 'Conditional', align: 'center' },
  { name: 'is_required', label: 'Required', field: 'is_required', align: 'center' },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'options', label: 'Options', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const questionTypeOptions = [
  { label: 'Open Text', value: 'open_text' },
  { label: 'Multiple Choice', value: 'multiple_choice' },
  { label: 'Multiple Select', value: 'multiple_select' },
  { label: 'Rating', value: 'rating' },
  { label: 'Yes/No', value: 'yes_no' }
]

// Pricing
const pricingConfigs = ref([])
const showAddPricingDialog = ref(false)
const newPricing = ref({
  hub_id: null,
  item_type: 'battery_capacity',
  item_reference: '',
  unit_type: 'per_day',
  price: 0
})

const pricingColumns = [
  { name: 'item_type', label: 'Item Type', field: 'item_type', align: 'left' },
  { name: 'item_reference', label: 'Reference', field: 'item_reference', align: 'left' },
  { name: 'unit_type', label: 'Unit', field: 'unit_type', align: 'left' },
  { name: 'price', label: 'Price', field: 'price', align: 'right', format: (val, row) => {
    const currency = row.currency || hubSettings.value.default_currency || 'USD'
    const symbol = getCurrencySymbol(currency)
    return `${symbol}${val}`
  }},
  { name: 'is_active', label: 'Active', field: row => row.is_active ? 'Yes' : 'No', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

// Cost Structures
const costStructures = ref([])
const costStructureSearch = ref('')
const showAddStructureDialog = ref(false)
const structureTab = ref('basic')  // Tab state for cost structure dialog
const editingStructure = ref(null)
const newStructure = ref({
  name: '',
  description: '',
  item_type: 'battery_capacity',
  item_reference: '',
  components: [],
  duration_options: [],
  count_initial_checkout_as_recharge: false,
  is_pay_to_own: false,
  item_total_cost: null,
  allow_multiple_items: true,
  allow_custom_duration: true
})

const structureColumns = [
  { name: 'name', label: 'Structure Name', field: 'name', align: 'left', style: 'width: 200px' },
  { name: 'item_type', label: 'Item Type', field: 'item_type', align: 'left' },
  { name: 'item_reference', label: 'Reference', field: 'item_reference', align: 'left' },
  { name: 'components', label: 'Components', field: 'components', align: 'left', style: 'max-width: 300px' },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

// Filtered cost structures based on search
const filteredCostStructures = computed(() => {
  if (!costStructureSearch.value) {
    return costStructures.value
  }

  const searchLower = costStructureSearch.value.toLowerCase()
  return costStructures.value.filter(structure => {
    // Search in structure name
    if (structure.name && structure.name.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in description
    if (structure.description && structure.description.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in item type
    if (structure.item_type && structure.item_type.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in item reference
    if (structure.item_reference && structure.item_reference.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in component names
    if (structure.components && structure.components.length > 0) {
      const hasMatchingComponent = structure.components.some(comp =>
        comp.component_name && comp.component_name.toLowerCase().includes(searchLower)
      )
      if (hasMatchingComponent) {
        return true
      }
    }

    return false
  })
})

// Check if the current structure has any per_recharge components
const hasPerRechargeComponent = computed(() => {
  return newStructure.value.components.some(comp => comp.unit_type === 'per_recharge')
})

const isStructureValid = computed(() => {
  return newStructure.value.name &&
         newStructure.value.item_type &&
         newStructure.value.item_reference &&
         newStructure.value.components.length > 0 &&
         newStructure.value.components.every(c => c.component_name && c.unit_type && c.rate > 0)
})

// Hub Settings
const hubSettings = ref({
  debt_notification_threshold: -100,
  default_currency: 'USD',
  currency_symbol: null,
  overdue_notification_hours: 24,
  vat_percentage: 0,
  timezone: 'UTC',
  default_table_rows_per_page: 50,
  battery_status_green_hours: 3,
  battery_status_orange_hours: 8
})

const currencyOptions = ['USD', 'GBP', 'EUR', 'MWK']

// Common timezones
const allTimezones = [
  'UTC',
  'Africa/Nairobi',
  'Africa/Lagos',
  'Africa/Cairo',
  'Africa/Johannesburg',
  'Africa/Accra',
  'Africa/Dar_es_Salaam',
  'Africa/Kampala',
  'Africa/Kigali',
  'Africa/Lusaka',
  'Africa/Harare',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'America/New_York',
  'America/Chicago',
  'America/Los_Angeles',
  'Asia/Dubai',
  'Asia/Kolkata',
  'Asia/Singapore'
]

const timezoneOptions = ref(allTimezones)

const filterTimezones = (val, update) => {
  update(() => {
    if (val === '') {
      timezoneOptions.value = allTimezones
    } else {
      const needle = val.toLowerCase()
      timezoneOptions.value = allTimezones.filter(
        tz => tz.toLowerCase().includes(needle)
      )
    }
  })
}

// Currency symbol mapping
const getCurrencySymbol = (currency) => {
  const symbols = {
    'USD': '$',
    'GBP': '£',
    'EUR': '€',
    'MWK': 'MK'
  }
  return symbols[currency] || currency
}

// Computed property for current currency symbol
const currentCurrencySymbol = computed(() => {
  return getCurrencySymbol(hubSettings.value.default_currency || 'USD')
})

// Load data
const loadDurations = async () => {
  if (!activeHubId.value) return
  try {
    loading.value = true
    const response = await settingsAPI.getDurationPresets(activeHubId.value)
    durationPresets.value = response.data.presets
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to load duration presets', position: 'top' })
  } finally {
    loading.value = false
  }
}

const loadTypes = async () => {
  if (!activeHubId.value) return
  try {
    loading.value = true
    const response = await settingsAPI.getPUETypes(activeHubId.value)
    pueTypes.value = response.data.pue_types || []
  } catch (error) {
    console.error('Failed to load PUE types:', error)
    $q.notify({ type: 'negative', message: 'Failed to load PUE types', position: 'top' })
  } finally {
    loading.value = false
  }
}

const loadPricing = async () => {
  if (!activeHubId.value) return
  try {
    loading.value = true
    const response = await settingsAPI.getPricingConfigs({ hub_id: activeHubId.value })
    pricingConfigs.value = response.data.pricing_configs
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to load pricing configs', position: 'top' })
  } finally {
    loading.value = false
  }
}

const loadHubSettings = async () => {
  if (!activeHubId.value) return
  try {
    const response = await settingsAPI.getHubSettings(activeHubId.value)
    hubSettings.value = response.data
  } catch (error) {
    console.error('Failed to load hub settings:', error)
  }
}

// Actions
const saveDuration = async () => {
  try {
    if (editingDuration.value) {
      // Update existing
      await settingsAPI.updateDurationPreset(editingDuration.value.preset_id, {
        ...newDuration.value,
        hub_id: activeHubId.value
      })
      $q.notify({ type: 'positive', message: 'Duration preset updated', position: 'top' })
    } else {
      // Create new
      await settingsAPI.createDurationPreset({
        ...newDuration.value,
        hub_id: activeHubId.value
      })
      $q.notify({ type: 'positive', message: 'Duration preset added', position: 'top' })
    }
    showAddDurationDialog.value = false
    editingDuration.value = null
    newDuration.value = { label: '', duration_value: 1, duration_unit: 'days', sort_order: 0 }
    await loadDurations()
  } catch (error) {
    $q.notify({ type: 'negative', message: `Failed to ${editingDuration.value ? 'update' : 'add'} preset`, position: 'top' })
  }
}

const deleteDuration = async (preset) => {
  $q.dialog({
    title: 'Confirm',
    message: 'Delete this duration preset?',
    cancel: true
  }).onOk(async () => {
    try {
      await settingsAPI.deleteDurationPreset(preset.preset_id)
      $q.notify({ type: 'positive', message: 'Preset deleted', position: 'top' })
      await loadDurations()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Failed to delete preset', position: 'top' })
    }
  })
}

const saveType = async () => {
  try {
    if (editingType.value) {
      // Update existing
      await settingsAPI.updatePUEType(editingType.value.type_id, {
        ...newType.value,
        hub_id: activeHubId.value
      })
      $q.notify({ type: 'positive', message: 'PUE type updated', position: 'top' })
    } else {
      // Create new
      await settingsAPI.createPUEType({
        ...newType.value,
        hub_id: activeHubId.value
      })
      $q.notify({ type: 'positive', message: 'PUE type added', position: 'top' })
    }
    showAddTypeDialog.value = false
    editingType.value = null
    newType.value = { type_name: '', description: '' }
    await loadTypes()
  } catch (error) {
    $q.notify({ type: 'negative', message: `Failed to ${editingType.value ? 'update' : 'add'} type`, position: 'top' })
  }
}

const deleteType = async (type) => {
  $q.dialog({
    title: 'Confirm',
    message: 'Delete this PUE type?',
    cancel: true
  }).onOk(async () => {
    try {
      await settingsAPI.deletePUEType(type.type_id)
      $q.notify({ type: 'positive', message: 'Type deleted', position: 'top' })
      await loadTypes()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Failed to delete type', position: 'top' })
    }
  })
}

// Payment Types functions
const loadPaymentTypes = async () => {
  if (!activeHubId.value) return
  loadingPaymentTypes.value = true
  try {
    const response = await settingsAPI.getPaymentTypes({
      hub_id: activeHubId.value
    })
    paymentTypes.value = response.data.payment_types || []
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load payment types',
      position: 'top'
    })
  } finally {
    loadingPaymentTypes.value = false
  }
}

const savePaymentType = async () => {
  if (!newPaymentType.value.type_name) {
    $q.notify({
      type: 'warning',
      message: 'Please enter a payment type name',
      position: 'top'
    })
    return
  }

  try {
    await settingsAPI.createPaymentType({
      type_name: newPaymentType.value.type_name,
      description: newPaymentType.value.description,
      hub_id: activeHubId.value
    })

    $q.notify({
      type: 'positive',
      message: 'Payment type created successfully',
      position: 'top'
    })

    showAddPaymentTypeDialog.value = false
    newPaymentType.value = { type_name: '', description: '' }
    await loadPaymentTypes()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create payment type',
      position: 'top'
    })
  }
}

const togglePaymentType = async (paymentType) => {
  try {
    await settingsAPI.updatePaymentType(paymentType.type_id, {
      is_active: !paymentType.is_active
    })

    $q.notify({
      type: 'positive',
      message: `Payment type ${paymentType.is_active ? 'deactivated' : 'activated'}`,
      position: 'top'
    })

    await loadPaymentTypes()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to update payment type',
      position: 'top'
    })
  }
}

const deletePaymentType = async (paymentType) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete payment type "${paymentType.type_name}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await settingsAPI.deletePaymentType(paymentType.type_id)

      $q.notify({
        type: 'positive',
        message: 'Payment type deleted',
        position: 'top'
      })

      await loadPaymentTypes()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete payment type',
        position: 'top'
      })
    }
  })
}

// ============================================================================
// Customer Field Options Functions
// ============================================================================

const loadCustomerFieldOptions = async () => {
  if (!activeHubId.value) return
  loadingCustomerOptions.value = true
  try {
    const response = await settingsAPI.getCustomerFieldOptions({
      hub_id: activeHubId.value
    })
    const options = response.data || []

    // Separate options by field_name
    gesiOptions.value = options.filter(opt => opt.field_name === 'gesi_status')
    businessCategoryOptions.value = options.filter(opt => opt.field_name === 'business_category')
    signupReasonOptions.value = options.filter(opt => opt.field_name === 'main_reason_for_signup')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load customer field options',
      position: 'top'
    })
  } finally {
    loadingCustomerOptions.value = false
  }
}

const openAddCustomerOptionDialog = (fieldName) => {
  newCustomerOption.value = {
    field_name: fieldName,
    option_value: '',
    description: '',
    sort_order: 0
  }

  if (fieldName === 'gesi_status') {
    showAddGesiDialog.value = true
  } else if (fieldName === 'business_category') {
    showAddBusinessCategoryDialog.value = true
  } else if (fieldName === 'main_reason_for_signup') {
    showAddSignupReasonDialog.value = true
  }
}

const saveCustomerOption = async (fieldName) => {
  if (!newCustomerOption.value.option_value) {
    $q.notify({
      type: 'warning',
      message: 'Please enter an option value',
      position: 'top'
    })
    return
  }

  try {
    await settingsAPI.createCustomerFieldOption({
      field_name: fieldName,
      option_value: newCustomerOption.value.option_value,
      description: newCustomerOption.value.description,
      sort_order: newCustomerOption.value.sort_order,
      hub_id: activeHubId.value
    })

    $q.notify({
      type: 'positive',
      message: 'Option created successfully',
      position: 'top'
    })

    // Close the appropriate dialog
    if (fieldName === 'gesi_status') {
      showAddGesiDialog.value = false
    } else if (fieldName === 'business_category') {
      showAddBusinessCategoryDialog.value = false
    } else if (fieldName === 'main_reason_for_signup') {
      showAddSignupReasonDialog.value = false
    }

    newCustomerOption.value = { field_name: '', option_value: '', description: '', sort_order: 0 }
    await loadCustomerFieldOptions()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create option',
      position: 'top'
    })
  }
}

const editCustomerOption = async (option) => {
  editingCustomerOption.value = option

  $q.dialog({
    title: 'Edit Option',
    message: 'Update option details',
    prompt: {
      model: option.option_value,
      type: 'text',
      label: 'Option Value'
    },
    cancel: true
  }).onOk(async (newValue) => {
    try {
      await settingsAPI.updateCustomerFieldOption(option.option_id, {
        option_value: newValue
      })

      $q.notify({
        type: 'positive',
        message: 'Option updated',
        position: 'top'
      })

      await loadCustomerFieldOptions()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to update option',
        position: 'top'
      })
    }
  })
}

const deleteCustomerOption = async (option) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete option "${option.option_value}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await settingsAPI.deleteCustomerFieldOption(option.option_id)

      $q.notify({
        type: 'positive',
        message: 'Option deleted',
        position: 'top'
      })

      await loadCustomerFieldOptions()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete option',
        position: 'top'
      })
    }
  })
}

// Return Survey Functions
const loadHubSurveySettings = async () => {
  if (!activeHubId.value) return

  try {
    const response = await hubsAPI.get(activeHubId.value)
    returnSurveyRequired.value = response.data.return_survey_required || false
  } catch (error) {
    console.error('Failed to load hub survey settings:', error)
  }
}

const updateReturnSurveyRequired = async (value) => {
  if (!activeHubId.value) return

  try {
    await hubsAPI.update(activeHubId.value, {
      return_survey_required: value
    })

    $q.notify({
      type: 'positive',
      message: `Return surveys are now ${value ? 'required' : 'optional'}`,
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to update return survey setting:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to update return survey setting',
      position: 'top'
    })
    // Revert the change on error
    returnSurveyRequired.value = !value
  }
}

const loadSurveyQuestions = async () => {
  loadingSurveyQuestions.value = true
  try {
    const params = {
      hub_id: activeHubId.value,
      is_active: surveyShowInactive.value ? undefined : true
    }

    if (surveyFilterType.value === 'battery') {
      params.applies_to_battery = true
    } else if (surveyFilterType.value === 'pue') {
      params.applies_to_pue = true
    }

    const response = await surveyAPI.getQuestions(params)
    surveyQuestions.value = response.data.questions || []
  } catch (error) {
    console.error('Failed to load survey questions:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load survey questions',
      position: 'top'
    })
  } finally {
    loadingSurveyQuestions.value = false
  }
}

// Option management functions
const addOptionToList = () => {
  if (!newQuestionOption.value.option_text || !newQuestionOption.value.option_value) {
    $q.notify({
      type: 'warning',
      message: 'Please enter both option text and value',
      position: 'top'
    })
    return
  }

  if (editingOptionIndex.value !== null) {
    // Update existing option
    currentQuestionOptions.value[editingOptionIndex.value] = { ...newQuestionOption.value }
    editingOptionIndex.value = null
  } else {
    // Add new option
    currentQuestionOptions.value.push({ ...newQuestionOption.value })
  }

  // Reset form
  newQuestionOption.value = {
    option_text: '',
    option_value: '',
    is_open_text_trigger: false,
    sort_order: 0
  }
}

const editOptionInList = (index) => {
  editingOptionIndex.value = index
  newQuestionOption.value = { ...currentQuestionOptions.value[index] }
}

const removeOptionFromList = (index) => {
  currentQuestionOptions.value.splice(index, 1)
}

const cancelEditOption = () => {
  editingOptionIndex.value = null
  newQuestionOption.value = {
    option_text: '',
    option_value: '',
    is_open_text_trigger: false,
    sort_order: 0
  }
}

const saveSurveyQuestion = async () => {
  try {
    // Validate rating fields
    if (newSurveyQuestion.value.question_type === 'rating') {
      if (!newSurveyQuestion.value.rating_min || !newSurveyQuestion.value.rating_max) {
        $q.notify({
          type: 'warning',
          message: 'Please specify minimum and maximum rating values',
          position: 'top'
        })
        return
      }
      if (!newSurveyQuestion.value.rating_min_label || !newSurveyQuestion.value.rating_max_label) {
        $q.notify({
          type: 'warning',
          message: 'Please provide labels for minimum and maximum rating values',
          position: 'top'
        })
        return
      }
      if (newSurveyQuestion.value.rating_min >= newSurveyQuestion.value.rating_max) {
        $q.notify({
          type: 'warning',
          message: 'Maximum rating must be greater than minimum rating',
          position: 'top'
        })
        return
      }
    }

    // Auto-create Yes/No options if question type is yes_no
    let optionsToSave = [...currentQuestionOptions.value]
    if (newSurveyQuestion.value.question_type === 'yes_no') {
      optionsToSave = [
        { option_text: 'Yes', option_value: 'yes', is_open_text_trigger: false, sort_order: 0 },
        { option_text: 'No', option_value: 'no', is_open_text_trigger: false, sort_order: 1 }
      ]
    }

    // Validate options if question type requires them (but not rating)
    const requiresOptions = ['multiple_choice', 'multiple_select'].includes(newSurveyQuestion.value.question_type)
    if (requiresOptions && optionsToSave.length === 0) {
      $q.notify({
        type: 'warning',
        message: 'Please add at least one answer option',
        position: 'top'
      })
      return
    }

    let questionId
    if (editingSurveyQuestion.value) {
      // Update existing question
      questionId = editingSurveyQuestion.value.question_id
      await surveyAPI.updateQuestion(questionId, newSurveyQuestion.value)

      // Delete existing options and recreate them
      const needsOptions = ['multiple_choice', 'multiple_select', 'yes_no'].includes(newSurveyQuestion.value.question_type)
      if (needsOptions && editingSurveyQuestion.value.options) {
        for (const option of editingSurveyQuestion.value.options) {
          try {
            await surveyAPI.deleteQuestionOption(option.option_id)
          } catch (e) {
            console.error('Failed to delete option:', e)
          }
        }
      }

      $q.notify({
        type: 'positive',
        message: 'Survey question updated',
        position: 'top'
      })
    } else {
      // Create new question
      const response = await surveyAPI.createQuestion({
        ...newSurveyQuestion.value,
        hub_id: activeHubId.value
      })
      questionId = response.data.question_id

      $q.notify({
        type: 'positive',
        message: 'Survey question created',
        position: 'top'
      })
    }

    // Save options if question type requires them
    const needsOptions = ['multiple_choice', 'multiple_select', 'yes_no'].includes(newSurveyQuestion.value.question_type)
    if (needsOptions && optionsToSave.length > 0) {
      for (const option of optionsToSave) {
        try {
          await surveyAPI.addQuestionOption(questionId, option)
        } catch (e) {
          console.error('Failed to save option:', e)
        }
      }
    }

    showAddSurveyQuestionDialog.value = false
    showEditSurveyQuestionDialog.value = false
    editingSurveyQuestion.value = null
    resetSurveyQuestionForm()
    await loadSurveyQuestions()
  } catch (error) {
    console.error('Failed to save survey question:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save survey question',
      position: 'top'
    })
  }
}

const editSurveyQuestion = (question) => {
  editingSurveyQuestion.value = question
  newSurveyQuestion.value = {
    question_text: question.question_text,
    question_type: question.question_type,
    help_text: question.help_text || '',
    applies_to_battery: question.applies_to_battery,
    applies_to_pue: question.applies_to_pue,
    parent_question_id: question.parent_question_id,
    show_if_parent_answer: question.show_if_parent_answer || '',
    rating_min: question.rating_min || 1,
    rating_max: question.rating_max || 10,
    rating_min_label: question.rating_min_label || '',
    rating_max_label: question.rating_max_label || '',
    is_required: question.is_required,
    is_active: question.is_active,
    sort_order: question.sort_order
  }

  // Load existing options if question has them
  if (question.options && question.options.length > 0) {
    currentQuestionOptions.value = question.options.map(opt => ({
      option_text: opt.option_text,
      option_value: opt.option_value,
      is_open_text_trigger: opt.is_open_text_trigger || false,
      sort_order: opt.sort_order || 0
    }))
  } else {
    currentQuestionOptions.value = []
  }

  showAddSurveyQuestionDialog.value = true
}

const deleteSurveyQuestion = async (question) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete survey question "${question.question_text}"? This will also delete all associated options and responses.`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await surveyAPI.deleteQuestion(question.question_id)
      $q.notify({
        type: 'positive',
        message: 'Survey question deleted',
        position: 'top'
      })
      await loadSurveyQuestions()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete survey question',
        position: 'top'
      })
    }
  })
}

const viewQuestionOptions = (question) => {
  viewingQuestionOptions.value = question
  showQuestionOptionsDialog.value = true
}

const resetSurveyQuestionForm = () => {
  newSurveyQuestion.value = {
    question_text: '',
    question_type: 'open_text',
    help_text: '',
    applies_to_battery: true,
    applies_to_pue: true,
    parent_question_id: null,
    show_if_parent_answer: '',
    rating_min: 1,
    rating_max: 10,
    rating_min_label: '',
    rating_max_label: '',
    is_required: true,
    is_active: true,
    sort_order: 0
  }
  currentQuestionOptions.value = []
  editingOptionIndex.value = null
  newQuestionOption.value = {
    option_text: '',
    option_value: '',
    is_open_text_trigger: false,
    sort_order: 0
  }
}

const getQuestionTypeColor = (type) => {
  const colors = {
    'open_text': 'blue-grey',
    'multiple_choice': 'blue',
    'multiple_select': 'purple',
    'rating': 'orange',
    'yes_no': 'teal'
  }
  return colors[type] || 'grey'
}

const formatQuestionType = (type) => {
  const labels = {
    'open_text': 'Open Text',
    'multiple_choice': 'Multiple Choice',
    'multiple_select': 'Multiple Select',
    'rating': 'Rating',
    'yes_no': 'Yes/No'
  }
  return labels[type] || type
}

const exportSurveyResponses = async () => {
  try {
    const params = {
      hub_id: activeHubId.value
    }

    console.log('Exporting survey responses with params:', params)
    const response = await surveyAPI.exportResponses(params)
    console.log('Export response:', response)

    // The response.data is already a blob when using responseType: 'blob'
    const blob = response.data

    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `survey_responses_${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()

    // Clean up
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      link.remove()
    }, 100)

    $q.notify({
      type: 'positive',
      message: 'Survey responses exported successfully',
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to export survey responses:', error)
    console.error('Error details:', error.response?.data)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to export survey responses',
      position: 'top'
    })
  }
}

const addPricing = async () => {
  try {
    // Set hub_id to activeHubId before submitting
    const pricingData = {
      ...newPricing.value,
      hub_id: activeHubId.value
    }
    await settingsAPI.createPricingConfig(pricingData)
    $q.notify({ type: 'positive', message: 'Pricing added', position: 'top' })
    showAddPricingDialog.value = false
    newPricing.value = {
      hub_id: null,
      item_type: 'battery_capacity',
      item_reference: '',
      unit_type: 'per_day',
      price: 0
    }
    await loadPricing()
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to add pricing', position: 'top' })
  }
}

const deletePricing = async (pricing) => {
  $q.dialog({
    title: 'Confirm',
    message: 'Delete this pricing config?',
    cancel: true
  }).onOk(async () => {
    try {
      await settingsAPI.deletePricingConfig(pricing.pricing_id)
      $q.notify({ type: 'positive', message: 'Pricing deleted', position: 'top' })
      await loadPricing()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Failed to delete pricing', position: 'top' })
    }
  })
}

const saveHubSettings = async () => {
  if (!activeHubId.value) return
  try {
    await settingsAPI.updateHubSettings(activeHubId.value, hubSettings.value)
    $q.notify({ type: 'positive', message: 'Settings saved', position: 'top' })
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to save settings', position: 'top' })
  }
}

// Utility function to only allow whole number keys
const onlyNumbersKeypress = (evt) => {
  const charCode = evt.which ? evt.which : evt.keyCode
  // Allow: backspace, delete, tab, escape, enter
  if ([8, 9, 27, 13, 46].includes(charCode)) {
    return true
  }
  // Allow: digits 0-9
  if (charCode >= 48 && charCode <= 57) {
    return true
  }
  // Prevent all other keys
  evt.preventDefault()
  return false
}

// Utility function to allow decimal numbers (with one decimal point)
const onlyDecimalKeypress = (evt) => {
  const charCode = evt.which ? evt.which : evt.keyCode
  const inputElement = evt.target

  // Allow: backspace, delete, tab, escape, enter
  if ([8, 9, 27, 13, 46].includes(charCode)) {
    return true
  }

  // Allow: digits 0-9
  if (charCode >= 48 && charCode <= 57) {
    return true
  }

  // Allow: decimal point (46 = '.') but only if there isn't one already
  if (charCode === 46 && inputElement.value.indexOf('.') === -1) {
    return true
  }

  // Prevent all other keys
  evt.preventDefault()
  return false
}

const editDuration = (preset) => {
  editingDuration.value = preset
  newDuration.value = {
    label: preset.label,
    duration_value: preset.duration_value,
    duration_unit: preset.duration_unit,
    sort_order: preset.sort_order
  }
  showAddDurationDialog.value = true
}

const editType = (type) => {
  editingType.value = type
  newType.value = {
    type_name: type.type_name,
    description: type.description
  }
  showAddTypeDialog.value = true
}

const editPricing = (pricing) => {
  // TODO: Implement edit dialog
  $q.notify({ message: 'Edit feature coming soon', position: 'top' })
}

// Load hubs for superadmin
const loadHubs = async () => {
  if (!authStore.isSuperAdmin) return
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

// Handler for when hub changes in pricing dialog
const onPricingHubChange = async (selectedHubId) => {
  if (!selectedHubId) {
    batteryCapacitiesAtHub.value = []
    pueTypesAtHub.value = []
    pueItemsAtHub.value = []
    return
  }

  try {
    // Load battery capacities at this hub
    const batteriesResponse = await hubsAPI.getBatteries(selectedHubId)
    const capacities = [...new Set(
      batteriesResponse.data
        .filter(b => b.battery_capacity_wh)
        .map(b => String(b.battery_capacity_wh))
    )].sort((a, b) => parseInt(a) - parseInt(b))

    batteryCapacitiesAtHub.value = capacities
    batteryCapacityOptions.value = capacities

    // Load batteries at this hub with formatted labels
    batteriesAtHub.value = batteriesResponse.data.map(b => ({
      battery_id: b.battery_id,
      label: `${b.model || 'Battery'} (${b.battery_capacity_wh}Wh) - ID: ${b.battery_id}`
    }))
    filteredBatteries.value = batteriesAtHub.value

    // Load PUE types at this hub
    const typesResponse = await settingsAPI.getPUETypes(selectedHubId)
    pueTypesAtHub.value = typesResponse.data.types || []
    filteredPUETypes.value = pueTypesAtHub.value

    // Load PUE items at this hub
    const pueResponse = await hubsAPI.getPUE(selectedHubId)
    pueItemsAtHub.value = pueResponse.data || []
    filteredPUEItems.value = pueItemsAtHub.value
  } catch (error) {
    console.error('Failed to load hub data for pricing:', error)
  }
}

// Handler for when item type changes
const onItemTypeChange = () => {
  newPricing.value.item_reference = ''

  // Load data for the active hub
  if (activeHubId.value) {
    onPricingHubChange(activeHubId.value)
  }
}

// Handler for when hub selector changes (for superadmins)
const onHubChange = async (newHubId) => {
  if (!newHubId) return

  // Reload all settings for the new hub
  await Promise.all([
    loadDurations(),
    loadTypes(),
    loadPaymentTypes(),
    loadPricing(),
    loadCostStructures(),
    loadHubSettings()
  ])

  // Also reload data for pricing dialog if it's open
  if (showAddPricingDialog.value) {
    onPricingHubChange(newHubId)
  }
}

// Filter functions for searchable dropdowns
const filterBatteryCapacities = (val, update) => {
  update(() => {
    if (val === '') {
      batteryCapacityOptions.value = batteryCapacitiesAtHub.value
    } else {
      const needle = val.toLowerCase()
      batteryCapacityOptions.value = batteryCapacitiesAtHub.value.filter(
        c => c.toLowerCase().includes(needle)
      )
    }
  })
}

const filterBatteriesForCostStructure = (val, update) => {
  update(() => {
    if (val === '') {
      filteredBatteries.value = batteriesAtHub.value
    } else {
      const needle = val.toLowerCase()
      filteredBatteries.value = batteriesAtHub.value.filter(
        b => b.label.toLowerCase().includes(needle) ||
             String(b.battery_id).includes(needle)
      )
    }
  })
}

const filterPUETypesForPricing = (val, update) => {
  update(() => {
    if (val === '') {
      filteredPUETypes.value = pueTypesAtHub.value
    } else {
      const needle = val.toLowerCase()
      filteredPUETypes.value = pueTypesAtHub.value.filter(
        t => t.type_name.toLowerCase().includes(needle) ||
             (t.description && t.description.toLowerCase().includes(needle))
      )
    }
  })
}

const filterPUEItemsForPricing = (val, update) => {
  update(() => {
    if (val === '') {
      filteredPUEItems.value = pueItemsAtHub.value
    } else {
      const needle = val.toLowerCase()
      filteredPUEItems.value = pueItemsAtHub.value.filter(
        p => p.name.toLowerCase().includes(needle) ||
             (p.description && p.description.toLowerCase().includes(needle)) ||
             String(p.pue_id).includes(needle)
      )
    }
  })
}

// Cost Structure Functions
const loadCostStructures = async () => {
  if (!activeHubId.value) return
  try {
    loading.value = true
    const response = await settingsAPI.getCostStructures({ hub_id: activeHubId.value, is_active: null })
    costStructures.value = response.data.cost_structures
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to load cost structures', position: 'top' })
  } finally {
    loading.value = false
  }
}

const addComponent = () => {
  const newComponent = {
    component_name: 'Daily Rate',  // Default name for default unit_type
    unit_type: 'per_day',
    rate: 0,
    is_calculated_on_return: false,
    sort_order: newStructure.value.components.length,
    // Late fee defaults
    late_fee_action: 'continue',
    late_fee_rate: null,
    late_fee_grace_days: 0,
    // Pay-to-own defaults
    contributes_to_ownership: true,
    is_percentage_of_remaining: false,
    percentage_value: null,
    // Recurring payment defaults
    is_recurring_payment: false,
    recurring_interval: null
  }
  newStructure.value.components.push(newComponent)
}

const removeComponent = (index) => {
  newStructure.value.components.splice(index, 1)
  // Update sort orders
  newStructure.value.components.forEach((comp, idx) => {
    comp.sort_order = idx
  })
}

const onUnitTypeChange = (component) => {
  // Auto-populate component name based on unit type, but only if empty or matches a previous unit type name
  const unitTypeLabels = {
    'per_day': 'Daily Rate',
    'per_week': 'Weekly Rate',
    'per_month': 'Monthly Rate',
    'per_hour': 'Hourly Rate',
    'per_kwh': 'kWh Usage',
    'per_kg': 'Weight Charge',
    'per_recharge': 'Recharge Fee',
    'one_time': 'One-Time Fee',
    'fixed': 'Fixed Fee'
  }

  // Only auto-populate if the name is empty or matches one of the standard names
  const standardNames = Object.values(unitTypeLabels)
  if (!component.component_name || standardNames.includes(component.component_name)) {
    component.component_name = unitTypeLabels[component.unit_type] || ''
  }
}

// Get the current charge type for a component
const getComponentChargeType = (component) => {
  if (component.is_recurring_payment) {
    return 'recurring'
  } else if (component.is_calculated_on_return) {
    return 'on_return'
  } else {
    return 'upfront'
  }
}

// Set the charge type for a component
const setComponentChargeType = (component, chargeType) => {
  component.is_calculated_on_return = chargeType === 'on_return'
  component.is_recurring_payment = chargeType === 'recurring'

  // Initialize recurring_interval to 1.0 if not set and recurring is selected
  if (chargeType === 'recurring' && !component.recurring_interval) {
    component.recurring_interval = 1.0
  }
}

// Get the interval unit text based on unit_type
const getIntervalUnit = (unitType) => {
  const unitMap = {
    'per_day': 'day(s)',
    'per_week': 'week(s)',
    'per_month': 'month(s)',
    'per_hour': 'hour(s)',
    'per_kwh': 'billing cycle(s)',
    'per_kg': 'billing cycle(s)',
    'per_recharge': 'recharge(s)',
    'one_time': 'occurrence(s)',
    'fixed': 'billing cycle(s)'
  }
  return unitMap[unitType] || 'interval(s)'
}

const addDurationOption = () => {
  newStructure.value.duration_options.push({
    input_type: 'dropdown',
    label: 'Rental Duration',
    custom_unit: 'days',
    default_value: null,
    min_value: null,
    max_value: null,
    dropdown_choices: [],  // Array of {value, unit, label}
    sort_order: newStructure.value.duration_options.length
  })
}

const addDropdownChoice = (optionIndex) => {
  if (!newStructure.value.duration_options[optionIndex].dropdown_choices) {
    newStructure.value.duration_options[optionIndex].dropdown_choices = []
  }
  newStructure.value.duration_options[optionIndex].dropdown_choices.push({
    value: 1,
    unit: 'days',
    label: '1 Day'
  })
}

const removeDropdownChoice = (optionIndex, choiceIndex) => {
  newStructure.value.duration_options[optionIndex].dropdown_choices.splice(choiceIndex, 1)
}

const removeDurationOption = (index) => {
  newStructure.value.duration_options.splice(index, 1)
  // Update sort orders
  newStructure.value.duration_options.forEach((opt, idx) => {
    opt.sort_order = idx
  })
}

const onStructureItemTypeChange = () => {
  // Set item_reference to "all" for general types
  if (newStructure.value.item_type === 'battery' || newStructure.value.item_type === 'pue') {
    newStructure.value.item_reference = 'all'
  } else {
    newStructure.value.item_reference = ''
  }

  // Clear pay-to-own if item type doesn't support it
  if (!['pue_item', 'battery_item'].includes(newStructure.value.item_type)) {
    newStructure.value.is_pay_to_own = false
    newStructure.value.item_total_cost = null
    newStructure.value.allow_multiple_items = true
  }

  // Load data for the active hub
  if (activeHubId.value) {
    onPricingHubChange(activeHubId.value)
  }
}

const onPayToOwnToggle = (value) => {
  // When enabling pay-to-own, set constraints
  if (value) {
    newStructure.value.allow_multiple_items = false
    // Clear duration options as they don't apply to pay-to-own
    newStructure.value.duration_options = []
  } else {
    newStructure.value.allow_multiple_items = true
    newStructure.value.item_total_cost = null
  }
}

const saveStructure = async () => {
  try {
    // Process duration options for the new structure (with unit-aware dropdown_options)
    const processedDurationOptions = newStructure.value.duration_options.map(opt => {
      const processed = {
        input_type: opt.input_type,
        label: opt.label,
        sort_order: opt.sort_order
      }

      if (opt.input_type === 'custom') {
        processed.custom_unit = opt.custom_unit
        processed.default_value = opt.default_value
        processed.min_value = opt.min_value
        processed.max_value = opt.max_value
      } else if (opt.input_type === 'dropdown' && opt.dropdown_choices && opt.dropdown_choices.length > 0) {
        // Store dropdown_options as JSON with {value, unit, label} objects
        processed.dropdown_options = JSON.stringify(opt.dropdown_choices)
      }

      return processed
    })

    const structureData = {
      hub_id: activeHubId.value,
      name: newStructure.value.name,
      description: newStructure.value.description,
      item_type: newStructure.value.item_type,
      item_reference: String(newStructure.value.item_reference),
      components: JSON.stringify(newStructure.value.components),
      duration_options: processedDurationOptions.length > 0 ? JSON.stringify(processedDurationOptions) : undefined,
      count_initial_checkout_as_recharge: newStructure.value.count_initial_checkout_as_recharge,
      is_pay_to_own: newStructure.value.is_pay_to_own,
      item_total_cost: newStructure.value.item_total_cost,
      allow_multiple_items: newStructure.value.allow_multiple_items,
      allow_custom_duration: newStructure.value.allow_custom_duration
    }

    if (editingStructure.value) {
      // Update existing
      await settingsAPI.updateCostStructure(editingStructure.value.structure_id, structureData)
      $q.notify({ type: 'positive', message: 'Cost structure updated', position: 'top' })
    } else {
      // Create new
      await settingsAPI.createCostStructure(structureData)
      $q.notify({ type: 'positive', message: 'Cost structure created', position: 'top' })
    }

    showAddStructureDialog.value = false
    editingStructure.value = null
    resetStructureForm()
    await loadCostStructures()
  } catch (error) {
    console.error('Save structure error:', error)
    $q.notify({ type: 'negative', message: `Failed to ${editingStructure.value ? 'update' : 'create'} structure`, position: 'top' })
  }
}

const editStructure = (structure) => {
  editingStructure.value = structure

  // Parse duration options to convert dropdown_options JSON string back to array
  const durationOptions = (structure.duration_options || []).map(opt => {
    const parsed = {...opt}
    if (opt.dropdown_options && typeof opt.dropdown_options === 'string') {
      try {
        parsed.dropdown_choices = JSON.parse(opt.dropdown_options)
      } catch (e) {
        parsed.dropdown_choices = []
      }
    } else {
      parsed.dropdown_choices = opt.dropdown_options || []
    }
    delete parsed.dropdown_options
    return parsed
  })

  // Ensure components have pay-to-own and recurring payment defaults
  const components = (structure.components || []).map(comp => ({
    ...comp,
    contributes_to_ownership: comp.contributes_to_ownership !== undefined ? comp.contributes_to_ownership : true,
    is_percentage_of_remaining: comp.is_percentage_of_remaining !== undefined ? comp.is_percentage_of_remaining : false,
    percentage_value: comp.percentage_value || null,
    is_recurring_payment: comp.is_recurring_payment !== undefined ? comp.is_recurring_payment : false,
    recurring_interval: comp.recurring_interval || null
  }))

  newStructure.value = {
    name: structure.name,
    description: structure.description || '',
    item_type: structure.item_type,
    item_reference: structure.item_reference,
    components: components,
    duration_options: durationOptions,
    count_initial_checkout_as_recharge: structure.count_initial_checkout_as_recharge !== undefined ? structure.count_initial_checkout_as_recharge : false,
    is_pay_to_own: structure.is_pay_to_own !== undefined ? structure.is_pay_to_own : false,
    item_total_cost: structure.item_total_cost || null,
    allow_multiple_items: structure.allow_multiple_items !== undefined ? structure.allow_multiple_items : true,
    allow_custom_duration: structure.allow_custom_duration !== undefined ? structure.allow_custom_duration : true
  }
  showAddStructureDialog.value = true
}

const toggleStructureActive = async (structure) => {
  try {
    await settingsAPI.updateCostStructure(structure.structure_id, {
      is_active: !structure.is_active
    })
    $q.notify({ type: 'positive', message: `Structure ${structure.is_active ? 'deactivated' : 'activated'}`, position: 'top' })
    await loadCostStructures()
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to update structure', position: 'top' })
  }
}

const deleteStructure = async (structure) => {
  $q.dialog({
    title: 'Confirm',
    message: `Delete cost structure "${structure.name}"? This action cannot be undone.`,
    cancel: true
  }).onOk(async () => {
    try {
      await settingsAPI.deleteCostStructure(structure.structure_id)
      $q.notify({ type: 'positive', message: 'Cost structure deleted', position: 'top' })
      await loadCostStructures()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Failed to delete structure', position: 'top' })
    }
  })
}

const cancelStructureEdit = () => {
  editingStructure.value = null
  structureTab.value = 'basic'  // Reset to basic tab
  resetStructureForm()
}

const resetStructureForm = () => {
  structureTab.value = 'basic'  // Reset to basic tab
  newStructure.value = {
    name: '',
    description: '',
    item_type: 'battery_capacity',
    item_reference: '',
    components: [],
    duration_options: [],
    count_initial_checkout_as_recharge: false,
    is_pay_to_own: false,
    item_total_cost: null,
    allow_multiple_items: true,
    allow_custom_duration: true
  }
}

// Watch for hub changes and reload settings
watch(activeHubId, (newHubId, oldHubId) => {
  if (newHubId && newHubId !== oldHubId) {
    // Reload all hub-specific settings when hub changes
    loadHubSettings()
    loadDurations()
    loadTypes()
    loadPaymentTypes()
    loadPricing()
    loadCostStructures()
    loadHubSurveySettings()
    onPricingHubChange(newHubId)
  }
})

onMounted(async () => {
  // Load hubs first for superadmin
  await loadHubs()

  // Set initial hub for superadmin if not already set
  if (authStore.isSuperAdmin && !selectedHubId.value && hubOptions.value.length > 0) {
    selectedHubId.value = hubOptions.value[0].hub_id
  }

  // Load all settings data
  loadDurations()
  loadTypes()
  loadPaymentTypes()
  loadCustomerFieldOptions()
  loadSurveyQuestions()
  loadHubSurveySettings()
  loadPricing()
  loadCostStructures()
  loadHubSettings()

  // Load data for pricing dialog
  if (activeHubId.value) {
    onPricingHubChange(activeHubId.value)
  }
})
</script>
