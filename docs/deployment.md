# Deployment Guide

## Architecture

```
                    ┌─────────────┐
                    │   Vercel    │
                    │  (Next.js)  │
                    │  Web Console│
                    └──────┬──────┘
                           │ NEXT_PUBLIC_API_URL
                           ▼
┌──────────────────────────────────────────┐
│              Railway                      │
│  ┌─────────────┐    ┌─────────────────┐  │
│  │  API Service │    │  Worker Service  │  │
│  │  (FastAPI)   │    │  (Celery)       │  │
│  └──────┬───────┘    └────────┬────────┘  │
└─────────┼─────────────────────┼───────────┘
          │                     │
    ┌─────┴─────┐         ┌────┴────┐
    │   Neon    │         │ Upstash │
    │ Postgres  │         │  Redis  │
    └───────────┘         └─────────┘
```

| Service | Platform | Cost |
|---|---|---|
| API (FastAPI + Alembic) | Railway | ~$5/mo (usage-based) |
| Worker (Celery) | Railway | ~$2/mo (usage-based) |
| Web Console (Next.js) | Vercel | Free tier |
| PostgreSQL 16 | Neon | Free tier (0.5 GB) |
| Redis | Upstash | Free tier (10k cmds/day) |

---

## Step 1: Provision Databases

### Neon (PostgreSQL)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a project → name it `jevops`
3. Copy the connection string from the dashboard:
   ```
   postgresql://jevops:password@ep-xxx-123456.us-east-2.aws.neon.tech/jevops?sslmode=require
   ```
4. Extract the parts for env vars:
   ```
   JEVOPS_DB_HOST=ep-xxx-123456.us-east-2.aws.neon.tech
   JEVOPS_DB_PORT=5432
   JEVOPS_DB_USER=jevops
   JEVOPS_DB_PASSWORD=<password>
   JEVOPS_DB_NAME=jevops
   ```

### Upstash (Redis)

