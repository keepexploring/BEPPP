<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-sm q-gutter-sm">
      <div class="text-h5">Data</div>
      <q-space />
      <div v-if="authStore.isSuperAdmin" class="row items-center q-gutter-sm">
        <q-icon name="warning" color="orange" size="sm" v-if="selectedHub === null" />
        <HubFilter
          v-model="selectedHub"
          @change="onHubChange"
          style="min-width: 220px"
          :class="selectedHub === null ? 'hub-filter-highlight' : ''"
        />
      </div>
    </div>

    <q-tabs
      v-model="activeTab"
      dense
      align="left"
      class="text-grey-7"
      active-color="primary"
      indicator-color="primary"
    >
      <q-tab name="rental-history" icon="history" label="Rental History" />
      <q-tab name="power-usage" icon="bolt" label="Power Usage" />
      <q-tab name="report" icon="summarize" label="Report Builder" />
      <q-tab name="telemetry" icon="timeline" label="Telemetry" />
      <q-tab name="gps-track" icon="route" label="GPS Track" />
    </q-tabs>

    <q-separator class="q-mb-md" />

    <q-tab-panels v-model="activeTab" animated keep-alive>

      <!-- ===================== RENTAL HISTORY ===================== -->
      <q-tab-panel name="rental-history" class="q-pa-none">
        <div class="row q-col-gutter-sm q-mb-md items-end">
          <div class="col-12 col-sm-3">
            <q-select
              v-model="rh.batteryId"
              :options="batteryOptions"
              option-value="value"
              option-label="label"
              emit-value
              map-options
              label="Battery (all if empty)"
              outlined
              dense
              clearable
            />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="rh.startDate" type="date" label="From" outlined dense />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="rh.endDate" type="date" label="To" outlined dense />
          </div>
          <div class="col-12 col-sm-2">
            <q-select
              v-model="rh.groupBy"
              :options="groupByOptions"
              label="Group by"
              outlined
              dense
              emit-value
              map-options
            />
          </div>
          <div class="col-auto">
            <q-btn label="Apply" icon="refresh" color="primary" dense @click="loadRentalHistory" :loading="rh.loading" />
          </div>
          <div class="col-auto">
            <q-btn label="CSV" icon="download" outline color="primary" dense @click="downloadRentalHistoryCSV" :disable="!rh.rentals.length" />
          </div>
        </div>

        <div v-if="rh.stats.total > 0" class="row q-col-gutter-sm q-mb-md">
          <div class="col-6 col-sm-3">
            <q-card flat bordered>
              <q-card-section class="text-center q-pa-sm">
                <div class="text-h6">{{ rh.stats.total }}</div>
                <div class="text-caption text-grey-6">Total Rentals</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-6 col-sm-3">
            <q-card flat bordered>
              <q-card-section class="text-center q-pa-sm">
                <div class="text-h6">{{ rh.stats.mean }}h</div>
                <div class="text-caption text-grey-6">Mean Duration</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-6 col-sm-3">
            <q-card flat bordered>
              <q-card-section class="text-center q-pa-sm">
                <div class="text-h6">{{ rh.stats.median }}h</div>
                <div class="text-caption text-grey-6">Median Duration</div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-6 col-sm-3">
            <q-card flat bordered>
              <q-card-section class="text-center q-pa-sm">
                <div class="text-h6">{{ rh.stats.stdDev }}h</div>
                <div class="text-caption text-grey-6">Std Dev</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <q-card flat bordered class="q-mb-md" v-if="rh.chartData">
          <q-card-section>
            <div style="height: 260px">
              <Bar :data="rh.chartData" :options="rhChartOptions" />
            </div>
          </q-card-section>
        </q-card>

        <q-table
          :rows="rh.rentals"
          :columns="rhColumns"
          row-key="rental_id"
          :loading="rh.loading"
          :pagination="{ rowsPerPage: 15 }"
          flat
          bordered
          dense
          no-data-label="Apply filters above to load rental history"
        />
      </q-tab-panel>

      <!-- ===================== POWER USAGE ===================== -->
      <q-tab-panel name="power-usage" class="q-pa-none">
        <div v-if="!canAccessAnalytics">
          <q-banner class="bg-orange text-white" rounded>
            <template v-slot:avatar><q-icon name="lock" /></template>
            Power analytics requires Admin or Data Admin access.
          </q-banner>
        </div>

        <div v-else>
          <!-- Group-by toggle -->
          <div class="row q-col-gutter-sm q-mb-sm items-center">
            <div class="col-auto">
              <div class="text-caption text-grey-7 q-mb-xs">Group by</div>
              <q-btn-toggle
                v-model="pu.groupBy"
                :options="[
                  { label: 'Battery selection', value: 'battery' },
                  { label: 'PUE type rented', value: 'pue_type' }
                ]"
                dense
                unelevated
                toggle-color="primary"
                color="grey-3"
                text-color="grey-8"
              />
            </div>
          </div>

          <div class="row q-col-gutter-sm q-mb-md items-end">
            <!-- Battery selection (battery mode) -->
            <div v-if="pu.groupBy === 'battery'" class="col-12 col-sm-4">
              <q-select
                v-model="pu.batteryIds"
                :options="batteryOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                label="Batteries (empty = all)"
                outlined
                dense
                multiple
                use-chips
              />
            </div>
            <!-- PUE type selection (pue_type mode) -->
            <div v-else class="col-12 col-sm-4">
              <q-select
                v-model="pu.pueTypeIds"
                :options="pueTypeOptions"
                option-value="value"
                option-label="label"
                emit-value
                map-options
                label="PUE types (empty = all)"
                outlined
                dense
                multiple
                use-chips
              />
            </div>
            <div class="col-6 col-sm-2">
              <q-input v-model="pu.startDate" type="date" label="From" outlined dense />
            </div>
            <div class="col-6 col-sm-2">
              <q-input v-model="pu.endDate" type="date" label="To" outlined dense />
            </div>
            <div class="col-12 col-sm-2">
              <q-select
                v-model="pu.aggPeriod"
                :options="aggPeriodOptions"
                label="Bucket"
                outlined
                dense
                emit-value
                map-options
              />
            </div>
            <div class="col-auto">
              <q-btn label="Apply" icon="refresh" color="primary" dense @click="loadPowerUsage" :loading="pu.loading" />
            </div>
            <div class="col-auto">
              <q-btn label="CSV" icon="download" outline color="primary" dense @click="downloadPowerCSV"
                :disable="!pu.rawStatsData && !pu.rawPueData" />
            </div>
          </div>

          <!-- Battery mode charts -->
          <template v-if="pu.groupBy === 'battery'">
            <q-card flat bordered class="q-mb-sm">
              <q-card-section>
                <div class="q-mb-sm">
                  <div class="row items-center q-gutter-sm flex-wrap">
                    <div class="text-caption text-grey-6">Bars:</div>
                    <q-checkbox dense v-model="pu.series.meanIn" label="Mean In (W)" color="green-8" size="sm" />
                    <q-checkbox dense v-model="pu.series.meanOut" label="Mean Out (W)" color="red-8" size="sm" />
                    <q-checkbox dense v-model="pu.series.kwhIn" label="Total kWh In" color="green-5" size="sm" />
                    <q-checkbox dense v-model="pu.series.kwhOut" label="Total kWh Out" color="red-5" size="sm" />
                    <q-separator vertical style="height:18px" />
                    <div class="text-caption text-grey-6">Overlays (when mean shown):</div>
                    <q-checkbox dense v-model="pu.series.medianIn" label="Median In" color="teal" size="sm" :disable="!pu.series.meanIn" />
                    <q-checkbox dense v-model="pu.series.stdIn" label="±Std In" color="green-7" size="sm" :disable="!pu.series.meanIn" />
                    <q-checkbox dense v-model="pu.series.medianOut" label="Median Out" color="orange-9" size="sm" :disable="!pu.series.meanOut" />
                    <q-checkbox dense v-model="pu.series.stdOut" label="±Std Out" color="red-7" size="sm" :disable="!pu.series.meanOut" />
                  </div>
                </div>
                <div style="height: 280px">
                  <Bar v-if="pu.powerChartData" :data="pu.powerChartData" :options="puPowerChartOptions" />
                  <div v-else class="flex flex-center full-height text-grey-5">Apply filters to load data</div>
                </div>
              </q-card-section>
            </q-card>
            <q-card flat bordered>
              <q-card-section>
                <div class="text-subtitle2 text-grey-7 q-mb-xs">State of Charge (%)</div>
                <div style="height: 180px">
                  <Line v-if="pu.socChartData" :data="pu.socChartData" :options="puSocChartOptions" />
                  <div v-else class="flex flex-center full-height text-grey-5">Apply filters to load data</div>
                </div>
              </q-card-section>
            </q-card>
          </template>

          <!-- PUE type mode chart -->
          <template v-else>
            <q-card flat bordered class="q-mb-sm">
              <q-card-section>
                <div class="q-mb-sm">
                  <div class="row items-center q-gutter-sm flex-wrap">
                    <div class="text-caption text-grey-6">Bars:</div>
                    <q-checkbox dense v-model="pu.series.meanOut" label="Mean Consumed (W)" color="red-8" size="sm" />
                    <q-checkbox dense v-model="pu.series.kwhOut" label="Total kWh Consumed" color="red-5" size="sm" />
                    <q-separator vertical style="height:18px" />
                    <div class="text-caption text-grey-6">Overlays:</div>
                    <q-checkbox dense v-model="pu.series.medianOut" label="Median" color="orange-9" size="sm" :disable="!pu.series.meanOut" />
                    <q-checkbox dense v-model="pu.series.stdOut" label="±Std Dev" color="red-7" size="sm" :disable="!pu.series.meanOut" />
                  </div>
                  <div class="text-caption text-grey-5 q-mt-xs">
                    <q-icon name="info" size="xs" class="q-mr-xs" />
                    Power data is aggregated per PUE type based on battery usage recorded at rental time.
                  </div>
                </div>
                <div style="height: 300px">
                  <Bar v-if="pu.pueTypeChartData" :data="pu.pueTypeChartData" :options="puePowerChartOptions" />
                  <div v-else class="flex flex-center full-height text-grey-5">Apply filters to load data</div>
                </div>
              </q-card-section>
            </q-card>
            <div v-if="pu.pueTypeSummary.length" class="row q-col-gutter-sm q-mt-xs">
              <div v-for="s in pu.pueTypeSummary" :key="s.name" class="col-6 col-sm-3">
                <q-card flat bordered>
                  <q-card-section class="text-center q-pa-sm">
                    <div class="text-h6">{{ s.avgPower }}W</div>
                    <div class="text-caption text-grey-6">{{ s.name }}</div>
                    <div class="text-caption text-grey-5">avg consumed · {{ s.dataPoints }} pts</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </template>
        </div>
      </q-tab-panel>

      <!-- ===================== REPORT BUILDER ===================== -->
      <q-tab-panel name="report" class="q-pa-none">
        <!-- Controls -->
        <div class="row q-col-gutter-sm q-mb-md items-end">
          <div class="col-12 col-sm-3">
            <q-select
              v-model="rb.userId"
              :options="userOptions"
              option-value="value"
              option-label="label"
              emit-value
              map-options
              label="User"
              outlined
              dense
            />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="rb.startDate" type="date" label="From" outlined dense />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="rb.endDate" type="date" label="To" outlined dense />
          </div>
          <div class="col-auto">
            <q-btn-toggle
              v-model="rb.statMode"
              :options="[{ label: 'Mean', value: 'mean' }, { label: 'Median', value: 'median' }]"
              dense
              rounded
              outline
              color="primary"
              size="sm"
            />
          </div>
          <div class="col-auto">
            <q-btn label="Generate" icon="summarize" color="primary" dense @click="loadReport" :loading="rb.loading" :disable="!rb.userId" />
          </div>
          <div class="col-auto" v-if="rb.daily.length">
            <q-btn label="Daily CSV" icon="download" outline color="primary" dense @click="downloadReportCSV" />
          </div>
          <div class="col-auto" v-if="rb.rentals.length">
            <q-btn label="Rentals CSV" icon="download" outline color="grey-7" dense @click="downloadRentalsCSV" />
          </div>
        </div>

        <!-- Summary cards -->
        <div v-if="rb.stats" class="q-mb-md">
          <div class="text-subtitle2 text-grey-7 q-mb-sm">Summary ({{ rb.statMode === 'mean' ? 'Mean' : 'Median' }})</div>
          <div class="row q-col-gutter-sm">
            <div class="col-6 col-sm-2">
              <q-card flat bordered>
                <q-card-section class="text-center q-pa-sm">
                  <div class="text-h6">{{ rb.stats.total_rentals }}</div>
                  <div class="text-caption text-grey-6">Total Rentals</div>
                  <q-tooltip>Total number of battery rentals by this user in the selected period.</q-tooltip>
                </q-card-section>
              </q-card>
            </div>
            <div class="col-6 col-sm-2">
              <q-card flat bordered>
                <q-card-section class="text-center q-pa-sm">
                  <div class="text-h6">{{ rb.stats.days_used }} <span class="text-caption text-grey-5">/ {{ rb.stats.period_days }}d</span></div>
                  <div class="text-caption text-grey-6">Days with Rentals</div>
                  <q-tooltip>Number of distinct days the user had at least one rental, out of the total days in the selected period.</q-tooltip>
                </q-card-section>
              </q-card>
            </div>
            <div class="col-6 col-sm-2">
              <q-card flat bordered>
                <q-card-section class="text-center q-pa-sm">
                  <div class="text-h6">{{ rb.statMode === 'mean' ? rb.stats.uses_per_active_day_mean : rb.stats.uses_per_active_day_median }}</div>
                  <div class="text-caption text-grey-6">Rentals / Active Day</div>
                  <div class="text-caption text-grey-5">SD {{ rb.stats.uses_per_active_day_sd ?? '—' }}</div>
                  <q-tooltip>{{ rb.statMode === 'mean' ? 'Mean' : 'Median' }} number of rentals per day, counting only days where at least one rental occurred. SD = standard deviation.</q-tooltip>
                </q-card-section>
              </q-card>
            </div>
            <div class="col-6 col-sm-2">
              <q-card flat bordered>
                <q-card-section class="text-center q-pa-sm">
                  <div class="text-h6">{{ rb.statMode === 'mean' ? rb.stats.duration_mean_h : rb.stats.duration_median_h }}h</div>
                  <div class="text-caption text-grey-6">Avg Rental Duration</div>
                  <div class="text-caption text-grey-5">SD {{ rb.stats.duration_sd_h ?? '—' }}h</div>
                  <q-tooltip>{{ rb.statMode === 'mean' ? 'Mean' : 'Median' }} duration of each rental from checkout to return (in hours). A 1-day rental = ~24h. SD = standard deviation of durations.</q-tooltip>
                </q-card-section>
              </q-card>
            </div>
            <div class="col-6 col-sm-2" v-if="rb.stats.power_mean_w != null">
              <q-card flat bordered>
                <q-card-section class="text-center q-pa-sm">
                  <div class="text-h6">{{ rb.statMode === 'mean' ? rb.stats.power_mean_w : rb.stats.power_median_w }}W</div>
                  <div class="text-caption text-grey-6">Avg Discharge Power</div>
                  <q-tooltip>{{ rb.statMode === 'mean' ? 'Mean' : 'Median' }} discharge power (W) during active rental periods. Charging periods are excluded. Requires telemetry data from the battery.</q-tooltip>
                </q-card-section>
              </q-card>
            </div>
            <div class="col-6 col-sm-2" v-if="rb.stats.wh_per_day_mean != null">
              <q-card flat bordered>
                <q-card-section class="text-center q-pa-sm">
                  <div class="text-h6">{{ rb.statMode === 'mean' ? rb.stats.wh_per_day_mean : rb.stats.wh_per_day_median }}Wh</div>
                  <div class="text-caption text-grey-6">Avg Wh / Active Day</div>
                  <q-tooltip>{{ rb.statMode === 'mean' ? 'Mean' : 'Median' }} energy discharged (Wh) per day, counting only days with rentals. Requires telemetry data.</q-tooltip>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </div>

        <!-- Power timeline chart -->
        <q-card v-if="rbPowerChart" flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-subtitle2 text-grey-7 q-mb-xs">Power Usage Over Time (W)</div>
            <div style="height: 220px">
              <Line :data="rbPowerChart" :options="rbPowerChartOptions" />
            </div>
          </q-card-section>
        </q-card>

        <!-- Daily breakdown table -->
        <div v-if="rb.daily.length" class="q-mb-md">
          <div class="text-subtitle2 text-grey-7 q-mb-sm">Daily Breakdown</div>
          <q-table
            :rows="rb.daily"
            :columns="rbDailyColumns"
            row-key="date"
            :pagination="{ rowsPerPage: 0 }"
            flat
            bordered
            dense
            hide-bottom
          >
            <template v-slot:body="props">
              <q-tr :props="props">
                <q-td key="date" :props="props">
                  <strong>{{ new Date(props.row.date + 'T12:00:00').toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }) }}</strong>
                </q-td>
                <q-td key="uses" :props="props" class="text-center">{{ props.row.uses }}</q-td>
                <q-td key="total_duration_h" :props="props" class="text-right">{{ props.row.total_duration_h }}</q-td>
                <q-td key="total_wh" :props="props" class="text-right">{{ props.row.total_wh != null ? props.row.total_wh.toFixed(1) : '—' }}</q-td>
                <q-td key="power_max_w" :props="props" class="text-right">{{ props.row.power_max_w != null ? props.row.power_max_w.toFixed(1) : '—' }}</q-td>
                <q-td key="power_min_w" :props="props" class="text-right">{{ props.row.power_min_w != null ? props.row.power_min_w.toFixed(1) : '—' }}</q-td>
                <q-td key="power_mean_w" :props="props" class="text-right">{{ props.row.power_mean_w != null ? props.row.power_mean_w.toFixed(1) : '—' }}</q-td>
                <q-td key="power_sd_w" :props="props" class="text-right">{{ props.row.power_sd_w != null ? props.row.power_sd_w.toFixed(1) : '—' }}</q-td>
              </q-tr>
              <q-tr v-for="rental in props.row.rentals" :key="rental.rental_id" :props="props" class="bg-grey-1">
                <q-td colspan="2" class="text-caption text-grey-7 q-pl-lg">
                  <q-icon name="battery_charging_full" size="xs" class="q-mr-xs" />
                  {{ rental.battery_id }} —
                  {{ rental.start ? new Date(rental.start).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '' }}
                  → {{ rental.end ? new Date(rental.end).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Active' }}
                </q-td>
                <q-td class="text-right text-caption text-grey-7">{{ rental.duration_h != null ? rental.duration_h + 'h' : '—' }}</q-td>
                <q-td colspan="5" class="text-caption text-grey-5">{{ rental.status }}</q-td>
              </q-tr>
            </template>
          </q-table>
        </div>

        <!-- Rentals table -->
        <div v-if="rb.rentals.length">
          <div class="text-subtitle2 text-grey-7 q-mb-sm">All Rentals in Period</div>
          <q-table
            :rows="rb.rentals"
            :columns="rbColumns"
            row-key="rental_id"
            :loading="rb.loading"
            :pagination="{ rowsPerPage: 10 }"
            flat
            bordered
            dense
            no-data-label="Select a user and click Generate"
          />
        </div>

        <div v-else-if="!rb.loading" class="text-center text-grey-5 q-py-xl">
          Select a user and date range, then click Generate
        </div>
      </q-tab-panel>

      <!-- ===================== TELEMETRY ===================== -->
      <q-tab-panel name="telemetry" class="q-pa-none">
        <div class="row q-col-gutter-sm q-mb-md items-end">
          <div class="col-12 col-sm-3">
            <q-select
              v-model="tel.batteryId"
              :options="batteryOptions"
              option-value="value"
              option-label="label"
              emit-value
              map-options
              label="Battery"
              outlined
              dense
            />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="tel.startDate" type="date" label="From" outlined dense />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="tel.endDate" type="date" label="To" outlined dense />
          </div>
          <div class="col-auto">
            <q-btn
              label="Load"
              icon="download"
              color="primary"
              dense
              @click="loadTelemetry"
              :loading="tel.loading"
              :disable="!tel.batteryId"
            />
          </div>
          <div class="col-auto" v-if="tel.data.length">
            <q-btn label="CSV" icon="download" outline color="primary" dense @click="downloadTelemetryCSV" />
          </div>
        </div>

        <div v-if="tel.data.length">
          <div class="text-caption text-grey-6 q-mb-sm">{{ tel.data.length }} data points</div>

          <q-card flat bordered class="q-mb-sm">
            <q-card-section>
              <div class="text-subtitle2 text-grey-7 q-mb-xs">State of Charge (%)</div>
              <div style="height: 180px">
                <Line :data="telSocChart" :options="telLineOptions(0, 100, '%')" />
              </div>
            </q-card-section>
          </q-card>

          <q-card flat bordered class="q-mb-sm">
            <q-card-section>
              <div class="text-subtitle2 text-grey-7 q-mb-xs">Voltage (V)</div>
              <div style="height: 180px">
                <Line :data="telVoltageChart" :options="telLineOptions(null, null, 'V')" />
              </div>
            </q-card-section>
          </q-card>

          <q-card flat bordered class="q-mb-sm">
            <q-card-section>
              <div class="text-subtitle2 text-grey-7 q-mb-xs">Current (A) — positive = charging</div>
              <div style="height: 180px">
                <Line :data="telCurrentChart" :options="telCurrentOptions" />
              </div>
            </q-card-section>
          </q-card>

          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle2 text-grey-7 q-mb-xs">Temperature (°C)</div>
              <div style="height: 180px">
                <Line :data="telTempChart" :options="telLineOptions(null, null, '°C')" />
              </div>
            </q-card-section>
          </q-card>
        </div>

        <div v-else-if="!tel.loading" class="text-center text-grey-5 q-py-xl">
          Select a battery and date range, then click Load
        </div>
      </q-tab-panel>

      <!-- ===================== GPS TRACK ===================== -->
      <q-tab-panel name="gps-track" class="q-pa-none">
        <div class="row q-col-gutter-sm q-mb-md items-end">
          <div class="col-12 col-sm-3">
            <q-select
              v-model="gps.batteryId"
              :options="batteryOptions"
              option-value="value"
              option-label="label"
              emit-value
              map-options
              label="Battery"
              outlined
              dense
            />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="gps.startDate" type="date" label="From" outlined dense />
          </div>
          <div class="col-6 col-sm-2">
            <q-input v-model="gps.endDate" type="date" label="To" outlined dense />
          </div>
          <div class="col-auto">
            <q-btn
              label="Load"
              icon="route"
              color="primary"
              dense
              @click="loadGpsTrack"
              :loading="gps.loading"
              :disable="!gps.batteryId"
            />
          </div>
          <div class="col-auto" v-if="gps.points.length">
            <q-chip dense color="blue-1" text-color="blue-9">
              {{ gps.points.length }} GPS points
            </q-chip>
          </div>
          <div class="col-auto" v-if="gps.points.length">
            <q-toggle v-model="gps_heatmap" label="Heatmap" dense />
          </div>
          <div class="col-auto" v-if="gps.points.length">
            <q-btn label="CSV" icon="download" outline color="primary" dense @click="downloadGpsCSV" />
          </div>
        </div>

        <div v-if="gps.points.length">
          <!-- Time slider -->
          <div class="row items-center q-col-gutter-sm q-mb-sm">
            <div class="col-auto">
              <q-btn
                :icon="gps.playing ? 'pause' : 'play_arrow'"
                round
                flat
                dense
                color="primary"
                @click="toggleGpsPlayback"
              />
            </div>
            <div class="col">
              <q-slider
                v-model="gps.sliderIndex"
                :min="0"
                :max="gps.points.length - 1"
                :step="1"
                color="primary"
                label
                :label-value="gpsCurrentPoint ? new Date(gpsCurrentPoint.timestamp).toLocaleString() : ''"
              />
            </div>
          </div>

          <!-- Current point info -->
          <div v-if="gpsCurrentPoint" class="row q-col-gutter-sm q-mb-sm">
            <div class="col-auto">
              <q-chip dense icon="schedule" color="grey-2">
                {{ new Date(gpsCurrentPoint.timestamp).toLocaleString() }}
              </q-chip>
            </div>
            <div class="col-auto">
              <q-chip dense icon="battery_charging_full" color="green-1" text-color="green-9">
                {{ gpsCurrentPoint.state_of_charge }}% SoC
              </q-chip>
            </div>
            <div class="col-auto">
              <q-chip dense icon="location_on" color="blue-1" text-color="blue-9">
                {{ gpsCurrentPoint.latitude?.toFixed(5) }}, {{ gpsCurrentPoint.longitude?.toFixed(5) }}
              </q-chip>
            </div>
            <div v-if="gpsCurrentPoint.altitude" class="col-auto">
              <q-chip dense icon="terrain" color="grey-2">
                {{ gpsCurrentPoint.altitude?.toFixed(0) }}m
              </q-chip>
            </div>
          </div>

          <!-- Map -->
          <div
            id="gps-map"
            style="height: 420px; border-radius: 8px; border: 1px solid #e0e0e0;"
          />
        </div>

        <div v-else-if="!gps.loading" class="text-center text-grey-5 q-py-xl">
          Select a battery and date range, then click Load. GPS data is only available for batteries with location tracking.
        </div>
      </q-tab-panel>

    </q-tab-panels>
  </q-page>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import api, { batteriesAPI, batteryRentalsAPI, hubsAPI, settingsAPI, dataAPI, analyticsAPI, usersAPI } from 'src/services/api.js'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'
import HubFilter from 'src/components/HubFilter.vue'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler)

const authStore = useAuthStore()
const hubSettingsStore = useHubSettingsStore()
const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol || '$')

