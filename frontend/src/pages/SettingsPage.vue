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
      <q-tab name="cost-structures" label="Cost Structures" />
      <q-tab name="subscriptions" label="Subscriptions" />
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
          </div>

          <div>
            <q-btn label="Save Settings" type="submit" color="primary" />
          </div>
        </q-form>
      </q-tab-panel>

      <!-- Subscriptions Tab -->
      <q-tab-panel name="subscriptions">
        <div class="row justify-between q-mb-md">
          <div class="text-h6">Subscription Packages</div>
          <q-btn color="primary" label="Add Package" @click="showAddSubscriptionDialog = true" />
        </div>

        <!-- Search Input -->
        <q-input
          v-model="subscriptionSearch"
          outlined
          dense
          placeholder="Search by package name, billing period, or price..."
          class="q-mb-md"
          clearable
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>

        <q-table
          :rows="filteredSubscriptionPackages"
          :columns="subscriptionColumns"
          row-key="package_id"
          :loading="loading"
        >
          <template v-slot:body-cell-billing_period="props">
            <q-td :props="props">
              <q-badge :color="getBillingPeriodColor(props.row.billing_period)">
                {{ formatBillingPeriod(props.row.billing_period) }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-price="props">
            <q-td :props="props">
              {{ getCurrencySymbol(props.row.currency) }}{{ props.row.price.toFixed(2) }}
            </q-td>
          </template>

          <template v-slot:body-cell-items="props">
            <q-td :props="props">
              <q-badge color="blue" v-if="props.row.items && props.row.items.length > 0">
                {{ props.row.items.length }} items
              </q-badge>
              <span v-else class="text-grey">No items</span>
            </q-td>
          </template>

          <template v-slot:body-cell-is_active="props">
            <q-td :props="props">
              <q-badge :color="props.row.is_active ? 'green' : 'grey'">
                {{ props.row.is_active ? 'Active' : 'Inactive' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                dense
                round
                icon="edit"
                color="primary"
                size="sm"
                @click="editSubscriptionPackage(props.row)"
              >
                <q-tooltip>Edit Package</q-tooltip>
              </q-btn>
              <q-btn
                flat
                dense
                round
                icon="delete"
                color="negative"
                size="sm"
                @click="confirmDeleteSubscriptionPackage(props.row)"
              >
                <q-tooltip>Delete Package</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
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

    <!-- Add/Edit Cost Structure Dialog -->
    <q-dialog v-model="showAddStructureDialog" persistent>
      <q-card style="min-width: 700px; max-width: 900px">
        <q-card-section>
          <div class="text-h6">{{ editingStructure ? 'Edit' : 'Create' }} Cost Structure</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
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
            option-label="name"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterPUEItemsForPricing"
            label="PUE Item"
            outlined
            hint="Type to search specific PUE item"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No PUE items found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-separator />

          <!-- Cost Components Section -->
          <div class="text-subtitle2 q-mt-md">Cost Components</div>
          <div class="text-caption text-grey-7 q-mb-sm">
            Add multiple cost components to build your pricing structure
          </div>

          <!-- Component List -->
          <div v-for="(component, index) in newStructure.components" :key="index" class="q-pa-md bg-grey-1 rounded-borders q-mb-sm">
            <div class="row q-gutter-md items-start">
              <div class="col-3">
                <q-input
                  v-model="component.component_name"
                  label="Component Name"
                  dense
                  outlined
                  hint="e.g., 'Daily Rate'"
                />
              </div>

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
                    {label: 'Fixed Fee', value: 'fixed'}
                  ]"
                  option-label="label"
                  option-value="value"
                  emit-value
                  map-options
                  label="Unit Type"
                  dense
                  outlined
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
                <q-checkbox
                  v-model="component.is_calculated_on_return"
                  label="Calculate on Return"
                  dense
                  :hint="component.is_calculated_on_return ? 'Uses actual data' : 'Estimated upfront'"
                />
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
          </div>

          <!-- Add Component Button -->
          <q-btn
            flat
            icon="add"
            label="Add Component"
            color="primary"
            @click="addComponent"
          />

          <!-- Duration Options Section -->
          <q-separator class="q-my-md" />
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
        </q-card-section>

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
            option-label="name"
            emit-value
            map-options
            label="PUE Item"
            outlined
            use-input
            input-debounce="0"
            @filter="filterPUEItemsForPricing"
            :disable="!newPricing.hub_id && authStore.isSuperAdmin"
            :hint="!newPricing.hub_id && authStore.isSuperAdmin ? 'Select a hub first' : 'Select specific PUE item'"
          >
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.name }} (ID: {{ scope.opt.pue_id }})</q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
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
              {label: 'Per Hour', value: 'per_hour'},
              {label: 'Per Kg', value: 'per_kg'},
              {label: 'Per Month', value: 'per_month'},
              {label: 'Per kWh', value: 'per_kwh'}
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

    <!-- Add/Edit Subscription Package Dialog -->
    <q-dialog v-model="showAddSubscriptionDialog" persistent>
      <q-card style="min-width: 700px; max-width: 800px">
        <q-card-section>
          <div class="text-h6">{{ isEditingSubscription ? 'Edit' : 'Add' }} Subscription Package</div>
        </q-card-section>

        <q-card-section class="q-pt-none" style="max-height: 70vh; overflow-y: auto">
          <!-- Package Name -->
          <q-input
            v-model="newSubscriptionPackage.package_name"
            label="Package Name"
            outlined
            dense
            class="q-mb-md"
            :rules="[val => !!val || 'Package name is required']"
          />

          <!-- Description -->
          <q-input
            v-model="newSubscriptionPackage.description"
            label="Description"
            type="textarea"
            outlined
            dense
            rows="2"
            class="q-mb-md"
          />

          <!-- Billing Period and Price -->
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-6">
              <q-select
                v-model="newSubscriptionPackage.billing_period"
                :options="[
                  {label: 'Daily', value: 'daily'},
                  {label: 'Weekly', value: 'weekly'},
                  {label: 'Monthly', value: 'monthly'},
                  {label: 'Yearly', value: 'yearly'}
                ]"
                label="Billing Period"
                outlined
                dense
                emit-value
                map-options
                :rules="[val => !!val || 'Billing period is required']"
              />
            </div>
            <div class="col-6">
              <q-input
                v-model.number="newSubscriptionPackage.price"
                type="number"
                label="Price"
                :prefix="currentCurrencySymbol"
                outlined
                dense
                step="0.01"
                :rules="[val => val >= 0 || 'Price must be positive']"
              />
            </div>
          </div>

          <!-- Concurrent Limits -->
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-6">
              <q-input
                v-model.number="newSubscriptionPackage.max_concurrent_batteries"
                type="number"
                label="Max Concurrent Batteries"
                outlined
                dense
                min="1"
                step="1"
                hint="Enter a whole number, or leave empty for unlimited"
                :rules="[val => val === null || val === undefined || val === '' || (Number.isInteger(val) && val > 0) || 'Must be a positive whole number or empty']"
                @keypress="onlyNumbersKeypress"
              />
            </div>
            <div class="col-6">
              <q-input
                v-model.number="newSubscriptionPackage.max_concurrent_pue"
                type="number"
                label="Max Concurrent PUE Items"
                outlined
                dense
                min="1"
                step="1"
                hint="Enter a whole number, or leave empty for unlimited"
                :rules="[val => val === null || val === undefined || val === '' || (Number.isInteger(val) && val > 0) || 'Must be a positive whole number or empty']"
                @keypress="onlyNumbersKeypress"
              />
            </div>
          </div>

          <!-- kWh Limits -->
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-6">
              <q-input
                v-model.number="newSubscriptionPackage.included_kwh"
                type="number"
                label="Included kWh per Period"
                outlined
                dense
                step="0.1"
                min="0"
                hint="Leave empty for unlimited"
                clearable
                @keypress="onlyDecimalKeypress"
              />
            </div>
            <div class="col-6">
              <q-input
                v-model.number="newSubscriptionPackage.overage_rate_kwh"
                type="number"
                label="Overage Rate per kWh"
                :prefix="currentCurrencySymbol"
                outlined
                dense
                step="0.01"
                min="0"
                hint="Charge for kWh over included amount"
                clearable
                @keypress="onlyDecimalKeypress"
              />
            </div>
          </div>

          <!-- Auto Renew -->
          <q-checkbox
            v-model="newSubscriptionPackage.auto_renew"
            label="Auto-renew by default"
            class="q-mb-md"
          />

          <!-- Package Items -->
          <div class="text-subtitle2 q-mb-sm">Included Items</div>
          <q-card flat bordered class="q-mb-md">
            <q-card-section>
              <div v-if="newSubscriptionPackage.items.length === 0" class="text-grey text-center q-pa-md">
                No items added yet
              </div>

              <div v-for="(item, index) in newSubscriptionPackage.items" :key="index" class="q-mb-sm">
                <q-card flat bordered>
                  <q-card-section class="row items-center q-pa-sm">
                    <div class="col">
                      <div class="text-weight-medium">{{ getItemTypeLabel(item.item_type) }}</div>
                      <div class="text-caption text-grey">{{ getItemReferenceLabel(item) }}</div>
                      <div class="text-caption" v-if="item.quantity_limit">
                        Limit: {{ item.quantity_limit }} item(s)
                      </div>
                    </div>
                    <div>
                      <q-btn
                        flat
                        dense
                        round
                        icon="delete"
                        color="negative"
                        size="sm"
                        @click="removeSubscriptionItem(index)"
                      />
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <q-btn
                flat
                color="primary"
                icon="add"
                label="Add Item"
                @click="showAddSubscriptionItemDialog = true"
                class="q-mt-sm full-width"
              />
            </q-card-section>
          </q-card>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup @click="resetSubscriptionForm" />
          <q-btn
            flat
            :label="isEditingSubscription ? 'Update' : 'Create'"
            color="primary"
            @click="saveSubscriptionPackage"
            :loading="saving"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Subscription Item Dialog -->
    <q-dialog v-model="showAddSubscriptionItemDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Add Item to Package</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <!-- Item Type -->
          <q-select
            v-model="newSubscriptionItem.item_type"
            :options="[
              {label: 'All Batteries', value: 'battery', description: 'Applies to all batteries'},
              {label: 'Specific Battery Capacity', value: 'battery_capacity', description: 'Applies to specific capacity'},
              {label: 'Specific Battery', value: 'battery_item', description: 'Applies to one specific battery'},
              {label: 'All PUE Items', value: 'pue', description: 'Applies to all PUE equipment'},
              {label: 'Specific PUE Type', value: 'pue_type', description: 'Applies to specific PUE type'},
              {label: 'Specific PUE Item', value: 'pue_item', description: 'Applies to one PUE item'}
            ]"
            label="Item Type"
            outlined
            dense
            emit-value
            map-options
            @update:model-value="onSubscriptionItemTypeChange"
            class="q-mb-md"
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

          <!-- Item Reference (conditional) -->
          <q-select
            v-if="newSubscriptionItem.item_type === 'battery_capacity'"
            v-model="newSubscriptionItem.item_reference"
            :options="batteryCapacityOptions"
            label="Battery Capacity"
            outlined
            dense
            use-input
            input-debounce="300"
            @filter="filterBatteryCapacities"
            hint="Type to search capacity (Wh)"
            class="q-mb-md"
          />

          <q-select
            v-if="newSubscriptionItem.item_type === 'battery_item'"
            v-model="newSubscriptionItem.item_reference"
            :options="filteredBatteriesForSubscription"
            option-value="battery_id"
            option-label="label"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterBatteriesForSubscription"
            label="Battery"
            outlined
            dense
            hint="Type to search by model or ID"
            class="q-mb-md"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No batteries found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-select
            v-if="newSubscriptionItem.item_type === 'pue_type'"
            v-model="newSubscriptionItem.item_reference"
            :options="filteredPUETypesForSubscription"
            option-value="type_id"
            option-label="type_name"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterPUETypesForSubscription"
            label="PUE Type"
            outlined
            dense
            hint="Type to search PUE types"
            class="q-mb-md"
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
            v-if="newSubscriptionItem.item_type === 'pue_item'"
            v-model="newSubscriptionItem.item_reference"
            :options="filteredPUEItemsForSubscription"
            option-value="pue_id"
            option-label="name"
            emit-value
            map-options
            use-input
            input-debounce="300"
            @filter="filterPUEItemsForSubscription"
            label="PUE Item"
            outlined
            dense
            hint="Type to search PUE items by name"
            class="q-mb-md"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No PUE items found
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <!-- Quantity Limit -->
          <q-input
            v-model.number="newSubscriptionItem.quantity_limit"
            type="number"
            label="Quantity Limit"
            outlined
            dense
            min="1"
            step="1"
            hint="Leave empty for unlimited (whole numbers only)"
            clearable
            @keypress="onlyNumbersKeypress"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup @click="resetSubscriptionItemForm" />
          <q-btn flat label="Add" color="primary" @click="addSubscriptionItem" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { settingsAPI, hubsAPI, pueAPI } from 'src/services/api'
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

