"""
Panel Dashboard for Battery Analytics
Integrated with Battery Rental Management System
"""

import panel as pn
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import hvplot.pandas
import holoviews as hv
from bokeh.models import HoverTool

# Enable Panel extensions
pn.extension('tabulator', 'plotly', sizing_mode='stretch_width')
hv.extension('bokeh')

# Configuration
API_URL = "http://localhost:8000"

class BatteryAnalyticsDashboard:
    def __init__(self):
        self.api_url = API_URL
        self.token = None
        self.hub_id = None
        self.time_period = "last_month"

        # Data caches
        self.battery_data = None
        self.revenue_data = None
        self.hub_summary = None

    def set_params_from_url(self):
        """Extract parameters from URL query string"""
        if pn.state.location:
            query_params = pn.state.location.search_params

            if 'token' in query_params:
                self.token = query_params['token']

            if 'hub_id' in query_params:
                self.hub_id = int(query_params['hub_id'])

            if 'time_period' in query_params:
                self.time_period = query_params['time_period']

    def get_headers(self):
        """Get authorization headers for API requests"""
        if self.token:
            return {'Authorization': f'Bearer {self.token}'}
        return {}

    def fetch_hub_summary(self):
        """Fetch hub summary data from API"""
        try:
            response = requests.get(
                f"{self.api_url}/analytics/hub-summary",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.hub_summary = pd.DataFrame(data)
                return self.hub_summary
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching hub summary: {e}")
            return pd.DataFrame()

    def fetch_revenue_data(self):
        """Fetch revenue data from API"""
        try:
            params = {'time_period': self.time_period}

            response = requests.get(
                f"{self.api_url}/analytics/revenue",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                self.revenue_data = response.json()
                return self.revenue_data
            else:
                return {}
        except Exception as e:
            print(f"Error fetching revenue data: {e}")
            return {}

    def fetch_battery_performance(self):
        """Fetch battery performance data from API"""
        try:
            params = {'time_period': self.time_period}

            if self.hub_id:
                params['hub_id'] = self.hub_id

            response = requests.get(
                f"{self.api_url}/analytics/battery-performance",
                params=params,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.battery_data = pd.DataFrame(data.get('batteries', []))
                return self.battery_data
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching battery performance: {e}")
            return pd.DataFrame()

    def create_hub_summary_plot(self):
        """Create hub summary visualization"""
        df = self.fetch_hub_summary()

        if df.empty:
            return pn.pane.Markdown("### No hub data available")

        # Create bar chart for active vs total batteries
        plot = df.hvplot.bar(
            x='hub_name',
            y=['total_batteries', 'active_batteries'],
            title='Batteries by Hub',
            height=400,
            ylabel='Number of Batteries',
            xlabel='Hub',
            legend='top_right',
            color=['#1976D2', '#26A69A']
        )

        return pn.pane.HoloViews(plot, sizing_mode='stretch_both')

    def create_revenue_plot(self):
        """Create revenue visualization"""
        revenue = self.fetch_revenue_data()

        if not revenue:
            return pn.pane.Markdown("### No revenue data available")

        # Create indicator for total revenue
        total_revenue = revenue.get('total_revenue', 0)

        indicator = pn.indicators.Number(
            name='Total Revenue',
            value=total_revenue,
            format='${value:,.2f}',
            font_size='36pt',
            title_size='18pt',
            colors=[(0, 'red'), (50, 'gold'), (100, 'green')]
        )

        return pn.Column(
            indicator,
            pn.pane.Markdown(f"**Period:** {self.time_period.replace('_', ' ').title()}")
        )

    def create_battery_performance_plot(self):
        """Create battery performance visualization"""
        df = self.fetch_battery_performance()

        if df.empty:
            return pn.pane.Markdown("### No battery performance data available")

        # Create scatter plot for battery utilization
        if 'utilization_rate' in df.columns and 'rental_count' in df.columns:
            plot = df.hvplot.scatter(
                x='rental_count',
                y='utilization_rate',
                by='status',
                title='Battery Utilization vs Rental Count',
                height=400,
                xlabel='Number of Rentals',
                ylabel='Utilization Rate (%)',
                legend='top_right',
                size=100,
                alpha=0.7
            )

            return pn.pane.HoloViews(plot, sizing_mode='stretch_both')
        else:
            return pn.pane.Markdown("### Battery performance metrics not available")

    def create_battery_table(self):
        """Create interactive battery data table"""
        df = self.fetch_battery_performance()

        if df.empty:
            return pn.pane.Markdown("### No battery data available")

        # Create Tabulator table
        table = pn.widgets.Tabulator(
            df,
            pagination='remote',
            page_size=10,
            sizing_mode='stretch_both',
            layout='fit_data_table',
            theme='bootstrap4'
        )

        return table

    def create_dashboard(self):
        """Create the main dashboard layout"""
        # Set parameters from URL
        self.set_params_from_url()

        # Header
        header = pn.pane.Markdown(
            """
            # Battery Analytics Dashboard
            ### Real-time insights into battery rental operations
            """,
            sizing_mode='stretch_width'
        )

        # Create tabs for different views
        tabs = pn.Tabs(
            ('Overview', pn.Column(
                pn.Row(
                    self.create_revenue_plot(),
                    self.create_hub_summary_plot(),
                    sizing_mode='stretch_width'
                ),
                sizing_mode='stretch_both'
            )),
            ('Battery Performance', pn.Column(
                self.create_battery_performance_plot(),
                sizing_mode='stretch_both'
            )),
            ('Data Table', pn.Column(
                self.create_battery_table(),
                sizing_mode='stretch_both'
            )),
            dynamic=True,
            sizing_mode='stretch_both'
        )

        # Footer
        footer = pn.pane.Markdown(
            f"""
            ---
            *Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
            """,
            sizing_mode='stretch_width'
        )

        # Combine all components
        dashboard = pn.Column(
            header,
            tabs,
            footer,
            sizing_mode='stretch_both'
        )

        return dashboard

# Create dashboard instance
dashboard = BatteryAnalyticsDashboard()

# Make it servable
dashboard.create_dashboard().servable(title='Battery Analytics')
