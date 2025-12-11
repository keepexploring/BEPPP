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
    """Enhanced Battery Analytics Dashboard with hierarchical selection"""

    # Parameters
    view_level = param.Selector(
        default='hub',
        objects=['hub', 'battery', 'pue_rental'],
        label="View Level"
    )

    selected_hub = param.Integer(default=None, allow_None=True, label="Hub")
    selected_battery = param.Integer(default=None, allow_None=True, label="Battery")
    selected_rental = param.Integer(default=None, allow_None=True, label="PUE Rental")

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
        self.hub_options = self.load_hub_options()
        self.battery_options = []
        self.rental_options = []

        # Set default hub if available
        if self.hub_options:
            self.selected_hub = self.hub_options[0]['hub_id']

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

    def load_battery_options(self, hub_id=None):
        """Load batteries for selected hub"""
        try:
            if hub_id:
                query = text("""
                    SELECT battery_id, hub_id
                    FROM bepppbattery
                    WHERE hub_id = :hub_id
                    ORDER BY battery_id
                """)
                params = {'hub_id': hub_id}
            else:
                query = text("""
                    SELECT battery_id, hub_id
                    FROM bepppbattery
                    ORDER BY battery_id
                """)
                params = {}

            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                return [{'battery_id': row.battery_id, 'hub_id': row.hub_id}
                        for row in result]
        except Exception as e:
            print(f"Error loading batteries: {e}")
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

    @param.depends('view_level', 'selected_hub', 'selected_battery', 'selected_rental',
                   'time_scale', 'aggregation_interval', watch=True)
    def load_data(self):
        """Load and aggregate data based on selection"""
        try:
            time_filter = self.get_time_filter()

            # Build query based on view level
            if self.view_level == 'hub':
                # Aggregate all batteries in hub
                where_clause = "WHERE b.hub_id = :hub_id" if self.selected_hub else ""
                params = {'hub_id': self.selected_hub} if self.selected_hub else {}

            elif self.view_level == 'battery':
                # Single battery or all batteries in hub
                if self.selected_battery:
                    where_clause = "WHERE ld.battery_id = :battery_id"
                    params = {'battery_id': self.selected_battery}
                elif self.selected_hub:
                    where_clause = "WHERE b.hub_id = :hub_id"
                    params = {'hub_id': self.selected_hub}
                else:
                    where_clause = ""
                    params = {}

            elif self.view_level == 'pue_rental':
                # PUE rental specific
                if self.selected_rental:
                    where_clause = "WHERE r.rentral_id = :rental_id"
                    params = {'rental_id': self.selected_rental}
                elif self.selected_hub:
                    where_clause = "WHERE b.hub_id = :hub_id AND r.is_active = true"
                    params = {'hub_id': self.selected_hub}
                else:
                    where_clause = "WHERE r.is_active = true"
                    params = {}
            else:
                where_clause = ""
                params = {}

            # Add time filter
            if time_filter:
                time_clause = " AND ld.timestamp >= :time_filter" if where_clause else " WHERE ld.timestamp >= :time_filter"
                where_clause += time_clause
                params['time_filter'] = time_filter

            # Base query
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
                    SUM(ld.usb_power) as usb_power
                FROM livedata ld
                JOIN bepppbattery b ON ld.battery_id = b.battery_id
                LEFT JOIN rental r ON ld.battery_id = r.battery_id
                    AND r.is_active = true
                    AND r.battery_returned_date IS NULL
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
                    'usb_power': 'sum'
                }).dropna()

            return self.data

        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def get_title_prefix(self):
        """Get title prefix based on current selection"""
        if self.view_level == 'hub':
            if self.selected_hub:
                hub_name = next((h['hub_name'] for h in self.hub_options if h['hub_id'] == self.selected_hub), 'Unknown')
                return f"Hub: {hub_name}"
            return "All Hubs"
        elif self.view_level == 'battery':
            if self.selected_battery:
                return f"Battery {self.selected_battery}"
            elif self.selected_hub:
                hub_name = next((h['hub_name'] for h in self.hub_options if h['hub_id'] == self.selected_hub), 'Unknown')
                return f"All Batteries - Hub: {hub_name}"
            return "All Batteries"
        elif self.view_level == 'pue_rental':
            if self.selected_rental:
                return f"PUE Rental {self.selected_rental}"
            return "All Active PUE Rentals"
        return "System"

    @param.depends('view_level', 'selected_hub', 'selected_battery', 'selected_rental',
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

    @param.depends('view_level', 'selected_hub', 'selected_battery', 'selected_rental',
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

    @param.depends('view_level', 'selected_hub', 'selected_battery', 'selected_rental',
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

    @param.depends('view_level', 'selected_hub', 'selected_battery', 'selected_rental',
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
        """Create the main dashboard view"""

        # Header
        header = pn.pane.Markdown(
            """
            # 🔋 Enhanced Battery Analytics Dashboard
            ### Hierarchical analysis: Hub → Battery → PUE Rental
            """,
            sizing_mode='stretch_width',
            styles={'background': '#1976D2', 'color': 'white', 'padding': '20px', 'border-radius': '5px'}
        )

        # View Level Selector
        view_level_selector = pn.widgets.RadioButtonGroup(
            name='View Level',
            options={'Hub View': 'hub', 'Battery View': 'battery', 'PUE Rental View': 'pue_rental'},
            value=self.view_level,
            button_type='primary'
        )

        def update_view_level(event):
            self.view_level = event.new
            # Refresh options when view level changes
            if self.view_level == 'battery':
                self.battery_options = self.load_battery_options(self.selected_hub)
            elif self.view_level == 'pue_rental':
                self.rental_options = self.load_rental_options(self.selected_hub)

        view_level_selector.param.watch(update_view_level, 'value')

        # Hub Selector
        hub_selector = pn.widgets.Select(
            name='Select Hub',
            options={f"{h['hub_name']} (ID: {h['hub_id']})": h['hub_id'] for h in self.hub_options},
            value=self.selected_hub,
            width=300
        )

        def update_hub(event):
            self.selected_hub = event.new
            self.battery_options = self.load_battery_options(self.selected_hub)
            self.rental_options = self.load_rental_options(self.selected_hub)

        hub_selector.param.watch(update_hub, 'value')

        # Dynamic selector based on view level
        @pn.depends(view_level_selector.param.value)
        def dynamic_selector(view_level):
            if view_level == 'battery':
                self.battery_options = self.load_battery_options(self.selected_hub)
                battery_opts = {f"Battery {b['battery_id']}": b['battery_id']
                               for b in self.battery_options}
                battery_selector = pn.widgets.Select(
                    name='Select Battery',
                    options={'All Batteries in Hub': None, **battery_opts},
                    value=self.selected_battery,
                    width=300
                )

                def update_battery(event):
                    self.selected_battery = event.new

                battery_selector.param.watch(update_battery, 'value')
                return battery_selector

            elif view_level == 'pue_rental':
                self.rental_options = self.load_rental_options(self.selected_hub)
                rental_opts = {f"Rental {r['rentral_id']} - Battery {r['battery_id']} - {r['user_name']}": r['rentral_id']
                              for r in self.rental_options}
                rental_selector = pn.widgets.Select(
                    name='Select PUE Rental',
                    options={'All Active Rentals': None, **rental_opts},
                    value=self.selected_rental,
                    width=400
                )

                def update_rental(event):
                    self.selected_rental = event.new

                rental_selector.param.watch(update_rental, 'value')
                return rental_selector

            return pn.pane.Markdown("_Showing all data for selected hub_")

        # Time controls
        time_controls = pn.Row(
            pn.Param(
                self.param.time_scale,
                widgets={'time_scale': pn.widgets.RadioButtonGroup}
            ),
            pn.Param(
                self.param.aggregation_interval,
                widgets={'aggregation_interval': pn.widgets.Select}
            ),
            sizing_mode='stretch_width'
        )

        # Controls
        controls = pn.Column(
            view_level_selector,
            pn.Row(
                hub_selector,
                dynamic_selector,
                sizing_mode='stretch_width'
            ),
            time_controls,
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
