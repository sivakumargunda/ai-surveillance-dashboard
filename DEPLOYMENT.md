# Deployment Guide

This project deploys as two parts:

- FastAPI backend for alerts, camera streams, zones, and health checks.
- React frontend built as static files.

## 1. Prepare Environment

Copy the example environment file and edit values for your server:

```bash
cp .env.example .env
```

Important production values:

- `CORS_ORIGINS`: the deployed frontend URL, for example `https://sentinel.example.com`.
- `REACT_APP_API_BASE_URL`: the deployed API URL, for example `https://api.sentinel.example.com`.
- `AUTO_START_CAMERAS`: use `false` for API-only deploys, `true` for an edge server connected to cameras.
- `MULTI_CAM_URLS`: comma-separated camera URLs only if the deployment machine can reach them.
- `DATABASE_URL`: keep SQLite for demos, use PostgreSQL for production scale.

## 2. Backend

Run locally in production mode:

```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Docker:

```bash
docker build -t sentinel-api .
docker run --env-file .env -p 8000:8000 -v "%cd%/artifacts:/app/artifacts" sentinel-api
```

Docker Compose:

```bash
docker compose up --build
```

## 3. Frontend

Build with the production API URL:

```bash
cd frontend
REACT_APP_API_BASE_URL=https://your-api-domain.com npm run build
```

On PowerShell:

```powershell
cd frontend
$env:REACT_APP_API_BASE_URL="https://your-api-domain.com"
npm run build
```

Deploy `frontend/build` to any static host such as nginx, Vercel, Netlify, S3, or CloudFront.

## 4. Camera Deployment Notes

Cloud servers usually cannot reach private camera URLs like `192.168.x.x`.

Use one of these patterns:

- Deploy the backend on an edge machine in the same network as the cameras.
- Connect cloud backend to the camera network through VPN.
- Expose secure RTSP/HTTP streams with authentication and firewall rules.

For headless servers, set:

```bash
SHOW_WINDOW=false
AUTO_START_CAMERAS=true
```

## 5. Pre-Deploy Checks

Run these before shipping:

```bash
python -m compileall api.py core pipeline ingestion scripts
python -c "import api; print(api.app.title)"
cd frontend && npm run build
```
