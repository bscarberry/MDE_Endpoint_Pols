# Cloudflare Deployment Options

## Important Note

**Cloudflare Pages is designed for static sites** (HTML, CSS, JavaScript) and frameworks that build to static files (Next.js, Astro, etc.). It does **not support Python Flask applications** directly.

However, you have several excellent options to deploy this Flask app and leverage Cloudflare:

## Recommended Approach: Backend + Cloudflare DNS/CDN

Deploy your Flask backend to a Python-compatible platform, then use Cloudflare for DNS and CDN:

### Option 1: Railway + Cloudflare (Recommended)

**Railway** is perfect for Flask apps and works great with Cloudflare:

1. **Deploy to Railway:**
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli

   # Login and deploy
   railway login
   railway init
   railway up
   ```

2. **Configure Environment Variables in Railway:**
   - Add all variables from your `.env` file in Railway dashboard
   - Railway provides: `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`, `FLASK_SECRET_KEY`

3. **Get Railway URL:**
   - Railway gives you a URL like: `your-app.up.railway.app`

4. **Configure Cloudflare:**
   - Add your custom domain in Railway
   - Point your Cloudflare DNS to Railway (CNAME record)
   - Enable Cloudflare CDN and DDoS protection

**Railway Configuration (`railway.toml`):**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 wsgi:app"
healthcheckPath = "/api/health"
restartPolicyType = "on-failure"
```

### Option 2: Render + Cloudflare

**Render** is another excellent choice:

1. **Deploy to Render:**
   - Connect your GitHub repo
   - Select "Web Service"
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 wsgi:app`

2. **Environment Variables:**
   - Add in Render dashboard

3. **Point Cloudflare DNS:**
   - CNAME to your Render URL
   - Enable CDN

**Render Blueprint (`render.yaml`):**
```yaml
services:
  - type: web
    name: defender-xdr-manager
    runtime: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 wsgi:app"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: FLASK_DEBUG
        value: false
    healthCheckPath: /api/health
```

### Option 3: Fly.io + Cloudflare

**Fly.io** offers edge deployment close to Cloudflare's model:

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "--timeout", "120", "wsgi:app"]
```

**fly.toml:**
```toml
app = "defender-xdr-manager"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  FLASK_ENV = "production"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[http_service.concurrency]
  type = "requests"
  hard_limit = 250
  soft_limit = 200

[[http_service.checks]]
  interval = "15s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/api/health"
```

Deploy:
```bash
fly launch
fly deploy
```

## Option 4: Heroku (Easiest)

Already configured! Just:

```bash
heroku create your-app-name
heroku config:set TENANT_ID=xxx CLIENT_ID=xxx CLIENT_SECRET=xxx FLASK_SECRET_KEY=xxx
git push heroku main
```

Then point Cloudflare DNS to Heroku.

## Option 5: Azure App Service (Microsoft Ecosystem)

Best for Microsoft-centric deployments:

```bash
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name defender-xdr-manager --runtime "PYTHON:3.11"
az webapp config appsettings set --resource-group myResourceGroup --name defender-xdr-manager --settings @env-vars.json
az webapp deployment source config --name defender-xdr-manager --resource-group myResourceGroup --repo-url https://github.com/yourusername/repo --branch main --manual-integration
```

## Why Not Pure Cloudflare Pages?

**Cloudflare Pages limitations:**
- Only supports static sites (HTML/CSS/JS)
- Pages Functions are lightweight JS/TypeScript, not Python
- No Python runtime available
- No WSGI server support

**To use Cloudflare Pages, you would need to:**
1. Completely rewrite the backend in JavaScript/TypeScript
2. Use Cloudflare Workers for API calls
3. Implement MSAL.js for client-side Azure AD auth
4. Store secrets in environment variables (less secure for client-side)

This would be a **complete rewrite** of the application.

## Recommended Setup

**Best Practice Architecture:**

```
User Request
    ↓
Cloudflare DNS/CDN (your-domain.com)
    ↓
Backend Platform (Railway/Render/Fly.io/Heroku/Azure)
    ↓
Flask App (Gunicorn WSGI Server)
    ↓
Microsoft Graph & Defender APIs
```

**Benefits:**
- ✅ Cloudflare CDN for static assets
- ✅ Cloudflare DDoS protection
- ✅ Cloudflare SSL/TLS
- ✅ Python/Flask backend support
- ✅ Easy scaling
- ✅ Health monitoring

## Quick Start Recommendation

**For fastest deployment with Cloudflare integration:**

1. **Deploy to Railway** (free tier, great performance):
   ```bash
   npm i -g @railway/cli
   railway login
   railway init
   railway up
   ```

2. **Add environment variables** in Railway dashboard

3. **Get your Railway URL** (e.g., `myapp.up.railway.app`)

4. **Configure Cloudflare:**
   - Add a CNAME record: `app` → `myapp.up.railway.app`
   - Enable "Proxied" (orange cloud)
   - Your app is now at: `app.yourdomain.com`

**Total deployment time: ~10 minutes**

## Cost Comparison

| Platform | Free Tier | Paid Starting |
|----------|-----------|---------------|
| Railway | $5 credit/month | $5/month |
| Render | 750 hours/month | $7/month |
| Fly.io | 3 shared VMs | $1.94/month |
| Heroku | No free tier | $5/month |
| Azure App Service | 60 min/day | $13/month |

## Support

Choose the platform that best fits your needs:
- **Railway**: Easiest, great DX
- **Render**: Simple, reliable
- **Fly.io**: Edge deployment, fast
- **Heroku**: Most mature, largest ecosystem
- **Azure**: Best Microsoft integration

All work excellently with Cloudflare DNS and CDN!
