# 🌐 Deployment & Portfolio Showcase Guide

NexusGate is packaged with a **multi-stage `Dockerfile`** that compiles the React/Vite dashboard and bundles it directly inside the FastAPI server. This allows you to deploy the entire full-stack application as **one single service** with zero CORS configuration.

## 1. Push to GitHub
```bash
git init
git add .
git commit -m "feat: initial release of NexusGate LLM Gateway"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/llm-gateway.git
git push -u origin main
```

## 2. Deploy on Render (Free Tier)
1. Go to [render.com](https://render.com) and click **New + → Web Service**.
2. Connect your `llm-gateway` GitHub repository.
3. Configure the service:
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`
4. Add Environment Variables:
   - `SANDBOX_MODE` = `true`
   - `SEED_DEMO_DATA` = `true`
   - `CACHE_ENABLED` = `true`
5. Click **Create Web Service**. Within ~3 minutes, you will receive a public URL (`https://nexusgate-xxxx.onrender.com`) ready to share on your LinkedIn, resume, and GitHub bio!

## 3. Deploy on Railway / Fly.io
- **Railway**: Click *New Project → Deploy from GitHub Repo*. Railway automatically detects the `Dockerfile` and exposes port `8000`.
- **Fly.io**: Run `fly launch` in the root directory and `fly deploy`.
