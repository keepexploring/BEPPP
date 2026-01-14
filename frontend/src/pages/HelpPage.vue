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
  { id: 'support', label: 'Support' }
]

const scrollToSection = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>
