<template>
  <q-page class="q-pa-md" style="max-width: 800px">
    <div class="text-h5 q-mb-xs">Release Info</div>
    <div class="text-caption text-grey-6 q-mb-lg">BEPPP Solar Battery Hub — version history</div>

    <q-timeline color="primary">

      <q-timeline-entry
        title="v1.8 — Hub admin permissions, historical records, rental time editing"
        subtitle="June 2026"
        icon="manage_accounts"
        color="primary"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Hub Admin role can now edit battery status and add/manage notes and job cards</li>
            <li>Historical rental records: enter paper records via the new "Historical Record" button on the Rentals page — availability check is skipped, payment can be recorded, status is set to returned immediately</li>
            <li>Superadmin can edit rental return times directly from the rental detail page (Edit Times button)</li>
            <li>Hub settings: configurable default return time (e.g. 10:00) — automatically applied when creating battery rentals</li>
            <li>Battery status changes made by hub admins are restricted to their own hub</li>
            <li>ID photo upload: file picker now available in addition to camera (previously was camera-only)</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.7 — Mobile UX, global search, deposit fixes, cache improvements"
        subtitle="May 2026"
        icon="search"
        color="primary"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Global search (Ctrl+K): now includes page shortcuts and hub results; role-scoped (kiosk operators see only customers and batteries)</li>
            <li>Mobile UX: all dialogs now fit portrait screens; low-priority table columns hidden on small screens; Job Cards shows tab view on mobile</li>
            <li>Deposit display fix: customer detail page now updates immediately after a rental is created (was showing stale cached value)</li>
            <li>Cache staleness: Rental, Battery, and PUE detail pages now refresh automatically when background data sync completes</li>
            <li>Failed sync: added Discard All button to the failed mutations dialog</li>
            <li>Help page: new sections covering the Deposit System, Data Page, and Global Search</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.6 — Hub filtering, CSV exports, release page"
        subtitle="May 2026"
        icon="filter_list"
        color="primary"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Superadmins can now switch hubs on the Data page and Users page via a prominent hub selector</li>
            <li>User loading fixed — single API call replaces fragile per-hub loop</li>
            <li>Power Usage tab: CSV download for battery split-stats and PUE type data</li>
            <li>User Detail page: CSV download on Battery History and PUE History tabs</li>
            <li>Currency selectors now support all 11 currencies (ZAR, KES, UGX, TZS, NGN, GHS, RWF added)</li>
            <li>This release info page added</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.5 — Power chart redesign, delta sync, deployment fixes"
        subtitle="April 2026"
        icon="bolt"
        color="teal"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Power Usage tab: separate bars for Mean In / Mean Out / kWh In / kWh Out with optional median and ±std dev overlays</li>
            <li>PUE Power tab: "consumed" framing (power out shown as positive), toggle for total kWh</li>
            <li>Backend <code>split_stats</code> aggregation: separately computes mean/median/std for charging vs discharging per time bucket</li>
            <li>Delta sync: background revalidation uses <code>modified_after</code> param on 6 endpoints for incremental fetches</li>
            <li>Connection quality detection: 2G/3G uses delta-only, 4G/WiFi gets periodic full refresh every 30 min</li>
            <li>Currency symbols now use hub settings store (supports USD, GBP, EUR, MWK, ZAR, KES, UGX, TZS, NGN, GHS, RWF)</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.4 — Battery swap, upfront payments, deposit holds"
        subtitle="March 2026"
        icon="swap_horiz"
        color="purple"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Battery swap: swap to an available battery mid-rental with optional recharge fee and skip-to-debt option</li>
            <li>Upfront payment collection on rental creation (both battery and PUE forms)</li>
            <li>Deposit holds: cost structures can require a deposit; credit is held on rental and released on return</li>
            <li>User detail page: deposit hold card and credit summary</li>
            <li>SWR (stale-while-revalidate) refresh on all pages</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.3 — Customers page, GESI multi-select, survey improvements"
        subtitle="March 2026"
        icon="people"
        color="orange"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Customers page added (filtered user list, hub_admin view)</li>
            <li>GESI signup questions: multi-select, energy split (electricity + heat/other)</li>
            <li>Survey CSV export with timeframe selector (last week / last month / custom / all)</li>
            <li>Decimal durations in cost structures (e.g. 0.5 × month)</li>
            <li>Mobile CSS overflow fixes, PWA screen rotation unlocked</li>
            <li>Daily database backup/restore scripts (<code>make db-backup</code>, <code>make db-restore</code>)</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.2 — Offline PWA, job cards, webhook logs"
        subtitle="February 2026"
        icon="wifi_off"
        color="blue"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Full offline PWA with IndexedDB queue — creates, edits, returns all work offline</li>
            <li>Background sync with temp ID substitution and entity chaining</li>
            <li>Failed mutation UI: red chip in toolbar, retry/discard per item</li>
            <li>Job cards: Kanban board with battery/user/PUE links, drag between columns</li>
            <li>Webhook logs page for superadmins</li>
            <li>GZip compression, stale-while-revalidate caching</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.1 — Battery rentals, PUE rentals, analytics"
        subtitle="January 2026"
        icon="battery_charging_full"
        color="green"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>Battery rental lifecycle: create, return, payment, recharge tracking</li>
            <li>PUE (Productive Use Equipment) rentals with pay-to-own option</li>
            <li>Cost structures: flexible pricing components (per day, per recharge, deposit, etc.)</li>
            <li>Analytics: hub summary, power usage, battery performance, revenue</li>
            <li>Multi-hub support for superadmins</li>
            <li>QR code scanning for batteries and users</li>
          </ul>
        </div>
      </q-timeline-entry>

      <q-timeline-entry
        title="v1.0 — Initial deployment"
        subtitle="December 2025"
        icon="rocket_launch"
        color="grey"
      >
        <div class="text-body2">
          <ul class="q-pl-md q-my-xs">
            <li>User management, battery inventory, hub management</li>
            <li>Authentication with JWT, role-based access (superadmin, hub_admin, data_admin, user)</li>
            <li>Signup survey and user registration flow</li>
            <li>Panel dashboard for field operators</li>
            <li>DigitalOcean Docker deployment with nginx, SSL, automated migrations</li>
          </ul>
        </div>
      </q-timeline-entry>

    </q-timeline>
  </q-page>
</template>

<script setup>
// Static release info page — update entries above when shipping new versions
</script>
