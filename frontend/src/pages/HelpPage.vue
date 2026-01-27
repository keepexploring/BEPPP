<template>
  <q-page class="q-pa-md">
    <div class="row justify-center">
      <div class="col-12 col-md-10 col-lg-8">
        <!-- Header -->
        <div class="text-h4 q-mb-md flex items-center">
          <q-icon name="help_outline" size="md" class="q-mr-sm" color="primary" />
          Help & User Guide
        </div>
        <p class="text-subtitle1 text-grey-7 q-mb-xl">
          Complete guide to using the Battery Hub Management System
        </p>

        <!-- Quick Links -->
        <q-card class="q-mb-lg">
          <q-card-section>
            <div class="text-h6 q-mb-md">Quick Links</div>
            <div class="row q-col-gutter-sm">
              <div class="col-6 col-sm-4 col-md-3" v-for="link in quickLinks" :key="link.id">
                <q-btn
                  outline
                  color="primary"
                  :label="link.label"
                  @click="scrollToSection(link.id)"
                  class="full-width"
                  size="sm"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Getting Started -->
        <q-card id="getting-started" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="flag" />
              Getting Started
            </div>
          </q-card-section>
          <q-card-section>
            <p class="text-body1">
              The Battery Hub Management System helps you manage solar hubs, batteries, and productive use equipment (PUE) rentals. Here's the typical workflow:
            </p>
            <q-stepper v-model="step" vertical flat class="bg-grey-1">
              <q-step
                :name="1"
                title="Set up your Hub"
                icon="hub"
                :done="step > 1"
              >
                Create or configure your solar hub with location and capacity information.
              </q-step>
              <q-step
                :name="2"
                title="Add Equipment"
                icon="inventory"
                :done="step > 2"
              >
                Add batteries and PUE items to your inventory.
              </q-step>
              <q-step
                :name="3"
                title="Configure Pricing"
                icon="payments"
                :done="step > 3"
              >
                Set up cost structures for rentals and pay-to-own options.
              </q-step>
              <q-step
                :name="4"
                title="Manage Rentals"
                icon="receipt"
              >
                Create rentals, track returns, and manage customer accounts.
              </q-step>
            </q-stepper>
          </q-card-section>
        </q-card>

        <!-- Hubs -->
        <q-card id="hubs" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="hub" />
              Managing Hubs
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What is a Hub?</div>
            <p>A Hub represents a solar energy location where batteries and equipment are stored and rented.</p>

            <div class="text-h6 q-mt-md q-mb-sm">How to Add a Hub</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Navigate to <strong>Hubs</strong> from the side menu</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click the <strong>Add Hub</strong> button</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>
                  Fill in the details:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Hub ID:</strong> Unique identifier</li>
                    <li><strong>What3Words Location:</strong> e.g., main.solar.hub</li>
                    <li><strong>Solar Capacity:</strong> Total solar panel capacity in kW</li>
                    <li><strong>Country:</strong> Hub location</li>
                    <li><strong>Coordinates:</strong> Optional GPS location</li>
                  </ul>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>Click <strong>Save</strong></q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- Batteries -->
        <q-card id="batteries" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="battery_charging_full" />
              Managing Batteries
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">Adding Batteries</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Go to <strong>Batteries</strong> in the side menu</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click <strong>Add Battery</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>
                  Enter battery information:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Battery ID:</strong> Unique identifier (e.g., 101)</li>
                    <li><strong>Short ID:</strong> User-friendly code (optional)</li>
                    <li><strong>Hub:</strong> Select which hub this battery belongs to</li>
                    <li><strong>Capacity:</strong> Battery capacity in Wh</li>
                    <li><strong>Status:</strong> Available, In Use, or Maintenance</li>
                  </ul>
                </q-item-section>
              </q-item>
            </q-list>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <strong>Tip:</strong> Each battery gets a unique secret key for webhook authentication. Keep this secure!
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- PUE Equipment -->
        <q-card id="pue" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="devices" />
              Managing PUE Equipment
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What is PUE?</div>
            <p>Productive Use Equipment (PUE) includes items like lights, radios, fans, and other appliances that customers can rent alongside batteries.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Adding PUE Items</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Navigate to <strong>Equipment (PUE)</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click <strong>Add Equipment</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>
                  Fill in the details:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Equipment Type:</strong> Select from PUE Types</li>
                    <li><strong>Name:</strong> Descriptive name</li>
                    <li><strong>Description:</strong> Details about the item</li>
                    <li><strong>Power Rating:</strong> Watts consumed</li>
                    <li><strong>Status:</strong> Available or Maintenance</li>
                  </ul>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- Cost Structures -->
        <q-card id="cost-structures" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="payments" />
              Cost Structures & Pricing - Deep Dive
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">Understanding Cost Structures</div>
            <p class="text-body1">
              Cost Structures are the foundation of your rental pricing system. They define how much customers pay,
              how payments are structured over time, and whether equipment can be owned through a Pay-to-Own program.
              Think of them as reusable pricing templates that you can apply to different equipment types.
            </p>

            <q-banner class="bg-blue-1 q-mt-md q-mb-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <div class="text-subtitle1"><strong>Key Concept:</strong></div>
              <div>Cost Structures separate pricing logic from equipment. You create the pricing model once,
              then apply it to multiple rentals. This ensures consistency and makes price changes easy.</div>
            </q-banner>

            <div class="text-h6 q-mt-lg q-mb-sm">The Cost Structure Workflow</div>
            <p class="text-body2 q-mb-md">Follow this workflow to understand how cost structures flow through the system:</p>

            <q-timeline color="primary" class="q-mb-lg">
              <q-timeline-entry icon="settings" title="1. Create Cost Structure">
                <div>Admin defines pricing model in Settings page with all components and rules</div>
              </q-timeline-entry>
              <q-timeline-entry icon="devices" title="2. Link to Equipment">
                <div>Cost Structure is optionally linked to specific PUE items or used during rental creation</div>
              </q-timeline-entry>
              <q-timeline-entry icon="person_add" title="3. Create Rental">
                <div>When creating a rental, select which Cost Structure to apply for this customer</div>
              </q-timeline-entry>
              <q-timeline-entry icon="calculate" title="4. System Calculates">
                <div>System automatically calculates: rental fees, deposits, recurring payments, and ownership progress</div>
              </q-timeline-entry>
              <q-timeline-entry icon="payments" title="5. Customer Pays">
                <div>Payments are tracked against the Cost Structure's rules and applied to balances</div>
              </q-timeline-entry>
              <q-timeline-entry icon="check_circle" title="6. Ownership or Return">
                <div>If Pay-to-Own: ownership transfers when thresholds met. Otherwise: equipment returned with deposit refund</div>
              </q-timeline-entry>
            </q-timeline>

            <div class="text-h6 q-mt-lg q-mb-sm">Creating a Cost Structure: Step-by-Step</div>
            <q-stepper v-model="costStructureStep" vertical flat class="bg-grey-1 q-mb-md">
              <q-step :name="1" title="Access Settings" icon="settings" :done="costStructureStep > 1">
                <div class="q-mb-sm">Navigate to <strong>Settings</strong> page (admin only)</div>
                <div class="text-caption">Only administrators can create and modify cost structures</div>
                <q-stepper-navigation>
                  <q-btn @click="costStructureStep = 2" color="primary" label="Continue" />
                </q-stepper-navigation>
              </q-step>

              <q-step :name="2" title="Basic Information" icon="edit" :done="costStructureStep > 2">
                <div class="q-mb-md">
                  <div class="text-subtitle1 q-mb-xs"><strong>Name:</strong></div>
                  <div class="q-ml-md text-body2">Give your cost structure a descriptive name:</div>
                  <ul class="q-ml-lg">
                    <li>"Standard Battery Rental" - Basic battery pricing</li>
                    <li>"Premium PUE with Pay-to-Own" - Higher-tier equipment with ownership option</li>
                    <li>"Monthly Subscription - Solar Panel" - Recurring monthly payment model</li>
                  </ul>
                </div>
                <q-stepper-navigation>
                  <q-btn @click="costStructureStep = 3" color="primary" label="Continue" />
                  <q-btn flat @click="costStructureStep = 1" color="primary" label="Back" class="q-ml-sm" />
                </q-stepper-navigation>
              </q-step>

              <q-step :name="3" title="Cost Components" icon="payments" :done="costStructureStep > 3">
                <div class="text-subtitle1 q-mb-sm"><strong>Configure All Cost Components:</strong></div>

                <q-list bordered class="q-mb-md">
                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Base Daily Rental Fee</q-item-label>
                      <q-item-label caption>The per-day cost charged to the customer</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>Example:</strong> $2.50/day means a 30-day rental costs $75 in rental fees
                      </div>
                    </q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Deposit Amount</q-item-label>
                      <q-item-label caption>Refundable security deposit collected upfront</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>Example:</strong> $50 deposit - Refunded when equipment returned in good condition
                      </div>
                      <div class="q-mt-xs text-body2">
                        <strong>Pay-to-Own:</strong> Can be configured to count toward ownership price
                      </div>
                    </q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Late Fee Structure</q-item-label>
                      <q-item-label caption>Penalty charged for overdue equipment</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>Example:</strong> $5/day after due date passes
                      </div>
                    </q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Recurring Payment Option (PUE Only)</q-item-label>
                      <q-item-label caption>Enable automatic recurring charges for ongoing rentals</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>Example:</strong> Charge $60 every 30 days automatically
                      </div>
                      <div class="q-mt-xs text-body2">
                        <strong>Use Case:</strong> Long-term rentals like solar panels or refrigerators
                      </div>
                    </q-item-section>
                  </q-item>
                </q-list>

                <q-stepper-navigation>
                  <q-btn @click="costStructureStep = 4" color="primary" label="Continue" />
                  <q-btn flat @click="costStructureStep = 2" color="primary" label="Back" class="q-ml-sm" />
                </q-stepper-navigation>
              </q-step>

              <q-step :name="4" title="Pay-to-Own Configuration (Optional)" icon="shopping_cart" :done="costStructureStep > 4">
                <div class="text-subtitle1 q-mb-sm"><strong>Enable Pay-to-Own Option:</strong></div>
                <p class="text-body2">Pay-to-Own allows customers to own equipment by making payments over time. Enable this feature and configure:</p>

                <q-list bordered class="q-mb-md">
                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Ownership Price</q-item-label>
                      <q-item-label caption>Total amount customer must pay to own the equipment</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>Example:</strong> $300 - Once payments reach this amount, ownership transfers
                      </div>
                    </q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Apply Deposit to Ownership</q-item-label>
                      <q-item-label caption>Toggle: Should deposit count toward ownership price?</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>If Enabled:</strong> $50 deposit immediately counts as $50 toward $300 ownership price
                      </div>
                      <div class="q-mt-xs text-body2">
                        <strong>If Disabled:</strong> Deposit is separate and refundable (doesn't count)
                      </div>
                    </q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Apply Rental Payments to Ownership</q-item-label>
                      <q-item-label caption>Toggle: Should rental fees count toward ownership price?</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>If Enabled:</strong> Each $2.50/day rental payment reduces the ownership balance
                      </div>
                      <div class="q-mt-xs text-body2">
                        <strong>If Disabled:</strong> Rental fees are pure rental cost (doesn't build equity)
                      </div>
                    </q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">Minimum Payment Threshold</q-item-label>
                      <q-item-label caption>Optional: Minimum amount required before ownership transfer</q-item-label>
                      <div class="q-mt-sm text-body2">
                        <strong>Example:</strong> Require at least $250 in direct payments (excluding credits)
                      </div>
                    </q-item-section>
                  </q-item>
                </q-list>

                <q-banner class="bg-amber-1">
                  <template v-slot:avatar>
                    <q-icon name="lightbulb" color="amber-8" />
                  </template>
                  <div class="text-subtitle2"><strong>Important:</strong></div>
                  <div>Pay-to-Own is only available for PUE equipment, NOT for batteries. Batteries use standard rental model only.</div>
                </q-banner>

                <q-stepper-navigation class="q-mt-md">
                  <q-btn @click="costStructureStep = 5" color="primary" label="Continue" />
                  <q-btn flat @click="costStructureStep = 3" color="primary" label="Back" class="q-ml-sm" />
                </q-stepper-navigation>
              </q-step>

              <q-step :name="5" title="Save & Apply" icon="check_circle" :done="costStructureStep > 5">
                <div class="q-mb-md">
                  <div class="text-subtitle1 q-mb-sm"><strong>Review and Save</strong></div>
                  <p class="text-body2">Once saved, your Cost Structure will be available when creating rentals.</p>
                </div>
                <q-stepper-navigation>
                  <q-btn @click="costStructureStep = 1" color="primary" label="Finish" />
                  <q-btn flat @click="costStructureStep = 4" color="primary" label="Back" class="q-ml-sm" />
                </q-stepper-navigation>
              </q-step>
            </q-stepper>

            <div class="text-h6 q-mt-lg q-mb-sm">How Cost Structures Link to Rentals</div>
            <p class="text-body2 q-mb-md">When you create a rental, you select a Cost Structure. Here's what happens:</p>

            <q-card flat bordered class="bg-blue-grey-1 q-mb-md">
              <q-card-section>
                <div class="text-subtitle1 q-mb-sm"><strong>Linking Process:</strong></div>
                <ol class="q-pl-md">
                  <li class="q-mb-sm"><strong>Rental Creation:</strong> Admin selects customer, equipment, and Cost Structure</li>
                  <li class="q-mb-sm"><strong>System Copies Values:</strong> The Cost Structure's values are copied to the rental record</li>
                  <li class="q-mb-sm"><strong>Rental is Independent:</strong> Once created, the rental has its own values (changing the Cost Structure won't affect existing rentals)</li>
                  <li class="q-mb-sm"><strong>Calculations Begin:</strong> System uses these values to calculate all charges and ownership progress</li>
                </ol>
              </q-card-section>
            </q-card>

            <div class="text-h6 q-mt-lg q-mb-sm">Calculation Logic Explained</div>
            <p class="text-body2 q-mb-md">Understanding how the system calculates costs is crucial:</p>

            <q-expansion-item
              expand-separator
              icon="calculate"
              label="Standard Rental Calculation (No Pay-to-Own)"
              header-class="bg-grey-3"
              class="q-mb-sm"
            >
              <q-card>
                <q-card-section>
                  <div class="text-subtitle2 q-mb-sm"><strong>Formula:</strong></div>
                  <div class="q-mb-md bg-grey-2 q-pa-md" style="font-family: monospace;">
                    Total Cost = Deposit + (Daily Rate × Number of Days) + Late Fees
                  </div>

                  <div class="text-subtitle2 q-mb-sm"><strong>Example Calculation:</strong></div>
                  <ul class="q-pl-md">
                    <li>Deposit: $50 (refundable)</li>
                    <li>Daily Rate: $2.50/day</li>
                    <li>Rental Period: 30 days</li>
                    <li>Returned On Time: Yes</li>
                  </ul>

                  <div class="q-mt-md bg-green-1 q-pa-md">
                    <div class="text-weight-bold">At Rental Start:</div>
                    <div>Customer pays: $50 (deposit) + $75 (30 × $2.50) = <strong>$125</strong></div>

                    <div class="text-weight-bold q-mt-md">At Return:</div>
                    <div>Customer receives back: <strong>$50</strong> (deposit refund)</div>
                    <div>Net cost to customer: <strong>$75</strong></div>
                  </div>
                </q-card-section>
              </q-card>
            </q-expansion-item>

            <q-expansion-item
              expand-separator
              icon="shopping_cart"
              label="Pay-to-Own Calculation (PUE Only)"
              header-class="bg-grey-3"
              class="q-mb-sm"
            >
              <q-card>
                <q-card-section>
                  <div class="text-subtitle2 q-mb-sm"><strong>Formula:</strong></div>
                  <div class="q-mb-md bg-grey-2 q-pa-md" style="font-family: monospace;">
                    Ownership Progress = (Deposit × deposit_applies) + (Rental Payments × payments_apply) + Direct Payments<br/>
                    Ownership Complete = Ownership Progress ≥ Ownership Price
                  </div>

                  <div class="text-subtitle2 q-mb-sm"><strong>Example Calculation:</strong></div>
                  <div class="text-body2 q-mb-sm"><strong>Cost Structure Settings:</strong></div>
                  <ul class="q-pl-md q-mb-md">
                    <li>Ownership Price: $300</li>
                    <li>Deposit: $50 (applies to ownership: YES)</li>
                    <li>Daily Rate: $2.50/day</li>
                    <li>Rental Payments Apply to Ownership: YES</li>
                  </ul>

                  <div class="bg-amber-1 q-pa-md q-mb-md">
                    <div class="text-weight-bold">Month 1:</div>
                    <div>Customer pays: $50 (deposit) + $75 (30 days)</div>
                    <div>Ownership Progress: $50 + $75 = <strong>$125 / $300</strong></div>
                    <div class="text-caption">Still renting - needs $175 more</div>

                    <div class="text-weight-bold q-mt-md">Month 2:</div>
                    <div>Customer pays: $75 (30 days)</div>
                    <div>Ownership Progress: $125 + $75 = <strong>$200 / $300</strong></div>
                    <div class="text-caption">Still renting - needs $100 more</div>

                    <div class="text-weight-bold q-mt-md">Month 3:</div>
                    <div>Customer pays: $75 (30 days)</div>
                    <div>Ownership Progress: $200 + $75 = <strong>$275 / $300</strong></div>
                    <div class="text-caption">Still renting - needs $25 more</div>

                    <div class="text-weight-bold q-mt-md">Month 4 (Day 10):</div>
                    <div>Customer pays: $25 (10 days)</div>
                    <div>Ownership Progress: $275 + $25 = <strong>$300 / $300</strong></div>
                    <div class="text-success text-weight-bold">✓ OWNERSHIP TRANSFERRED!</div>
                  </div>

                  <div class="bg-green-1 q-pa-md">
                    <div class="text-weight-bold">Total Cost to Own:</div>
                    <div>$50 + $75 + $75 + $75 + $25 = <strong>$300</strong></div>
                    <div class="text-caption q-mt-xs">Customer now owns the equipment after ~100 days</div>
                  </div>
                </q-card-section>
              </q-card>
            </q-expansion-item>

            <q-expansion-item
              expand-separator
              icon="event"
              label="Recurring Payment Calculation (PUE Only)"
              header-class="bg-grey-3"
              class="q-mb-md"
            >
              <q-card>
                <q-card-section>
                  <div class="text-subtitle2 q-mb-sm"><strong>How Recurring Payments Work:</strong></div>
                  <p class="text-body2">For long-term PUE rentals, you can enable recurring payments that automatically charge the customer at regular intervals.</p>

                  <div class="text-subtitle2 q-mt-md q-mb-sm"><strong>Configuration:</strong></div>
                  <ul class="q-pl-md q-mb-md">
                    <li>Enable "Recurring Payment" in Cost Structure</li>
                    <li>Set interval: e.g., every 30 days</li>
                    <li>Set amount: e.g., $60 per interval</li>
                  </ul>

                  <div class="bg-blue-1 q-pa-md">
                    <div class="text-weight-bold">Example Timeline:</div>
                    <div class="q-mt-sm">Day 1: Rental starts - Customer pays deposit + first month</div>
                    <div class="q-mt-sm">Day 30: System auto-charges $60 to customer account</div>
                    <div class="q-mt-sm">Day 60: System auto-charges $60 to customer account</div>
                    <div class="q-mt-sm">Day 90: System auto-charges $60 to customer account</div>
                    <div class="q-mt-sm text-caption">Continues until rental is returned or ownership transferred</div>
                  </div>

                  <q-banner class="bg-orange-1 q-mt-md">
                    <template v-slot:avatar>
                      <q-icon name="warning" color="orange-8" />
                    </template>
                    <div><strong>Important:</strong> Recurring payments are processed by a cron job that runs daily. If customer credit is insufficient, notifications are sent.</div>
                  </q-banner>
                </q-card-section>
              </q-card>
            </q-expansion-item>

            <div class="text-h6 q-mt-lg q-mb-sm">Practical Examples</div>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-positive text-white">
                <div class="text-subtitle1"><strong>Scenario 1: Simple Battery Rental</strong></div>
              </q-card-section>
              <q-card-section>
                <div><strong>Equipment:</strong> Standard 12V Battery</div>
                <div><strong>Cost Structure:</strong> "Basic Battery - $3/day"</div>
                <div><strong>Configuration:</strong> $50 deposit, $3/day, no pay-to-own</div>
                <div><strong>Customer rents for 20 days</strong></div>

                <div class="q-mt-md">
                  <div>Customer pays upfront: $50 + (20 × $3) = <strong>$110</strong></div>
                  <div>At return: Receives <strong>$50</strong> deposit back</div>
                  <div class="text-weight-bold">Final cost: $60</div>
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-info text-white">
                <div class="text-subtitle1"><strong>Scenario 2: Pay-to-Own Solar Panel</strong></div>
              </q-card-section>
              <q-card-section>
                <div><strong>Equipment:</strong> 100W Solar Panel</div>
                <div><strong>Cost Structure:</strong> "Solar Panel Pay-to-Own"</div>
                <div><strong>Configuration:</strong></div>
                <ul class="q-pl-md">
                  <li>Ownership Price: $400</li>
                  <li>Deposit: $100 (applies to ownership)</li>
                  <li>Daily Rate: $4/day (applies to ownership)</li>
                  <li>Recurring: $120 every 30 days</li>
                </ul>

                <div class="q-mt-md">
                  <div><strong>Month 1:</strong> Deposit $100 + Initial $120 = <strong>$220 / $400</strong></div>
                  <div><strong>Month 2:</strong> $220 + $120 = <strong>$340 / $400</strong></div>
                  <div><strong>Month 3:</strong> $340 + $120 = <strong>$460 / $400</strong></div>
                  <div class="text-success text-weight-bold q-mt-sm">✓ Ownership transferred in Month 3!</div>
                  <div class="text-caption">Customer pays total $360, receives $60 credit for overpayment</div>
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-warning text-white">
                <div class="text-subtitle1"><strong>Scenario 3: Late Return with Fees</strong></div>
              </q-card-section>
              <q-card-section>
                <div><strong>Equipment:</strong> Battery</div>
                <div><strong>Cost Structure:</strong> $2/day, $50 deposit, $5/day late fee</div>
                <div><strong>Agreed rental:</strong> 30 days</div>
                <div><strong>Actual return:</strong> 35 days (5 days late)</div>

                <div class="q-mt-md">
                  <div>Original payment: $50 + (30 × $2) = $110</div>
                  <div>Late fees: 5 × $5 = <strong>$25</strong></div>
                  <div>Additional rental days: 5 × $2 = <strong>$10</strong></div>
                  <div class="text-weight-bold q-mt-sm">Customer owes additional: $35</div>
                  <div>Deducted from deposit: $50 - $35 = $15 refunded</div>
                </div>
              </q-card-section>
            </q-card>

            <div class="text-h6 q-mt-lg q-mb-sm">Best Practices</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Create Multiple Tiers</q-item-label>
                  <q-item-label caption>
                    Have "Basic", "Standard", and "Premium" cost structures to offer customers choices
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Use Descriptive Names</q-item-label>
                  <q-item-label caption>
                    Names like "Battery Standard $3/day" are clearer than "Plan A"
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Set Realistic Ownership Prices</q-item-label>
                  <q-item-label caption>
                    For Pay-to-Own, price should be fair market value, not inflated
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Consider Your Costs</q-item-label>
                  <q-item-label caption>
                    Factor in equipment depreciation, maintenance, and opportunity cost when setting rates
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Test Before Deployment</q-item-label>
                  <q-item-label caption>
                    Create a test rental to verify calculations work as expected
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- Pay-to-Own -->
        <q-card id="pay-to-own" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="shopping_cart" />
              Pay-to-Own System
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What is Pay-to-Own?</div>
            <p>Pay-to-own allows customers to eventually own their rented PUE equipment after making payments over time.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Setting Up Pay-to-Own</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Create or edit a <strong>Cost Structure</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Enable <strong>Pay-to-Own</strong> toggle</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>
                  Configure pay-to-own settings:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Ownership Price:</strong> Total price to own the equipment</li>
                    <li><strong>Apply Deposits:</strong> Whether deposits count toward ownership</li>
                    <li><strong>Apply Rental Payments:</strong> Whether rentals count toward ownership</li>
                    <li><strong>Minimum Payments:</strong> Required payments before ownership transfer</li>
                  </ul>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>The system automatically tracks payments and ownership progress</q-item-section>
              </q-item>
            </q-list>

            <q-banner class="bg-amber-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="lightbulb" color="amber-8" />
              </template>
              <strong>Note:</strong> Pay-to-own is available for PUE equipment rentals only, not batteries.
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- Battery Rentals -->
        <q-card id="battery-rentals" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="battery_charging_full" />
              Creating Battery Rentals
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">How to Create a Battery Rental</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Navigate to <strong>Rentals</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click <strong>New Battery Rental</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>
                  Select rental details:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Customer:</strong> Search and select user</li>
                    <li><strong>Battery:</strong> Choose available battery</li>
                    <li><strong>Cost Structure:</strong> Select pricing model</li>
                    <li><strong>Duration:</strong> Choose rental period</li>
                    <li><strong>Deposit:</strong> Collect refundable deposit</li>
                  </ul>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>Review costs and click <strong>Create Rental</strong></q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Rental Status</div>
            <q-list bordered dense>
              <q-item>
                <q-item-section avatar><q-badge color="positive">Active</q-badge></q-item-section>
                <q-item-section>Battery is currently rented out</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-badge color="warning">Overdue</q-badge></q-item-section>
                <q-item-section>Rental period has expired</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-badge color="grey">Completed</q-badge></q-item-section>
                <q-item-section>Battery has been returned</q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- PUE Rentals -->
        <q-card id="pue-rentals" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="devices" />
              Creating PUE Rentals
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">How to Create a PUE Rental</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Go to <strong>Rentals</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click <strong>New PUE Rental</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>
                  Configure the rental:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Customer:</strong> Select user</li>
                    <li><strong>Equipment:</strong> Add one or more PUE items</li>
                    <li><strong>Cost Structure:</strong> Choose pricing (with or without pay-to-own)</li>
                    <li><strong>Duration:</strong> Select rental period</li>
                    <li><strong>Recurring Payment:</strong> Optional for ongoing rentals</li>
                  </ul>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>System calculates total cost and tracks ownership progress (if pay-to-own)</q-item-section>
              </q-item>
            </q-list>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <strong>Multiple Items:</strong> You can rent multiple PUE items in a single rental transaction.
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- Returns -->
        <q-card id="returns" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="keyboard_return" />
              Processing Returns
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">How to Process a Return</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Open the <strong>Rentals</strong> page</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Find the active rental and click to view details</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Click the <strong>Return</strong> button</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>
                  Review and confirm:
                  <ul class="q-mt-sm q-ml-md">
                    <li>System calculates final costs including any late fees</li>
                    <li>Deposit is refunded automatically</li>
                    <li>Battery/equipment status returns to "Available"</li>
                  </ul>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">What Happens on Return?</div>
            <q-timeline color="primary" class="q-mt-md">
              <q-timeline-entry icon="calculate" subtitle="System calculates">
                <div>Total rental costs, late fees, and outstanding payments</div>
              </q-timeline-entry>
              <q-timeline-entry icon="account_balance_wallet" subtitle="Deposit processing">
                <div>Refundable deposit is returned to customer account</div>
              </q-timeline-entry>
              <q-timeline-entry icon="update" subtitle="Status update">
                <div>Rental marked as completed, equipment marked as available</div>
              </q-timeline-entry>
              <q-timeline-entry icon="receipt" subtitle="Records updated">
                <div>Transaction history and account balance updated</div>
              </q-timeline-entry>
            </q-timeline>
          </q-card-section>
        </q-card>

        <!-- User Accounts -->
        <q-card id="user-accounts" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="account_balance_wallet" />
              User Accounts & Credits
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">Account System</div>
            <p>Each user has an account that tracks their balance, payments, and transaction history.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Adding Credit</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Go to <strong>Accounts</strong> (admin only)</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Find the user and click <strong>Add Credit</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Enter amount and payment method</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>Credit is immediately available for rentals</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Taking Payment</div>
            <p>Payments can be recorded when customers pay for rentals, deposits, or outstanding balances. The system automatically debits from account credit or creates receivables.</p>
          </q-card-section>
        </q-card>

        <!-- Admin Tools -->
        <q-card id="admin-tools" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="admin_panel_settings" />
              Admin Tools
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">Settings Page</div>
            <p>Admins have access to system-wide settings including:</p>
            <q-list bordered dense class="q-mb-md">
              <q-item>
                <q-item-section avatar><q-icon name="payments" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Cost Structures:</strong> Pricing models</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="category" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>PUE Types:</strong> Equipment categories</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="credit_card" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Payment Types:</strong> Payment methods</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="subscriptions" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Subscription Packages:</strong> Recurring service plans</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">User Management</div>
            <p>Create and manage users with different access levels:</p>
            <q-list bordered dense>
              <q-item>
                <q-item-section avatar><q-badge color="grey">User</q-badge></q-item-section>
                <q-item-section>Can rent equipment and view their own account</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-badge color="primary">Admin</q-badge></q-item-section>
                <q-item-section>Can manage rentals, equipment, and settings</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-badge color="purple">Superadmin</q-badge></q-item-section>
                <q-item-section>Full system access including user management</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-badge color="info">Data Admin</q-badge></q-item-section>
                <q-item-section>Read-only access across multiple hubs</q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>

        <!-- Return Surveys -->
        <q-card id="return-surveys" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="quiz" />
              Return Surveys
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What are Return Surveys?</div>
            <p>Return surveys allow you to collect valuable feedback from customers when they return rented equipment. Create custom survey questions to gather insights about customer satisfaction, equipment performance, and service quality.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Creating Survey Questions</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Navigate to <strong>Settings</strong> page (admin only)</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click on the <strong>Return Surveys</strong> tab</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Click <strong>Add Survey Question</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>
                  Configure your question:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Question Text:</strong> What you want to ask (e.g., "How satisfied were you with the battery performance?")</li>
                    <li><strong>Question Type:</strong> Select from available types</li>
                    <li><strong>Options:</strong> For multiple choice questions, add answer options</li>
                  </ul>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Available Question Types</div>
            <q-list bordered dense class="q-mb-md">
              <q-item>
                <q-item-section avatar><q-icon name="notes" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Text:</strong></q-item-label>
                  <q-item-label caption>Open-ended text response - good for detailed feedback and comments</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="star" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Rating:</strong></q-item-label>
                  <q-item-label caption>Numerical rating scale (e.g., 1-5 stars) - ideal for satisfaction scores</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="check_circle" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Yes/No:</strong></q-item-label>
                  <q-item-label caption>Simple binary choice - perfect for quick confirmations</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="list" color="primary" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Multiple Choice:</strong></q-item-label>
                  <q-item-label caption>Select from predefined options - great for categorized responses</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Adding Options to Multiple Choice Questions</div>
            <p class="text-body2 q-mb-sm">When you create a multiple choice question, you need to provide answer options:</p>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Select <strong>Multiple Choice</strong> as the question type</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Enter your question text</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Add options one by one (e.g., "Excellent", "Good", "Fair", "Poor")</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>Save the question with all its options</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">How Surveys Work in Practice</div>
            <q-timeline color="primary" class="q-mt-md q-mb-md">
              <q-timeline-entry icon="receipt" subtitle="Rental created">
                <div>Customer rents equipment - survey is linked but not yet visible</div>
              </q-timeline-entry>
              <q-timeline-entry icon="keyboard_return" subtitle="Return initiated">
                <div>Admin processes the return - survey dialog automatically appears</div>
              </q-timeline-entry>
              <q-timeline-entry icon="quiz" subtitle="Survey presented">
                <div>All active survey questions are shown to the admin to complete with customer</div>
              </q-timeline-entry>
              <q-timeline-entry icon="save" subtitle="Responses saved">
                <div>Survey responses are permanently saved with the rental record</div>
              </q-timeline-entry>
              <q-timeline-entry icon="analytics" subtitle="Data available">
                <div>Responses can be reviewed in rental history and exported for analysis</div>
              </q-timeline-entry>
            </q-timeline>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <div class="text-subtitle2"><strong>Key Benefits:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Track customer satisfaction trends over time</li>
                <li>Identify equipment or service issues early</li>
                <li>Gather data to improve rental operations</li>
                <li>Build customer engagement and show you care about feedback</li>
                <li>Export survey data for detailed analysis</li>
              </ul>
            </q-banner>

            <q-banner class="bg-amber-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="lightbulb" color="amber-8" />
              </template>
              <div class="text-subtitle2"><strong>Best Practices:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Keep surveys short (3-5 questions) to encourage completion</li>
                <li>Mix question types for variety and rich data</li>
                <li>Ask about equipment condition, customer satisfaction, and service quality</li>
                <li>Update questions periodically based on your needs</li>
                <li>Review responses regularly to identify patterns</li>
              </ul>
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- Data Download -->
        <q-card id="data-download" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="download" />
              Downloading Your Data
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">Overview</div>
            <p>The system provides powerful data export capabilities, allowing you to download information from various pages for analysis, reporting, and record-keeping. Export data to spreadsheet formats for easy manipulation and sharing.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Available Export Options</div>

            <q-list bordered class="q-mb-md">
              <q-item>
                <q-item-section avatar>
                  <q-icon name="battery_charging_full" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Battery Rental Data</q-item-label>
                  <q-item-label caption class="q-mt-xs">
                    <strong>Location:</strong> Rentals page > Battery Rentals tab
                  </q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Exported fields include:</strong>
                    <ul class="q-ml-md q-mt-xs">
                      <li>Rental ID and dates (start, end, actual return)</li>
                      <li>Customer information (name, contact, location)</li>
                      <li>Battery details (ID, capacity, hub)</li>
                      <li>Cost structure and pricing details</li>
                      <li>Deposit amount and status</li>
                      <li>Payment information and outstanding balance</li>
                      <li>Rental status (active, completed, overdue)</li>
                      <li>Late fees and additional charges</li>
                    </ul>
                  </div>
                  <div class="q-mt-sm text-body2">
                    <strong>Use cases:</strong> Financial reporting, customer history analysis, equipment utilization tracking
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="devices" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">PUE Rental Data</q-item-label>
                  <q-item-label caption class="q-mt-xs">
                    <strong>Location:</strong> Rentals page > PUE Rentals tab
                  </q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Exported fields include:</strong>
                    <ul class="q-ml-md q-mt-xs">
                      <li>Rental ID and timeline information</li>
                      <li>Customer details and contact information</li>
                      <li>Equipment list (types, names, power ratings)</li>
                      <li>Cost structure and payment schedules</li>
                      <li>Pay-to-own status and ownership progress</li>
                      <li>Recurring payment information</li>
                      <li>Deposit and refund status</li>
                      <li>Survey responses (if completed)</li>
                    </ul>
                  </div>
                  <div class="q-mt-sm text-body2">
                    <strong>Use cases:</strong> Pay-to-own tracking, equipment demand analysis, subscription revenue reporting
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="people" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">User/Customer Data</q-item-label>
                  <q-item-label caption class="q-mt-xs">
                    <strong>Location:</strong> Users page
                  </q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Exported fields include:</strong>
                    <ul class="q-ml-md q-mt-xs">
                      <li>User ID and registration date</li>
                      <li>Full name and contact information</li>
                      <li>Location details (village, region, coordinates)</li>
                      <li>User role and permissions level</li>
                      <li>Associated hub information</li>
                      <li>Account status (active, inactive)</li>
                      <li>Custom data fields (if configured)</li>
                      <li>Total rental history count</li>
                    </ul>
                  </div>
                  <div class="q-mt-sm text-body2">
                    <strong>Use cases:</strong> Customer database management, demographic analysis, marketing lists
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="account_balance_wallet" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Account Transaction Data</q-item-label>
                  <q-item-label caption class="q-mt-xs">
                    <strong>Location:</strong> Accounts page
                  </q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Exported fields include:</strong>
                    <ul class="q-ml-md q-mt-xs">
                      <li>Account ID and user information</li>
                      <li>Transaction date and timestamp</li>
                      <li>Transaction type (credit, debit, deposit, refund)</li>
                      <li>Amount and currency</li>
                      <li>Payment method used</li>
                      <li>Related rental or order reference</li>
                      <li>Current account balance</li>
                      <li>Transaction notes and descriptions</li>
                    </ul>
                  </div>
                  <div class="q-mt-sm text-body2">
                    <strong>Use cases:</strong> Financial reconciliation, audit trails, payment pattern analysis
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-lg q-mb-sm">How to Export Data</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Navigate to the page containing the data you want to export</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Look for the <strong>Export</strong> or <strong>Download</strong> button (usually near the top right)</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Click the button to initiate the download</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>The file will download to your browser's default download location</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">5</div></q-item-section>
                <q-item-section>Open the file with Excel, Google Sheets, or your preferred spreadsheet application</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">File Formats</div>
            <q-list bordered dense class="q-mb-md">
              <q-item>
                <q-item-section avatar><q-icon name="table_chart" color="green" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>CSV (Comma-Separated Values)</strong></q-item-label>
                  <q-item-label caption>Standard format compatible with all spreadsheet applications - most commonly used</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="description" color="green-8" /></q-item-section>
                <q-item-section>
                  <q-item-label><strong>Excel Format</strong></q-item-label>
                  <q-item-label caption>Native Microsoft Excel format (when available) - includes formatting</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Working with Exported Data</div>
            <p class="text-body2 q-mb-sm">Once you've exported your data, you can:</p>
            <ul class="q-ml-md q-mb-md">
              <li><strong>Filter and Sort:</strong> Organize data by date, amount, customer, or any other field</li>
              <li><strong>Create Pivot Tables:</strong> Summarize and analyze patterns in your data</li>
              <li><strong>Generate Charts:</strong> Visualize trends and insights</li>
              <li><strong>Perform Calculations:</strong> Add custom formulas for ROI, utilization rates, etc.</li>
              <li><strong>Combine Datasets:</strong> Merge data from different exports for comprehensive analysis</li>
              <li><strong>Share Reports:</strong> Send processed data to stakeholders or management</li>
              <li><strong>Archive Records:</strong> Keep historical snapshots for compliance or reference</li>
            </ul>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <div class="text-subtitle2"><strong>Data Export Tips:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Export data regularly for backup purposes</li>
                <li>Use filters before exporting to get only the data you need</li>
                <li>Check date ranges if the export includes time-based filtering</li>
                <li>Exported files capture the current state - data may change after export</li>
                <li>Large exports may take a few moments to generate</li>
              </ul>
            </q-banner>

            <q-banner class="bg-green-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="security" color="green-8" />
              </template>
              <div class="text-subtitle2"><strong>Data Privacy Note:</strong></div>
              <div class="text-body2">
                Exported files contain sensitive customer and financial information. Always:
                <ul class="q-ml-md q-mt-xs q-mb-none">
                  <li>Store exported files securely</li>
                  <li>Don't share files via unsecured channels</li>
                  <li>Delete old exports that are no longer needed</li>
                  <li>Follow your organization's data protection policies</li>
                </ul>
              </div>
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- Customer Data Fields -->
        <q-card id="customer-fields" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="edit_note" />
              Custom Customer Data Fields
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What are Custom Customer Fields?</div>
            <p>Custom customer data fields allow you to collect additional information about your customers beyond the standard name, phone, and location fields. This flexible system lets you tailor customer profiles to your specific business needs and local context.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Why Use Custom Fields?</div>
            <p class="text-body2 q-mb-sm">Standard customer profiles may not capture all the information you need. Custom fields enable you to:</p>
            <ul class="q-ml-md q-mb-md">
              <li><strong>Track local context:</strong> Village names, tribal affiliations, local landmarks</li>
              <li><strong>Understand demographics:</strong> Household size, number of children, age groups</li>
              <li><strong>Capture economic data:</strong> Occupation, income sources, farming activities</li>
              <li><strong>Record preferences:</strong> Preferred contact method, language, equipment interests</li>
              <li><strong>Store identifiers:</strong> National ID numbers, voter registration, alternative IDs</li>
              <li><strong>Document needs:</strong> Energy usage patterns, business type, specific requirements</li>
            </ul>

            <div class="text-h6 q-mt-md q-mb-sm">Creating Custom Fields</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Navigate to <strong>Settings</strong> page (admin only)</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Click on the <strong>Customer Fields</strong> tab</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Click <strong>Add Custom Field</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>
                  Configure the field:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Field Label:</strong> The name shown to users (e.g., "Village Name", "Household Size")</li>
                    <li><strong>Field Type:</strong> Select the appropriate input type</li>
                    <li><strong>Required:</strong> Whether the field must be filled in (optional)</li>
                    <li><strong>Display Order:</strong> Control where the field appears in forms</li>
                  </ul>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">5</div></q-item-section>
                <q-item-section>Save the field - it will immediately appear in user forms</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Available Field Types</div>
            <q-list bordered class="q-mb-md">
              <q-item>
                <q-item-section avatar>
                  <q-icon name="text_fields" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Text Field</q-item-label>
                  <q-item-label caption class="q-mt-xs">Single-line text input for short answers</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Best for:</strong> Names, IDs, short descriptions
                  </div>
                  <div class="text-body2 text-grey-7">
                    <strong>Example:</strong> "National ID Number", "Village Name", "Primary Occupation"
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="pin" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Number Field</q-item-label>
                  <q-item-label caption class="q-mt-xs">Numeric input with validation</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Best for:</strong> Quantities, counts, measurements
                  </div>
                  <div class="text-body2 text-grey-7">
                    <strong>Example:</strong> "Household Size", "Number of Children", "Farm Size (hectares)"
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="event" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Date Field</q-item-label>
                  <q-item-label caption class="q-mt-xs">Calendar date picker</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Best for:</strong> Dates, deadlines, milestones
                  </div>
                  <div class="text-body2 text-grey-7">
                    <strong>Example:</strong> "Date of Birth", "Account Opening Date", "Last Survey Date"
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="arrow_drop_down_circle" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Dropdown/Select Field</q-item-label>
                  <q-item-label caption class="q-mt-xs">Single choice from predefined options</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Best for:</strong> Categories, classifications, limited choices
                  </div>
                  <div class="text-body2 text-grey-7">
                    <strong>Example:</strong> "Customer Type" (New/Returning), "Region", "Income Level" (Low/Medium/High)
                  </div>
                  <div class="q-mt-sm">
                    <q-chip size="sm" color="blue-2" text-color="blue-9">Requires options to be configured</q-chip>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Adding Options to Dropdown Fields</div>
            <p class="text-body2 q-mb-sm">When you create a dropdown/select field, you need to define the available options:</p>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Select <strong>Dropdown/Select</strong> as the field type</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Enter the field label (e.g., "Primary Income Source")</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Add options one by one (e.g., "Farming", "Trading", "Employment", "Business", "Other")</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>Save the field with all options configured</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">How Custom Fields Appear</div>
            <q-timeline color="primary" class="q-mt-md q-mb-md">
              <q-timeline-entry icon="person_add" subtitle="User Creation Form">
                <div>Custom fields appear in the "Add User" dialog alongside standard fields</div>
              </q-timeline-entry>
              <q-timeline-entry icon="edit" subtitle="User Edit Form">
                <div>All custom fields are editable when updating user information</div>
              </q-timeline-entry>
              <q-timeline-entry icon="visibility" subtitle="User Detail Page">
                <div>Custom field values are displayed in the user's profile view</div>
              </q-timeline-entry>
              <q-timeline-entry icon="download" subtitle="Data Exports">
                <div>Custom fields are included in user data exports as additional columns</div>
              </q-timeline-entry>
            </q-timeline>

            <div class="text-h6 q-mt-md q-mb-sm">Practical Examples</div>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-positive text-white">
                <div class="text-subtitle1"><strong>Example 1: Rural Energy Program</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm"><strong>Custom fields configured:</strong></div>
                <ul class="q-ml-md">
                  <li><strong>Village Name</strong> (Text) - To track which villages are served</li>
                  <li><strong>Household Size</strong> (Number) - To understand energy needs</li>
                  <li><strong>Primary Income</strong> (Dropdown: Farming, Fishing, Trading, Other) - Economic segmentation</li>
                  <li><strong>Has Grid Connection</strong> (Dropdown: Yes, No, Intermittent) - Energy access baseline</li>
                  <li><strong>Land Ownership</strong> (Dropdown: Own Land, Rent, Communal) - Asset assessment</li>
                </ul>
                <div class="q-mt-md text-body2">
                  <strong>Result:</strong> Rich customer profiles enable targeted outreach and impact reporting
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-info text-white">
                <div class="text-subtitle1"><strong>Example 2: Urban Hub Operation</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm"><strong>Custom fields configured:</strong></div>
                <ul class="q-ml-md">
                  <li><strong>Business Type</strong> (Dropdown: Salon, Shop, Restaurant, Workshop, Other) - Customer segmentation</li>
                  <li><strong>Business Registration Number</strong> (Text) - Official verification</li>
                  <li><strong>Daily Operating Hours</strong> (Number) - Energy usage estimation</li>
                  <li><strong>Preferred Contact Method</strong> (Dropdown: Phone, WhatsApp, Email, In-Person) - Communication optimization</li>
                  <li><strong>Referral Source</strong> (Dropdown: Social Media, Friend, Flyer, Walk-in) - Marketing analytics</li>
                </ul>
                <div class="q-mt-md text-body2">
                  <strong>Result:</strong> Better customer service and targeted marketing campaigns
                </div>
              </q-card-section>
            </q-card>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <div class="text-subtitle2"><strong>Key Benefits:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Collect exactly the data you need without code changes</li>
                <li>Adapt to different cultural and geographic contexts</li>
                <li>Improve customer segmentation and targeting</li>
                <li>Generate more detailed reports and analytics</li>
                <li>Support research and impact assessment</li>
                <li>Comply with local data collection requirements</li>
              </ul>
            </q-banner>

            <q-banner class="bg-amber-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="lightbulb" color="amber-8" />
              </template>
              <div class="text-subtitle2"><strong>Best Practices:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Only add fields that you'll actually use and analyze</li>
                <li>Use dropdown fields when possible to standardize data entry</li>
                <li>Keep field labels clear and easy to understand for all staff</li>
                <li>Consider marking important fields as required</li>
                <li>Review and update field options periodically</li>
                <li>Train staff on why each field matters and how to use it</li>
                <li>Respect customer privacy - only collect necessary information</li>
              </ul>
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- Job Cards -->
        <q-card id="job-cards" class="q-mb-md">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="task" />
              Job Cards & Task Management
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What are Job Cards?</div>
            <p class="text-body1">
              Job Cards are a comprehensive task management system designed to help you track maintenance, repairs, follow-ups, and other operational tasks.
              They ensure nothing falls through the cracks by providing a centralized place to manage all work that needs to be done across your battery hub operations.
            </p>
            <p class="text-body2">
              Whether it's scheduling battery maintenance, tracking equipment repairs, planning customer follow-ups, or preparing for rental returns,
              Job Cards help you stay organized and accountable.
            </p>

            <div class="text-h6 q-mt-lg q-mb-sm">Where to Access Job Cards</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Click <strong>Job Cards</strong> in the sidebar navigation menu</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>View all job cards organized by status: To Do, In Progress, and Completed</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Click on any card to view details, update status, or add notes</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-lg q-mb-sm">Creating a New Job Card</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>From the Job Cards page, click the <strong>Create Job Card</strong> button</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Enter a clear, descriptive <strong>Title</strong> (e.g., "Inspect Battery #101 for maintenance")</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Add detailed <strong>Description</strong> explaining the task, context, and any special requirements</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>Set <strong>Priority Level</strong>, <strong>Due Date</strong>, and <strong>Assign</strong> to a staff member</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">5</div></q-item-section>
                <q-item-section>Optionally link to related entities (batteries, PUE items, customers, or rentals) for context</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">6</div></q-item-section>
                <q-item-section>Click <strong>Create</strong> to save the job card</q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-lg q-mb-sm">Job Card Fields Explained</div>
            <q-list bordered class="q-mb-md">
              <q-item>
                <q-item-section avatar>
                  <q-icon name="title" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Title</q-item-label>
                  <q-item-label caption class="q-mt-xs">A brief summary of the task</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Examples:</strong> "Monthly battery maintenance check", "Follow up with customer John Doe", "Repair damaged PUE solar panel"
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="description" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Description</q-item-label>
                  <q-item-label caption class="q-mt-xs">Detailed information about the task</q-item-label>
                  <div class="q-mt-sm text-body2">
                    Include step-by-step instructions, background information, tools needed, safety considerations, or any other relevant details
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="flag" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Priority Levels</q-item-label>
                  <q-item-label caption class="q-mt-xs">Indicates urgency and importance with color coding</q-item-label>
                  <div class="q-mt-sm">
                    <div class="row items-center q-mb-xs">
                      <q-badge color="red" class="q-mr-sm">High Priority</q-badge>
                      <span class="text-body2">Urgent tasks requiring immediate attention (safety issues, critical repairs, overdue items)</span>
                    </div>
                    <div class="row items-center q-mb-xs">
                      <q-badge color="orange" class="q-mr-sm">Medium Priority</q-badge>
                      <span class="text-body2">Important tasks that should be completed soon (scheduled maintenance, customer follow-ups)</span>
                    </div>
                    <div class="row items-center">
                      <q-badge color="green" class="q-mr-sm">Low Priority</q-badge>
                      <span class="text-body2">Routine tasks that can be scheduled flexibly (inventory checks, general improvements)</span>
                    </div>
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="checklist" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Status Workflow</q-item-label>
                  <q-item-label caption class="q-mt-xs">Track progress through three stages</q-item-label>
                  <div class="q-mt-sm">
                    <q-timeline color="primary" layout="dense" class="q-mt-sm">
                      <q-timeline-entry subtitle="To Do" icon="pending_actions">
                        <div class="text-body2">Task is created and waiting to be started</div>
                      </q-timeline-entry>
                      <q-timeline-entry subtitle="In Progress" icon="sync">
                        <div class="text-body2">Work has begun - task is actively being worked on</div>
                      </q-timeline-entry>
                      <q-timeline-entry subtitle="Completed" icon="check_circle">
                        <div class="text-body2">Task is finished and verified</div>
                      </q-timeline-entry>
                    </q-timeline>
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="event" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Due Date</q-item-label>
                  <q-item-label caption class="q-mt-xs">Deadline for task completion</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Purpose:</strong> Helps prioritize work and ensures timely completion. Visual indicators show approaching or overdue tasks.
                  </div>
                  <div class="text-body2">
                    <strong>Tip:</strong> Set realistic due dates that account for staff availability and task complexity
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="person" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Assigned To</q-item-label>
                  <q-item-label caption class="q-mt-xs">Specific staff member or user responsible for the task</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Benefits:</strong> Clear accountability, workload visibility, and enables staff to filter and view their own tasks
                  </div>
                  <div class="text-body2">
                    <strong>Best Practice:</strong> Assign tasks based on expertise, availability, and balanced workload distribution
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="link" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Entity Links</q-item-label>
                  <q-item-label caption class="q-mt-xs">Connect job cards to related system entities for context</q-item-label>
                  <div class="q-mt-sm text-body2">
                    <strong>Link to:</strong>
                    <ul class="q-ml-md q-mt-xs">
                      <li><strong>Batteries:</strong> Maintenance tasks, repairs, inspections</li>
                      <li><strong>PUE Items:</strong> Equipment servicing, upgrades, troubleshooting</li>
                      <li><strong>Customers/Users:</strong> Follow-ups, support requests, account issues</li>
                      <li><strong>Rentals:</strong> Return preparations, payment follow-ups, delivery scheduling</li>
                    </ul>
                  </div>
                  <div class="q-mt-sm text-body2">
                    <strong>Benefit:</strong> Quick access to related information with one click - jump directly to the linked entity's detail page
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-lg q-mb-sm">Updating Job Card Status</div>
            <p class="text-body2 q-mb-sm">There are two ways to update the status of a job card:</p>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-blue-grey-1">
                <div class="text-subtitle1 q-mb-sm"><strong>Method 1: Drag and Drop</strong></div>
                <q-list dense class="q-mb-sm">
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                    <q-item-section>Click and hold on a job card</q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                    <q-item-section>Drag it to the desired column (To Do, In Progress, or Completed)</q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                    <q-item-section>Release to drop - status updates automatically</q-item-section>
                  </q-item>
                </q-list>
                <q-banner class="bg-blue-2 text-body2">
                  <strong>Quick & Intuitive:</strong> Perfect for rapidly updating multiple tasks during team meetings or daily reviews
                </q-banner>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-blue-grey-1">
                <div class="text-subtitle1 q-mb-sm"><strong>Method 2: Manual Update</strong></div>
                <q-list dense class="q-mb-sm">
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                    <q-item-section>Click on a job card to open its detail view</q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                    <q-item-section>Click the <strong>Edit</strong> button</q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                    <q-item-section>Select the new status from the dropdown</q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                    <q-item-section>Save your changes</q-item-section>
                  </q-item>
                </q-list>
                <q-banner class="bg-blue-2 text-body2">
                  <strong>Detailed Approach:</strong> Use when you also need to update other fields or add notes
                </q-banner>
              </q-card-section>
            </q-card>

            <div class="text-h6 q-mt-lg q-mb-sm">Filtering and Searching Job Cards</div>
            <p class="text-body2 q-mb-md">Quickly find specific tasks using the built-in filtering and search tools:</p>

            <q-list bordered class="q-mb-md">
              <q-item>
                <q-item-section avatar>
                  <q-icon name="search" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Text Search</q-item-label>
                  <q-item-label caption class="q-mt-xs">Search by title, description, or assigned person</q-item-label>
                  <div class="q-mt-sm text-body2">
                    Type keywords in the search box to instantly filter the list
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="filter_list" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Priority Filter</q-item-label>
                  <q-item-label caption class="q-mt-xs">Show only high, medium, or low priority tasks</q-item-label>
                  <div class="q-mt-sm text-body2">
                    Focus on urgent work by filtering to high-priority items only
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="person_search" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Assignment Filter</q-item-label>
                  <q-item-label caption class="q-mt-xs">View tasks assigned to specific staff members</q-item-label>
                  <div class="q-mt-sm text-body2">
                    Perfect for individual staff members to see their personal task list
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="calendar_today" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Due Date Filter</q-item-label>
                  <q-item-label caption class="q-mt-xs">Filter by upcoming, today, overdue, or date range</q-item-label>
                  <div class="q-mt-sm text-body2">
                    Identify overdue tasks or plan for upcoming deadlines
                  </div>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item>
                <q-item-section avatar>
                  <q-icon name="link" color="primary" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Entity Filter</q-item-label>
                  <q-item-label caption class="q-mt-xs">Show tasks linked to specific batteries, equipment, customers, or rentals</q-item-label>
                  <div class="q-mt-sm text-body2">
                    See all tasks related to a particular battery or customer account
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-lg q-mb-sm">Common Use Cases</div>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-positive text-white">
                <div class="text-subtitle1"><strong>Use Case 1: Battery Maintenance Schedules</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm">
                  <strong>Scenario:</strong> Your batteries need regular maintenance every 90 days to ensure optimal performance and longevity.
                </div>
                <div class="text-body2 q-mb-sm"><strong>Job Card Setup:</strong></div>
                <ul class="q-ml-md q-mb-md">
                  <li><strong>Title:</strong> "Quarterly maintenance - Battery #101"</li>
                  <li><strong>Priority:</strong> Medium</li>
                  <li><strong>Due Date:</strong> 90 days from last service</li>
                  <li><strong>Assigned To:</strong> Maintenance technician</li>
                  <li><strong>Linked Entity:</strong> Battery #101</li>
                  <li><strong>Description:</strong> "Check connections, test capacity, clean terminals, inspect casing for damage, update maintenance log"</li>
                </ul>
                <div class="text-body2">
                  <strong>Benefit:</strong> Never miss critical maintenance intervals, extend battery life, prevent unexpected failures
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-info text-white">
                <div class="text-subtitle1"><strong>Use Case 2: Equipment Repair Tracking</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm">
                  <strong>Scenario:</strong> A customer returns a PUE solar panel that's not charging properly. It needs diagnosis and repair.
                </div>
                <div class="text-body2 q-mb-sm"><strong>Job Card Setup:</strong></div>
                <ul class="q-ml-md q-mb-md">
                  <li><strong>Title:</strong> "Repair - Solar Panel #SP-205 not charging"</li>
                  <li><strong>Priority:</strong> High (equipment out of circulation)</li>
                  <li><strong>Due Date:</strong> 3 days from now</li>
                  <li><strong>Assigned To:</strong> Equipment specialist</li>
                  <li><strong>Linked Entity:</strong> PUE Item #SP-205</li>
                  <li><strong>Description:</strong> "Customer reported panel stopped charging. Test output voltage, check wiring connections, inspect for physical damage. If repairable within 2 days, fix. Otherwise, mark for replacement."</li>
                </ul>
                <div class="text-body2">
                  <strong>Benefit:</strong> Track repair status, estimate downtime, plan equipment availability, maintain service quality
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-warning text-white">
                <div class="text-subtitle1"><strong>Use Case 3: Customer Follow-up Reminders</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm">
                  <strong>Scenario:</strong> A customer expressed interest in upgrading to a pay-to-own plan but wanted time to consider. You need to follow up.
                </div>
                <div class="text-body2 q-mb-sm"><strong>Job Card Setup:</strong></div>
                <ul class="q-ml-md q-mb-md">
                  <li><strong>Title:</strong> "Follow up: Sarah Kimani - Pay-to-Own interest"</li>
                  <li><strong>Priority:</strong> Medium</li>
                  <li><strong>Due Date:</strong> 1 week from conversation</li>
                  <li><strong>Assigned To:</strong> Customer service representative</li>
                  <li><strong>Linked Entity:</strong> User Sarah Kimani</li>
                  <li><strong>Description:</strong> "Sarah showed interest in pay-to-own solar panel during last visit. Follow up via phone to answer questions, explain payment plan options, and schedule demonstration if interested."</li>
                </ul>
                <div class="text-body2">
                  <strong>Benefit:</strong> Improve customer engagement, convert leads, provide timely service, build relationships
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-deep-purple-3 text-white">
                <div class="text-subtitle1"><strong>Use Case 4: Rental Return Preparations</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm">
                  <strong>Scenario:</strong> A battery rental is ending in 2 days. You need to prepare for return, inspection, and refund processing.
                </div>
                <div class="text-body2 q-mb-sm"><strong>Job Card Setup:</strong></div>
                <ul class="q-ml-md q-mb-md">
                  <li><strong>Title:</strong> "Prepare for return - Battery #103 - John Doe rental"</li>
                  <li><strong>Priority:</strong> High</li>
                  <li><strong>Due Date:</strong> 1 day before rental end date</li>
                  <li><strong>Assigned To:</strong> Hub manager</li>
                  <li><strong>Linked Entity:</strong> Rental #R-458</li>
                  <li><strong>Description:</strong> "Contact customer to confirm return date/time. Prepare inspection checklist. Calculate final charges including any late fees. Process deposit refund. Update battery status to available after inspection."</li>
                </ul>
                <div class="text-body2">
                  <strong>Benefit:</strong> Smooth return process, accurate accounting, good customer experience, quick equipment turnaround
                </div>
              </q-card-section>
            </q-card>

            <q-card flat bordered class="q-mb-md">
              <q-card-section class="bg-teal-3 text-white">
                <div class="text-subtitle1"><strong>Use Case 5: PUE Inspection Scheduling</strong></div>
              </q-card-section>
              <q-card-section>
                <div class="text-body2 q-mb-sm">
                  <strong>Scenario:</strong> PUE equipment needs periodic inspection to ensure safe operation and identify wear before it causes problems.
                </div>
                <div class="text-body2 q-mb-sm"><strong>Job Card Setup:</strong></div>
                <ul class="q-ml-md q-mb-md">
                  <li><strong>Title:</strong> "Monthly safety inspection - All PUE lights and fans"</li>
                  <li><strong>Priority:</strong> Medium</li>
                  <li><strong>Due Date:</strong> First Monday of each month</li>
                  <li><strong>Assigned To:</strong> Safety officer</li>
                  <li><strong>Linked Entity:</strong> PUE Type: Lights and Fans</li>
                  <li><strong>Description:</strong> "Inspect all light fixtures and fans for: frayed wiring, loose connections, worn switch mechanisms, physical damage, unusual sounds. Document findings and create repair job cards for any issues found."</li>
                </ul>
                <div class="text-body2">
                  <strong>Benefit:</strong> Prevent safety incidents, maintain equipment quality, extend equipment life, ensure regulatory compliance
                </div>
              </q-card-section>
            </q-card>

            <div class="text-h6 q-mt-lg q-mb-sm">Best Practices for Job Card Management</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Set Realistic Due Dates</q-item-label>
                  <q-item-label caption>
                    Account for staff availability, task complexity, and dependencies when setting deadlines. Buffer time for unexpected issues.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Assign Clear Ownership</q-item-label>
                  <q-item-label caption>
                    Every job card should have one clearly responsible person. Avoid "team" assignments that create ambiguity about accountability.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Update Status Regularly</q-item-label>
                  <q-item-label caption>
                    Make status updates part of your daily routine. Move cards to "In Progress" when you start and "Completed" when done. This keeps everyone informed.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Link to Relevant Entities</q-item-label>
                  <q-item-label caption>
                    Always link job cards to related batteries, equipment, customers, or rentals. This provides crucial context and makes it easy to find related information.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Use Priority Levels Effectively</q-item-label>
                  <q-item-label caption>
                    Reserve "High" priority for truly urgent tasks. If everything is high priority, nothing is. Be strategic to maintain priority system value.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Write Detailed Descriptions</q-item-label>
                  <q-item-label caption>
                    Include all necessary context, step-by-step instructions, tools needed, and success criteria. This helps others understand and complete tasks efficiently.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Review Regularly as a Team</q-item-label>
                  <q-item-label caption>
                    Hold brief daily or weekly job card reviews. Discuss progress, reassign if needed, identify blockers, and celebrate completed work.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Archive Completed Cards</q-item-label>
                  <q-item-label caption>
                    Keep completed job cards for reference and accountability, but periodically archive old ones to keep the active list manageable and focused.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Create Recurring Tasks</q-item-label>
                  <q-item-label caption>
                    For regular maintenance or inspections, create job cards in advance with appropriate due dates. This ensures routine work never gets forgotten.
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-item>
                <q-item-section avatar top>
                  <q-icon name="tips_and_updates" color="amber" size="md" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Balance Your Workload</q-item-label>
                  <q-item-label caption>
                    Use the assignment filter to check individual staff workloads. Distribute tasks evenly to prevent burnout and ensure all work gets done on time.
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <div class="text-subtitle2"><strong>Key Benefits of Job Cards:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Never forget important tasks or maintenance schedules</li>
                <li>Clear accountability with task assignments</li>
                <li>Visual workflow tracking with drag-and-drop status updates</li>
                <li>Prioritization helps focus on what matters most</li>
                <li>Context preservation by linking to batteries, equipment, customers, and rentals</li>
                <li>Team coordination and transparency about who's doing what</li>
                <li>Historical record of work completed</li>
                <li>Improved customer service through timely follow-ups</li>
                <li>Better equipment maintenance and longer lifespan</li>
                <li>Reduced downtime and operational efficiency</li>
              </ul>
            </q-banner>

            <q-banner class="bg-green-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="psychology" color="green-8" />
              </template>
              <div class="text-subtitle2"><strong>Pro Tips:</strong></div>
              <ul class="q-ml-md q-mb-none">
                <li>Start each day by reviewing your assigned job cards and priorities</li>
                <li>Break large tasks into multiple smaller job cards for better progress tracking</li>
                <li>Use job cards to delegate work and empower team members</li>
                <li>Create job cards immediately when issues are discovered - don't rely on memory</li>
                <li>Add photos or attachments to job cards for visual reference (if feature available)</li>
                <li>Set up notifications or reminders for approaching due dates</li>
                <li>Export completed job cards periodically for performance reviews and reporting</li>
                <li>Learn from completed job cards to improve time estimates and processes</li>
              </ul>
            </q-banner>
          </q-card-section>
        </q-card>

        <!-- Support -->
        <q-card id="support" class="q-mb-xl">
          <q-card-section class="bg-primary text-white">
            <div class="text-h5">
              <q-icon name="support_agent" />
              Need More Help?
            </div>
          </q-card-section>
          <q-card-section>
            <p class="text-body1">
              If you need additional assistance or have questions not covered in this guide, please contact your system administrator.
            </p>
            <div class="q-mt-md">
              <q-btn
                outline
                color="primary"
                label="View Documentation"
                icon="description"
                href="https://github.com/keepexploring/BEPPP"
                target="_blank"
              />
            </div>

            <q-banner class="bg-blue-1 q-mt-md">
              <template v-slot:avatar>
                <q-icon name="info" color="primary" />
              </template>
              <div class="text-subtitle2"><strong>Note on User Access:</strong></div>
              <div class="text-body2">
                While the system has user login functionality implemented, user credentials are not currently
                being provided to end customers. This feature can be enabled and rolled out when ready.
                Currently, admins manage all rental operations on behalf of customers.
              </div>
            </q-banner>
          </q-card-section>
        </q-card>

      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'

const step = ref(1)
const costStructureStep = ref(1)

const quickLinks = [
  { id: 'getting-started', label: 'Getting Started' },
  { id: 'hubs', label: 'Hubs' },
  { id: 'batteries', label: 'Batteries' },
  { id: 'pue', label: 'PUE Equipment' },
  { id: 'cost-structures', label: 'Cost Structures' },
  { id: 'pay-to-own', label: 'Pay-to-Own' },
  { id: 'battery-rentals', label: 'Battery Rentals' },
  { id: 'pue-rentals', label: 'PUE Rentals' },
  { id: 'returns', label: 'Returns' },
  { id: 'user-accounts', label: 'User Accounts' },
  { id: 'admin-tools', label: 'Admin Tools' },
  { id: 'job-cards', label: 'Job Cards' },
  { id: 'return-surveys', label: 'Return Surveys' },
  { id: 'data-download', label: 'Download Data' },
  { id: 'customer-fields', label: 'Customer Fields' },
  { id: 'support', label: 'Support' }
]

const scrollToSection = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>