// Hub selection — superadmins can switch, others locked to their hub
const selectedHub = ref(authStore.isSuperAdmin ? null : (authStore.user?.hub_id || null))
const canAccessAnalytics = computed(() =>
  ['ADMIN', 'SUPERADMIN', 'DATA_ADMIN'].includes((authStore.role || '').toUpperCase())
)

const batteries = ref([])
const users = ref([])
const pueTypes = ref([])
const activeTab = ref('rental-history')

const batteryOptions = computed(() =>
  batteries.value.map(b => ({
    value: b.battery_id,
    label: b.short_id ? `${b.battery_id} (${b.short_id})` : b.battery_id
  }))
)

const userOptions = computed(() => [
  { value: null, label: 'All Users' },
  ...users.value.map(u => ({ value: u.user_id, label: u.Name || u.username }))
])

const pueTypeOptions = computed(() =>
  pueTypes.value.map(t => ({ value: t.type_id, label: t.type_name }))
)

const groupByOptions = [
  { value: 'day', label: 'Day' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' }
]

const aggPeriodOptions = [
  { value: 'hour', label: 'Hour' },
  { value: 'day', label: 'Day' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' }
]

function defaultRange() {
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - 30)
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10)
  }
}

// ===================== RENTAL HISTORY =====================

const rh = ref({
  batteryId: null,
  startDate: defaultRange().start,
  endDate: defaultRange().end,
  groupBy: 'day',
  loading: false,
  rentals: [],
  stats: { total: 0 },
  chartData: null
})

