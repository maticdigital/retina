# Retina — Railway Deployment Guide

This project deploys as **two separate Railway services** within one Railway project:

| Service | Directory | Runtime | Purpose |
|---------|-----------|---------|---------|
| `retina-api` | `/` (root) | Python 3.11 | FastAPI backend |
| `retina-web` | `/web` | Node 20 | React/Vite frontend |

---

## Prerequisites

- Railway account at [railway.app](https://railway.app)
- GitHub repo connected to Railway
- Supabase project already running with tables/RLS configured

---

## Step 1: Create Railway Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Select the `maticdigital/retina` repository
4. This creates the project — you will add two services inside it

---

## Step 2: Deploy the Backend (`retina-api`)

### 2a. Create the service

1. In your Railway project, click **"+ New Service"** → **"GitHub Repo"**
2. Select the `retina` repo
3. Railway auto-detects Python via `requirements.txt` and `nixpacks.toml`
4. In **Settings → General**:
   - Set **Service Name** to `retina-api`
   - **Root Directory**: leave empty (uses repo root `/`)
5. In **Settings → Networking**:
   - Click **"Generate Domain"** — note the URL (e.g. `retina-api-production.up.railway.app`)

### 2b. Set environment variables

Go to the service **Variables** tab and add each of these:

| Variable | Value | Where to find it |
|----------|-------|-------------------|
| `SUPABASE_URL` | `https://xafturogqjhwtubwoval.supabase.co` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Supabase → Settings → API → `service_role` key (secret) |
| `SUPABASE_ANON_KEY` | `eyJ...` | Supabase → Settings → API → `anon` public key |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `PAGESPEED_API_KEY` | `AIza...` | Google Cloud Console → APIs & Services → Credentials |
| `BUILTWITH_API_KEY` | `...` | [api.builtwith.com](https://api.builtwith.com) → Account |
| `CORS_ORIGINS` | `https://retina-web-production.up.railway.app` | The frontend Railway URL (set after Step 3) |
| `PORT` | `8000` | Railway injects this automatically — only set if needed |

> **Note:** Do NOT set `DYLD_LIBRARY_PATH` — that is macOS-only. Railway runs Linux and nixpacks.toml handles system deps.

### 2c. Verify deployment

After deploy completes, visit:
```
https://<your-api-domain>/health
```
Expected response: `{"status": "ok"}`

Also check:
```
https://<your-api-domain>/docs
```
This opens the FastAPI Swagger UI.

---

## Step 3: Deploy the Frontend (`retina-web`)

### 3a. Create the service

1. In the same Railway project, click **"+ New Service"** → **"GitHub Repo"**
2. Select the same `retina` repo again
3. In **Settings → General**:
   - Set **Service Name** to `retina-web`
   - **Root Directory**: set to `web`
4. In **Settings → Networking**:
   - Click **"Generate Domain"** — note the URL (e.g. `retina-web-production.up.railway.app`)

### 3b. Set environment variables

Go to the service **Variables** tab and add:

| Variable | Value | Where to find it |
|----------|-------|-------------------|
| `VITE_API_URL` | `https://retina-api-production.up.railway.app` | The backend Railway URL from Step 2 |
| `VITE_SUPABASE_URL` | `https://xafturogqjhwtubwoval.supabase.co` | Same as backend (for future client-side use) |
| `VITE_SUPABASE_ANON_KEY` | `eyJ...` | Same anon key as backend (for future client-side use) |
| `NODE_ENV` | `production` | Hardcoded value |

> **Important:** `VITE_` prefixed variables are baked into the JS bundle at **build time**. If you change them, you must **redeploy** the frontend (not just restart).

### 3c. Verify deployment

Visit your frontend URL:
```
https://<your-web-domain>/
```
You should see the Retina login page. Open browser DevTools → Network and confirm API calls go to your backend URL (not `localhost:8000`).

---

## Step 4: Wire CORS (Backend → Frontend)

Now that you have the frontend URL, go back to the **retina-api** service:

1. Go to **Variables**
2. Set `CORS_ORIGINS` to the frontend URL:
   ```
   https://retina-web-production.up.railway.app
   ```
   For multiple origins, comma-separate them:
   ```
   https://retina-web-production.up.railway.app,https://retina.maticdigital.com
   ```
3. Redeploy the backend (Railway auto-redeploys on variable change)

---

## Step 5: Update Supabase Auth Config

Go to **Supabase Dashboard → Authentication → URL Configuration**:

### Site URL
Set to your frontend URL:
```
https://retina-web-production.up.railway.app
```

### Redirect URLs
Add all of these (one per line):
```
https://retina-web-production.up.railway.app/**
http://localhost:5173/**
http://127.0.0.1:5173/**
```

This ensures password reset emails and email confirmations redirect to the correct domain.

---

## Step 6: Smoke Test

Run through this checklist after both services are deployed:

- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `GET /docs` opens Swagger UI
- [ ] Frontend loads the login page
- [ ] Login with existing credentials succeeds
- [ ] Dashboard loads with project list
- [ ] Open a project detail page
- [ ] Lens detail pages load with scores
- [ ] PDF export triggers and completes (check `/projects/{id}/export/status`)
- [ ] Downloaded PDF contains screenshot and all lens pages

---

## Troubleshooting

### Backend returns 500
Check Railway logs for the service. The export background task logs which step failed:
- `Data adapter failed: ...` → Supabase connection or query issue
- `PDF render failed: ...` → WeasyPrint or template issue
- `Upload failed: ...` → Supabase Storage bucket issue

### Frontend shows "Network Error" or CORS errors
1. Confirm `VITE_API_URL` is set correctly (no trailing slash)
2. Confirm `CORS_ORIGINS` on the backend includes the exact frontend URL
3. Redeploy both services after changing env vars

### WeasyPrint errors on Railway
The `nixpacks.toml` in the repo root installs all required system libraries. If you see `OSError: cannot load library` errors, check that Railway is using the nixpacks.toml and that all packages in `[phases.setup].nixPkgs` resolved.

### VITE_API_URL not taking effect
`VITE_` env vars are compile-time only. Changing them requires a full redeploy (not just restart). In Railway: Settings → Deploy → Trigger Redeploy.

---

## Environment Variables — Complete Reference

### Backend (`retina-api`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key (bypasses RLS) |
| `SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key |
| `PAGESPEED_API_KEY` | Yes | Google PageSpeed Insights API key |
| `BUILTWITH_API_KEY` | Yes | BuiltWith API key |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |

### Frontend (`retina-web`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Full backend URL (no trailing slash) |
| `VITE_SUPABASE_URL` | No | Supabase URL (for future client-side features) |
| `VITE_SUPABASE_ANON_KEY` | No | Supabase anon key (for future client-side features) |
| `NODE_ENV` | No | Set to `production` |
