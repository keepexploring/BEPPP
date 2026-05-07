 Analytics Development Workflow - Implementation Plan

 Overview

 Establish a progressive enhancement workflow that enables rapid analytics prototyping in Jupyter notebooks
 while building production-ready native Quasar components. This creates a sustainable pipeline where analytics
 evolve from exploration → prototype → production.

 User Requirements

 - Hybrid approach: Native Quasar components for mature/stable analytics, keep Jupyter/Panel iframe for
 exploratory work
 - Development workflow: Prototype in Jupyter → Auto-generate FastAPI endpoints → Create Quasar components
 - Visualization types: Time series charts, statistical summaries, geographic maps, business dashboards
 - Key goal: Easy way to continuously develop and add analytics features as system evolves

 Current State

 - ✅ Panel dashboard embedded via iframe at /analytics page
 - ✅ 7 existing analytics API endpoints (/analytics/hub-summary, /analytics/power-usage, etc.)
 - ✅ JupyterLab running at port 8888
 - ✅ Rich data available: battery telemetry (30+ fields), rentals, financials

 ---
 Phase 1: Infrastructure Setup (Week 1)

 1.1 Install JavaScript Charting Libraries

 Rationale: Multi-library approach for optimal performance
 - Apache ECharts - Complex time-series, large datasets (100k+ points), interactive features
 - Chart.js - Lightweight KPIs and simple charts (faster load times)
 - Leaflet - Geographic/GPS mapping

 cd frontend
 npm install vue-echarts echarts
 npm install vue-chartjs chart.js chartjs-adapter-date-fns
 npm install @vue-leaflet/vue-leaflet leaflet

 1.2 Create Component Structure

 Create these directories and files:

 frontend/src/
 ├── components/analytics/
 │   ├── BaseChart.vue           # Foundation wrapper with loading/error states
 │   ├── TimeSeriesChart.vue     # ECharts time-series component
 │   ├── KPICard.vue             # Simple metric cards
 │   └── AnalyticsSkeleton.vue   # Loading placeholder
 ├── composables/
 │   ├── useAnalytics.js         # Analytics API calls and state
 │   └── useChartConfig.js       # Shared ECharts/Chart.js configs
 └── pages/
     └── BatteryAnalyticsPage.vue # First native analytics page

 Critical Files to Create:

 1. frontend/src/components/analytics/BaseChart.vue
   - Reusable wrapper for all charts
   - Handles loading, error, empty states
   - Export functionality (CSV)
   - Refresh button
   - Consistent UI/UX across all analytics
 2. frontend/src/composables/useAnalytics.js
   - Centralized analytics API calls
   - Loading/error state management
   - Quasar notification integration
   - Specialized composables (useBatteryPerformance, usePowerUsage, etc.)
 3. frontend/src/components/analytics/TimeSeriesChart.vue
   - ECharts line chart with zoom/pan
   - Multi-series support (multiple batteries)
   - Configurable axes (x: timestamp, y: any metric)
   - Mobile-responsive

 1.3 Create Jupyter Notebook Infrastructure

 Create these files:

 notebooks/
 ├── templates/
 │   └── analytics_template.ipynb  # Structured template for API export
 ├── prototypes/                   # Active development notebooks
 ├── production/                   # Notebooks promoted to API
 └── archive/                      # Deprecated/superseded notebooks

 notebooks/templates/analytics_template.ipynb structure:
 - Cell 1: Metadata (endpoint name, parameters, auth requirements)
 - Cell 2: Imports and database connection
 - Cell 3: Pydantic request model (matches API)
 - Cell 4: load_data() function (becomes API logic)
 - Cell 5: transform_data() function (data processing)
 - Cell 6: format_response() function (API response format)
 - Cell 7: Visualization (for notebook testing)
 - Cell 8: Export configuration

 1.4 Create Notebook-to-API Converter

 scripts/notebook_to_api.py
 - Parses Jupyter notebook cells
 - Extracts marked functions (load_data, transform_data, format_response)
 - Extracts Pydantic models
 - Generates FastAPI endpoint code
 - Appends to api/app/main.py

 # Usage
 python scripts/notebook_to_api.py notebooks/battery_efficiency.ipynb

 ---
 Phase 2: First Native Analytics Component (Week 2-3)

 2.1 Pick First Feature to Migrate

 Recommended: Revenue Dashboard (high usage, simple charts, stable requirements)

 Workflow:

 Step 1: Prototype in Jupyter (1-2 days)
 # notebooks/prototypes/revenue_analytics.ipynb
 # - Define API contract
 # - Write SQL queries for revenue data
 # - Aggregate by time period
 # - Visualize with hvPlot
 # - Test edge cases

 Step 2: Export to API (2-4 hours)
 # Auto-generate endpoint
 python scripts/notebook_to_api.py notebooks/prototypes/revenue_analytics.ipynb

 # Manual review and enhancement
 # - Add authentication checks
 # - Add error handling
 # - Test endpoint with curl/Postman

 Step 3: Create Quasar Component (2-4 hours)
 <!-- frontend/src/components/analytics/RevenueChart.vue -->
 <template>
   <BaseChart
     title="Revenue Over Time"
     :data="revenueData"
     :loading="loading"
     :error="error"
     @refresh="loadData"
   >
     <template #default="{ data }">
       <TimeSeriesChart
         :chart-data="data"
         x-axis-key="date"
         y-axis-key="revenue"
       />
     </template>
   </BaseChart>
 </template>

 <script setup>
 import { ref, onMounted } from 'vue'
 import { useAnalytics } from 'src/composables/useAnalytics'
 import BaseChart from './BaseChart.vue'
 import TimeSeriesChart from './TimeSeriesChart.vue'

 const { loading, error, fetchAnalytics } = useAnalytics()
 const revenueData = ref([])

 const loadData = async () => {
   const result = await fetchAnalytics('revenue', {
     time_period: 'last_month'
   })
   revenueData.value = result.data
 }

 onMounted(() => loadData())
 </script>

 Step 4: Add to Analytics Page (1 hour)
 <!-- Enhance existing AnalyticsPage.vue -->
 <template>
   <q-page>
     <q-tabs v-model="activeTab">
       <q-tab name="dashboard" label="Dashboard" />
       <q-tab name="panel" label="Advanced Analytics" />
     </q-tabs>

     <q-tab-panels v-model="activeTab">
       <q-tab-panel name="dashboard">
         <!-- Native Quasar components -->
         <div class="row q-col-gutter-md">
           <div class="col-12">
             <RevenueChart />
           </div>
           <!-- Add more components as they're built -->
         </div>
       </q-tab-panel>

       <q-tab-panel name="panel">
         <!-- Keep existing Panel iframe -->
         <iframe :src="panelUrl" class="panel-iframe" />
       </q-tab-panel>
     </q-tab-panels>
   </q-page>
 </template>

 2.2 Extend API Service

 Update frontend/src/services/api.js:
 export const analyticsAPI = {
   // Existing endpoints
   hubSummary: (params) => api.get('/analytics/hub-summary', { params }),
   powerUsage: (data) => api.post('/analytics/power-usage', data),
   // ... existing endpoints ...

   // New endpoints (as they're added)
   batteryEfficiency: (data) => api.post('/analytics/battery-efficiency', data),
   rentalTrends: (data) => api.post('/analytics/rental-trends', data),
   // etc.
 }

 ---
 Phase 3: Progressive Migration Strategy (Ongoing)

 3.1 Migration Priority Matrix

 Migrate to Native Quasar (High Priority):
 1. ✅ Revenue charts - Used daily, simple bar/line charts
 2. ✅ KPI summary cards - Fast to build, high value
 3. ✅ Battery status overview - Already have data, simple UI
 4. ⏳ Rental trends - Moderate complexity, frequent use

 Keep in Panel (Low Priority):
 - Ad-hoc research queries (Panel excels at rapid iteration)
 - Experimental visualizations (not worth building UI yet)
 - Complex multi-dimensional analysis (Panel/Bokeh better suited)
 - One-off analyses for specific requests

 3.2 Decision Framework

 Migrate to native Quasar when:
 - ✅ Used daily or weekly by multiple users (not one-off)
 - ✅ Requirements are stable (not changing frequently)
 - ✅ Complexity is manageable (can build in 4-8 hours)
 - ✅ Performance is acceptable (Panel iframe working fine)

 3.3 Dual-Tab Approach

 Keep both interfaces available:
 - "Dashboard" tab: Native Quasar components (fast, mobile-friendly, integrated)
 - "Advanced Analytics" tab: Panel iframe (exploratory, research, complex analysis)

 Users can choose based on their needs:
 - Quick insights → Dashboard tab
 - Deep dive analysis → Advanced Analytics tab

 ---
 Phase 4: Development Process Documentation

 4.1 Standard Workflow (Any New Analytic)

 ┌─────────────────────────────────────┐
 │ 1. PROTOTYPE (Jupyter)              │  1-3 days
 │    - Copy analytics_template.ipynb   │
 │    - Define API contract             │
 │    - Write queries and logic         │
 │    - Test visualizations             │
 └─────────────────────────────────────┘
            ↓
 ┌─────────────────────────────────────┐
 │ 2. EXPORT TO API (FastAPI)          │  2-4 hours
 │    - Run notebook_to_api.py          │
 │    - Review generated code           │
 │    - Add auth and error handling     │
 │    - Test endpoint                   │
 └─────────────────────────────────────┘
            ↓
 ┌─────────────────────────────────────┐
 │ 3. BUILD COMPONENT (Quasar)         │  2-4 hours
 │    - Create .vue component           │
 │    - Use BaseChart wrapper           │
 │    - Wire up composable              │
 │    - Test responsiveness             │
 └─────────────────────────────────────┘
            ↓
 ┌─────────────────────────────────────┐
 │ 4. INTEGRATE & TEST                 │  1 hour
 │    - Add to analytics page           │
 │    - Test with real users            │
 │    - Gather feedback                 │
 │    - Iterate if needed               │
 └─────────────────────────────────────┘

 4.2 Git Workflow

 # Feature branch
 git checkout -b feature/battery-efficiency-analytics

 # Commit notebook
 git add notebooks/prototypes/battery_efficiency.ipynb
 git commit -m "Add battery efficiency prototype notebook"

 # Commit API
 git add api/app/main.py
 git commit -m "Add /analytics/battery-efficiency endpoint"

 # Commit frontend
 git add frontend/src/components/analytics/BatteryEfficiencyChart.vue
 git commit -m "Add battery efficiency chart component"

 # Create PR
 gh pr create --title "Add battery efficiency analytics"

 ---
 Implementation Steps Summary

 Immediate Actions (Week 1)

 1. ✅ Install npm packages (echarts, chartjs, leaflet)
 2. ✅ Create frontend/src/components/analytics/ directory
 3. ✅ Create frontend/src/components/analytics/BaseChart.vue
 4. ✅ Create frontend/src/composables/useAnalytics.js
 5. ✅ Create notebooks/templates/analytics_template.ipynb
 6. ✅ Create scripts/notebook_to_api.py

 First Implementation (Week 2-3)

 7. ✅ Pick first feature (recommend: Revenue Dashboard)
 8. ✅ Prototype in Jupyter notebook
 9. ✅ Export to FastAPI endpoint
 10. ✅ Create Quasar component
 11. ✅ Add dual-tab layout to AnalyticsPage.vue
 12. ✅ Test and gather feedback

 Ongoing (Week 4+)

 13. 🔄 Migrate one feature per week
 14. 🔄 Document lessons learned
 15. 🔄 Build component library
 16. 🔄 Optimize performance

 ---
 Critical Files

 Files to Create

 1. frontend/src/components/analytics/BaseChart.vue - Foundation component
 2. frontend/src/composables/useAnalytics.js - Analytics API client
 3. notebooks/templates/analytics_template.ipynb - Notebook template
 4. scripts/notebook_to_api.py - Notebook-to-API converter
 5. frontend/src/components/analytics/TimeSeriesChart.vue - ECharts wrapper
 6. frontend/src/pages/BatteryAnalyticsPage.vue - First native page (optional)

 Files to Modify

 1. frontend/src/pages/AnalyticsPage.vue - Add dual-tab layout (lines 1-100)
 2. frontend/src/services/api.js - Add new analytics endpoints (after line 229)
 3. api/app/main.py - Add new analytics endpoints (after line 8416)
 4. frontend/package.json - Add new dependencies

 Files to Reference

 1. api/app/main.py:8004-8416 - Existing analytics endpoint patterns
 2. frontend/src/services/api.js:213-229 - Existing analytics API client
 3. panel_dashboard/battery_analytics_v3.py - Panel implementation for reference

 ---
 Success Metrics

 Week 1:
 - Infrastructure set up (components, composables, scripts)
 - Notebook template created and documented

 Week 3:
 - First native analytics component deployed (revenue or KPIs)
 - Dual-tab interface working in production

 Month 2:
 - 3-4 high-priority analytics migrated to native
 - Component library established and documented
 - Development workflow proven and repeatable

 Long-term:
 - 80% of daily-use analytics in native Quasar
 - Panel iframe used primarily for research/exploration
 - One new analytic can be added in 1 week (prototype → production)

 ---
 Key Benefits

 1. Rapid Prototyping: Jupyter allows quick experimentation
 2. Auto-Generation: notebook_to_api.py reduces manual coding
 3. Progressive Enhancement: Keep Panel while building native components
 4. Reusable Components: BaseChart and TimeSeriesChart speed up future work
 5. Mobile-Friendly: Native Quasar components work better on phones/tablets
 6. Maintainable: Clear separation between exploration (Jupyter) and production (Quasar)

 ---
 Notes

 - Start with simple features (revenue, KPIs) before tackling complex time-series
 - Keep Panel iframe - it's valuable for exploratory work
 - Document each analytic in notebook README
 - Test on mobile devices, not just desktop
 - ECharts handles large datasets (>10k points) much better than Chart.js
 - Use Chart.js for simple charts where ECharts would be overkill