const rhColumns = [
  { name: 'rental_id', label: 'ID', field: 'rental_id', align: 'left', sortable: true },
  { name: 'battery_id', label: 'Battery', field: 'battery_id', align: 'left' },
  { name: 'user_name', label: 'User', field: 'user_name', align: 'left' },
  {
    name: 'rental_start_date',
    label: 'Start',
    field: 'rental_start_date',
    align: 'left',
    format: v => v ? new Date(v).toLocaleString() : '-',
    sortable: true
  },
  {
    name: 'actual_return_date',
    label: 'Returned',
    field: 'actual_return_date',
    align: 'left',
    format: v => v ? new Date(v).toLocaleString() : 'Active'
  },
  { name: 'duration', label: 'Duration (h)', field: 'duration', align: 'right', sortable: true },
  { name: 'rental_status', label: 'Status', field: 'rental_status', align: 'left' }
]

const rhChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 20 } },
    y: { beginAtZero: true, title: { display: true, text: 'Rentals' } }
  }
}

function getRentalDuration(rental) {
  const start = new Date(rental.rental_start_date)
  const endStr = rental.actual_return_date || rental.rental_end_date
  if (!endStr) return null
  return Math.round(((new Date(endStr) - start) / 3600000) * 10) / 10
}

function getGroupKey(dateStr, groupBy) {
  const d = new Date(dateStr)
  if (groupBy === 'month') {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  }
  if (groupBy === 'week') {
    const day = d.getDay() || 7
    d.setDate(d.getDate() - day + 1)
    return d.toISOString().slice(0, 10)
  }
  return d.toISOString().slice(0, 10)
}