1. Sign up at [upstash.com](https://upstash.com)
2. Create a Redis database → region matching your Railway region
3. Copy connection details:
   ```
   JEVOPS_REDIS_HOST=xxx.upstash.io
   JEVOPS_REDIS_PORT=6379
   CELERY_BROKER_URL=rediss://default:<password>@xxx.upstash.io:6379/1
   CELERY_RESULT_BACKEND=rediss://default:<password>@xxx.upstash.io:6379/2
   ```

> **Note:** Upstash uses `rediss://` (TLS). Make sure the Celery URLs use `rediss://`, not `redis://`.

---

## Step 2: Deploy API + Worker on Railway

### Install Railway CLI

```bash
npm i -g @railway/cli
railway login
```

### Create Project

```bash
cd /path/to/jevops
railway init    # Creates a new Railway project
```

### Deploy the API Service

```bash
cd apps/api
railway up
```

Railway auto-detects the `Dockerfile` and `railway.toml`. After the first deploy:

1. Go to the Railway dashboard → your project → API service
2. Open **Settings → Networking** → **Generate Domain** (gives you `https://your-api.up.railway.app`)
3. Open **Variables** and add:

```
JEVOPS_ENVIRONMENT=production
JEVOPS_LOG_FORMAT=json
JEVOPS_DB_HOST=ep-xxx-123456.us-east-2.aws.neon.tech
JEVOPS_DB_PORT=5432
JEVOPS_DB_USER=jevops
JEVOPS_DB_PASSWORD=<neon password>
JEVOPS_DB_NAME=jevops
JEVOPS_REDIS_HOST=xxx.upstash.io
JEVOPS_REDIS_PORT=6379
JEVOPS_JEV_PROVIDER=mock
JEVOPS_SECURITY_API_KEY_PEPPER=<generate: openssl rand -hex 32>
JEVOPS_SECURITY_CORS_ORIGINS=["https://your-app.vercel.app"]
JEVOPS_SECURITY_RATE_LIMIT_PER_MINUTE=120
PORT=8000
```

### Deploy the Worker Service

In the Railway dashboard:

1. Click **+ New Service** → **From Repo** (same repo)
2. Set **Root Directory** to `apps/api`
3. In **Settings**:
   - **Start Command**: `uv run celery -A jevops.workers.celery_app:celery_app worker -l info`
4. Add the same env vars as the API **plus**:

```
CELERY_BROKER_URL=rediss://default:<password>@xxx.upstash.io:6379/1
CELERY_RESULT_BACKEND=rediss://default:<password>@xxx.upstash.io:6379/2
```

### Run Migrations + Seed

The API's `start.sh` runs `alembic upgrade head` on every deploy. For the initial seed:

```bash
# SSH into Railway (or use the Railway shell)
railway run --service api -- uv run python -m jevops.database.seed
```

Or call the reset endpoint. It is disabled unless `JEVOPS_SECURITY_DEMO_RESET_TOKEN` is set on the API service, and it **wipes all data**:
```bash
curl -X POST https://your-api.up.railway.app/v1/demo/reset -H "X-Demo-Reset-Token: $JEVOPS_SECURITY_DEMO_RESET_TOKEN"
```
Unset the token again afterwards so the endpoint stays disabled.

### Verify

```bash
curl https://your-api.up.railway.app/health
# {"status":"ok"}
```

---

## Step 3: Deploy Web Console on Vercel

### Install Vercel CLI

```bash
npm i -g vercel
```

### Deploy

```bash
cd apps/web
vercel
```

Follow the prompts:
- **Link to existing project?** No → create new
- **Framework?** Next.js (auto-detected)
- **Root directory?** `./` (since you're in `apps/web`)

### Set Environment Variables

In the Vercel dashboard → your project → **Settings → Environment Variables**:

```
NEXT_PUBLIC_API_URL = https://your-api.up.railway.app
NEXT_PUBLIC_API_KEY = jvo_live_<prefix>_<secret>
```

> Get the API key from the seed output, or by calling `POST /v1/demo/reset` with the `X-Demo-Reset-Token` header (see above).

### Redeploy

```bash
vercel --prod
```

### Verify

Open `https://your-app.vercel.app` — should show the JevOps operations console.

---

## Step 4: Connect TypeSafe Jev (Optional)

To use the real Jev model instead of the mock provider:

1. Get an API key from [TypeSafe AI](https://typesafe.ai)
2. Add to Railway API env vars:
   ```
   JEVOPS_JEV_PROVIDER=typesafe
   JEVOPS_JEV_API_KEY=<your key>
   ```
3. Redeploy the API service

---

## CI/CD

### Automatic Deploys

**Railway:** Link your GitHub repo in the Railway dashboard → every push to `main` triggers a deploy.

**Vercel:** Link your GitHub repo in the Vercel dashboard → every push to `main` triggers a deploy. Set **Root Directory** to `apps/web`.

### GitHub Actions (Existing)

The existing `.github/workflows/ci.yml` runs lint + tests on every push/PR. No changes needed — Railway and Vercel handle deployment separately.

---

## Post-Deployment Checklist

- [ ] `curl https://your-api.up.railway.app/health` returns `{"status":"ok"}`
- [ ] `POST /v1/demo/reset` succeeds and returns an API key
- [ ] Swagger UI accessible at `https://your-api.up.railway.app/docs`
- [ ] Web console loads at `https://your-app.vercel.app`
- [ ] Web console can fetch decisions from the API (check browser console for CORS errors)
- [ ] `JEVOPS_SECURITY_API_KEY_PEPPER` is set to a unique random value (not the default)
- [ ] `JEVOPS_SECURITY_CORS_ORIGINS` includes your Vercel domain
- [ ] Worker is running (check Railway logs for `celery@... ready`)

---

## Troubleshooting

### CORS Errors in Browser

The web console on Vercel calls the API on Railway — this is a cross-origin request. Make sure:

```
JEVOPS_SECURITY_CORS_ORIGINS=["https://your-app.vercel.app"]
```

### Neon Connection Timeouts

Neon suspends idle databases on the free tier. The first request after idle may take 3-5 seconds. If you see connection errors:

- Neon has a `?sslmode=require` requirement — ensure your connection uses it
- The `asyncpg` driver handles this by default via the connection string

### Upstash Redis TLS

Upstash requires TLS. Use `rediss://` (double s) in Celery URLs, not `redis://`.

### Alembic Migrations Fail

If migrations fail on deploy, check the Railway build logs. Common issues:

- Missing `psycopg2` dependency — the Dockerfile installs it via `uv sync`
- Wrong DB credentials — verify env vars in Railway dashboard
- The `alembic/env.py` reads the DB URL from `JEVOPS_DB_*` env vars at runtime, not from `alembic.ini`

### Railway Port

Railway auto-assigns `PORT`. The `start.sh` script uses `${PORT:-8000}`. Do not hardcode port 8000 in Railway env vars unless needed.

---

## Custom Domain (Optional)

### Railway

1. Dashboard → API service → **Settings → Networking → Custom Domain**
2. Add your domain (e.g., `api.jevops.yourdomain.com`)
3. Add the CNAME record shown in your DNS provider

### Vercel

1. Dashboard → Project → **Settings → Domains**
2. Add your domain (e.g., `console.jevops.yourdomain.com`)
3. Add the DNS records shown

Update `JEVOPS_SECURITY_CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` to match the new domains.

---

## Development

For local development, nothing changes:

```bash
make up          # Postgres (port 5433) + Redis via Docker
make migrate     # Run migrations
make seed        # Seed demo data
make dev         # Start API on :8000
```
