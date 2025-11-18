# Battery Rental Management PWA

A comprehensive Progressive Web Application (PWA) built with Quasar Framework for managing battery rental kiosks. Features include hub management, battery tracking, user administration, equipment (PUE) management, rental operations, and interactive analytics powered by Panel/HoloViews.

## Features

### Core Management
- **Hub Management**: Create, view, update, and delete battery rental hubs/kiosks
- **Battery Management**: Track battery inventory, status, capacity, and real-time data
- **User Management**: Administer users with role-based access control (user, admin, superadmin, data_admin)
- **PUE Management**: Manage Productive Use Equipment available for rental
- **Rental Operations**: Create rentals, track active/returned rentals, process returns

### Analytics Dashboard
- Interactive data visualizations using Panel/HoloViews
- Hub performance metrics
- Battery utilization statistics
- Revenue tracking
- Real-time data monitoring

### Security
- JWT-based authentication
- Role-based access control
- Secure API integration
- Token refresh support

## Tech Stack

- **Frontend Framework**: Quasar Framework (Vue 3)
- **State Management**: Pinia
- **HTTP Client**: Axios
- **Analytics**: Panel/HoloViews (Python)
- **UI Components**: Quasar Material Design components
- **Build Tool**: Vite

## Prerequisites

- Node.js 16+ and npm
- Python 3.8+ (for Panel analytics)
- Running API backend (see main project README)

## Installation

### 1. Clone and Navigate

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` to point to your API and Panel servers:

```env
API_URL=http://localhost:8000
PANEL_URL=http://localhost:5100
```

### 4. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:9000`

## Setting Up Panel Analytics

### 1. Install Python Dependencies

```bash
cd ../panel_dashboard
pip install -r requirements.txt
```

### 2. Start Panel Server

```bash
./start_panel.sh
```

Or manually:

```bash
panel serve battery_analytics.py \
  --port 5100 \
  --allow-websocket-origin="localhost:9000" \
  --show
```

The Panel dashboard will be available at `http://localhost:5100/battery_analytics`

## Default Login Credentials

Use the credentials from your API backend:

```
Username: admin
Password: admin123
```

**⚠️ Change these immediately in production!**

## User Roles

- **user**: Basic access to view data and create rentals
- **admin**: Full management capabilities except deleting critical resources
- **superadmin**: Complete access including deletion of resources
- **data_admin**: Special access for data analytics and reporting
- **battery**: API-only access for battery devices

## Building for Production

### Build PWA

```bash
npm run build:pwa
```

The built files will be in `dist/pwa`

### Production Environment Variables

Update `.env` for production:

```env
API_URL=https://api.yourdomain.com
PANEL_URL=https://panel.yourdomain.com
```

## Project Structure

```
frontend/
├── src/
│   ├── boot/              # Boot files (axios, auth)
│   ├── components/        # Reusable Vue components
│   ├── layouts/           # Layout components
│   │   └── MainLayout.vue # Main app layout with navigation
│   ├── pages/             # Page components
│   │   ├── DashboardPage.vue
│   │   ├── HubsPage.vue
│   │   ├── BatteriesPage.vue
│   │   ├── UsersPage.vue
│   │   ├── PUEPage.vue
│   │   ├── RentalsPage.vue
│   │   ├── AnalyticsPage.vue  # Panel iframe integration
│   │   └── admin/
│   │       └── WebhookLogsPage.vue
│   ├── router/            # Vue Router configuration
│   ├── services/          # API service layer
│   │   └── api.js         # Axios API client
│   ├── stores/            # Pinia stores
│   │   ├── auth.js        # Authentication store
│   │   └── index.js       # Store initialization
│   └── css/               # Global styles
├── public/                # Static assets
└── quasar.config.js       # Quasar configuration
```

## Available Pages

### Public
- `/login` - Login page

### Protected (requires authentication)
- `/` - Dashboard with quick stats and actions
- `/analytics` - Interactive analytics dashboard (Panel iframe)
- `/hubs` - Hub management
- `/hubs/:id` - Hub detail page
- `/batteries` - Battery inventory
- `/batteries/:id` - Battery detail with real-time data
- `/pue` - Equipment (PUE) management
- `/rentals` - Rental operations
- `/rentals/:id` - Rental detail page

### Admin Only
- `/users` - User administration
- `/admin/webhooks` - Webhook logs

## API Integration

All API calls are centralized in `src/services/api.js`:

```javascript
import { hubsAPI, batteriesAPI, rentalsAPI } from 'src/services/api'

// Example usage
const hubs = await hubsAPI.list()
const battery = await batteriesAPI.get(batteryId)
await rentalsAPI.create(rentalData)
```

## Panel Analytics Integration

The Analytics page uses an iframe to embed Panel dashboards:

```vue
<iframe
  :src="panelUrl"
  class="panel-iframe"
  frameborder="0"
/>
```

The Panel URL includes:
- Authentication token
- Selected hub ID
- Time period filter

This approach provides:
- Full Python analytics capabilities
- Complete separation of concerns
- Easy to deploy and scale
- No complex JavaScript charting libraries needed

## Responsive Design

The PWA is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices
- Can be installed as a native app

## Development Tips

### Hot Reload

Quasar supports hot module replacement. Changes to Vue files will reflect immediately.

### Debugging

Use Vue DevTools browser extension for:
- Component inspection
- Pinia store debugging
- Route navigation tracking

### API Testing

Use the browser's Network tab to inspect API calls and responses.

## Troubleshooting

### API Connection Issues

1. Verify API is running: `curl http://localhost:8000/health`
2. Check CORS settings in API
3. Verify `.env` has correct `API_URL`

### Panel Not Loading

1. Ensure Panel server is running: `ps aux | grep panel`
2. Check Panel logs for errors
3. Verify websocket origin matches your frontend domain
4. Check browser console for iframe errors

### Build Errors

1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear Quasar cache: `rm -rf .quasar`
3. Update dependencies: `npm update`

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

[Your License]

## Support

For issues and questions:
- Check the API documentation
- Review Quasar documentation: https://quasar.dev
- Review Panel documentation: https://panel.holoviz.org