function calcStats(durations, total) {
  if (!durations.length) return { total, mean: '-', median: '-', stdDev: '-' }
  const sorted = [...durations].sort((a, b) => a - b)
  const mean = durations.reduce((a, b) => a + b, 0) / durations.length
  const mid = Math.floor(sorted.length / 2)
  const median = sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
  const stdDev = Math.sqrt(durations.reduce((acc, v) => acc + (v - mean) ** 2, 0) / durations.length)
  return {
    total,
    mean: Math.round(mean * 10) / 10,
    median: Math.round(median * 10) / 10,
    stdDev: Math.round(stdDev * 10) / 10
  }
}

async function loadRentalHistory() {
  rh.value.loading = true
  try {
    const params = {}
    if (rh.value.batteryId) params.battery_id = rh.value.batteryId
    if (selectedHub.value) params.hub_id = selectedHub.value
    const res = await batteryRentalsAPI.list(params)
    let data = Array.isArray(res.data) ? res.data : Array.isArray(res) ? res : []

    const start = new Date(rh.value.startDate)
    const end = new Date(rh.value.endDate + 'T23:59:59')
    data = data.filter(r => {
      const d = new Date(r.rental_start_date)
      return d >= start && d <= end
    })

    data = data.map(r => ({ ...r, duration: getRentalDuration(r) }))
    rh.value.rentals = data

    const durations = data.map(r => r.duration).filter(d => d !== null)
    rh.value.stats = calcStats(durations, data.length)

    const groups = {}
    for (const r of data) {
      const key = getGroupKey(r.rental_start_date, rh.value.groupBy)
      groups[key] = (groups[key] || 0) + 1
    }
    const labels = Object.keys(groups).sort()
    rh.value.chartData = {
      labels,
      datasets: [{
        label: 'Rentals',
        data: labels.map(l => groups[l]),
        backgroundColor: 'rgba(33, 150, 243, 0.7)',
        borderRadius: 4
      }]
    }
  } finally {
    rh.value.loading = false
  }
}

function downloadRentalHistoryCSV() {
  const headers = ['rental_id', 'battery_id', 'user_name', 'rental_start_date', 'actual_return_date', 'duration_hours', 'status']
  const rows = rh.value.rentals.map(r => [
    r.rental_id, r.battery_id, r.user_name || '', r.rental_start_date,
    r.actual_return_date || '', r.duration ?? '', r.rental_status
  ])
  downloadCSV([headers, ...rows], 'rental_history.csv')
}

function downloadPowerCSV() {
  if (pu.value.groupBy === 'battery' && pu.value.rawStatsData) {
    const headers = ['time_group', 'in_mean_w', 'in_median_w', 'in_std_w', 'in_count', 'out_mean_w', 'out_median_w', 'out_std_w', 'out_count']
    const rows = pu.value.rawStatsData.map(r => [
      r.time_group, r.in_mean ?? '', r.in_median ?? '', r.in_std ?? '', r.in_count ?? '',
      r.out_mean ?? '', r.out_median ?? '', r.out_std ?? '', r.out_count ?? ''
    ])
    downloadCSV([headers, ...rows], 'power_usage.csv')
  } else if (pu.value.groupBy === 'pue_type' && pu.value.rawPueData) {
    const { rows, allTypes } = pu.value.rawPueData
    const headers = ['time_group', ...allTypes.flatMap(t => [`${t}_out_mean_w`, `${t}_out_kwh`])]
    const csvRows = rows.map(r => [r.time_group, ...allTypes.flatMap(t => [r[`${t}_out_mean`] ?? '', r[`${t}_out_kwh`] ?? ''])])
    downloadCSV([headers, ...csvRows], 'pue_power_usage.csv')
  }
}

// ===================== POWER USAGE =====================

