"""
Enhanced Panel Dashboard for Battery Analytics with Hub and PUE Analytics
Features:
- Hub-level, battery-level, and PUE rental-level views
- Configurable aggregation intervals (hourly, 2-hour, 3-hour, etc.)
- Interactive hierarchical selection
- Real-time data from database
"""

import panel as pn
import pandas as pd
import param
from datetime import datetime, timedelta
import hvplot.pandas
import holoviews as hv
from sqlalchemy import create_engine, text
import os
import jwt
from functools import wraps

# Enable Panel extensions with Material Design theme
pn.extension(
    'tabulator',
    sizing_mode='stretch_width',
    design='material',
    template='material'
)
hv.extension('bokeh')

# Global CSS for better spacing
pn.config.raw_css.append("""
.bk-root {
    padding: 15px;
}
.panel-widget-box {
    margin: 15px;
    padding: 15px;
}
.bk-tabs-header {
    padding: 10px;
}
.bk-tab {
    padding: 12px 20px;
    margin: 5px;
}
""")

# JWT configuration from environment variables
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://beppp:changeme@db:5432/beppp')

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None

class EnhancedBatteryAnalyticsDashboard(param.Parameterized):
    """Enhanced Battery Analytics Dashboard with flexible multi-select aggregation"""

    # Time parameters
    time_scale = param.Selector(
        default='24h',
        objects=['1h', '6h', '24h', '7d', '30d', 'all'],
        label="Time Scale"
    )

    aggregation_interval = param.Selector(
        default='30 Minutes',
        objects=['30 Minutes', '1 Hour', '2 Hours', '3 Hours', '6 Hours', '12 Hours', '1 Day'],
        label="Aggregation Interval"
    )

    # Multi-select filter parameters
    selected_hubs = param.ListSelector(default=[], label="Hubs")
    selected_batteries = param.ListSelector(default=[], label="Batteries")

    # Trigger parameter to force updates
    update_trigger = param.Integer(default=0)

    # Battery capacity filter
    min_capacity = param.Number(default=0, bounds=(0, None), label="Min Capacity (Wh)")
    max_capacity = param.Number(default=10000, bounds=(0, None), label="Max Capacity (Wh)")

    # PUE filters
    selected_pue_types = param.ListSelector(default=[], label="PUE Types")
    selected_pue_items = param.ListSelector(default=[], label="PUE Items")
    selected_rentals = param.ListSelector(default=[], label="Rentals")
    filter_batteries_with_pue = param.Boolean(default=False, label="Only batteries with PUE rentals")

    # Advanced filter mode
    use_advanced_filters = param.Boolean(default=False, label="Use Advanced Filters")

    # Single battery selection for detailed view
    selected_single_battery = param.Selector(default=None, label="Select Battery for Detailed View")

    # Mapping from display labels to pandas time codes
    aggregation_mapping = {
        '30 Minutes': '30T',
        '1 Hour': '1H',
        '2 Hours': '2H',
        '3 Hours': '3H',
        '6 Hours': '6H',
        '12 Hours': '12H',
        '1 Day': '1D'
    }

    def __init__(self, **params):
        super().__init__(**params)
        self.engine = create_engine(DATABASE_URL)
        self.data = None

        # Load all available options for multi-select
        self.hub_options = self.load_hub_options()
        self.battery_options = self.load_all_battery_options()
        self.pue_type_options = self.load_pue_type_options()
        self.pue_item_options = self.load_pue_item_options()

        # Set parameter objects after loading options
        self.param.selected_hubs.objects = [h['hub_id'] for h in self.hub_options]
        self.param.selected_batteries.objects = [b['battery_id'] for b in self.battery_options]
        self.param.selected_pue_types.objects = self.pue_type_options
        self.param.selected_pue_items.objects = [p['pue_item_id'] for p in self.pue_item_options]

        # Initialize with ALL hubs and ALL batteries selected by default
        self.selected_hubs = [h['hub_id'] for h in self.hub_options]
        self.selected_batteries = [b['battery_id'] for b in self.battery_options]

        # Don't load data on init - user must click Update button to load data
        # This prevents showing stale data when filters are changed
        # self.load_data()

    def _update_batteries(self, new_value):
        """Helper to update selected_batteries when CrossSelector changes"""
        print(f"DEBUG _update_batteries: CrossSelector changed to {new_value}", flush=True)
        print(f"DEBUG _update_batteries: Length = {len(new_value) if new_value else 0}", flush=True)
        self.selected_batteries = new_value

    def trigger_update(self, event=None):
        """Triggered when update button is clicked"""
        print("=" * 80, flush=True)
        print("DEBUG: Update button clicked!", flush=True)
        print(f"DEBUG: Current selected_batteries: {self.selected_batteries}", flush=True)
        print(f"DEBUG: Type: {type(self.selected_batteries)}", flush=True)
        print(f"DEBUG: Length: {len(self.selected_batteries) if self.selected_batteries else 0}", flush=True)
        print("=" * 80, flush=True)
        self.load_data()
        self.update_trigger += 1
        print(f"DEBUG: Update complete! New update_trigger: {self.update_trigger}", flush=True)

    def load_hub_options(self):
        """Load available hubs"""
        try:
            query = text("""
                SELECT hub_id, what_three_word_location as hub_name
                FROM solarhub
                ORDER BY hub_id
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [{'hub_id': row.hub_id, 'hub_name': row.hub_name}
                        for row in result]
        except Exception as e:
            print(f"Error loading hubs: {e}")
            return []

    def load_all_battery_options(self):
        """Load all batteries with capacity information"""
        try:
            query = text("""
                SELECT
                    battery_id,
                    hub_id,
                    battery_capacity_wh,
                    status
                FROM bepppbattery
                ORDER BY battery_id
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [{'battery_id': row.battery_id,
                        'hub_id': row.hub_id,
                        'capacity_wh': row.battery_capacity_wh or 0,
                        'status': row.status}
                        for row in result]
        except Exception as e:
            print(f"Error loading batteries: {e}")
            import traceback
            traceback.print_exc()
            return []

    def load_pue_type_options(self):
        """Load distinct PUE types from rental_pue_item"""
        try:
            query = text("""
                SELECT DISTINCT pue.pue_type
                FROM pue_item pue
                WHERE pue.pue_type IS NOT NULL
                ORDER BY pue.pue_type
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row.pue_type for row in result if row.pue_type]
        except Exception as e:
            print(f"Error loading PUE types: {e}")
            return []

    def load_pue_item_options(self):
        """Load all PUE items"""
        try:
            query = text("""
                SELECT
                    pue_item_id,
                    pue_type,
                    brand,
                    model,
                    wattage
                FROM pue_item
                ORDER BY pue_type, brand, model
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [{'pue_item_id': row.pue_item_id,
                        'pue_type': row.pue_type,
                        'brand': row.brand or '',
                        'model': row.model or '',
                        'wattage': row.wattage or 0}
                        for row in result]
        except Exception as e:
            print(f"Error loading PUE items: {e}")
            return []

    def get_filtered_battery_options(self, selected_hubs, min_capacity, max_capacity):
        """
        Get battery options filtered by selected hubs and capacity range.
        Returns a dictionary of {display_name: battery_id} for the CrossSelector.
        """
        print(f"DEBUG get_filtered_battery_options called: hubs={selected_hubs}, min={min_capacity}, max={max_capacity}", flush=True)
        filtered_batteries = []

        for b in self.battery_options:
            # Filter by hub if any hubs are selected
            if selected_hubs and b['hub_id'] not in selected_hubs:
                continue

            # Filter by capacity range
            capacity = b['capacity_wh']
            if capacity < min_capacity or capacity > max_capacity:
                continue

            filtered_batteries.append(b)

        print(f"DEBUG get_filtered_battery_options returning {len(filtered_batteries)} batteries", flush=True)
        # Return as dictionary for CrossSelector options
        return {f"Battery {b['battery_id']} ({b['capacity_wh']}Wh, {b['status']})": b['battery_id']
                for b in filtered_batteries}

    def load_rental_options(self, hub_id=None):
        """Load active PUE rentals for selected hub"""
        try:
            if hub_id:
                query = text("""
                    SELECT
                        r.rentral_id,
                        r.battery_id,
                        r.user_id,
                        u.Name as user_name,
                        b.hub_id
                    FROM rental r
                    JOIN bepppbattery b ON r.battery_id = b.battery_id
                    JOIN "user" u ON r.user_id = u.user_id
                    WHERE b.hub_id = :hub_id
                    AND r.is_active = true
                    AND r.battery_returned_date IS NULL
                    ORDER BY r.rentral_id DESC
                """)
                params = {'hub_id': hub_id}
            else:
                query = text("""
                    SELECT
                        r.rentral_id,
                        r.battery_id,
                        r.user_id,
                        u.Name as user_name,
                        b.hub_id
                    FROM rental r
                    JOIN bepppbattery b ON r.battery_id = b.battery_id
                    JOIN "user" u ON r.user_id = u.user_id
                    WHERE r.is_active = true
                    AND r.battery_returned_date IS NULL
                    ORDER BY r.rentral_id DESC
                """)
                params = {}

            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                return [{'rentral_id': row.rentral_id,
                        'battery_id': row.battery_id,
                        'user_name': row.user_name,
                        'hub_id': row.hub_id}
                        for row in result]
        except Exception as e:
            print(f"Error loading rentals: {e}")
            return []

    def get_time_filter(self):
        """Get time range based on selected time scale"""
        now = datetime.now()

        time_deltas = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
            'all': None
        }

        delta = time_deltas.get(self.time_scale)
        return now - delta if delta else None

    def load_data(self):
        """Load and aggregate data based on multi-select filters"""
        try:
            time_filter = self.get_time_filter()
            where_clauses = []
            params = {}

            # Build WHERE clauses based on filters

            # Hub filter
            if self.selected_hubs and len(self.selected_hubs) > 0:
                where_clauses.append("b.hub_id = ANY(:hub_ids)")
                params['hub_ids'] = self.selected_hubs

            # Battery filter - if no batteries selected, return empty data
            print(f"DEBUG load_data: selected_batteries = {self.selected_batteries}", flush=True)
            print(f"DEBUG load_data: selected_batteries type = {type(self.selected_batteries)}", flush=True)
            print(f"DEBUG load_data: selected_batteries length = {len(self.selected_batteries) if self.selected_batteries else 0}", flush=True)

            if not self.selected_batteries or len(self.selected_batteries) == 0:
                # Set empty DataFrame when no batteries are selected
                # Must match the structure of a query result to properly trigger empty state
                print("DEBUG load_data: Setting empty DataFrame - no batteries selected", flush=True)
                self.data = pd.DataFrame(columns=[
                    'timestamp', 'state_of_charge', 'voltage', 'current_amps',
                    'power_watts', 'temp_battery', 'charging_current', 'charger_power',
                    'charger_voltage', 'usb_power', 'usb_voltage', 'amp_hours_consumed',
                    'total_charge_consumed'
                ])
                print(f"DEBUG load_data: self.data is now empty: {self.data.empty}", flush=True)
                print(f"DEBUG load_data: self.data shape: {self.data.shape}", flush=True)
                print(f"DEBUG load_data: self.data columns: {list(self.data.columns)}", flush=True)
                return
            else:
                where_clauses.append("ld.battery_id = ANY(:battery_ids)")
                params['battery_ids'] = self.selected_batteries
                print(f"DEBUG load_data: Filtering for battery IDs: {self.selected_batteries}", flush=True)

            # Capacity range filter
            if self.min_capacity > 0 or self.max_capacity < 10000:
                where_clauses.append("b.battery_capacity_wh BETWEEN :min_cap AND :max_cap")
                params['min_cap'] = self.min_capacity
                params['max_cap'] = self.max_capacity

            # PUE type filter - batteries that have rentals with specific PUE types
            if self.selected_pue_types and len(self.selected_pue_types) > 0:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM rental r
                        JOIN rental_pue_item rpi ON r.rentral_id = rpi.rental_id
                        JOIN pue_item pue ON rpi.pue_item_id = pue.pue_item_id
                        WHERE r.battery_id = ld.battery_id
                        AND pue.pue_type = ANY(:pue_types)
                    )
                """)
                params['pue_types'] = self.selected_pue_types

            # Filter to only batteries with ANY PUE rentals
            if self.filter_batteries_with_pue:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM rental r
                        JOIN rental_pue_item rpi ON r.rentral_id = rpi.rental_id
                        WHERE r.battery_id = ld.battery_id
                    )
                """)

            # Time filter
            if time_filter:
                where_clauses.append("ld.timestamp >= :time_filter")
                params['time_filter'] = time_filter

            # Combine all WHERE clauses
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Enhanced query with all data fields
            query = text(f"""
                SELECT
                    ld.timestamp,
                    AVG(ld.state_of_charge) as state_of_charge,
                    AVG(ld.voltage) as voltage,
                    SUM(ld.current_amps) as current_amps,
                    SUM(ld.power_watts) as power_watts,
                    AVG(ld.temp_battery) as temp_battery,
                    SUM(ld.charging_current) as charging_current,
                    SUM(ld.charger_power) as charger_power,
                    AVG(ld.charger_voltage) as charger_voltage,
                    SUM(ld.usb_power) as usb_power,
                    AVG(ld.usb_voltage) as usb_voltage,
                    SUM(ld.amp_hours_consumed) as amp_hours_consumed,
                    SUM(ld.total_charge_consumed) as total_charge_consumed
                FROM livedata ld
                JOIN bepppbattery b ON ld.battery_id = b.battery_id
                {where_clause}
                GROUP BY ld.timestamp
                ORDER BY ld.timestamp ASC
            """)

            # Load data
            self.data = pd.read_sql(query, self.engine, params=params)

            if not self.data.empty:
                self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
                self.data = self.data.set_index('timestamp')

                # Apply aggregation interval (convert label to pandas time code)
                interval_code = self.aggregation_mapping.get(self.aggregation_interval, '30T')
                self.data = self.data.resample(interval_code).agg({
                    'state_of_charge': 'mean',
                    'voltage': 'mean',
                    'current_amps': 'sum',
                    'power_watts': 'sum',
                    'temp_battery': 'mean',
                    'charging_current': 'sum',
                    'charger_power': 'sum',
                    'charger_voltage': 'mean',
                    'usb_power': 'sum',
                    'usb_voltage': 'mean',
                    'amp_hours_consumed': 'sum',
                    'total_charge_consumed': 'sum'
                })

                # Fill missing values with forward fill then back fill
                self.data = self.data.ffill().bfill()

            return self.data

        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def get_title_prefix(self):
        """Get title prefix based on current filters"""
        parts = []

        # Hubs
        if self.selected_hubs and len(self.selected_hubs) > 0:
            if len(self.selected_hubs) == 1:
                hub_name = next((h['hub_name'] for h in self.hub_options if h['hub_id'] == self.selected_hubs[0]), 'Unknown')
                parts.append(f"Hub: {hub_name}")
            else:
                parts.append(f"{len(self.selected_hubs)} Hubs")

        # Batteries
        if self.selected_batteries and len(self.selected_batteries) > 0:
            if len(self.selected_batteries) == 1:
                parts.append(f"Battery {self.selected_batteries[0]}")
            else:
                parts.append(f"{len(self.selected_batteries)} Batteries")

        # Capacity filter
        if self.min_capacity > 0 or self.max_capacity < 10000:
            parts.append(f"{self.min_capacity}-{self.max_capacity}Wh")

        # PUE types
        if self.selected_pue_types and len(self.selected_pue_types) > 0:
            if len(self.selected_pue_types) == 1:
                parts.append(f"PUE: {self.selected_pue_types[0]}")
            else:
                parts.append(f"{len(self.selected_pue_types)} PUE types")

        # PUE filter flag
        if self.filter_batteries_with_pue:
            parts.append("With PUE Rentals")

        return " | ".join(parts) if parts else "All Data"

    @param.depends('update_trigger')
    def power_plot(self):
        """Create power consumption plot with aggregation"""
        # Data is loaded when update button is clicked
        print(f"DEBUG power_plot: update_trigger={self.update_trigger}", flush=True)
        print(f"DEBUG power_plot: self.data is None: {self.data is None}", flush=True)
        print(f"DEBUG power_plot: self.data.empty: {self.data.empty if self.data is not None else 'N/A'}", flush=True)

        if self.data is None or self.data.empty:
            print("DEBUG power_plot: Returning 'No data available' message", flush=True)
            return pn.pane.Markdown("### No data available for current selection")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval  # Already a display label

        plot = self.data.hvplot.line(
            y='power_watts',
            title=f'{title_prefix} - Power Consumption ({interval_label} intervals)',
            ylabel='Power (W)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#FF9800',
            line_width=2,
            grid=True
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def soc_plot(self):
        """Create SOC plot"""
        # Data is loaded when update button is clicked
        print(f"DEBUG soc_plot: update_trigger={self.update_trigger}", flush=True)
        print(f"DEBUG soc_plot: self.data is None: {self.data is None}", flush=True)
        print(f"DEBUG soc_plot: self.data.empty: {self.data.empty if self.data is not None else 'N/A'}", flush=True)

        if self.data is None or self.data.empty:
            print("DEBUG soc_plot: Returning 'No data available' message", flush=True)
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval  # Already a display label

        plot = self.data.hvplot.area(
            y='state_of_charge',
            title=f'{title_prefix} - State of Charge ({interval_label} intervals)',
            ylabel='SOC (%)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#4CAF50',
            alpha=0.6,
            grid=True,
            ylim=(0, 100)
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def voltage_plot(self):
        """Create voltage plot"""
        # Data is loaded when update button is clicked

        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval  # Already a display label

        plot = self.data.hvplot.line(
            y='voltage',
            title=f'{title_prefix} - Average Voltage ({interval_label} intervals)',
            ylabel='Voltage (V)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#1976D2',
            line_width=2,
            grid=True
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def temperature_plot(self):
        """Create temperature plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval

        plot = self.data.hvplot.line(
            y='temp_battery',
            title=f'{title_prefix} - Battery Temperature ({interval_label} intervals)',
            ylabel='Temperature (°C)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#F44336',
            line_width=2,
            grid=True
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def current_plot(self):
        """Create current (amps) plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval

        # Overlay battery current and charging current
        battery_current = self.data.hvplot.line(
            y='current_amps',
            label='Battery Current',
            ylabel='Current (A)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#2196F3',
            line_width=2,
            grid=True
        )

        charging_current = self.data.hvplot.line(
            y='charging_current',
            label='Charging Current',
            ylabel='Current (A)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#4CAF50',
            line_width=2,
            grid=True
        )

        plot = (battery_current * charging_current).opts(
            title=f'{title_prefix} - Current Flow ({interval_label} intervals)',
            legend_position='top_right'
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def usb_power_plot(self):
        """Create USB power plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval

        plot = self.data.hvplot.line(
            y='usb_power',
            title=f'{title_prefix} - USB Power Consumption ({interval_label} intervals)',
            ylabel='USB Power (W)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#9C27B0',
            line_width=2,
            grid=True
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def charger_power_plot(self):
        """Create charger power plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval

        plot = self.data.hvplot.line(
            y='charger_power',
            title=f'{title_prefix} - Charger Power Input ({interval_label} intervals)',
            ylabel='Charger Power (W)',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#FF5722',
            line_width=2,
            grid=True
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    @param.depends('update_trigger')
    def energy_consumed_plot(self):
        """Create energy consumed (Ah) plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        title_prefix = self.get_title_prefix()
        interval_label = self.aggregation_interval

        plot = self.data.hvplot.line(
            y='amp_hours_consumed',
            title=f'{title_prefix} - Amp Hours Consumed ({interval_label} intervals)',
            ylabel='Ah Consumed',
            xlabel='Time',
            height=400,
            responsive=True,
            color='#795548',
            line_width=2,
            grid=True
        )

        return pn.Card(
            pn.pane.HoloViews(plot, sizing_mode='stretch_width'),
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'border': '1px solid #e0e0e0'}
        )

    def load_single_battery_data(self, battery_id):
        """Load data for a single battery without aggregation"""
        if not battery_id:
            return pd.DataFrame()

        try:
            time_filter = self.get_time_filter()
            params = {'battery_id': battery_id}
            where_clauses = ["ld.battery_id = :battery_id"]

            if time_filter:
                where_clauses.append("ld.timestamp >= :time_filter")
                params['time_filter'] = time_filter

            where_clause = "WHERE " + " AND ".join(where_clauses)

            query = text(f"""
                SELECT
                    ld.timestamp,
                    ld.state_of_charge,
                    ld.voltage,
                    ld.current_amps,
                    ld.power_watts,
                    ld.temp_battery,
                    ld.charging_current,
                    ld.charger_power,
                    ld.charger_voltage,
                    ld.usb_power,
                    ld.usb_voltage,
                    ld.amp_hours_consumed,
                    ld.total_charge_consumed
                FROM livedata ld
                {where_clause}
                ORDER BY ld.timestamp ASC
            """)

            df = pd.read_sql(query, self.engine, params=params)

            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')

                # Apply aggregation interval
                interval_code = self.aggregation_mapping.get(self.aggregation_interval, '30T')
                df = df.resample(interval_code).agg({
                    'state_of_charge': 'mean',
                    'voltage': 'mean',
                    'current_amps': 'sum',
                    'power_watts': 'sum',
                    'temp_battery': 'mean',
                    'charging_current': 'sum',
                    'charger_power': 'sum',
                    'charger_voltage': 'mean',
                    'usb_power': 'sum',
                    'usb_voltage': 'mean',
                    'amp_hours_consumed': 'sum',
                    'total_charge_consumed': 'sum'
                })

                df = df.ffill().bfill()

            return df

        except Exception as e:
            print(f"Error loading single battery data: {e}", flush=True)
            return pd.DataFrame()

    @param.depends('selected_single_battery', 'update_trigger')
    def single_battery_view(self):
        """Create comprehensive single battery view"""
        if not self.selected_single_battery:
            return pn.pane.Markdown("### Please select a battery from the dropdown above")

        # Load data for this specific battery
        battery_data = self.load_single_battery_data(self.selected_single_battery)

        if battery_data.empty:
            return pn.pane.Markdown(f"### No data available for Battery {self.selected_single_battery}")

        # Create multi-metric plot (Victron-style)
        import holoviews as hv

        # SOC plot
        soc_plot = battery_data.hvplot.line(
            y='state_of_charge',
            label='SOC (%)',
            color='#4CAF50',
            line_width=2,
            ylabel='SOC (%)',
            height=250,
            responsive=True,
            grid=True
        )

        # Power plot (consumption and charging)
        power_plot = battery_data.hvplot.line(
            y='power_watts',
            label='Power (W)',
            color='#FF9800',
            line_width=2,
            ylabel='Power (W)',
            height=250,
            responsive=True,
            grid=True
        )

        charger_plot = battery_data.hvplot.line(
            y='charger_power',
            label='Charger (W)',
            color='#2196F3',
            line_width=2,
            ylabel='Charger (W)',
            height=250,
            responsive=True,
            grid=True
        )

        # Voltage plot
        voltage_plot = battery_data.hvplot.line(
            y='voltage',
            label='Voltage (V)',
            color='#9C27B0',
            line_width=2,
            ylabel='Voltage (V)',
            height=250,
            responsive=True,
            grid=True
        )

        # Current plot
        current_plot = battery_data.hvplot.line(
            y='current_amps',
            label='Current (A)',
            color='#00BCD4',
            line_width=2,
            ylabel='Current (A)',
            height=250,
            responsive=True,
            grid=True
        )

        # Temperature plot
        temp_plot = battery_data.hvplot.line(
            y='temp_battery',
            label='Temperature (°C)',
            color='#F44336',
            line_width=2,
            ylabel='Temp (°C)',
            height=250,
            responsive=True,
            grid=True
        )

        # USB Power
        usb_plot = battery_data.hvplot.line(
            y='usb_power',
            label='USB Power (W)',
            color='#795548',
            line_width=2,
            ylabel='USB (W)',
            height=250,
            responsive=True,
            grid=True
        )

        # Statistics panel for this battery
        stats_md = f"""
        ### Battery {self.selected_single_battery} Statistics

        | Metric | Value |
        |--------|-------|
        | **Data Points** | {len(battery_data)} |
        | **Avg SOC** | {battery_data['state_of_charge'].mean():.1f}% |
        | **Avg Voltage** | {battery_data['voltage'].mean():.2f}V |
        | **Avg Power** | {battery_data['power_watts'].mean():.2f}W |
        | **Peak Power** | {battery_data['power_watts'].max():.2f}W |
        | **Avg Temperature** | {battery_data['temp_battery'].mean():.1f}°C |
        | **Total Ah Consumed** | {battery_data['amp_hours_consumed'].sum():.2f}Ah |
        | **Avg Charger Power** | {battery_data['charger_power'].mean():.2f}W |
        | **Avg USB Power** | {battery_data['usb_power'].mean():.2f}W |
        """

        return pn.Column(
            pn.pane.Markdown(stats_md, sizing_mode='stretch_width'),
            pn.layout.Divider(),
            pn.pane.Markdown(f"### State of Charge"),
            pn.pane.HoloViews(soc_plot, sizing_mode='stretch_width'),
            pn.pane.Markdown(f"### Power Consumption & Charging"),
            pn.pane.HoloViews((power_plot * charger_plot).opts(legend_position='top_right'), sizing_mode='stretch_width'),
            pn.pane.Markdown(f"### Voltage & Current"),
            pn.Row(
                pn.pane.HoloViews(voltage_plot, sizing_mode='stretch_width'),
                pn.pane.HoloViews(current_plot, sizing_mode='stretch_width'),
            ),
            pn.pane.Markdown(f"### Temperature & USB Power"),
            pn.Row(
                pn.pane.HoloViews(temp_plot, sizing_mode='stretch_width'),
                pn.pane.HoloViews(usb_plot, sizing_mode='stretch_width'),
            ),
            sizing_mode='stretch_both'
        )

    def load_battery_hub_history(self):
        """Load battery check-in/check-out history from rental data"""
        try:
            time_filter = self.get_time_filter()
            where_clauses = []
            params = {}

            # Filter by selected batteries
            if self.selected_batteries and len(self.selected_batteries) > 0:
                where_clauses.append("r.battery_id = ANY(:battery_ids)")
                params['battery_ids'] = self.selected_batteries

            # Filter by selected hubs
            if self.selected_hubs and len(self.selected_hubs) > 0:
                where_clauses.append("b.hub_id = ANY(:hub_ids)")
                params['hub_ids'] = self.selected_hubs

            # Time filter
            if time_filter:
                where_clauses.append("(r.timestamp_taken >= :time_filter OR r.battery_returned_date >= :time_filter)")
                params['time_filter'] = time_filter

            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            query = text(f"""
                SELECT
                    r.battery_id,
                    b.hub_id,
                    h.what_three_word_location as hub_name,
                    r.timestamp_taken,
                    r.battery_returned_date,
                    r.status
                FROM rental r
                JOIN bepppbattery b ON r.battery_id = b.battery_id
                JOIN solarhub h ON b.hub_id = h.hub_id
                {where_clause}
                ORDER BY r.timestamp_taken ASC
            """)

            df = pd.read_sql(query, self.engine, params=params)
            return df

        except Exception as e:
            print(f"Error loading battery hub history: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    @param.depends('update_trigger')
    def battery_hub_history_view(self):
        """Create battery location/checkout history visualization"""
        history = self.load_battery_hub_history()

        if history.empty:
            return pn.pane.Markdown("### No rental history available for filtered batteries")

        # Calculate battery counts at each hub over time
        timeline_data = []

        for _, row in history.iterrows():
            start = pd.to_datetime(row['timestamp_taken'])

            # Battery checked out (leaves hub)
            timeline_data.append({
                'timestamp': start,
                'hub_name': row['hub_name'],
                'hub_id': row['hub_id'],
                'battery_id': row['battery_id'],
                'event': 'checkout',
                'change': -1
            })

            # Battery returned (comes back to hub)
            if row['status'] != 'active' and pd.notna(row['battery_returned_date']):
                return_time = pd.to_datetime(row['battery_returned_date'])
                timeline_data.append({
                    'timestamp': return_time,
                    'hub_name': row['hub_name'],
                    'hub_id': row['hub_id'],
                    'battery_id': row['battery_id'],
                    'event': 'return',
                    'change': 1
                })

        if not timeline_data:
            return pn.pane.Markdown("### No checkout/return events found in selected time range")

        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values('timestamp')

        # Group by hub and calculate running count
        plots = []
        colors = ['#1976D2', '#FF9800', '#4CAF50', '#F44336', '#9C27B0', '#00BCD4']

        for i, hub_id in enumerate(timeline_df['hub_id'].unique()):
            hub_data = timeline_df[timeline_df['hub_id'] == hub_id].copy()
            hub_name = hub_data['hub_name'].iloc[0]

            # Calculate cumulative change
            hub_data = hub_data.set_index('timestamp')
            hub_data['cumulative_change'] = hub_data['change'].cumsum()

            # Start from initial count (number of batteries at this hub)
            initial_count = sum(1 for b in self.battery_options if b['hub_id'] == hub_id)
            hub_data['battery_count'] = initial_count + hub_data['cumulative_change']

            color = colors[i % len(colors)]

            plot = hub_data['battery_count'].hvplot.line(
                label=f"{hub_name} (Hub {hub_id})",
                color=color,
                line_width=2,
                ylabel='Number of Batteries',
                xlabel='Time',
                height=400,
                responsive=True,
                grid=True
            )
            plots.append(plot)

        # Combine all hub plots
        if plots:
            combined_plot = plots[0]
            for plot in plots[1:]:
                combined_plot = combined_plot * plot

            combined_plot = combined_plot.opts(
                title='Battery Count at Each Hub Over Time',
                legend_position='top_right'
            )

            stats_md = f"""
            ### Battery Location Tracking

            - **Total Events:** {len(timeline_df)} (checkouts + returns)
            - **Hubs Tracked:** {len(plots)}
            - **Time Range:** {timeline_df['timestamp'].min().strftime('%Y-%m-%d')} to {timeline_df['timestamp'].max().strftime('%Y-%m-%d')}
            - **Batteries:** {timeline_df['battery_id'].nunique()} unique batteries
            """

            return pn.Column(
                pn.pane.Markdown(stats_md),
                pn.pane.HoloViews(combined_plot, sizing_mode='stretch_width'),
                sizing_mode='stretch_both'
            )
        else:
            return pn.pane.Markdown("### No hub data to display")

    @param.depends('update_trigger')
    def stats_panel(self):
        """Create statistics summary"""
        # Data is loaded when update button is clicked

        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No statistics available")

        stats = {
            'Data Points': len(self.data),
            'Avg Power': f"{self.data['power_watts'].mean():.2f} W",
            'Peak Power': f"{self.data['power_watts'].max():.2f} W",
            'Avg Voltage': f"{self.data['voltage'].mean():.2f} V",
            'Avg SOC': f"{self.data['state_of_charge'].mean():.1f} %",
            'Avg Temp': f"{self.data['temp_battery'].mean():.1f} °C"
        }

        indicators = []
        colors = ['#1976D2', '#FF9800', '#F44336', '#4CAF50', '#9C27B0', '#00BCD4']

        for i, (key, value) in enumerate(stats.items()):
            ind = pn.indicators.String(
                name=key,
                value=str(value),
                font_size='18pt',
                title_size='12pt',
                default_color=colors[i % len(colors)]
            )
            indicators.append(ind)

        return pn.FlexBox(*indicators, justify_content='space-around')

    def view(self):
        """Create the main dashboard view with multi-select filters"""

        # Header
        header = pn.pane.Markdown(
            """
            # 🔋 Enhanced Battery Analytics Dashboard
            ### Multi-select filters with flexible aggregation
            """,
            sizing_mode='stretch_width',
            styles={'background': '#1976D2', 'color': 'white', 'padding': '20px', 'border-radius': '5px'}
        )

        # STEP 1: Hub Selection
        hub_options = {f"{h['hub_name']} (ID: {h['hub_id']})": h['hub_id'] for h in self.hub_options}
        hub_selector = pn.widgets.CheckBoxGroup(
            name='1️⃣ Select Hubs (or none for all)',
            options=hub_options,
            value=list(self.selected_hubs),
            inline=False
        )
        hub_selector.link(self, callbacks={'value': lambda target, event: setattr(target, 'selected_hubs', event.new)})

        # STEP 2: Capacity Range Filter
        min_capacity_input = pn.widgets.IntInput(
            name='Min Capacity (Wh)',
            value=int(self.min_capacity),
            start=0,
            end=10000,
            step=100,
            width=200
        )
        min_capacity_input.link(self, value='min_capacity')

        max_capacity_input = pn.widgets.IntInput(
            name='Max Capacity (Wh)',
            value=int(self.max_capacity),
            start=0,
            end=10000,
            step=100,
            width=200
        )
        max_capacity_input.link(self, value='max_capacity')

        capacity_filter = pn.Column(
            pn.pane.Markdown("**2️⃣ Filter by Capacity Range**"),
            pn.Row(min_capacity_input, max_capacity_input)
        )

        # STEP 3: Battery Selection (dynamically filtered by hub and capacity)
        # Use pn.bind to make options reactive to hub and capacity changes
        battery_selector = pn.widgets.CrossSelector(
            name='3️⃣ Select Batteries (all included by default, move left to exclude)',
            value=list(self.selected_batteries),
            options=pn.bind(self.get_filtered_battery_options,
                          self.param.selected_hubs,
                          self.param.min_capacity,
                          self.param.max_capacity),
            height=300,
            sizing_mode='stretch_width'
        )
        # Use param.watch to sync changes back to parameter
        battery_selector.param.watch(lambda event: setattr(self, 'selected_batteries', event.new), 'value')

        # PUE type multi-select
        pue_selector = pn.widgets.CheckBoxGroup(
            name='🔌 PUE Types (batteries with these PUE rentals)',
            options=self.pue_type_options,
            value=list(self.selected_pue_types),
            inline=False
        )
        pue_selector.link(self, callbacks={'value': lambda target, event: setattr(target, 'selected_pue_types', event.new)})

        # PUE filter checkbox
        pue_filter_checkbox = pn.widgets.Checkbox(
            name='Only show batteries with PUE rentals',
            value=self.filter_batteries_with_pue
        )
        pue_filter_checkbox.link(self, value='filter_batteries_with_pue')

        # Time controls
        time_controls = pn.Column(
            pn.pane.Markdown("**📅 Time Range & Aggregation**"),
            pn.Param(
                self.param.time_scale,
                widgets={'time_scale': {'type': pn.widgets.RadioButtonGroup, 'button_type': 'success'}}
            ),
            pn.Param(
                self.param.aggregation_interval,
                widgets={'aggregation_interval': pn.widgets.Select}
            )
        )

        # Update button - simple button with on_click callback
        update_button = pn.widgets.Button(
            name='🔄 Update Dashboard',
            button_type='primary',
            width=300,
            height=50
        )
        update_button.on_click(self.trigger_update)

        # Last updated info
        last_updated_info = pn.pane.Markdown(
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Battery Hub Management System*",
            sizing_mode='stretch_width',
            margin=(10, 10, 10, 10),
            styles={'text-align': 'center', 'color': '#666', 'font-size': '12px'}
        )

        # Cascading filters panel (collapsible)
        cascading_filters = pn.Card(
            pn.Column(
                hub_selector,
                pn.layout.Divider(),
                capacity_filter,
                pn.layout.Divider(),
                battery_selector,
                pn.layout.Divider(),
                pue_filter_checkbox,
                pue_selector,
            ),
            title='🔍 Cascading Filters (Hub → Capacity → Batteries → PUE)',
            collapsed=False,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        # Controls section - wrapped in collapsible Card
        controls = pn.Card(
            pn.Column(
                time_controls,
                cascading_filters,
                pn.layout.Divider(),
                pn.Row(
                    pn.layout.HSpacer(),
                    update_button,
                    pn.layout.HSpacer(),
                    sizing_mode='stretch_width'
                ),
                last_updated_info,
                sizing_mode='stretch_width'
            ),
            title='⚙️ Filters & Controls',
            collapsed=False,
            collapsible=True,
            sizing_mode='stretch_width',
            header_background='#1976D2',
            header_color='white',
            margin=(10, 10, 10, 10)
        )

        # Information cards for each tab
        overview_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** Summary statistics and side-by-side comparison of Power and State of Charge.

            **Aggregation:** Data is aggregated across ALL filtered batteries:
            - **Power (Watts):** SUM of power consumption from all selected batteries
            - **State of Charge (SOC):** MEAN (average) SOC across all selected batteries
            - **Voltage:** MEAN voltage across all batteries
            - **Temperature:** MEAN temperature across all batteries
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        power_soc_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** Power consumption and State of Charge over time.

            **Aggregation:**
            - **Power (Watts):** SUM across all filtered batteries (total fleet power)
            - **State of Charge (%):** MEAN (average) across all filtered batteries

            **Time interval:** Data is resampled according to your selected aggregation interval.
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        voltage_current_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** Battery voltage and current flow (both battery current and charging current).

            **Aggregation:**
            - **Voltage (V):** MEAN (average) voltage across all filtered batteries
            - **Battery Current (A):** SUM of current across all batteries (negative = discharge, positive = charge)
            - **Charging Current (A):** SUM of charging current across all batteries

            **Note:** Current values show total fleet current draw or charge.
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        temperature_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** Battery temperature over time.

            **Aggregation:**
            - **Temperature (°C):** MEAN (average) temperature across all filtered batteries

            **Use case:** Monitor thermal performance and identify potential overheating issues.
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        usb_power_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** USB port power consumption over time.

            **Aggregation:**
            - **USB Power (W):** SUM of USB power output across all filtered batteries

            **Use case:** Track power drawn from USB ports by connected devices.
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        charger_power_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** Solar charger power input over time.

            **Aggregation:**
            - **Charger Power (W):** SUM of charger power input across all filtered batteries

            **Use case:** Monitor solar charging performance and total energy being harvested.
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        energy_consumed_info = pn.Card(
            pn.pane.Markdown("""
            **What this shows:** Cumulative energy consumed measured in Amp-hours (Ah).

            **Aggregation:**
            - **Amp Hours Consumed (Ah):** SUM across all filtered batteries

            **Use case:** Track total energy consumption over time. This is a cumulative metric.
            """),
            title='ℹ️ About this tab',
            collapsed=True,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        # Tabs with info cards
        tabs = pn.Tabs(
            ('📊 Overview', pn.Column(
                overview_info,
                self.stats_panel,
                pn.Row(
                    self.power_plot,
                    self.soc_plot,
                    sizing_mode='stretch_width'
                ),
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('⚡ Power & SOC', pn.Column(
                power_soc_info,
                self.power_plot,
                self.soc_plot,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('🔋 Voltage & Current', pn.Column(
                voltage_current_info,
                self.voltage_plot,
                self.current_plot,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('🌡️ Temperature', pn.Column(
                temperature_info,
                self.temperature_plot,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('🔌 USB Power', pn.Column(
                usb_power_info,
                self.usb_power_plot,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('⚡ Charger Power', pn.Column(
                charger_power_info,
                self.charger_power_plot,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('📈 Energy Consumed (Ah)', pn.Column(
                energy_consumed_info,
                self.energy_consumed_plot,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('📍 Hub Location Tracking', pn.Column(
                pn.Card(
                    pn.pane.Markdown("""
                    **What this shows:** Battery count at each hub over time based on rental checkout/return events.

                    **How it works:**
                    - When a battery is checked out, the count at that hub decreases
                    - When a battery is returned, the count at that hub increases
                    - Each line represents a different hub

                    **Use case:** Track battery inventory levels at each hub location over time.
                    """),
                    title='ℹ️ About this tab',
                    collapsed=True,
                    collapsible=True,
                    sizing_mode='stretch_width'
                ),
                self.battery_hub_history_view,
                sizing_mode='stretch_both',
                margin=(15, 15, 15, 15)
            )),
            ('🔋 Single Battery Detail', pn.Column(
                pn.Card(
                    pn.pane.Markdown("""
                    **What this shows:** Complete overview of a single selected battery.

                    **Data shown:**
                    - State of Charge over time
                    - Power consumption vs. charging (overlaid)
                    - Voltage and Current side-by-side
                    - Temperature and USB Power side-by-side
                    - Summary statistics table

                    **How to use:** Select a battery from the dropdown below to view its detailed metrics.
                    """),
                    title='ℹ️ About this tab',
                    collapsed=True,
                    collapsible=True,
                    sizing_mode='stretch_width'
                ),
                pn.Card(
                    pn.Column(
                        pn.pane.Markdown("### Select a battery from your filtered list:"),
                        pn.Param(
                            self.param.selected_single_battery,
                            widgets={
                                'selected_single_battery': {
                                    'type': pn.widgets.Select,
                                    'name': 'Battery',
                                    'options': {f"Battery {b}": b for b in self.selected_batteries} if self.selected_batteries else {"No batteries": None},
                                    'width': 400
                                }
                            }
                        )
                    ),
                    sizing_mode='stretch_width',
                    margin=(10, 10, 10, 10),
                    styles={'background': '#fafafa'}
                ),
                pn.layout.Divider(),
                self.single_battery_view,
                sizing_mode='stretch_both',
                margin=(15, 15, 100, 15)  # Extra bottom margin to prevent footer overlap
            )),
            dynamic=True,
            sizing_mode='stretch_both'
        )

        # Main layout (footer removed - now in controls section)
        dashboard = pn.Column(
            header,
            controls,
            tabs,
            sizing_mode='stretch_both'
        )

        return dashboard

# Module-level code that runs once at startup
print("=== DEBUG: Module loading ===")
print(f"Session args at module load: {pn.state.session_args}")

# Get token from query parameters (evaluated at module load - THIS IS THE PROBLEM!)
token = pn.state.session_args.get('token', [None])[0]
print(f"Token from args at module load: {token}")

if token:
    token = token.decode('utf-8') if isinstance(token, bytes) else token
    print(f"Decoded token (first 50 chars): {token[:50] if token else None}...")

# Verify token
if not token:
    print("No token provided at module load")
    error_view = pn.Column(
        "# 🔒 Authentication Required",
        "Please log in through the main application to access the analytics dashboard.",
        pn.pane.Markdown("[Return to Login](https://data.beppp.cloud)"),
        styles={'padding': '50px', 'text-align': 'center'}
    )
    error_view.servable(title='Battery Analytics Dashboard')
else:
    payload = verify_token(token)
    print(f"Token verification result: {payload}")

    if not payload:
        print("Invalid token at module load")
        error_view = pn.Column(
            "# 🔒 Invalid Authentication",
            "Your session has expired or is invalid. Please log in again.",
            pn.pane.Markdown("[Return to Login](https://data.beppp.cloud)"),
            styles={'padding': '50px', 'text-align': 'center'}
        )
        error_view.servable(title='Battery Analytics Dashboard')
    else:
        # Token is valid, create and return the dashboard
        print(f"Token valid for user: {payload.get('sub')}")
        try:
            dashboard = EnhancedBatteryAnalyticsDashboard()
            dashboard.view().servable(title='Battery Analytics Dashboard')
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            import traceback
            traceback.print_exc()
            error_view = pn.Column(
                "# ⚠️ Error Loading Dashboard",
                f"An error occurred: {str(e)}",
                styles={'padding': '50px', 'text-align': 'center'}
            )
            error_view.servable(title='Battery Analytics Dashboard')
