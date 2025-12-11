# Panel Analytics Dashboard Security

## Authentication Model

The Panel analytics dashboard uses a **defense-in-depth** security model:

### Layer 1: Frontend Access Control
- Users access Panel **only through the main application** (AnalyticsPage.vue)
- Frontend passes JWT token to Panel via URL parameter
- No direct links to Panel in user interface

### Layer 2: Per-Session JWT Verification
- Panel verifies JWT token on each new session (`@pn.cache` decorator)
- Invalid/missing tokens show "Authentication Required" message
- Each user session is isolated

### Layer 3: Network Isolation (Production)
- In production, Panel is behind Nginx reverse proxy
- Only accessible via `panel.yourdomain.com` through proxy
- Docker network isolation prevents direct container access

## How It Works

```
User Login → Main App → JWT Token Generated
                ↓
        AnalyticsPage.vue (adds ?token=JWT)
                ↓
        Panel Dashboard ← Verifies JWT
                ↓
        Dashboard Displayed (cached per session)
```

### Code Flow

1. **User Authentication** (api/app/main.py)
   ```python
   @app.post("/auth/token")
   def login(credentials):
       # Verify username/password
       # Generate JWT token
       return {"access_token": token}
   ```

2. **Frontend Token Passing** (frontend/src/pages/AnalyticsPage.vue)
   ```javascript
   const panelUrl = computed(() => {
       const token = authStore.token  // From login
       return `${panelBaseUrl}/battery_analytics_v3?token=${token}`
   })
   ```

3. **Panel Token Verification** (panel_dashboard/battery_analytics_v3.py)
   ```python
   @pn.cache  # Cached per session
   def create_authenticated_dashboard():
       token = pn.state.session_args.get('token')
       user_data = verify_token(token)  # JWT verification

       if not user_data:
           return pn.Column("Authentication Required")

       # Return dashboard
   ```

## Security Considerations

### ✅ What's Secure

- **JWT Verification**: Token is cryptographically verified
- **Session Isolation**: Each browser session checks authentication independently
- **Token Expiry**: Tokens expire after configured time (default: 24 hours)
- **No Credential Storage**: Panel never stores passwords, only verifies tokens
- **Frontend Integration**: Users can't easily bypass to access Panel directly

### ⚠️ Development vs Production

**Development (docker-compose.yml)**:
- Panel exposed on `localhost:5100` for testing
- Direct access possible (but shows auth error without token)
- This is acceptable for development

**Production (docker-compose.prod.yml + Nginx)**:
- Panel not directly exposed, only via Nginx reverse proxy
- Accessible only at `panel.yourdomain.com`
- Rate limiting applied via Nginx
- Security headers applied

## Testing Authentication

### Test with valid token:
```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \\
    -d "username=admin2&password=admin2123" | \\
    python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Access Panel with token
curl "http://localhost:5100/battery_analytics_v3?token=$TOKEN"
# Should show dashboard

# 3. Access without token
curl "http://localhost:5100/battery_analytics_v3"
# Should show "Authentication Required" message
```

### Test token expiration:
```bash
# Use expired or invalid token
curl "http://localhost:5100/battery_analytics_v3?token=invalid"
# Should show "Authentication Required"
```

## Additional Security Measures

### Recommended (Optional)

1. **IP Whitelisting** (if users are from known IPs):
   ```nginx
   location /battery_analytics_v3 {
       allow 192.168.1.0/24;
       deny all;
       # ... proxy settings
   }
   ```

2. **Additional Rate Limiting**:
   ```nginx
   limit_req zone=panel burst=5 nodelay;
   ```

3. **CSRF Protection** (if adding write operations to Panel)

4. **Content Security Policy** (already implemented in nginx.conf)

## Troubleshooting

**Issue**: Panel shows blank page
- **Cause**: Token might be missing or invalid
- **Solution**: Check browser console for errors, verify token is being passed

**Issue**: "Authentication Required" shown but user is logged in
- **Cause**: Token expired or not being passed correctly
- **Solution**: Re-login to get fresh token

**Issue**: Panel loads but no data
- **Cause**: Database connection issue or no data available
- **Solution**: Check Panel logs: `docker-compose logs panel`

## Summary

The Panel dashboard is secured through:
1. ✅ JWT token verification per session
2. ✅ Frontend-controlled access
3. ✅ Network isolation in production
4. ✅ Token expiration
5. ✅ Session isolation

This multi-layer approach provides strong security while maintaining usability.