const pu = ref({
  groupBy: 'battery',       // 'battery' | 'pue_type'
  batteryIds: [],
  pueTypeIds: [],
  startDate: defaultRange().start,
  endDate: defaultRange().end,
  aggPeriod: 'day',
  loading: false,
  powerChartData: null,
  socChartData: null,
  pueTypeChartData: null,
  pueTypeSummary: [],
  rawStatsData: null,       // cached battery split_stats rows for reactive rebuild
  rawPueData: null,         // cached { rows, allTypes } for reactive PUE rebuild
  series: {
    meanIn: true,
    meanOut: true,
    kwhIn: false,
    kwhOut: false,
    stdIn: false,
    medianIn: false,
    stdOut: false,
    medianOut: false,
  }
})

const PERIOD_HOURS = { hour: 1, day: 24, week: 168, month: 730 }

const puPowerChartOptions = computed(() => {
  const s = pu.value.series
  const hasW = s.meanIn || s.meanOut || s.medianIn || s.medianOut || s.stdIn || s.stdOut
  const hasKwh = s.kwhIn || s.kwhOut
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      tooltip: {
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y
            if (ctx.dataset.yAxisID === 'y1') return `${ctx.dataset.label}: ${Math.abs(v)?.toFixed(3)} kWh`
            return `${ctx.dataset.label}: ${v?.toFixed(1)} W`
          }
        }
      }
    },
    scales: {
      x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 20 } },
      y: { display: hasW, position: 'left', title: { display: true, text: 'Power (W)' } },
      y1: { display: hasKwh, position: 'right', title: { display: true, text: 'Energy (kWh)' }, grid: { drawOnChartArea: false } }
    }
  }
})

const puSocChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 20 } },
    y: { min: 0, max: 100, title: { display: true, text: 'SoC (%)' } }
  }
}

// Colour palette for PUE types
const PUE_COLOURS = [
  'rgba(33,150,243,0.75)', 'rgba(76,175,80,0.75)', 'rgba(255,152,0,0.75)',
  'rgba(156,39,176,0.75)', 'rgba(244,67,54,0.75)', 'rgba(0,188,212,0.75)',
  'rgba(255,193,7,0.75)',  'rgba(63,81,181,0.75)',
]

const puePowerChartOptions = computed(() => {
  const s = pu.value.series
  const hasKwh = s.kwhOut
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      tooltip: {
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y
            if (ctx.dataset.yAxisID === 'y1') return `${ctx.dataset.label}: ${Math.abs(v)?.toFixed(3)} kWh`
            return `${ctx.dataset.label}: ${Math.abs(v)?.toFixed(1)} W`
          }
        }
      }
    },
    scales: {
      x: { stacked: false, ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 20 } },
      y: { display: true, position: 'left', title: { display: true, text: 'Power (W)' }, ticks: { callback: v => Math.abs(v) } },
      y1: { display: hasKwh, position: 'right', title: { display: true, text: 'Energy (kWh)' }, grid: { drawOnChartArea: false }, ticks: { callback: v => Math.abs(v) } }
    }
  }
})

function pivotByTime(data, metric, aggFn) {
  const byTime = {}
  for (const row of data) {
    if (!byTime[row.time_group]) byTime[row.time_group] = []
    byTime[row.time_group].push(row[metric])
  }
  const labels = Object.keys(byTime).sort()
  const values = labels.map(t => {
    const arr = byTime[t]
    return aggFn === 'sum'
      ? arr.reduce((a, b) => a + b, 0)
      : arr.reduce((a, b) => a + b, 0) / arr.length
  })
  return { labels, values }
}

function fmtTimeLabel(t, period) {
  const d = new Date(t)
  if (isNaN(d)) return t
  if (period === 'hour') return d.toLocaleString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  if (period === 'month') return d.toLocaleString([], { month: 'short', year: 'numeric' })
  return d.toLocaleString([], { month: 'short', day: '2-digit' })
}

async function loadPowerUsage() {
  pu.value.loading = true
  try {
    if (pu.value.groupBy === 'pue_type') {
      await loadPowerByPUEType()
    } else {
      await loadPowerByBattery()
    }
  } finally {
    pu.value.loading = false
  }
}

async function loadPowerByBattery() {
  const batterySelection = pu.value.batteryIds.length
    ? { battery_ids: pu.value.batteryIds }
    : { all_batteries: true, ...(selectedHub.value ? { hub_ids: [selectedHub.value] } : {}) }

  const baseReq = {
    battery_selection: batterySelection,
    start_time: `${pu.value.startDate}T00:00:00`,
    end_time: `${pu.value.endDate}T23:59:59`,
    aggregation_period: pu.value.aggPeriod,
  }

  const [powerRes, socRes] = await Promise.all([
    analyticsAPI.powerUsage({ ...baseReq, metric: 'power_watts', aggregation_function: 'split_stats' }),
    analyticsAPI.powerUsage({ ...baseReq, metric: 'state_of_charge', aggregation_function: 'mean' })
  ])

  const rows = ((powerRes.data || powerRes).data) || []
  const socRows = ((socRes.data || socRes).data) || []
  const { labels: sLabels, values: sValues } = pivotByTime(socRows, 'state_of_charge', 'mean')

  pu.value.rawStatsData = rows.length ? rows : null

  buildPowerChart(rows)

  pu.value.socChartData = rows.length ? {
    labels: sLabels.map(t => fmtTimeLabel(t, pu.value.aggPeriod)),
    datasets: [{
      label: 'SoC %',
      data: sValues,
      borderColor: 'rgba(33, 150, 243, 0.9)',
      backgroundColor: 'rgba(33, 150, 243, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: sValues.length > 60 ? 0 : 3
    }]
  } : null
}

function buildPowerChart(rows) {
  if (!rows || !rows.length) { pu.value.powerChartData = null; return }

  const sorted = [...rows].sort((a, b) => a.time_group < b.time_group ? -1 : 1)
  const periodH = PERIOD_HOURS[pu.value.aggPeriod] || 24
  const labels = sorted.map(r => fmtTimeLabel(r.time_group, pu.value.aggPeriod))
  const s = pu.value.series
  const datasets = []

  // Std dev bands (line pairs with fill, drawn first so they render behind bars)
  if (s.stdIn && s.meanIn) {
    datasets.push({
      label: 'Std Dev In (upper)',
      type: 'line', yAxisID: 'y',
      data: sorted.map(r => r.in_mean != null ? +((r.in_mean) + (r.in_std || 0)).toFixed(1) : null),
      borderColor: 'transparent', backgroundColor: 'rgba(76,175,80,0.18)',
      borderWidth: 0, pointRadius: 0, fill: '+1', tension: 0.2,
    })
    datasets.push({
      label: 'Std Dev In (lower)',
      type: 'line', yAxisID: 'y',
      data: sorted.map(r => r.in_mean != null ? +((r.in_mean) - (r.in_std || 0)).toFixed(1) : null),
      borderColor: 'transparent', backgroundColor: 'transparent',
      borderWidth: 0, pointRadius: 0, fill: false, tension: 0.2,
    })
  }
  if (s.stdOut && s.meanOut) {
    datasets.push({
      label: 'Std Dev Out (upper)',
      type: 'line', yAxisID: 'y',
      data: sorted.map(r => r.out_mean != null ? +((r.out_mean) + (r.out_std || 0)).toFixed(1) : null),
      borderColor: 'transparent', backgroundColor: 'rgba(244,67,54,0.18)',
      borderWidth: 0, pointRadius: 0, fill: '+1', tension: 0.2,
    })
    datasets.push({
      label: 'Std Dev Out (lower)',
      type: 'line', yAxisID: 'y',
      data: sorted.map(r => r.out_mean != null ? +((r.out_mean) - (r.out_std || 0)).toFixed(1) : null),
      borderColor: 'transparent', backgroundColor: 'transparent',
      borderWidth: 0, pointRadius: 0, fill: false, tension: 0.2,
    })
  }

  // Mean power bars (W, left axis)
  if (s.meanIn) datasets.push({
    label: 'Mean In (W)', type: 'bar', yAxisID: 'y',
    data: sorted.map(r => r.in_mean != null ? +r.in_mean.toFixed(1) : 0),
    backgroundColor: 'rgba(76, 175, 80, 0.8)', borderRadius: 3,
  })
  if (s.meanOut) datasets.push({
    label: 'Mean Out (W)', type: 'bar', yAxisID: 'y',
    data: sorted.map(r => r.out_mean != null ? +r.out_mean.toFixed(1) : 0),
    backgroundColor: 'rgba(244, 67, 54, 0.8)', borderRadius: 3,
  })

  // Median lines
  if (s.medianIn && s.meanIn) datasets.push({
    label: 'Median In (W)', type: 'line', yAxisID: 'y',
    data: sorted.map(r => r.in_median != null ? +r.in_median.toFixed(1) : null),
    borderColor: 'rgba(0, 188, 140, 0.9)', backgroundColor: 'transparent',
    borderWidth: 2, borderDash: [6, 3], pointRadius: sorted.length > 60 ? 0 : 4,
    fill: false, tension: 0,
  })
  if (s.medianOut && s.meanOut) datasets.push({
    label: 'Median Out (W)', type: 'line', yAxisID: 'y',
    data: sorted.map(r => r.out_median != null ? +r.out_median.toFixed(1) : null),
    borderColor: 'rgba(255, 152, 0, 0.9)', backgroundColor: 'transparent',
    borderWidth: 2, borderDash: [6, 3], pointRadius: sorted.length > 60 ? 0 : 4,
    fill: false, tension: 0,
  })

  // Total kWh bars (right axis y1)
  if (s.kwhIn) datasets.push({
    label: 'Total In (kWh)', type: 'bar', yAxisID: 'y1',
    data: sorted.map(r => r.in_mean != null ? +(r.in_mean * periodH / 1000).toFixed(4) : 0),
    backgroundColor: 'rgba(76, 175, 80, 0.4)', borderColor: 'rgba(76, 175, 80, 0.7)',
    borderWidth: 1, borderRadius: 3,
  })
  if (s.kwhOut) datasets.push({
    label: 'Total Out (kWh)', type: 'bar', yAxisID: 'y1',
    data: sorted.map(r => r.out_mean != null ? +(r.out_mean * periodH / 1000).toFixed(4) : 0),
    backgroundColor: 'rgba(244, 67, 54, 0.4)', borderColor: 'rgba(244, 67, 54, 0.7)',
    borderWidth: 1, borderRadius: 3,
  })

  pu.value.powerChartData = datasets.length ? { labels, datasets } : null
}

