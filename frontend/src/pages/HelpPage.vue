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
              Cost Structures & Pricing
            </div>
          </q-card-section>
          <q-card-section>
            <div class="text-h6 q-mb-sm">What are Cost Structures?</div>
            <p>Cost Structures define pricing models for rentals. You can create different pricing tiers for batteries and PUE items.</p>

            <div class="text-h6 q-mt-md q-mb-sm">Creating a Cost Structure</div>
            <q-list bordered separator class="q-mb-md">
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">1</div></q-item-section>
                <q-item-section>Go to <strong>Settings</strong> (admin only)</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">2</div></q-item-section>
                <q-item-section>Scroll to <strong>Cost Structures</strong> section</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">3</div></q-item-section>
                <q-item-section>Click <strong>Add Cost Structure</strong></q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><div class="text-h6 text-primary">4</div></q-item-section>
                <q-item-section>
                  Configure pricing:
                  <ul class="q-mt-sm q-ml-md">
                    <li><strong>Name:</strong> e.g., "Standard Battery Rental"</li>
                    <li><strong>Base Cost:</strong> Daily rental fee</li>
                    <li><strong>Deposit:</strong> Refundable deposit amount</li>
                    <li><strong>Duration Options:</strong> Add pricing for different rental periods</li>
                  </ul>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-h6 q-mt-md q-mb-sm">Cost Components</div>
            <p>Each cost structure can include multiple components:</p>
            <q-list bordered dense class="q-mb-md">
              <q-item>
                <q-item-section avatar><q-icon name="check_circle" color="positive" /></q-item-section>
                <q-item-section><strong>Base Rental Fee:</strong> Regular rental cost per day/week</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="check_circle" color="positive" /></q-item-section>
                <q-item-section><strong>Deposit:</strong> Refundable security deposit</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="check_circle" color="positive" /></q-item-section>
                <q-item-section><strong>Late Fees:</strong> Penalties for overdue returns</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar><q-icon name="check_circle" color="positive" /></q-item-section>
                <q-item-section><strong>Recurring Payments:</strong> For ongoing rentals</q-item-section>
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
              If you need additional assistance or have questions not covered in this guide:
            </p>
            <div class="q-mt-md">
              <q-btn
                outline
                color="primary"
                label="Contact Support"
                icon="email"
                href="mailto:support@beppp.cloud"
                class="q-mr-sm"
              />
              <q-btn
                outline
                color="primary"
                label="View Documentation"
                icon="description"
                href="https://github.com/keepexploring/BEPPP"
                target="_blank"
              />
            </div>
          </q-card-section>
        </q-card>

      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'

const step = ref(1)

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
