# Database Migration: Self-hosted → DigitalOcean Managed PostgreSQL

## Why

- **Resilience**: Automated backups, point-in-time recovery, automatic failover
- **Monitoring**: Built-in dashboards, connection pooling, alerts
- **Cost**: Remove dependency on droplet daily backups → reduce to weekly or disable, saving ~$5–10/month
- **Managed Postgres**: ~$15/month (1 vCPU, 1GB RAM) on DO — suitable for current load

---

## Pre-migration checklist

- [ ] Take a DigitalOcean **droplet snapshot** before starting (manual safety net)
- [ ] Confirm managed DB cluster is in the **same region** as the droplet (e.g. `lon1`)
- [ ] Note current `.env` `DATABASE_URL` value on the server

---

## Step 1: Deploy current code changes first

```bash
git push origin main
ssh root@46.101.83.125 "bash /opt/battery-hub/update.sh"
```

The Alembic migration (`f6g7h8i9j0k1` — adds `agreed_period_price` to `puerental`) runs automatically on container restart.

---

## Step 2: Create DO Managed PostgreSQL cluster

1. DigitalOcean Dashboard → **Databases** → **Create Database**
2. Engine: **PostgreSQL 15** (match current version)
3. Region: same as droplet (e.g. `lon1`)
4. Plan: Basic / 1GB RAM to start
5. Name it e.g. `battery-hub-db`
6. Once created, note the **connection string** (format: `postgresql://user:pass@host:port/defaultdb?sslmode=require`)

---

## Step 3: Dump production data

SSH into the droplet and dump from the running container:

```bash
ssh root@46.101.83.125

# Dump from current self-hosted container
docker exec battery-hub-db pg_dump -U beppp beppp > /tmp/beppp_migration.sql

# Verify dump looks sensible
wc -l /tmp/beppp_migration.sql
head -20 /tmp/beppp_migration.sql
```

---

## Step 4: Restore into managed DB

From the droplet (DO managed DB is accessible within the same region without SSL cert issues):

```bash
# The managed DB connection string from DO dashboard (with sslmode=require)
export MANAGED_DB_URL="postgresql://doadmin:PASS@host:PORT/defaultdb?sslmode=require"

# Create the beppp database (if managed DB doesn't auto-create it)
psql "$MANAGED_DB_URL" -c "CREATE DATABASE beppp;"

# Restore
psql "postgresql://doadmin:PASS@host:PORT/beppp?sslmode=require" < /tmp/beppp_migration.sql
```

> Note: If DO uses `defaultdb` as the only database, restore directly into it and update `POSTGRES_DB` in `.env` to `defaultdb`.

---

## Step 5: Update `.env` on droplet

```bash
nano /opt/battery-hub/.env
```

Change `DATABASE_URL` from:
```
DATABASE_URL=postgresql://beppp:PASSWORD@postgres:5432/beppp
```
To (the managed DB connection string):
```
DATABASE_URL=postgresql://doadmin:PASS@managed-host:PORT/beppp?sslmode=require
```

Also update any other services that reference the DB (cron container, panel container — they all read `DATABASE_URL` from `.env`).

---

## Step 6: Update docker-compose.prod.yml

Remove the `postgres` service and its volume — the app now connects to the external managed DB. The `api` service no longer needs `depends_on: postgres`.

Key diff:

```yaml
# Remove this entire service block:
  postgres:
    image: postgres:15-alpine
    ...

# Remove from volumes:
volumes:
  postgres_data:
    driver: local

# In api service, remove:
    depends_on:
      postgres:
        condition: service_healthy
# (keep depends_on for other services if needed, or remove depends_on entirely)
```

Commit this change to the repo.

---

## Step 7: Restart and verify

```bash
cd /opt/battery-hub
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Watch logs — Alembic should say "already up to date"
docker logs battery-hub-api --tail 50 -f
```

Check the app is working: open the frontend, log in, verify rentals load.

---

## Step 8: Cleanup

Once confirmed working for 24–48 hours:

```bash
# Remove old postgres volume (frees disk space)
docker volume rm battery-hub_postgres_data
```

On DigitalOcean:
- **Droplet backups**: Change from daily to weekly (or disable if managed DB backups are sufficient)
- DO Managed DB provides: daily automated backups with 7-day retention by default

---

## Rollback plan

If anything goes wrong after Step 7:

1. Revert `.env` `DATABASE_URL` back to `postgres:5432/beppp`
2. Re-add the `postgres` service to `docker-compose.prod.yml`
3. `docker-compose -f docker-compose.prod.yml up -d postgres`
4. Wait for it to be healthy, then restart api/panel/cron

The droplet snapshot taken before starting also provides a full recovery point.

---

## Cost summary (estimate)

| Item | Before | After |
|---|---|---|
| Droplet daily backups | ~$8/month | ~$4/month (weekly) or $0 |
| Managed PostgreSQL | $0 | ~$15/month |
| **Net change** | | **+$7–11/month** |

The reliability and time saved on DB maintenance justifies the cost increase.
