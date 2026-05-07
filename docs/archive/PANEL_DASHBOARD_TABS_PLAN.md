# Panel Dashboard Tabs Plan

**Created:** 2025-12-11
**Status:** Planning

---

## Tab Structure

### Tab 1: Single Battery Detailed View (Victron-Style)
- **Dropdown selector** to choose ONE battery from filtered list
- **Multi-axis plot** showing:
  - State of Charge (%)
  - Voltage (V)
  - Current (A) - charge/discharge
  - Power (W)
  - Temperature (°C)
  - USB Power (W)
  - Charger Power (W)
- Similar to Victron VRM portal layouts

### Tab 2: State of Charge (SOC)
- Time series plot of SOC for all filtered batteries
- Individual lines per battery or averaged
- Legend with battery IDs

### Tab 3: Real-Time Power (Watts)
- Time series of power consumption (watts) for filtered batteries
- Shows instantaneous power draw

### Tab 4: kWh Consumed (Time Series)
- Energy consumption over time in kWh
- Calculated from power data

### Tab 5: Cumulative kWh
- Running total of energy consumed
- Cumulative sum plot

### Tab 6: USB Power (Time Series)
- USB port power consumption over time (watts)
- Shows power drawn from USB ports

### Tab 7: USB kWh Consumed
- Energy consumed through USB ports (kWh)
- Time series

### Tab 8: Voltage & Current
- Dual-axis plot:
  - Battery voltage (V)
  - Battery current (A)
- Shows charge/discharge patterns

### Tab 9: Temperature
- Battery temperature over time
- Multiple batteries on same plot

### Tab 10: Aggregated Mean Power
- Average power across all filtered batteries
- Single line showing fleet-wide mean power

### Tab 11: Aggregated Total Power (Watts)
- Sum of power from all filtered batteries
- Total system power draw

### Tab 12: Aggregated Cumulative kWh
- Total cumulative energy consumed by all batteries
- Fleet-wide energy usage

### Tab 13: Aggregated kWh (Time Series)
- Total kWh consumed over time (not cumulative)
- Sum across all batteries

### Tab 14: Charging vs Consumption
- Dual plot showing:
  - Total charging power (sum)
  - Total consumption power (sum)
- Aggregated over selected interval (30min, 1hr, etc.)
- Shows balance of charge/discharge

### Tab 15: GPS Location Map
- **Single battery selector** dropdown
- Map widget (Panel + HoloViews or Folium)
- Time slider to move through battery location history
- Plot GPS coordinates on map
- Show path traveled

### Tab 16: Additional Data & Statistics
- Any other available fields from livedata
- Charger voltage/power details
- System statistics panel

---

## Data Fields Available

From `livedata` table:
- `state_of_charge` - SOC %
- `voltage` - Battery voltage
- `current_amps` - Battery current (+ charge, - discharge)
- `power_watts` - Power consumption
- `temp_battery` - Battery temperature
- `charging_current` - Charging current
- `charger_power` - Charger power input
- `charger_voltage` - Charger voltage
- `usb_power` - USB power output
- `usb_voltage` - USB voltage
- `amp_hours_consumed` - Ah consumed
- `total_charge_consumed` - Total charge consumed
- `latitude`, `longitude` - GPS coordinates (if available)
- `timestamp` - Time of measurement

---

## Implementation Plan

### Phase 1: Core Time Series Tabs (3-5 hours)
1. ✅ Cascading filters (DONE)
2. SOC tab
3. Power (Watts) tab
4. Voltage & Current tab
5. Temperature tab

### Phase 2: Energy Calculations (2-3 hours)
6. kWh time series (calculate from power_watts)
7. Cumulative kWh
8. USB kWh calculations

### Phase 3: Aggregated Views (2-3 hours)
9. Mean power aggregation
10. Total power aggregation
11. Charging vs Consumption
12. Aggregated kWh tabs

### Phase 4: Advanced Features (3-4 hours)
13. Single battery Victron-style multi-axis view
14. GPS map with time slider
15. Additional data tab

---

## Technical Notes

### Energy Calculations
- kWh = (power_watts * time_interval_hours) / 1000
- For resampled data at 30min intervals: kWh = (avg_power_watts * 0.5) / 1000
- Cumulative kWh = cumsum(kWh)

### Multi-Axis Plots
```python
import holoviews as hv
# Create multiple overlays with different y-axes
curve1 = hv.Curve(data, 'time', 'soc').opts(color='blue')
curve2 = hv.Curve(data, 'time', 'voltage').opts(color='red')
(curve1 * curve2).opts(multi_y=True)
```

### GPS Mapping
- Use `panel.pane.plot.Folium` or `hvplot` with tiles
- GeoViews for map backgrounds
- Time slider widget to filter GPS data by timestamp

### Performance Optimization
- Cache aggregated calculations
- Use `@pn.cache` decorator
- Limit data points for large time ranges
- Progressive loading for GPS data

---

## Tab Organization

**Group 1: Single Battery Analysis**
- Single Battery Detailed View
- GPS Location Map

**Group 2: Battery Metrics**
- State of Charge
- Voltage & Current
- Temperature

**Group 3: Power Analysis**
- Real-Time Power (Watts)
- kWh Consumed
- Cumulative kWh
- USB Power & kWh

**Group 4: Aggregated Fleet Views**
- Aggregated Mean Power
- Aggregated Total Power
- Aggregated kWh
- Charging vs Consumption

**Group 5: Additional**
- Other Data & Statistics

---

## Next Steps

1. Start with Phase 1 tabs (SOC, Power, Voltage/Current, Temperature)
2. Implement energy calculations for kWh tabs
3. Build aggregation methods for fleet-wide views
4. Add single battery detailed view with dropdown
5. Implement GPS mapping last (most complex)
