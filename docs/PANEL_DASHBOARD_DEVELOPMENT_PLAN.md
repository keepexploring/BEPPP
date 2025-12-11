# Panel Dashboard Development Plan

**Status:** In Progress
**Last Updated:** 2025-12-10

---

## Current State

### ✅ Completed Features

1. **Multi-Select Filter System**
   - Hub selection (checkboxes)
   - Battery selection (CrossSelector dual-list)
   - PUE type filtering
   - Capacity range filter (IntInput boxes)

2. **Database Integration**
   - Dynamic WHERE clause building
   - Supports filtering by:
     - Hub IDs (multi-select)
     - Battery IDs (multi-select)
     - Capacity range
     - PUE types
     - Batteries with PUE rentals

3. **Data Fields Queried**
   - state_of_charge, voltage, current_amps, power_watts
   - temp_battery, charging_current
   - charger_power, charger_voltage
   - usb_power, usb_voltage
   - amp_hours_consumed, total_charge_consumed

4. **Data Processing**
   - Time-based aggregation (30min to 1 day intervals)
   - Forward fill + back fill for missing values (not dropna)
   - Pandas resampling with proper aggregation functions

5. **Current Visualizations**
   - Power consumption plot
   - State of Charge (SOC) plot
   - Voltage plot
   - Statistics panel (counts, averages)

6. **Backups Created**
   - 9 incremental backups saved in `panel_dashboard/`

---

## 🚧 In Progress

### Cascading Filter Workflow

**Goal:** Logical, step-by-step filtering from broad to specific

**Flow:**
```
1. Select Hubs (or none for all)
   ↓
2. Filter by Capacity Range (min/max Wh)
   ↓
3. Optional: PUE Filters
   - Only batteries with PUE rentals checkbox
   - Specific PUE types (multi-select)
   - Specific PUE items from rentals
   ↓
4. FILTERED RESULTS: List of batteries matching criteria
   ↓
5. Select Batteries to Include
   - CrossSelector (dual-list: Available ← → Selected)
   - "Select All" / "Deselect All" buttons
   - Show count: "X batteries match filters"
   ↓
6. Apply to visualizations
```

**Current Issues:**
- ✅ Capacity filter now in correct position (step 2)
- ✅ Batteries now showing in CrossSelector
- ⚠️ Need to make capacity filter actually filter the battery list
- ❌ PUE item selection not yet implemented
- ❌ Select All/Deselect All buttons not added
- ❌ Filter count not shown

---

## 📋 TODO List (Priority Order)

### High Priority - Cascading Filters

1. **Make capacity filter work dynamically**
   - When min/max capacity changes, update battery CrossSelector options
   - Only show batteries within capacity range
   - Requires reactive/dynamic options

2. **Add PUE Item Selection**
   - Load PUE items from database (already done)
   - Create CrossSelector for PUE items
   - Filter batteries that have rentals with selected PUE items

3. **Add Filter Result Indicators**
   - Show "X batteries match your filters"
   - Show "Y batteries selected for visualization"
   - Update counts reactively

4. **Add Selection Buttons**
   - "Select All Filtered" button
   - "Deselect All" button
   - "Clear Filters" button

5. **Update Query Logic**
   - Add PUE item filtering to WHERE clause
   - Properly handle combinations of filters

---

### Medium Priority - Additional Visualizations

6. **Temperature Tab**
   - Line plot of battery temperature over time
   - Average/min/max indicators
   - Copy from v1 dashboard

7. **Current Flow Tab**
   - Battery current plot
   - Charging current plot (overlay)
   - Copy from v1 dashboard

8. **Energy Consumption Tab**
   - Cumulative charge consumed (Ah)
   - Total energy consumption plot
   - Copy from v1 dashboard

9. **USB Power Tab**
   - USB power consumption
   - USB voltage
   - New visualization

10. **Charger Tab**
    - Charger power input
    - Charger voltage
    - New visualization

11. **Data Table Tab**
    - Tabulator widget
    - Show all data in table format
    - Pagination
    - Export to CSV capability

---

### Low Priority - Enhancements

12. **Enhanced Statistics Panel**
    - Add median, std dev, sum
    - More comprehensive metrics
    - Min/max values

13. **Multi-Overlay Plots**
    - Charger power overlaid on power consumption
    - Charging current overlaid on battery current
    - Different colors/line styles

14. **Rental-Specific Filtering**
    - Select specific rental IDs
    - Filter by rental date ranges
    - Show rental user information

15. **Hub-Based Aggregation**
    - Aggregate all batteries by hub
    - Hub comparison view

---

## Technical Implementation Notes

### Reactive Filter Updates

To make capacity filter update battery list dynamically:

```python
@pn.depends('min_capacity', 'max_capacity', watch=False)
def get_filtered_batteries(min_cap, max_cap):
    filtered = [b for b in self.battery_options
                if min_cap <= b['capacity_wh'] <= max_cap]
    return {f"Battery {b['battery_id']} ({b['brand']}, {b['capacity_wh']}Wh)": b['battery_id']
            for b in filtered}

# Use in CrossSelector
battery_selector = pn.widgets.CrossSelector(
    name='Select Batteries',
    options=pn.bind(get_filtered_batteries, self.param.min_capacity, self.param.max_capacity),
    ...
)
```

### PUE Item Query

```sql
SELECT DISTINCT
    pue.pue_item_id,
    pue.pue_type,
    pue.brand,
    pue.model,
    pue.wattage
FROM pue_item pue
JOIN rental_pue_items rpi ON pue.pue_item_id = rpi.pue_item_id
JOIN rental r ON rpi.rental_id = r.rentral_id
WHERE r.is_active = true
ORDER BY pue.pue_type, pue.brand
```

### Database Schema References

**Tables Used:**
- `livedata` - Battery telemetry data
- `bepppbattery` - Battery inventory
- `solarhub` - Hub locations
- `pue_item` - PUE equipment inventory
- `rental` - Rental records
- `rental_pue_items` - PUE items in rentals

---

## Files Structure

```
panel_dashboard/
├── battery_analytics.py          # Original v1 (simple, more plots)
├── battery_analytics_v2.py        # v2 (hierarchical views)
├── battery_analytics_v3.py        # v3 (current, cascading filters)
├── battery_analytics_v3_backup_*.py  # 9 backup files
├── requirements.txt
└── start_panel.sh

Dockerfile.panel                   # Panel container build
docker-compose.yml                 # Service: panel on port 5100
```

---

## Next Session Tasks

1. Test current cascading filter UI
2. Implement dynamic capacity filtering
3. Add PUE item selector
4. Add filter result counts
5. Add temperature plot tab
6. Add data table tab

---

## Known Issues

1. **Capacity filter doesn't dynamically update battery list**
   - Need to use `pn.bind()` or `@pn.depends` for reactive updates

2. **No visual feedback on filter results**
   - Users don't know how many batteries match

3. **PUE filtering incomplete**
   - Can filter by type, but not by specific items

4. **Limited statistics**
   - Only basic averages, need median/std/sum

---

## Resources

- **Panel Docs:** https://panel.holoviz.org/
- **CrossSelector:** https://panel.holoviz.org/reference/widgets/CrossSelector.html
- **Reactive Functions:** https://panel.holoviz.org/how_to/callbacks/sync_callbacks.html
- **Database Schema:** `models.py`
- **API Endpoints:** `api/app/main.py`
