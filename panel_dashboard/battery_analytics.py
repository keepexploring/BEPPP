"""
Enhanced Panel Dashboard for Battery Analytics
Features:
- Interactive time-series plots for voltage, power, SOC, temperature
- Time scale selector (1 hour, 6 hours, 1 day, 7 days, 30 days, all time)
- Real-time data from database
- Multiple battery comparison
- Export data functionality
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

class BatteryAnalyticsDashboard(param.Parameterized):
    """Enhanced Battery Analytics Dashboard with time-series visualizations"""

    # Parameters
    battery_id = param.Integer(default=1, bounds=(1, None), label="Battery ID")
    view_mode = param.Selector(default='single', objects=['single', 'aggregated'], label="View Mode")
    time_scale = param.Selector(
        default='1h',
        objects=['1h', '6h', '24h', '7d', '30d', 'all'],
        label="Time Scale"
    )

    # Time scale labels for display
    time_scale_labels = {
        '1h': '1 Hour',
        '6h': '6 Hours',
        '24h': '24 Hours',
        '7d': '7 Days',
        '30d': '30 Days',
        'all': 'All Time'
    }

    def __init__(self, **params):
        super().__init__(**params)
        self.engine = create_engine(DATABASE_URL)
        self.data = None
        self.battery_options = self.load_battery_options()
        self.load_data()

    def load_battery_options(self):
        """Load available batteries with their hub information"""
        try:
            query = text("""
                SELECT
                    b.battery_id,
                    b.hub_id,
                    h.what_three_word_location as hub_name
                FROM bepppbattery b
                LEFT JOIN solarhub h ON b.hub_id = h.hub_id
                ORDER BY b.battery_id
            """)

            with self.engine.connect() as conn:
                result = conn.execute(query)
                batteries = []
                for row in result:
                    batteries.append({
                        'battery_id': row.battery_id,
                        'hub_id': row.hub_id,
                        'hub_name': row.hub_name or 'No Hub',
                        'label': f"Battery {row.battery_id} - {row.hub_name or 'No Hub'}"
                    })
                return batteries
        except Exception as e:
            print(f"Error loading battery options: {e}")
            return [{'battery_id': 1, 'hub_id': None, 'hub_name': 'Unknown', 'label': 'Battery 1 - Unknown'}]

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

    @param.depends('battery_id', 'time_scale', 'view_mode', watch=True)
    def load_data(self):
        """Load battery data from database"""
        try:
            time_filter = self.get_time_filter()

            if self.view_mode == 'aggregated':
                # Load aggregated data for all batteries
                if time_filter:
                    query = text("""
                        SELECT
                            timestamp,
                            AVG(state_of_charge) as state_of_charge,
                            AVG(voltage) as voltage,
                            SUM(current_amps) as current_amps,
                            SUM(power_watts) as power_watts,
                            AVG(temp_battery) as temp_battery,
                            SUM(charging_current) as charging_current,
                            SUM(usb_power) as usb_power,
                            AVG(usb_voltage) as usb_voltage,
                            SUM(charger_power) as charger_power,
                            AVG(charger_voltage) as charger_voltage,
                            SUM(amp_hours_consumed) as amp_hours_consumed,
                            SUM(total_charge_consumed) as total_charge_consumed
                        FROM livedata
                        WHERE timestamp >= :time_filter
                        GROUP BY timestamp
                        ORDER BY timestamp ASC
                    """)
                    params = {'time_filter': time_filter}
                else:
                    query = text("""
                        SELECT
                            timestamp,
                            AVG(state_of_charge) as state_of_charge,
                            AVG(voltage) as voltage,
                            SUM(current_amps) as current_amps,
                            SUM(power_watts) as power_watts,
                            AVG(temp_battery) as temp_battery,
                            SUM(charging_current) as charging_current,
                            SUM(usb_power) as usb_power,
                            AVG(usb_voltage) as usb_voltage,
                            SUM(charger_power) as charger_power,
                            AVG(charger_voltage) as charger_voltage,
                            SUM(amp_hours_consumed) as amp_hours_consumed,
                            SUM(total_charge_consumed) as total_charge_consumed
                        FROM livedata
                        GROUP BY timestamp
                        ORDER BY timestamp ASC
                    """)
                    params = {}
            else:
                # Load data for single battery
                if time_filter:
                    query = text("""
                        SELECT
                            timestamp,
                            state_of_charge,
                            voltage,
                            current_amps,
                            power_watts,
                            temp_battery,
                            charging_current,
                            usb_power,
                            usb_voltage,
                            charger_power,
                            charger_voltage,
                            amp_hours_consumed,
                            total_charge_consumed
                        FROM livedata
                        WHERE battery_id = :battery_id
                        AND timestamp >= :time_filter
                        ORDER BY timestamp ASC
                    """)
                    params = {'battery_id': self.battery_id, 'time_filter': time_filter}
                else:
                    query = text("""
                        SELECT
                            timestamp,
                            state_of_charge,
                            voltage,
                            current_amps,
                            power_watts,
                            temp_battery,
                            charging_current,
                            usb_power,
                            usb_voltage,
                            charger_power,
                            charger_voltage,
                            amp_hours_consumed,
                            total_charge_consumed
                        FROM livedata
                        WHERE battery_id = :battery_id
                        ORDER BY timestamp ASC
                    """)
                    params = {'battery_id': self.battery_id}

            self.data = pd.read_sql(query, self.engine, params=params)

            if not self.data.empty:
                self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
                self.data = self.data.set_index('timestamp')

            return self.data

        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()

    @param.depends('battery_id', 'time_scale', 'view_mode')
    def voltage_plot(self):
        """Create voltage vs time plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available for selected battery")

        title = 'Average Voltage Over Time (All Batteries)' if self.view_mode == 'aggregated' else f'Battery Voltage Over Time (Battery {self.battery_id})'

        plot = self.data.hvplot.line(
            y='voltage',
            title=title,
            ylabel='Voltage (V)',
            xlabel='Time',
            height=350,
            width=None,
            responsive=True,
            color='#1976D2',
            line_width=2,
            hover_cols=['state_of_charge', 'power_watts'],
            grid=True
        )

        return pn.pane.HoloViews(plot, sizing_mode='stretch_both')

    @param.depends('battery_id', 'time_scale', 'view_mode')
    def power_plot(self):
        """Create power vs time plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        # Create plot with power and charging power
        title = 'Total Power Demand Over Time (All Batteries)' if self.view_mode == 'aggregated' else f'Power Consumption Over Time (Battery {self.battery_id})'

        power_plot = self.data.hvplot.line(
            y='power_watts',
            title=title,
            ylabel='Power (W)',
            xlabel='Time',
            height=350,
            width=None,
            responsive=True,
            color='#FF9800',
            line_width=2,
            label='Power Output',
            grid=True
        )

        if 'charger_power' in self.data.columns:
            charger_plot = self.data.hvplot.line(
                y='charger_power',
                ylabel='Power (W)',
                color='#4CAF50',
                line_width=2,
                label='Charger Power',
                alpha=0.7
            )
            plot = power_plot * charger_plot
        else:
            plot = power_plot

        return pn.pane.HoloViews(plot, sizing_mode='stretch_both')

    @param.depends('battery_id', 'time_scale')
    def soc_plot(self):
        """Create state of charge vs time plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        plot = self.data.hvplot.area(
            y='state_of_charge',
            title=f'State of Charge Over Time (Battery {self.battery_id})',
            ylabel='State of Charge (%)',
            xlabel='Time',
            height=350,
            width=None,
            responsive=True,
            color='#4CAF50',
            alpha=0.6,
            hover_cols=['voltage', 'power_watts'],
            grid=True,
            ylim=(0, 100)
        )

        return pn.pane.HoloViews(plot, sizing_mode='stretch_both')

    @param.depends('battery_id', 'time_scale')
    def temperature_plot(self):
        """Create temperature vs time plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        plot = self.data.hvplot.line(
            y='temp_battery',
            title=f'Battery Temperature Over Time (Battery {self.battery_id})',
            ylabel='Temperature (°C)',
            xlabel='Time',
            height=350,
            width=None,
            responsive=True,
            color='#F44336',
            line_width=2,
            hover_cols=['voltage', 'state_of_charge'],
            grid=True
        )

        return pn.pane.HoloViews(plot, sizing_mode='stretch_both')

    @param.depends('battery_id', 'time_scale')
    def current_plot(self):
        """Create current vs time plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        # Plot both current and charging current
        current_plot = self.data.hvplot.line(
            y='current_amps',
            title=f'Current Flow Over Time (Battery {self.battery_id})',
            ylabel='Current (A)',
            xlabel='Time',
            height=350,
            width=None,
            responsive=True,
            color='#9C27B0',
            line_width=2,
            label='Battery Current',
            grid=True
        )

        if 'charging_current' in self.data.columns:
            charging_plot = self.data.hvplot.line(
                y='charging_current',
                ylabel='Current (A)',
                color='#00BCD4',
                line_width=2,
                label='Charging Current',
                alpha=0.7
            )
            plot = current_plot * charging_plot
        else:
            plot = current_plot

        return pn.pane.HoloViews(plot, sizing_mode='stretch_both')

    @param.depends('battery_id', 'time_scale')
    def energy_consumption_plot(self):
        """Create cumulative energy consumption plot"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        if 'total_charge_consumed' in self.data.columns:
            plot = self.data.hvplot.line(
                y='total_charge_consumed',
                title=f'Cumulative Energy Consumption (Battery {self.battery_id})',
                ylabel='Total Charge Consumed (Ah)',
                xlabel='Time',
                height=350,
                width=None,
                responsive=True,
                color='#FF5722',
                line_width=2,
                grid=True
            )
            return pn.pane.HoloViews(plot, sizing_mode='stretch_both')
        else:
            return pn.pane.Markdown("### Energy consumption data not available")

    @param.depends('battery_id', 'time_scale')
    def stats_panel(self):
        """Create statistics summary panel"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No statistics available")

        stats = {
            'Records': len(self.data),
            'Avg Voltage': f"{self.data['voltage'].mean():.2f} V",
            'Max Power': f"{self.data['power_watts'].max():.2f} W",
            'Avg Temp': f"{self.data['temp_battery'].mean():.1f} °C",
            'Avg SOC': f"{self.data['state_of_charge'].mean():.1f} %",
        }

        if 'total_charge_consumed' in self.data.columns and not self.data['total_charge_consumed'].isna().all():
            stats['Total Consumed'] = f"{self.data['total_charge_consumed'].iloc[-1]:.2f} Ah"

        # Create indicators
        indicators = []
        colors = ['#1976D2', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#00BCD4']

        for i, (key, value) in enumerate(stats.items()):
            ind = pn.indicators.String(
                name=key,
                value=value,
                font_size='20pt',
                title_size='14pt',
                default_color=colors[i % len(colors)]
            )
            indicators.append(ind)

        return pn.FlexBox(*indicators, justify_content='space-around')

    @param.depends('battery_id', 'time_scale')
    def data_table(self):
        """Create data table"""
        if self.data is None or self.data.empty:
            return pn.pane.Markdown("### No data available")

        # Reset index to show timestamp as column
        df_display = self.data.reset_index()

        # Format timestamp
        df_display['timestamp'] = df_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Round numeric columns
        numeric_cols = df_display.select_dtypes(include=['float64']).columns
        df_display[numeric_cols] = df_display[numeric_cols].round(2)

        table = pn.widgets.Tabulator(
            df_display,
            pagination='remote',
            page_size=20,
            sizing_mode='stretch_both',
            layout='fit_data_table',
            theme='bootstrap4',
            disabled=True
        )

        return table

    def view(self):
        """Create the main dashboard view"""

        # Header
        header = pn.pane.Markdown(
            """
            # 🔋 Battery Analytics Dashboard
            ### Real-time monitoring and analysis of battery performance
            """,
            sizing_mode='stretch_width',
            styles={'background': '#1976D2', 'color': 'white', 'padding': '20px', 'border-radius': '5px'}
        )

        # Battery selector with search
        battery_labels = {b['battery_id']: b['label'] for b in self.battery_options}
        battery_ids = list(battery_labels.keys())

        battery_select = pn.widgets.AutocompleteInput(
            name='Select Battery',
            options=list(battery_labels.values()),
            value=battery_labels.get(self.battery_id, f'Battery {self.battery_id}'),
            placeholder='Type to search by battery ID or hub name...',
            case_sensitive=False,
            search_strategy='includes',
            min_characters=1,
            width=400
        )

        # Update battery_id when selection changes
        def update_battery(event):
            # Find battery_id from label
            for b in self.battery_options:
                if b['label'] == event.new:
                    self.battery_id = b['battery_id']
                    break

        battery_select.param.watch(update_battery, 'value')

        # View mode toggle
        view_mode_toggle = pn.widgets.RadioButtonGroup(
            name='View Mode',
            options={'Single Battery': 'single', 'All Batteries (Aggregated)': 'aggregated'},
            value=self.view_mode,
            button_type='primary'
        )

        # Update view_mode when toggle changes
        def update_view_mode(event):
            self.view_mode = event.new

        view_mode_toggle.param.watch(update_view_mode, 'value')

        # Controls
        controls = pn.Column(
            pn.Row(
                view_mode_toggle,
                sizing_mode='stretch_width'
            ),
            pn.Row(
                battery_select if self.view_mode == 'single' else pn.pane.Markdown("### Showing aggregated data for all batteries"),
                pn.Param(
                    self.param.time_scale,
                    widgets={'time_scale': pn.widgets.RadioButtonGroup}
                ),
                sizing_mode='stretch_width'
            ),
            sizing_mode='stretch_width'
        )

        # Create tabs for different visualizations
        tabs = pn.Tabs(
            ('Overview', pn.Column(
                self.stats_panel,
                pn.Row(
                    self.soc_plot,
                    self.voltage_plot,
                    sizing_mode='stretch_width'
                ),
                sizing_mode='stretch_both'
            )),
            ('Power & Energy', pn.Column(
                pn.Row(
                    self.power_plot,
                    self.current_plot,
                    sizing_mode='stretch_width'
                ),
                self.energy_consumption_plot,
                sizing_mode='stretch_both'
            )),
            ('Temperature', pn.Column(
                self.temperature_plot,
                sizing_mode='stretch_both'
            )),
            ('Data Table', pn.Column(
                self.data_table,
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
dashboard = BatteryAnalyticsDashboard()

# Make it servable
dashboard.view().servable(title='Battery Analytics Dashboard')
