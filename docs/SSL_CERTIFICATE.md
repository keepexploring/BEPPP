# SSL Certificate Management

## Overview

SSL certificates are provided by **Let's Encrypt** via `certbot` on the DigitalOcean droplet. The deployment script (`deploy.sh`) sets up the initial certificates and a cron job for auto-renewal.

## Certificate Location

- **Let's Encrypt certs**: `/etc/letsencrypt/live/<MAIN_DOMAIN>/`
- **Nginx copy**: `/opt/battery-hub/nginx/ssl/`
  - `fullchain.pem` - certificate chain
  - `privkey.pem` - private key

## Domains Covered

All three domains are on a single certificate:
- `beppp.co.za` (main app)
- `api.beppp.co.za` (API)
- `panel.beppp.co.za` (analytics dashboard)

## Auto-Renewal Cron Job

The deploy script installs a monthly cron job. Verify it exists:

```bash
sudo crontab -l | grep certbot
```

Expected output:
```
0 0 1 * * certbot renew --quiet && docker compose -f /opt/battery-hub/docker-compose.prod.yml restart nginx
```

### Known Issue

The cron job restarts nginx but does **not** copy the renewed certs to the nginx ssl directory. If nginx reads from `/opt/battery-hub/nginx/ssl/` instead of mounting the Let's Encrypt directory directly, renewal will appear to succeed but nginx will keep using the old certs.

**Fix**: Replace the cron job with one that also copies the certs:

```bash
# Remove old cron entry and add fixed one
sudo crontab -l | grep -v certbot | sudo crontab -
(sudo crontab -l 2>/dev/null; echo '0 3 * * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/beppp.co.za/fullchain.pem /opt/battery-hub/nginx/ssl/ && cp /etc/letsencrypt/live/beppp.co.za/privkey.pem /opt/battery-hub/nginx/ssl/ && docker compose -f /opt/battery-hub/docker-compose.prod.yml restart nginx"') | sudo crontab -
```

This uses `--deploy-hook` which only runs when a cert is actually renewed.

## Manual Renewal

If auto-renewal fails or you need to renew immediately:

```bash
# SSH into the droplet
ssh root@<DROPLET_IP>

# Stop nginx to free port 80
docker compose -f /opt/battery-hub/docker-compose.prod.yml stop nginx

# Renew certificates
sudo certbot renew --force-renewal

# Copy renewed certs
sudo cp /etc/letsencrypt/live/beppp.co.za/fullchain.pem /opt/battery-hub/nginx/ssl/
sudo cp /etc/letsencrypt/live/beppp.co.za/privkey.pem /opt/battery-hub/nginx/ssl/

# Restart nginx
docker compose -f /opt/battery-hub/docker-compose.prod.yml start nginx
```

## Check Certificate Expiry

```bash
# From any machine
echo | openssl s_client -connect beppp.co.za:443 -servername beppp.co.za 2>/dev/null | openssl x509 -noout -dates

# On the droplet
sudo certbot certificates
```

Let's Encrypt certificates expire every 90 days. The cron job should renew them automatically when they have fewer than 30 days remaining.

## Troubleshooting

### Certificate not renewing
1. Check certbot logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`
2. Verify port 80 is accessible: `curl -I http://beppp.co.za`
3. Check DNS records still point to the droplet IP
4. Try manual renewal (see above)

### Rate limits
Let's Encrypt has rate limits: 5 duplicate certificates per week per domain. If you hit the limit, wait 7 days or use the staging environment for testing:
```bash
certbot certonly --staging --standalone -d beppp.co.za -d api.beppp.co.za -d panel.beppp.co.za
```
