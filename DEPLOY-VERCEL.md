# Retina — Vercel Deployment Guide

This project deploys as **two separate Vercel projects**:

| Service | Directory | Runtime | Purpose |
|---------|-----------|---------|---------|
| `retina-api` | `/` (root) | Python 3.11 | FastAPI backend |
| `retina-web` | `/web` | Node 20 | React/Vite frontend |

---

## Prerequisites

- Vercel account at [vercel.com](https://vercel.com)
- GitHub repo connected to Vercel
- Supabase project already running with tables/RLS configured

---

## Step 1: Deploy the Backend (`retina-api`)

### 1a. Create the Vercel project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **"Import Git Repository"**
3. Select the `retina` repository
4. Configure the project:
   - **Project Name**: `retina-api`
   - **Framework Preset**: Other
   - **Root Directory**: `.` (leave empty for root)
   - **Build Command**: Leave empty (Vercel auto-detects)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty (auto-detects requirements.txt)

### 1b. Set environment variables

In the Vercel dashboard, go to **Settings → Environment Variables** and add:

| Variable | Value | Where to find it |
|----------|-------|-------------------|
| `SUPABASE_URL` | `https://xafturogqjhwtubwoval.supabase.co` | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Supabase → Settings → API → `service_role` key (secret) |
| `SUPABASE_ANON_KEY` | `eyJ...` | Supabase → Settings → API → `anon` public key |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `PAGESPEED_API_KEY` | `AIza...` | Google Cloud Console → APIs & Services → Credentials |
| `BUILTWITH_API_KEY` | `...` | [api.builtwith.com](https://api.builtwith.com) → Account |
| `CORS_ORIGINS` | `https://retina-web.vercel.app` | The frontend Vercel URL (set after Step 2) |
| `PYTHONPATH` | `src` | Required for module imports |

### 1c. Deploy and verify

1. Click **Deploy** in the Vercel dashboard
2. After deployment, visit your API URL (e.g., `https://retina-api.vercel.app/health`)
3. Expected response: `{"status": "ok"}`
4. Also check: `https://retina-api.vercel.app/docs` for Swagger UI

---

## Step 2: Deploy the Frontend (`retina-web`)

### 2a. Create the Vercel project

1. Go to [vercel.com/new](https://vercel.com/new) again
2. Select the same `retina` repository
3. Configure the project:
   - **Project Name**: `retina-web`
   - **Framework Preset**: Vite
   - **Root Directory**: `web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm ci`

### 2b. Set environment variables

In the Vercel dashboard, go to **Settings → Environment Variables** and add:

| Variable | Value | Where to find it |
|----------|-------|-------------------|
| `VITE_API_URL` | `https://retina-api.vercel.app` | The backend Vercel URL from Step 1 |
| `VITE_SUPABASE_URL` | `https://xafturogqjhwtubwoval.supabase.co` | Same as backend |
| `VITE_SUPABASE_ANON_KEY` | `eyJ...` | Same anon key as backend |
| `NODE_ENV` | `production` | Hardcoded value |

> **Important:** `VITE_` prefixed variables are baked into the JS bundle at **build time**. If you change them, you must **redeploy** the frontend.

### 2c. Deploy and verify

1. Click **Deploy** in the Vercel dashboard
2. Visit your frontend URL (e.g., `https://retina-web.vercel.app/`)
3. You should see the Retina login page
4. Open browser DevTools → Network and confirm API calls go to your backend URL

---

## Step 3: Update CORS Configuration

Now that you have the frontend URL, go back to the **retina-api** project:

1. Go to **Settings → Environment Variables**
2. Update `CORS_ORIGINS` to the frontend URL:
   ```
   https://retina-web.vercel.app
   ```
   For multiple origins, comma-separate them:
   ```
   https://retina-web.vercel.app,https://retina.maticdigital.com
   ```
3. Redeploy the backend (Vercel auto-redeploys on variable change)

---

## Step 4: Update Supabase Auth Config

Go to **Supabase Dashboard → Authentication → URL Configuration**:

### Site URL
Set to your frontend URL:
```
https://retina-web.vercel.app
```

### Redirect URLs
Add all of these (one per line):
```
https://retina-web.vercel.app/**
http://localhost:5173/**
http://127.0.0.1:5173/**
```

---

## Important Notes

### Dependency Optimization

This deployment uses a lightweight `requirements.txt` (the original `pyproject.toml` is backed up as `pyproject.toml.bak`) to stay within Vercel's size limits. The following heavy dependencies are **excluded**:

- `weasyprint` - PDF generation (requires system libraries)
- `playwright` - Browser automation (large binary dependencies)

If you need these features, consider:
1. Using external services for PDF generation
2. Using lighter alternatives for browser automation
3. Moving heavy processing to a separate service

### Vercel Limitations

- **Function size limit**: 50MB (configured in vercel.json)
- **Function timeout**: 30 seconds (configured in vercel.json)
- **Cold starts**: First request may be slower
- **No persistent storage**: Use external services for file storage

---

## Troubleshooting

### Backend returns 500
Check Vercel function logs in the dashboard. Common issues:
- Missing environment variables
- Import errors due to excluded dependencies
- Function timeout (increase maxDuration if needed)

### Frontend shows "Network Error"
1. Confirm `VITE_API_URL` is set correctly (no trailing slash)
2. Confirm `CORS_ORIGINS` on the backend includes the exact frontend URL
3. Redeploy both projects after changing env vars

### Function size too large
If deployment fails due to size limits:
1. Review `requirements-vercel.txt` and remove unnecessary dependencies
2. Consider splitting heavy operations into separate microservices
3. Use external APIs instead of local processing

---

## Environment Variables — Complete Reference

### Backend (`retina-api`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key |
| `PAGESPEED_API_KEY` | Yes | Google PageSpeed Insights API key |
| `BUILTWITH_API_KEY` | Yes | BuiltWith API key |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |
| `PYTHONPATH` | Yes | Set to `src` for module imports |

### Frontend (`retina-web`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Full backend URL (no trailing slash) |
| `VITE_SUPABASE_URL` | No | Supabase URL (for future client-side features) |
| `VITE_SUPABASE_ANON_KEY` | No | Supabase anon key (for future client-side features) |
| `NODE_ENV` | No | Set to `production` |