watch(() => pu.value.series, () => {
  if (pu.value.groupBy === 'battery' && pu.value.rawStatsData) buildPowerChart(pu.value.rawStatsData)
  if (pu.value.groupBy === 'pue_type' && pu.value.rawPueData) buildPueChart(pu.value.rawPueData)
}, { deep: true })

// Green shades per PUE type (for consumed bars)
const PUE_CONSUMED_COLOURS = [
  'rgba(244,67,54,0.75)', 'rgba(229,115,115,0.75)', 'rgba(211,47,47,0.75)',
  'rgba(183,28,28,0.75)', 'rgba(255,138,101,0.75)', 'rgba(255,87,34,0.75)',
  'rgba(230,74,25,0.75)', 'rgba(191,54,12,0.75)',
]
const PUE_KWH_COLOURS = [
  'rgba(244,67,54,0.4)', 'rgba(229,115,115,0.4)', 'rgba(211,47,47,0.4)',
  'rgba(183,28,28,0.4)', 'rgba(255,138,101,0.4)', 'rgba(255,87,34,0.4)',
  'rgba(230,74,25,0.4)', 'rgba(191,54,12,0.4)',
]

async function loadPowerByPUEType() {
  const res = await analyticsAPI.powerByPUEType({
    pue_type_ids: pu.value.pueTypeIds.length ? pu.value.pueTypeIds : null,
    start_time: `${pu.value.startDate}T00:00:00`,
    end_time: `${pu.value.endDate}T23:59:59`,
    aggregation_period: pu.value.aggPeriod,
    aggregation_function: 'split_stats',
  })
  const body = res.data || res
  const rows = body.data || []
  const allTypes = body.pue_types || []

  if (!rows.length) {
    pu.value.pueTypeChartData = null
    pu.value.pueTypeSummary = []
    pu.value.rawPueData = null
    return
  }

  pu.value.rawPueData = { rows, allTypes }
  buildPueChart({ rows, allTypes })
}

function buildPueChart({ rows, allTypes }) {
  if (!rows || !rows.length) { pu.value.pueTypeChartData = null; return }

  const timeSet = new Set()
  rows.forEach(r => timeSet.add(r.time_group))
  const timeSorted = [...timeSet].sort()
  const fmtLabels = timeSorted.map(t => fmtTimeLabel(t, pu.value.aggPeriod))
  const periodH = PERIOD_HOURS[pu.value.aggPeriod] || 24
  const s = pu.value.series
  const datasets = []

  allTypes.forEach((typeName, idx) => {
    const getRow = tg => rows.find(r => r.time_group === tg && r.pue_type_name === typeName)

    if (s.meanOut) datasets.push({
      label: `${typeName}`,
      type: 'bar', yAxisID: 'y',
      data: timeSorted.map(tg => { const r = getRow(tg); return r?.out_mean != null ? +(Math.abs(r.out_mean).toFixed(1)) : 0 }),
      backgroundColor: PUE_CONSUMED_COLOURS[idx % PUE_CONSUMED_COLOURS.length],
      borderRadius: 3,
    })
    if (s.kwhOut) datasets.push({
      label: `${typeName} (kWh)`,
      type: 'bar', yAxisID: 'y1',
      data: timeSorted.map(tg => { const r = getRow(tg); return r?.out_mean != null ? +(Math.abs(r.out_mean) * periodH / 1000).toFixed(4) : 0 }),
      backgroundColor: PUE_KWH_COLOURS[idx % PUE_KWH_COLOURS.length],
      borderColor: PUE_CONSUMED_COLOURS[idx % PUE_CONSUMED_COLOURS.length],
      borderWidth: 1, borderRadius: 3,
    })
    if (s.medianOut && s.meanOut) datasets.push({
      label: `${typeName} median`,
      type: 'line', yAxisID: 'y',
      data: timeSorted.map(tg => { const r = getRow(tg); return r?.out_median != null ? +(Math.abs(r.out_median).toFixed(1)) : null }),
      borderColor: PUE_CONSUMED_COLOURS[idx % PUE_CONSUMED_COLOURS.length].replace('0.75', '1'),
      backgroundColor: 'transparent',
      borderWidth: 2, borderDash: [5, 3], pointRadius: timeSorted.length > 60 ? 0 : 4,
      fill: false, tension: 0,
    })
    if (s.stdOut && s.meanOut) {
      datasets.push({
        label: `${typeName} std upper`,
        type: 'line', yAxisID: 'y',
        data: timeSorted.map(tg => { const r = getRow(tg); return r?.out_mean != null ? +(Math.abs(r.out_mean) + (r.out_std || 0)).toFixed(1) : null }),
        borderColor: 'transparent', backgroundColor: PUE_CONSUMED_COLOURS[idx % PUE_CONSUMED_COLOURS.length].replace('0.75', '0.15'),
        borderWidth: 0, pointRadius: 0, fill: '+1', tension: 0.2,
      })
      datasets.push({
        label: `${typeName} std lower`,
        type: 'line', yAxisID: 'y',
        data: timeSorted.map(tg => { const r = getRow(tg); return r?.out_mean != null ? Math.max(0, +(Math.abs(r.out_mean) - (r.out_std || 0)).toFixed(1)) : null }),
        borderColor: 'transparent', backgroundColor: 'transparent',
        borderWidth: 0, pointRadius: 0, fill: false, tension: 0.2,
      })
    }
  })

  pu.value.pueTypeChartData = datasets.length ? { labels: fmtLabels, datasets } : null

  // Summary cards
  pu.value.pueTypeSummary = allTypes.map(typeName => {
    const typeRows = rows.filter(r => r.pue_type_name === typeName && r.out_mean != null)
    const avgPower = typeRows.length
      ? Math.round(typeRows.reduce((sum, r) => sum + Math.abs(r.out_mean), 0) / typeRows.length)
      : 0
    const totalCount = typeRows.reduce((sum, r) => sum + (r.out_count || 0), 0)
    return { name: typeName, avgPower, dataPoints: totalCount }
  })
}

// ===================== REPORT BUILDER =====================

const rb = ref({
  userId: null,
  startDate: defaultRange().start,
  endDate: defaultRange().end,
  statMode: 'mean',
  loading: false,
  rentals: [],
  stats: null,
  daily: [],
  powerTimeline: [],
})

