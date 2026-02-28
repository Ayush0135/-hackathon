# Deployment Guide

This application has two parts:
1. **Frontend**: A Next.js application.
2. **Backend**: A Python FastAPI server with **WebSockets**.

## \u26A0\uFE0F Critical Warning: WebSockets & Vercel
**Vercel does NOT support WebSockets** in its serverless functions. Because this application relies on WebSockets for real-time research updates, you **cannot** deploy the backend (`server.py`) to Vercel.

You must deploy the backend to a service that supports persistent servers, such as **Render**, **Railway**, or **Fly.io**.

---

## Step 1: Deploy Backend (Recommended: Render)

1. Push your code to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Connect your repository.
4. **Settings**:
   - **Root Directory**: `.` (The main folder)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py` (or `uvicorn server:app --host 0.0.0.0 --port $PORT`)
   - **Environment Variables**: Add your keys (`GROQ_API_KEY`, `ANTHROPIC_API_KEY`, etc.).
5. Deploy. You will get a URL (e.g., `https://my-research-agent.onrender.com`).

## Step 2: Configure Frontend

1. Go to `frontend/app/page.tsx` (or where the WebSocket URL is defined).
2. Update the WebSocket connection logic to use an Environment Variable or the production URL.

**Update `frontend/app/page.tsx`**:
```typescript
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
// Or for HTTP calls
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

## Step 3: Deploy Frontend (Vercel)

1. Go to [Vercel](https://vercel.com).
2. Import your Git repository.
3. **Configure Project**:
   - **Framework Preset**: Next.js
   - **\u26A0\uFE0F Root Directory**: Click "Edit" and select `frontend`. **(Crucial Step)**.
4. **Environment Variables**:
   - Add `NEXT_PUBLIC_WS_URL`.
     - Value: `wss://your-backend-url.onrender.com/ws` (Note: `wss://` for secure WebSocket).
   - Add `NEXT_PUBLIC_API_URL`.
     - Value: `https://your-backend-url.onrender.com`
5. Deploy.

## Troubleshooting 404 on Vercel
If you get a 404:
- Ensure you set the **Root Directory** to `frontend` in Vercel.
- If you didn't, Vercel tried to build the root folder, found no Next.js app, and deployed an empty static site.
