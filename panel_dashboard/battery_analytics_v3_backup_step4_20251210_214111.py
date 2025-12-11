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

# Enable Panel extensions
pn.extension('tabulator', sizing_mode='stretch_width')
hv.extension('bokeh')

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://beppp:changeme@db:5432/beppp')

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

    # Battery capacity filter
    min_capacity = param.Number(default=0, bounds=(0, None), label="Min Capacity (Wh)")
    max_capacity = param.Number(default=10000, bounds=(0, None), label="Max Capacity (Wh)")

    # PUE filters
    selected_pue_types = param.ListSelector(default=[], label="PUE Types")
    filter_batteries_with_pue = param.Boolean(default=False, label="Only batteries with PUE rentals")

    # Advanced filter mode
    use_advanced_filters = param.Boolean(default=False, label="Use Advanced Filters")

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

        # Set parameter objects after loading options
        self.param.selected_hubs.objects = [h['hub_id'] for h in self.hub_options]
        self.param.selected_batteries.objects = [b['battery_id'] for b in self.battery_options]
        self.param.selected_pue_types.objects = self.pue_type_options

        self.load_data()

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
                    capacity_wh,
                    brand,
                    model
                FROM bepppbattery
                ORDER BY battery_id
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [{'battery_id': row.battery_id,
                        'hub_id': row.hub_id,
                        'capacity_wh': row.capacity_wh or 0,
                        'brand': row.brand,
                        'model': row.model}
                        for row in result]
        except Exception as e:
            print(f"Error loading batteries: {e}")
            return []

    def load_pue_type_options(self):
        """Load distinct PUE types from rental_pue_items"""
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

    @param.depends('selected_hubs', 'selected_batteries', 'min_capacity', 'max_capacity',
                   'selected_pue_types', 'filter_batteries_with_pue',
                   'time_scale', 'aggregation_interval', watch=True)
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

            # Battery filter
            if self.selected_batteries and len(self.selected_batteries) > 0:
                where_clauses.append("ld.battery_id = ANY(:battery_ids)")
                params['battery_ids'] = self.selected_batteries

            # Capacity range filter
            if self.min_capacity > 0 or self.max_capacity < 10000:
                where_clauses.append("b.capacity_wh BETWEEN :min_cap AND :max_cap")
                params['min_cap'] = self.min_capacity
                params['max_cap'] = self.max_capacity

            # PUE type filter - batteries that have rentals with specific PUE types
            if self.selected_pue_types and len(self.selected_pue_types) > 0:
                where_clauses.append("""
                    EXISTS (
                        SELECT 1 FROM rental r
                        JOIN rental_pue_items rpi ON r.rentral_id = rpi.rental_id
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
                        JOIN rental_pue_items rpi ON r.rentral_id = rpi.rental_id
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
                }).dropna()

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

    @param.depends('selected_hubs', 'selected_batteries', 'min_capacity', 'max_capacity',
                   'selected_pue_types', 'filter_batteries_with_pue',
                   'time_scale', 'aggregation_interval')
    def power_plot(self):
        """Create power consumption plot with aggregation"""
        if self.data is None or self.data.empty:
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

        return pn.pane.HoloViews(plot, sizing_mode='stretch_width')

    @param.depends('selected_hubs', 'selected_batteries', 'min_capacity', 'max_capacity',
                   'selected_pue_types', 'filter_batteries_with_pue',
                   'time_scale', 'aggregation_interval')
    def soc_plot(self):
        """Create SOC plot"""
        if self.data is None or self.data.empty:
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

        return pn.pane.HoloViews(plot, sizing_mode='stretch_width')

    @param.depends('selected_hubs', 'selected_batteries', 'min_capacity', 'max_capacity',
                   'selected_pue_types', 'filter_batteries_with_pue',
                   'time_scale', 'aggregation_interval')
    def voltage_plot(self):
        """Create voltage plot"""
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

        return pn.pane.HoloViews(plot, sizing_mode='stretch_width')

    @param.depends('selected_hubs', 'selected_batteries', 'min_capacity', 'max_capacity',
                   'selected_pue_types', 'filter_batteries_with_pue',
                   'time_scale', 'aggregation_interval')
    def stats_panel(self):
        """Create statistics summary"""
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

        # Hub multi-select checkboxes
        hub_options = {f"{h['hub_name']} (ID: {h['hub_id']})": h['hub_id'] for h in self.hub_options}
        hub_selector = pn.widgets.CheckBoxGroup(
            name='🏢 Select Hubs (select multiple or none for all)',
            options=hub_options,
            value=list(self.selected_hubs),
            inline=False
        )
        hub_selector.link(self, callbacks={'value': lambda target, event: setattr(target, 'selected_hubs', event.new)})

        # Battery multi-select checkboxes
        battery_options = {f"Battery {b['battery_id']} ({b['brand']} {b['model']}, {b['capacity_wh']}Wh)": b['battery_id']
                          for b in self.battery_options}
        battery_selector = pn.widgets.CheckBoxGroup(
            name='🔋 Select Batteries (select multiple or none for all)',
            options=battery_options,
            value=list(self.selected_batteries),
            inline=False
        )
        battery_selector.link(self, callbacks={'value': lambda target, event: setattr(target, 'selected_batteries', event.new)})

        # Capacity range sliders
        capacity_filter = pn.Column(
            pn.pane.Markdown("**⚡ Battery Capacity Filter (Wh)**"),
            pn.widgets.IntSlider(
                name='Min Capacity',
                start=0,
                end=10000,
                step=500,
                value=int(self.min_capacity)
            ).link(self, value='min_capacity'),
            pn.widgets.IntSlider(
                name='Max Capacity',
                start=0,
                end=10000,
                step=500,
                value=int(self.max_capacity)
            ).link(self, value='max_capacity')
        )

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

        # Advanced filters panel (collapsible)
        advanced_filters = pn.Card(
            pn.Column(
                hub_selector,
                battery_selector,
                capacity_filter,
                pue_selector,
                pue_filter_checkbox,
            ),
            title='🔍 Advanced Filters',
            collapsed=False,
            collapsible=True,
            sizing_mode='stretch_width'
        )

        # Controls section
        controls = pn.Column(
            time_controls,
            advanced_filters,
            sizing_mode='stretch_width'
        )

        # Tabs
        tabs = pn.Tabs(
            ('Overview', pn.Column(
                self.stats_panel,
                pn.Row(
                    self.power_plot,
                    self.soc_plot,
                    sizing_mode='stretch_width'
                ),
                sizing_mode='stretch_both'
            )),
            ('Detailed Analysis', pn.Column(
                self.voltage_plot,
                pn.Row(
                    self.power_plot,
                    sizing_mode='stretch_width'
                ),
                sizing_mode='stretch_both'
            )),
            dynamic=True,
            sizing_mode='stretch_both'
        )

        # Footer
        footer = pn.pane.Markdown(
            f"""
            ---
            *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Battery Hub Management System*
            """,
            sizing_mode='stretch_width'
        )

        # Main layout
        dashboard = pn.Column(
            header,
            controls,
            tabs,
            footer,
            sizing_mode='stretch_both'
        )

        return dashboard

# Create dashboard instance
dashboard = EnhancedBatteryAnalyticsDashboard()

# Make it servable
dashboard.view().servable(title='Enhanced Battery Analytics Dashboard')