const rbPowerChart = computed(() => {
  if (!rb.value.powerTimeline.length) return null
  const pts = [...rb.value.powerTimeline].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  return {
    labels: pts.map(p => new Date(p.timestamp).toLocaleString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })),
    datasets: [{
      label: 'Power (W)',
      data: pts.map(p => p.power_watts),
      segment: {
        borderColor: ctx => (ctx.p0.parsed.y < 0 || ctx.p1.parsed.y < 0) ? 'rgb(229, 57, 53)' : 'rgb(0, 150, 136)',
        backgroundColor: ctx => (ctx.p0.parsed.y < 0 || ctx.p1.parsed.y < 0) ? 'rgba(229, 57, 53, 0.12)' : 'rgba(0, 150, 136, 0.08)',
      },
      borderColor: 'rgb(0, 150, 136)',
      backgroundColor: 'rgba(0, 150, 136, 0.08)',
      fill: true,
      tension: 0.2,
      pointRadius: pts.length > 100 ? 0 : 2,
      borderWidth: 1.5,
    }]
  }
})

const rbPowerChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 20 } },
    y: {
      title: { display: true, text: 'W' },
      grid: {
        color: ctx => ctx.tick.value === 0 ? 'rgba(0,0,0,0.25)' : 'rgba(0,0,0,0.06)',
        lineWidth: ctx => ctx.tick.value === 0 ? 1.5 : 1,
      }
    }
  }
}

const rbDailyColumns = [
  { name: 'date', label: 'Date', field: 'date', align: 'left', sortable: true },
  { name: 'uses', label: 'Uses', field: 'uses', align: 'center', sortable: true },
  { name: 'total_duration_h', label: 'Duration (h)', field: 'total_duration_h', align: 'right', sortable: true },
  { name: 'total_wh', label: 'Total Wh', field: 'total_wh', align: 'right', format: v => v != null ? v.toFixed(1) : '—' },
  { name: 'power_max_w', label: 'Peak W ↓', field: 'power_max_w', align: 'right', format: v => v != null ? v.toFixed(1) : '—' },
  { name: 'power_min_w', label: 'Min W ↓', field: 'power_min_w', align: 'right', format: v => v != null ? v.toFixed(1) : '—' },
  { name: 'power_mean_w', label: 'Mean W ↓', field: 'power_mean_w', align: 'right', format: v => v != null ? v.toFixed(1) : '—' },
  { name: 'power_sd_w', label: 'SD W', field: 'power_sd_w', align: 'right', format: v => v != null ? v.toFixed(1) : '—' },
]

const rbColumns = [
  { name: 'rental_id', label: 'ID', field: 'rental_id', align: 'left', sortable: true },
  { name: 'battery_id', label: 'Battery', field: 'battery_id', align: 'left' },
  { name: 'start', label: 'Start', field: 'start', align: 'left', format: v => v ? new Date(v).toLocaleString() : '-', sortable: true },
  { name: 'end', label: 'End', field: 'end', align: 'left', format: v => v ? new Date(v).toLocaleString() : 'Active' },
  { name: 'duration_h', label: 'Duration (h)', field: 'duration_h', align: 'right', sortable: true },
  { name: 'power_mean_w', label: 'Avg W', field: 'power_mean_w', align: 'right', format: v => v != null ? Number(v).toFixed(1) : '—' },
  { name: 'total_wh', label: 'Total Wh', field: 'total_wh', align: 'right', format: v => v != null ? Number(v).toFixed(1) : '—' },
  { name: 'status', label: 'Status', field: 'status', align: 'left' },
]

async function loadReport() {
  if (!rb.value.userId) return
  rb.value.loading = true
  try {
    const res = await analyticsAPI.userReport({
      user_id: rb.value.userId,
      start_date: rb.value.startDate,
      end_date: rb.value.endDate,
      hub_id: selectedHub.value,
    })
    const body = res.data ?? res
    rb.value.stats = body.summary || null
    rb.value.daily = body.daily || []
    rb.value.rentals = body.rentals || []
    rb.value.powerTimeline = body.power_timeline || []
  } finally {
    rb.value.loading = false
  }
}

function downloadReportCSV() {
  const headers = ['Date', 'Uses', 'Total Duration (h)', 'Total Wh', 'Power Max (W)', 'Power Min (W)', 'Power Mean (W)', 'Power Median (W)', 'Power SD (W)']
  const rows = rb.value.daily.map(d => [
    d.date, d.uses, d.total_duration_h, d.total_wh ?? '',
    d.power_max_w ?? '', d.power_min_w ?? '', d.power_mean_w ?? '', d.power_median_w ?? '', d.power_sd_w ?? ''
  ])
  downloadCSV([headers, ...rows], 'user_report_daily.csv')
}

function downloadRentalsCSV() {
  const headers = ['Rental ID', 'Battery', 'Start', 'End', 'Duration (h)', 'Status', 'Amount Paid', 'Power Mean (W)', 'Power Max (W)', 'Total Wh']
  const rows = rb.value.rentals.map(r => [
    r.rental_id, r.battery_id || '', r.start || '', r.end || '',
    r.duration_h ?? '', r.status, r.amount_paid ?? '',
    r.power_mean_w ?? '', r.power_max_w ?? '', r.total_wh ?? ''
  ])
  downloadCSV([headers, ...rows], 'user_report_rentals.csv')
}

// ===================== TELEMETRY =====================

const tel = ref({
  batteryId: null,
  startDate: defaultRange().start,
  endDate: defaultRange().end,
  loading: false,
  data: []
})

const telLabels = computed(() =>
  tel.value.data.map(d =>
    new Date(d.timestamp).toLocaleString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  )
)

const sparsePoints = computed(() => tel.value.data.length > 200 ? 0 : 2)

function telChart(field, color) {
  return {
    labels: telLabels.value,
    datasets: [{
      label: field,
      data: tel.value.data.map(d => d[field]),
      borderColor: color,
      backgroundColor: color.replace('rgb(', 'rgba(').replace(')', ', 0.08)'),
      fill: true,
      tension: 0.2,
      pointRadius: sparsePoints.value,
      borderWidth: 1.5
    }]
  }
}

const telSocChart = computed(() => telChart('state_of_charge', 'rgb(33, 150, 243)'))
const telVoltageChart = computed(() => telChart('voltage', 'rgb(156, 39, 176)'))
const telCurrentChart = computed(() => ({
  labels: telLabels.value,
  datasets: [{
    label: 'current_amps',
    data: tel.value.data.map(d => d.current_amps),
    segment: {
      borderColor: ctx => (ctx.p0.parsed.y < 0 || ctx.p1.parsed.y < 0) ? 'rgb(229, 57, 53)' : 'rgb(0, 150, 136)',
      backgroundColor: ctx => (ctx.p0.parsed.y < 0 || ctx.p1.parsed.y < 0) ? 'rgba(229, 57, 53, 0.12)' : 'rgba(0, 150, 136, 0.08)',
    },
    borderColor: 'rgb(0, 150, 136)',
    backgroundColor: 'rgba(0, 150, 136, 0.08)',
    fill: true,
    tension: 0.2,
    pointRadius: sparsePoints.value,
    borderWidth: 1.5
  }]
}))
const telTempChart = computed(() => telChart('temp_battery', 'rgb(255, 152, 0)'))

function telLineOptions(min, max, unit) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 15 } },
      y: {
        ...(min !== null ? { min } : {}),
        ...(max !== null ? { max } : {}),
        title: { display: true, text: unit }
      }
    }
  }
}

const telCurrentOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 15 } },
    y: {
      title: { display: true, text: 'A' },
      grid: {
        color: ctx => ctx.tick.value === 0 ? 'rgba(0,0,0,0.25)' : 'rgba(0,0,0,0.06)',
        lineWidth: ctx => ctx.tick.value === 0 ? 1.5 : 1,
      }
    }
  }
}))

async function loadTelemetry() {
  if (!tel.value.batteryId) return
  tel.value.loading = true
  try {
    const res = await dataAPI.getBatteryData(tel.value.batteryId, {
      start_timestamp: `${tel.value.startDate}T00:00:00`,
      end_timestamp: `${tel.value.endDate}T23:59:59`,
      limit: 2000
    })
    const body = res.data ?? res
    const data = Array.isArray(body) ? body : Array.isArray(body?.data) ? body.data : []
    tel.value.data = [...data].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  } finally {
    tel.value.loading = false
  }
}

