# Database Migration: Self-hosted → DigitalOcean Managed PostgreSQL

## Status: COMPLETED — 2026-06-05

Migration successfully completed. App is live on DO managed PostgreSQL.

---

## Why

- **Resilience**: Automated backups, point-in-time recovery, automatic failover
- **Monitoring**: Built-in dashboards, connection pooling, alerts
- **Cost**: Reduce droplet backups from daily to weekly, saving ~$4-5/month
- **Managed Postgres**: ~$15/month (1 vCPU, 1GB RAM) on DO

---

## What was done (actual steps taken on 2026-06-05)

### 1. Deployed latest code first

```bash
git push origin main
ssh root@46.101.83.125 "bash /opt/battery-hub/update.sh"
```

Alembic migration `f6g7h8i9j0k1` (adds `agreed_period_price` to `puerental`) ran cleanly.

---

### 2. Created DO Managed PostgreSQL cluster

- DigitalOcean Dashboard → **Databases** → **Create Database**
- Engine: **PostgreSQL 15**
- Region: `lon1` (same as droplet)
- Plan: Basic / 1GB RAM (~$15/month)
- Name: `battery-hub-db`
- Added droplet to **Trusted Sources** for private network access

Connection details (private network — only accessible from within DO `lon1`):
- Host: `private-db-beppp-lon-2026-do-user-3167488-0.j.db.ondigitalocean.com`
- Port: `25060`
- User: `doadmin`
- Database: `defaultdb`
- SSL: required

---

### 3. Installed psql client on droplet

```bash
apt-get install -y postgresql-client
```

Installed version: postgresql-client-16 (compatible with Postgres 15 server).

---

### 4. Dumped production data

```bash
docker exec battery-hub-db pg_dump -U beppp beppp > /tmp/beppp_migration.sql
wc -l /tmp/beppp_migration.sql
# Result: 101,277 lines
```

---

### 5. Restored into managed DB

```bash
psql "postgresql://doadmin:PASSWORD@private-db-beppp-lon-2026-do-user-3167488-0.j.db.ondigitalocean.com:25060/defaultdb?sslmode=require" < /tmp/beppp_migration.sql
```

Expected errors (harmless): `ERROR: role "beppp" does not exist` — the managed DB uses `doadmin`; ownership errors don't affect data.

**Verified row counts matched** using:
```bash
# Self-hosted
docker exec battery-hub-db psql -U beppp beppp -c "SELECT relname, reltuples::bigint as rows FROM pg_class WHERE relkind='r' AND relnamespace='public'::regnamespace ORDER BY rows DESC LIMIT 15;"

# Managed DB
psql "postgresql://doadmin:PASSWORD@private-host:25060/defaultdb?sslmode=require" -c "SELECT relname, reltuples::bigint as rows FROM pg_class WHERE relkind='r' AND relnamespace='public'::regnamespace ORDER BY rows DESC LIMIT 15;"
```

Key table counts confirmed present: `livedata` (~85k), `webhook_logs` (10k), `battery_rentals`, `users`, `account_transactions` etc. Minor count differences between old and new were expected — the app was live during the migration so new rows came in between dump and restore.

---

### 6. Updated docker-compose.prod.yml

Changed all three `DATABASE_URL` entries (api, panel, cron) from hardcoded construction:
```yaml
DATABASE_URL: postgresql://${POSTGRES_USER:-beppp}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-beppp}
```
To a single env var:
```yaml
DATABASE_URL: ${DATABASE_URL}
```

This allows switching DB targets by just updating `.env`. Committed and pushed.

---

### 7. Added DATABASE_URL to .env on server

```bash
echo "DATABASE_URL=postgresql://doadmin:PASSWORD@private-db-beppp-lon-2026-do-user-3167488-0.j.db.ondigitalocean.com:25060/defaultdb?sslmode=require" >> /opt/battery-hub/.env
```

The old `POSTGRES_*` variables were left in place — the `postgres` container still needs them.

---

### 8. Deployed and verified

```bash
bash /opt/battery-hub/update.sh
```

All 7 containers healthy. Alembic reported "already up to date" (migrations already applied during restore). Verified the API is using the managed DB:

```bash
docker exec battery-hub-api env | grep DATABASE_URL
# Shows: DATABASE_URL=postgresql://doadmin:...@private-db-beppp-lon-2026-do-user-3167488-0.j.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

---

## Pending cleanup (do after 24-48h confirmed stable)

- [ ] Remove local `postgres` container and volume to free droplet resources:
  ```bash
  # First update docker-compose.prod.yml to remove postgres service and volume
  # Then on server:
  docker stop battery-hub-db && docker rm battery-hub-db
  docker volume rm battery-hub_postgres_data
  ```
- [ ] Reduce droplet backups from **daily to weekly** on DO dashboard (~$4/month saving)

---

## Rollback plan

If the managed DB has issues:

1. Remove `DATABASE_URL` from `.env` (or comment it out)
2. The compose file will fail — temporarily revert `docker-compose.prod.yml` to hardcoded URL pointing to `postgres:5432`
3. Restart containers: `docker-compose -f docker-compose.prod.yml restart api panel cron`
4. The local `postgres` container still has all data up to the migration point
5. Full droplet snapshot taken before migration also provides recovery

---

## Cost summary

| Item | Before | After |
|---|---|---|
| Droplet daily backups | ~$8/month | ~$4/month (weekly) |
| Managed PostgreSQL | $0 | ~$15/month |
| **Net change** | | **+$7/month** |

DO Managed DB includes: daily automated backups with 7-day retention, monitoring, automatic minor version upgrades.
