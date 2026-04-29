# Deploy to Railway.app - Step by Step Guide

## Prerequisites
- GitHub account
- Railway.app account (free - sign up with GitHub)

---

## Step 1: Push Code to GitHub

### Option A: Create New Repository (Recommended)

1. Go to https://github.com/new
2. Create a new repository named `agroptics-api`
3. **Don't** initialize with README (we have files already)
4. Click "Create repository"

5. In your terminal, navigate to the `api` folder:
```bash
cd "AA GT Restructured files/api"
```

6. Initialize git and push:
```bash
git init
git add .
git commit -m "Initial commit - Agroptics API"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agroptics-api.git
git push -u origin main
```

### Option B: Use Existing Repository

If you already have a git repository:
```bash
cd "AA GT Restructured files/api"
git add .
git commit -m "Add Agroptics API"
git push
```

---

## Step 2: Deploy to Railway

### 2.1 Sign Up for Railway

1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub

### 2.2 Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `agroptics-api` repository
4. Click "Deploy Now"

### 2.3 Configure Deployment

Railway will auto-detect Python and start deploying!

**Wait 2-3 minutes** for the build to complete.

### 2.4 Get Your Public URL

1. Click on your deployment
2. Go to "Settings" tab
3. Scroll to "Networking"
4. Click "Generate Domain"
5. You'll get a URL like: `https://agroptics-api-production.up.railway.app`

---

## Step 3: Test Your Deployed API

### Test Health Check

Open in browser:
```
https://YOUR-APP.up.railway.app/api/v1/health
```

You should see:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "..."
}
```

### Test Interactive Docs

Open in browser:
```
https://YOUR-APP.up.railway.app/api/v1/docs
```

You'll see the same beautiful API docs, but now **publicly accessible**!

### Test API Endpoint

```bash
curl -X POST "https://YOUR-APP.up.railway.app/api/v1/process/indices" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif",
    "field_name": "Field_Test"
  }'
```

---

## Step 4: Share with Your Backend Team

Give them:

1. **API Base URL:** `https://YOUR-APP.up.railway.app`
2. **Interactive Docs:** `https://YOUR-APP.up.railway.app/api/v1/docs`
3. **Endpoints:**
   - `POST /api/v1/process/indices` - Single image
   - `POST /api/v1/process/indices/batch` - Multiple images
   - `POST /api/v1/process/water-balance` - Water balance
   - `POST /api/v1/process/complete` - Complete pipeline

---

## Troubleshooting

### Build Failed

**Check the logs:**
1. Go to Railway dashboard
2. Click on your deployment
3. Click "Deployments" tab
4. Click on the failed deployment
5. Check the build logs

**Common issues:**
- Missing `reference code` folder → Make sure to include it in git
- Missing dependencies → Check `requirements.txt`

### API Returns 500 Error

**Check runtime logs:**
1. Go to Railway dashboard
2. Click "View Logs"
3. Look for Python errors

**Common issues:**
- Import errors → Make sure folder structure is correct
- Missing files → Check that all files are committed to git

### Slow Response

Railway free tier has:
- Shared CPU
- 512MB RAM
- May sleep after inactivity (first request takes ~10s)

**Solutions:**
- Upgrade to paid plan ($5/month)
- Use Railway's "Keep Alive" feature
- Accept the cold start delay

---

## Alternative: Deploy to Render.com (Also Free)

If Railway doesn't work, try Render.com:

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your repository
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"

Render gives you:
- Free tier (750 hours/month)
- Auto HTTPS
- Auto deploy on git push

---

## Cost Comparison

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway | $5 credit/month | $5/month |
| Render | 750 hours/month | $7/month |
| Fly.io | 3 shared VMs | $1.94/VM/month |
| Heroku | None | $7/month |

**Recommendation:** Start with Railway (easiest), then move to Fly.io for production (best performance/price).

---

## Next Steps After Deployment

1. ✅ Test all endpoints
2. ✅ Share URL with backend team
3. ✅ Add API key authentication (optional)
4. ✅ Set up monitoring (Railway has built-in metrics)
5. ✅ Configure custom domain (optional)

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- This API's docs: https://YOUR-APP.up.railway.app/api/v1/docs