function downloadTelemetryCSV() {
  const headers = ['timestamp', 'state_of_charge', 'voltage', 'current_amps', 'power_watts', 'temp_battery', 'latitude', 'longitude', 'altitude']
  const rows = tel.value.data.map(d => headers.map(h => d[h] ?? ''))
  downloadCSV([headers, ...rows], `telemetry_${tel.value.batteryId}.csv`)
}

// ===================== GPS TRACK =====================

let leafletMap = null
let trackLayer = null
let markerLayer = null
let heatLayer = null
let playTimer = null
let cacheUpdateListener = null

const gps = ref({
  batteryId: null,
  startDate: defaultRange().start,
  endDate: defaultRange().end,
  loading: false,
  points: [],       // raw sorted GPS points
  sliderIndex: 0,
  playing: false,
  playSpeed: 1,     // multiplier
  showHeatmap: false,
})

const gps_heatmap = ref(false)

const gpsCurrentPoint = computed(() =>
  gps.value.points.length ? gps.value.points[gps.value.sliderIndex] : null
)

async function loadGpsTrack() {
  if (!gps.value.batteryId) return
  gps.value.loading = true
  gps.value.points = []
  try {
    const res = await dataAPI.getBatteryData(gps.value.batteryId, {
      start_timestamp: `${gps.value.startDate}T00:00:00`,
      end_timestamp: `${gps.value.endDate}T23:59:59`,
      limit: 5000,
    })
    const body = res.data ?? res
    const raw = Array.isArray(body) ? body : Array.isArray(body?.data) ? body.data : []
    gps.value.points = raw
      .filter(d => d.latitude && d.longitude)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    gps.value.sliderIndex = 0
    gps.value.playing = false
    clearInterval(playTimer)
    await nextTick()
    initMap()
  } finally {
    gps.value.loading = false
  }
}

function downloadGpsCSV() {
  const headers = ['timestamp', 'latitude', 'longitude', 'altitude', 'state_of_charge', 'power_watts']
  const rows = gps.value.points.map(p => headers.map(h => p[h] ?? ''))
  downloadCSV([headers, ...rows], `gps_${gps.value.batteryId}.csv`)
}

async function initMap() {
  await nextTick()
  const el = document.getElementById('gps-map')
  if (!el || !gps.value.points.length) return

  const L = (await import('leaflet')).default
  await import('leaflet/dist/leaflet.css')

  if (leafletMap) {
    leafletMap.remove()
    leafletMap = null
    trackLayer = null
    markerLayer = null
    heatLayer = null
  }

  const pts = gps.value.points
  const centre = [pts[0].latitude, pts[0].longitude]
  leafletMap = L.map(el).setView(centre, 13)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(leafletMap)

  drawTrack(L)
  drawMarker(L)
  drawHeatmap(L)
}

function drawTrack(L) {
  if (trackLayer) trackLayer.remove()
  const coords = gps.value.points.map(p => [p.latitude, p.longitude])
  trackLayer = L.polyline(coords, { color: '#1976D2', weight: 3, opacity: 0.8 }).addTo(leafletMap)

  // Clickable circles on each point
  coords.forEach((c, i) => {
    const pt = gps.value.points[i]
    L.circleMarker(c, { radius: 4, color: '#1565C0', fillColor: '#42A5F5', fillOpacity: 0.7 })
      .bindPopup(`<b>${new Date(pt.timestamp).toLocaleString()}</b><br>
        Lat: ${pt.latitude.toFixed(5)}, Lng: ${pt.longitude.toFixed(5)}<br>
        SoC: ${pt.state_of_charge ?? '-'}%`)
      .addTo(leafletMap)
      .on('click', () => { gps.value.sliderIndex = i })
  })

  leafletMap.fitBounds(trackLayer.getBounds(), { padding: [20, 20] })
}

function drawMarker(L) {
  if (markerLayer) markerLayer.remove()
  const pt = gps.value.points[gps.value.sliderIndex]
  if (!pt) return
  const icon = L.divIcon({
    className: '',
    html: `<div style="width:14px;height:14px;border-radius:50%;background:#E53935;border:3px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
  markerLayer = L.marker([pt.latitude, pt.longitude], { icon }).addTo(leafletMap)
}

function drawHeatmap(L) {
  if (heatLayer) { heatLayer.remove(); heatLayer = null }
  if (!gps_heatmap.value) return

  // Density heatmap via overlapping semi-transparent circles
  const layerGroup = L.layerGroup()
  gps.value.points.forEach(p => {
    L.circleMarker([p.latitude, p.longitude], {
      radius: 14,
      color: 'transparent',
      fillColor: '#E53935',
      fillOpacity: 0.08,
      interactive: false,
    }).addTo(layerGroup)
  })
  heatLayer = layerGroup
  heatLayer.addTo(leafletMap)
}

watch(() => gps.value.sliderIndex, async () => {
  if (!leafletMap || !gps.value.points.length) return
  const L = (await import('leaflet')).default
  drawMarker(L)
  const pt = gps.value.points[gps.value.sliderIndex]
  if (pt) leafletMap.panTo([pt.latitude, pt.longitude])
})

watch(gps_heatmap, async () => {
  if (!leafletMap || !gps.value.points.length) return
  const L = (await import('leaflet')).default
  drawHeatmap(L)
})

function toggleGpsPlayback() {
  if (gps.value.playing) {
    clearInterval(playTimer)
    gps.value.playing = false
  } else {
    gps.value.playing = true
    playTimer = setInterval(() => {
      if (gps.value.sliderIndex >= gps.value.points.length - 1) {
        clearInterval(playTimer)
        gps.value.playing = false
      } else {
        gps.value.sliderIndex++
      }
    }, Math.max(50, 200 / gps.value.playSpeed))
  }
}

onUnmounted(() => {
  clearInterval(playTimer)
  if (leafletMap) { leafletMap.remove(); leafletMap = null }
  if (cacheUpdateListener) window.removeEventListener('cache-updated', cacheUpdateListener)
})

// ===================== UTILS =====================

function downloadCSV(rows, filename) {
  const content = rows.map(r =>
    r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')
  ).join('\n')
  const blob = new Blob([content], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ===================== INIT =====================

async function loadPageData(hubId) {
  const [bRes, uRes, ptRes] = await Promise.all([
    api.get('/batteries/', { params: hubId ? { hub_id: hubId } : {}, _bypassOffline: true }).catch(() => null),
    usersAPI.list(hubId ? { hub_id: hubId } : {}).catch(() => null),
    api.get('/settings/pue-types', { params: hubId ? { hub_id: hubId } : {}, _bypassOffline: true }).catch(() => null),
  ])
  batteries.value = Array.isArray(bRes?.data) ? bRes.data : []
  users.value = Array.isArray(uRes?.data) ? uRes.data : []
  const ptBody = ptRes?.data
  pueTypes.value = Array.isArray(ptBody?.pue_types) ? ptBody.pue_types : []
}

async function onHubChange(hubId) {
  selectedHub.value = hubId
  await loadPageData(hubId)
}

onMounted(async () => {
  await loadPageData(selectedHub.value)

  // Update lists when SWR background revalidation brings fresh data
  cacheUpdateListener = (event) => {
    const url = event.detail?.url || ''
    const data = event.detail?.data
    if (!data) return
    if (/\/batteries\/(\?|$)/.test(url)) {
      const arr = Array.isArray(data) ? data : Array.isArray(data?.data) ? data.data : null
      if (arr) batteries.value = arr
    }
    if (url.includes('/users/') && !url.includes('/users/me')) {
      const arr = Array.isArray(data) ? data : Array.isArray(data?.data) ? data.data : null
      if (arr) users.value = arr
    }
    if (url.includes('/settings/pue-types')) {
      const arr = Array.isArray(data?.pue_types) ? data.pue_types : Array.isArray(data) ? data : null
      if (arr) pueTypes.value = arr
    }
  }
  window.addEventListener('cache-updated', cacheUpdateListener)
})
</script>

<style scoped>
.hub-filter-highlight :deep(.q-field__control) {
  border-color: #f57c00 !important;
  background: #fff8e1;
}
</style>
