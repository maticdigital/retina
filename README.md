# Retina
AI-enabled website intelligence platform for competitive benchmarking

## Deployment

This project is configured for **Vercel deployment** with optimized dependencies.

### Quick Start

1. **Backend**: Deploy from root directory → See `DEPLOY-VERCEL.md`
2. **Frontend**: Deploy from `/web` directory → See `DEPLOY-VERCEL.md`

### Key Files

- `vercel.json` - Backend deployment configuration
- `web/vercel.json` - Frontend deployment configuration  
- `requirements.txt` - Lightweight dependencies optimized for Vercel
- `DEPLOY-VERCEL.md` - Complete deployment guide

### Development

```bash
# Backend (FastAPI)
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend (React/Vite)
cd web
npm install
npm run dev
```