// Filtered options for subscription dialog (separate from pricing)
const filteredBatteriesForSubscription = ref([])
const filteredPUETypesForSubscription = ref([])
const filteredPUEItemsForSubscription = ref([])

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

const typeColumns = [
  { name: 'type_name', label: 'Type Name', field: 'type_name', align: 'left' },
  { name: 'description', label: 'Description', field: 'description', align: 'left' },
  { name: 'is_global', label: 'Global', field: row => row.is_global ? 'Yes' : 'No', align: 'center' },
  { name: 'actions', label: 'Actions', align: 'center' }
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
const subscriptionSearch = ref('')
const showAddStructureDialog = ref(false)
const editingStructure = ref(null)
const newStructure = ref({
  name: '',
  description: '',
  item_type: 'battery_capacity',
  item_reference: '',
  components: [],
  duration_options: []
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

// Filtered subscription packages based on search
const filteredSubscriptionPackages = computed(() => {
  if (!subscriptionSearch.value) {
    return subscriptionPackages.value
  }

  const searchLower = subscriptionSearch.value.toLowerCase()
  return subscriptionPackages.value.filter(pkg => {
    // Search in package name
    if (pkg.package_name && pkg.package_name.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in description
    if (pkg.description && pkg.description.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in billing period
    if (pkg.billing_period && pkg.billing_period.toLowerCase().includes(searchLower)) {
      return true
    }

    // Search in price
    if (pkg.price && String(pkg.price).includes(searchLower)) {
      return true
    }

    return false
  })
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
  overdue_notification_hours: 24,
  vat_percentage: 0,
  timezone: 'UTC'
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
    pueTypes.value = response.data.types
  } catch (error) {
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

// ============================================================================
// SUBSCRIPTION PACKAGES
// ============================================================================

const subscriptionPackages = ref([])
const showAddSubscriptionDialog = ref(false)
const showAddSubscriptionItemDialog = ref(false)
const isEditingSubscription = ref(false)
const saving = ref(false)

const newSubscriptionPackage = ref({
  package_name: '',
  description: '',
  billing_period: 'monthly',
  price: 0,
  max_concurrent_batteries: null,
  max_concurrent_pue: null,
  included_kwh: null,
  overage_rate_kwh: null,
  auto_renew: true,
  items: []
})

const newSubscriptionItem = ref({
  item_type: 'battery',
  item_reference: 'all',
  quantity_limit: null
})

const subscriptionColumns = [
  { name: 'package_name', label: 'Package Name', field: 'package_name', align: 'left', sortable: true },
  { name: 'billing_period', label: 'Billing', field: 'billing_period', align: 'center', sortable: true },
  { name: 'price', label: 'Price', field: 'price', align: 'right', sortable: true },
  { name: 'items', label: 'Items', align: 'center' },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const loadSubscriptionPackages = async () => {
  if (!activeHubId.value) return
  try {
    const response = await settingsAPI.getSubscriptionPackages(activeHubId.value, true)
    subscriptionPackages.value = response.data.packages || []
  } catch (error) {
    console.error('Failed to load subscription packages:', error)
    $q.notify({ type: 'negative', message: 'Failed to load subscription packages', position: 'top' })
  }
}

const saveSubscriptionPackage = async () => {
  if (!newSubscriptionPackage.value.package_name) {
    $q.notify({ type: 'warning', message: 'Package name is required', position: 'top' })
    return
  }

  saving.value = true
  try {
    const packageData = {
      hub_id: activeHubId.value,
      package_name: newSubscriptionPackage.value.package_name,
      description: newSubscriptionPackage.value.description,
      billing_period: newSubscriptionPackage.value.billing_period,
      price: newSubscriptionPackage.value.price,
      currency: hubSettings.value.default_currency || 'USD',
      max_concurrent_batteries: newSubscriptionPackage.value.max_concurrent_batteries || null,
      max_concurrent_pue: newSubscriptionPackage.value.max_concurrent_pue || null,
      included_kwh: newSubscriptionPackage.value.included_kwh || null,
      overage_rate_kwh: newSubscriptionPackage.value.overage_rate_kwh || null,
      auto_renew: newSubscriptionPackage.value.auto_renew,
      items: JSON.stringify(newSubscriptionPackage.value.items)
    }

    if (isEditingSubscription.value && newSubscriptionPackage.value.package_id) {
      // Update existing
      await settingsAPI.updateSubscriptionPackage(newSubscriptionPackage.value.package_id, packageData)
      $q.notify({ type: 'positive', message: 'Subscription package updated', position: 'top' })
    } else {
      // Create new
      await settingsAPI.createSubscriptionPackage(packageData)
      $q.notify({ type: 'positive', message: 'Subscription package created', position: 'top' })
    }

    showAddSubscriptionDialog.value = false
    resetSubscriptionForm()
    await loadSubscriptionPackages()
  } catch (error) {
    console.error('Failed to save subscription package:', error)
    $q.notify({ type: 'negative', message: 'Failed to save subscription package', position: 'top' })
  } finally {
    saving.value = false
  }
}

const editSubscriptionPackage = (pkg) => {
  isEditingSubscription.value = true
  newSubscriptionPackage.value = {
    package_id: pkg.package_id,
    package_name: pkg.package_name,
    description: pkg.description || '',
    billing_period: pkg.billing_period,
    price: pkg.price,
    max_concurrent_batteries: pkg.max_concurrent_batteries,
    max_concurrent_pue: pkg.max_concurrent_pue,
    included_kwh: pkg.included_kwh,
    overage_rate_kwh: pkg.overage_rate_kwh,
    auto_renew: pkg.auto_renew,
    items: pkg.items || []
  }
  showAddSubscriptionDialog.value = true
}

const confirmDeleteSubscriptionPackage = (pkg) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete subscription package "${pkg.package_name}"? This cannot be undone if there are active subscriptions.`,
    cancel: true
  }).onOk(async () => {
    try {
      await settingsAPI.deleteSubscriptionPackage(pkg.package_id)
      $q.notify({ type: 'positive', message: 'Subscription package deleted', position: 'top' })
      await loadSubscriptionPackages()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Failed to delete package. It may have active subscriptions.', position: 'top' })
    }
  })
}

const resetSubscriptionForm = () => {
  isEditingSubscription.value = false
  newSubscriptionPackage.value = {
    package_name: '',
    description: '',
    billing_period: 'monthly',
    price: 0,
    max_concurrent_batteries: null,
    max_concurrent_pue: null,
    included_kwh: null,
    overage_rate_kwh: null,
    auto_renew: true,
    items: []
  }
}

const onSubscriptionItemTypeChange = async (type) => {
  // Auto-set reference to 'all' for battery and pue types
  if (type === 'battery' || type === 'pue') {
    newSubscriptionItem.value.item_reference = 'all'
  } else {
    newSubscriptionItem.value.item_reference = ''
  }

  // Load data if not already loaded
  if (activeHubId.value) {
    // Initialize filtered lists with full data
    filteredBatteriesForSubscription.value = batteriesAtHub.value
    filteredPUETypesForSubscription.value = pueTypesAtHub.value
    filteredPUEItemsForSubscription.value = pueItemsAtHub.value

    // If data is empty, load it
    if (batteriesAtHub.value.length === 0 || pueItemsAtHub.value.length === 0) {
      await onPricingHubChange(activeHubId.value)
      // Re-initialize after loading
      filteredBatteriesForSubscription.value = batteriesAtHub.value
      filteredPUETypesForSubscription.value = pueTypesAtHub.value
      filteredPUEItemsForSubscription.value = pueItemsAtHub.value
    }
  }
}

const addSubscriptionItem = () => {
  if (!newSubscriptionItem.value.item_type) {
    $q.notify({ type: 'warning', message: 'Please select an item type', position: 'top' })
    return
  }

  if (!newSubscriptionItem.value.item_reference) {
    $q.notify({ type: 'warning', message: 'Please select an item', position: 'top' })
    return
  }

  newSubscriptionPackage.value.items.push({
    item_type: newSubscriptionItem.value.item_type,
    item_reference: String(newSubscriptionItem.value.item_reference),
    quantity_limit: newSubscriptionItem.value.quantity_limit || null
  })

  showAddSubscriptionItemDialog.value = false
  resetSubscriptionItemForm()
}

const removeSubscriptionItem = (index) => {
  newSubscriptionPackage.value.items.splice(index, 1)
}

const resetSubscriptionItemForm = () => {
  newSubscriptionItem.value = {
    item_type: 'battery',
    item_reference: 'all',
    quantity_limit: null
  }
}

const getItemTypeLabel = (itemType) => {
  const labels = {
    'battery': 'All Batteries',
    'battery_capacity': 'Battery Capacity',
    'battery_item': 'Specific Battery',
    'pue': 'All PUE Items',
    'pue_type': 'PUE Type',
    'pue_item': 'PUE Item'
  }
  return labels[itemType] || itemType
}

const getItemReferenceLabel = (item) => {
  if (item.item_reference === 'all') {
    return 'All items'
  }
  // For specific items, show the reference
  if (item.item_type === 'battery_capacity') {
    return `${item.item_reference} Wh`
  }
  if (item.item_type === 'battery_item') {
    // Find the battery to show its label
    const battery = batteriesAtHub.value.find(b => b.battery_id === parseInt(item.item_reference))
    return battery ? battery.label : `Battery ID: ${item.item_reference}`
  }
  if (item.item_type === 'pue_item') {
    // Find the PUE item to show its name
    const pueItem = pueItemsAtHub.value.find(p => p.pue_id === parseInt(item.item_reference))
    return pueItem ? pueItem.name || `PUE ${pueItem.pue_id}` : `PUE ID: ${item.item_reference}`
  }
  if (item.item_type === 'pue_type') {
    // Find the PUE type to show its name
    const pueType = pueTypesAtHub.value.find(t => t.type_name === item.item_reference || t.type_id === parseInt(item.item_reference))
    return pueType ? pueType.type_name : item.item_reference
  }
  return `ID: ${item.item_reference}`
}

const getBillingPeriodColor = (period) => {
  const colors = {
    'daily': 'orange',
    'weekly': 'blue',
    'monthly': 'green',
    'yearly': 'purple'
  }
  return colors[period] || 'grey'
}

const formatBillingPeriod = (period) => {
  return period.charAt(0).toUpperCase() + period.slice(1)
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
    filteredBatteriesForSubscription.value = batteriesAtHub.value

    // Load PUE types at this hub
    const typesResponse = await settingsAPI.getPUETypes(selectedHubId)
    pueTypesAtHub.value = typesResponse.data.types || []
    filteredPUETypes.value = pueTypesAtHub.value
    filteredPUETypesForSubscription.value = pueTypesAtHub.value

    // Load PUE items at this hub
    const pueResponse = await hubsAPI.getPUE(selectedHubId)
    pueItemsAtHub.value = pueResponse.data || []
    filteredPUEItems.value = pueItemsAtHub.value
    filteredPUEItemsForSubscription.value = pueItemsAtHub.value
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

// Filter functions for subscription dialog
const filterBatteriesForSubscription = (val, update) => {
  update(() => {
    if (val === '') {
      filteredBatteriesForSubscription.value = batteriesAtHub.value
    } else {
      const needle = val.toLowerCase()
      filteredBatteriesForSubscription.value = batteriesAtHub.value.filter(
        b => b.label.toLowerCase().includes(needle) ||
             String(b.battery_id).includes(needle)
      )
    }
  })
}

const filterPUETypesForSubscription = (val, update) => {
  update(() => {
    if (val === '') {
      filteredPUETypesForSubscription.value = pueTypesAtHub.value
    } else {
      const needle = val.toLowerCase()
      filteredPUETypesForSubscription.value = pueTypesAtHub.value.filter(
        t => t.type_name.toLowerCase().includes(needle) ||
             (t.description && t.description.toLowerCase().includes(needle))
      )
    }
  })
}

const filterPUEItemsForSubscription = (val, update) => {
  update(() => {
    if (val === '') {
      filteredPUEItemsForSubscription.value = pueItemsAtHub.value
    } else {
      const needle = val.toLowerCase()
      filteredPUEItemsForSubscription.value = pueItemsAtHub.value.filter(
        p => (p.item_name && p.item_name.toLowerCase().includes(needle)) ||
             (p.name && p.name.toLowerCase().includes(needle)) ||
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
  newStructure.value.components.push({
    component_name: '',
    unit_type: 'per_day',
    rate: 0,
    is_calculated_on_return: false,
    sort_order: newStructure.value.components.length
  })
}

const removeComponent = (index) => {
  newStructure.value.components.splice(index, 1)
  // Update sort orders
  newStructure.value.components.forEach((comp, idx) => {
    comp.sort_order = idx
  })
}

const addDurationOption = () => {
  newStructure.value.duration_options.push({
    input_type: 'dropdown',
    label: '',
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
  // Load data for the active hub
  if (activeHubId.value) {
    onPricingHubChange(activeHubId.value)
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
      duration_options: processedDurationOptions.length > 0 ? JSON.stringify(processedDurationOptions) : undefined
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

  newStructure.value = {
    name: structure.name,
    description: structure.description || '',
    item_type: structure.item_type,
    item_reference: structure.item_reference,
    components: JSON.parse(JSON.stringify(structure.components)), // Deep copy
    duration_options: durationOptions
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
  resetStructureForm()
}

const resetStructureForm = () => {
  newStructure.value = {
    name: '',
    description: '',
    item_type: 'battery_capacity',
    item_reference: '',
    components: [],
    duration_options: []
  }
}

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
  loadPricing()
  loadCostStructures()
  loadSubscriptionPackages()
  loadHubSettings()

  // Load data for pricing dialog
  if (activeHubId.value) {
    onPricingHubChange(activeHubId.value)
  }
})
</script>
