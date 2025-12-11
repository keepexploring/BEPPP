# JupyterLab for Panel Dashboard Development

This directory contains Jupyter notebooks for developing and testing Panel dashboards interactively.

## Quick Start

### Starting JupyterLab

```bash
make jupyter
```

This will:
- Build and start the JupyterLab container
- Mount the `notebooks/` and `panel_dashboard/` directories
- Make JupyterLab available at http://localhost:8888
- No password required (token authentication disabled for development)

### Accessing JupyterLab

Open your browser and navigate to:
```
http://localhost:8888
```

## Features

### What You Can Do in JupyterLab

1. **Interactive Panel Development**
   - Test Panel visualizations in real-time
   - Experiment with different chart types and layouts
   - Debug data transformations interactively

2. **Direct Database Access**
   - Query the PostgreSQL database using SQLAlchemy
   - Test database queries before adding them to production
   - Analyze battery data with pandas

3. **Edit Panel Dashboards**
   - Edit `/app/panel_dashboard/battery_analytics.py`
   - Create new dashboard modules
   - Test changes before deploying

4. **Create New Notebooks**
   - All notebooks in `/app/notebooks/` are persisted
   - Share notebooks with your team
   - Document analysis workflows

## Workflow

### 1. Develop in JupyterLab

Open the example notebook:
```
battery_analytics_example.ipynb
```

This notebook demonstrates:
- Loading data from the database
- Creating interactive visualizations
- Using Panel widgets
- Testing dashboard components

### 2. Edit Panel Dashboard Files

You can edit the main Panel dashboard directly in JupyterLab:

1. Navigate to `/app/panel_dashboard/battery_analytics.py`
2. Make your changes
3. Restart the Panel dashboard to apply changes

### 3. Apply Changes

After editing the Panel dashboard file, restart the Panel service:

```bash
make panel-restart
```

This will:
- Restart the Panel dashboard container
- Load your updated code
- Make changes visible at http://localhost:5100/battery_analytics

## Example Workflow

```bash
# 1. Start JupyterLab
make jupyter

# 2. Open http://localhost:8888 in your browser

# 3. Create/edit notebooks or panel_dashboard/battery_analytics.py

# 4. Test changes in JupyterLab

# 5. Restart Panel to deploy changes
make panel-restart

# 6. View updated dashboard at http://localhost:5100/battery_analytics
```

## Available Make Commands

```bash
make jupyter          # Start JupyterLab
make jupyter-stop     # Stop JupyterLab
make jupyter-logs     # View JupyterLab logs
make panel-restart    # Restart Panel dashboard after changes
make jupyter-open     # Open JupyterLab in browser (macOS/Linux)
```

## Environment Details

### Mounted Volumes

- `./notebooks` → `/app/notebooks` (persistent notebooks)
- `./panel_dashboard` → `/app/panel_dashboard` (dashboard code)
- `./models.py` → `/app/models.py` (database models)
- `./database.py` → `/app/database.py` (database connection)
- `./config.py` → `/app/config.py` (configuration)

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Application secret key

### Database Access

The database is accessible at:
```python
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
```

## Example Notebook

See `battery_analytics_example.ipynb` for a complete example showing:

- How to connect to the database
- Loading battery data
- Creating interactive visualizations with hvPlot
- Building Panel dashboards with widgets
- Testing and prototyping new features

## Tips

### Quick Data Loading

```python
import pandas as pd
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))

# Load recent battery data
query = text("""
    SELECT * FROM livedata
    WHERE battery_id = 1
    ORDER BY timestamp DESC
    LIMIT 100
""")

df = pd.read_sql(query, engine)
```

### Interactive Visualization

```python
import panel as pn
import hvplot.pandas

pn.extension()

# Create interactive plot
plot = df.hvplot.line(
    x='timestamp',
    y='voltage',
    height=400,
    responsive=True,
    grid=True
)

plot
```

### Testing Panel Components

```python
# Test a Panel widget
widget = pn.widgets.IntInput(name='Battery ID', value=1, start=1, end=100)
widget
```

## Troubleshooting

### JupyterLab Won't Start

```bash
# Check logs
make jupyter-logs

# Restart the container
docker-compose restart jupyter
```

### Panel Changes Not Showing

```bash
# Rebuild the Panel container
docker-compose build panel
docker-compose restart panel
```

### Database Connection Issues

Ensure the postgres container is running:
```bash
docker-compose ps postgres
```

## Security Note

**Important**: This JupyterLab setup has authentication disabled for development convenience. Do NOT use this configuration in production or expose it to the internet.

For production use:
1. Enable token authentication
2. Use strong passwords
3. Configure SSL/TLS
4. Restrict network access

## Next Steps

1. Explore `battery_analytics_example.ipynb`
2. Create your own analysis notebooks
3. Test new visualizations before adding to production
4. Document your workflows

Happy coding! 🚀
