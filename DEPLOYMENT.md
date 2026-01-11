# Production Deployment Guide

This guide explains how to deploy the Defender XDR Endpoint Policy Manager to production on Windows, Linux, and Azure App Service.

## Prerequisites

- Python 3.8 or higher
- Azure AD App Registration with appropriate permissions
- Production server (Windows, Linux, or Azure App Service)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure with your Azure AD credentials:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `TENANT_ID` - Your Azure AD Tenant ID
- `CLIENT_ID` - Your App Registration Client ID
- `CLIENT_SECRET` - Your App Registration Client Secret
- `FLASK_SECRET_KEY` - Generate a random secret key

**Generate a secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start the Production Server

#### Linux/Mac (using Gunicorn)
```bash
chmod +x start_production.sh
./start_production.sh
```

#### Windows (using Waitress)
```bash
start_production.bat
```

#### Manual Start (Gunicorn)
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 wsgi:app
```

#### Manual Start (Waitress)
```bash
waitress-serve --host=0.0.0.0 --port=5000 --threads=8 wsgi:app
```

## Production Configuration

### Environment Variables

**Required:**
- `TENANT_ID` - Azure AD Tenant ID
- `CLIENT_ID` - Azure AD Application Client ID
- `CLIENT_SECRET` - Azure AD Application Client Secret
- `FLASK_SECRET_KEY` - Random secret key for session encryption

**Optional:**
- `FLASK_ENV` - Set to `production` (default)
- `FLASK_DEBUG` - Set to `False` in production (default)
- `PORT` - Port to run on (default: 5000)
- `GRAPH_API_ENDPOINT` - Microsoft Graph API endpoint
- `DEFENDER_API_ENDPOINT` - Defender API endpoint

### Server Settings

**Gunicorn (Linux/Mac):**
- Workers: 4 (adjust based on CPU cores: 2-4 × CPU cores)
- Threads: 2 per worker
- Timeout: 120 seconds (API calls can take time)
- Worker class: `gthread` for threading support

**Waitress (Windows/Cross-platform):**
- Threads: 8 (adjust based on expected load)
- Connection limit: Auto-configured

## Deployment Options

### Option 1: Local Windows Server

**Using Waitress (recommended for Windows):**

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env` file with your credentials

3. Start the production server:
```bash
start_production.bat
```

**Manual start:**
```bash
waitress-serve --host=0.0.0.0 --port=5000 --threads=8 wsgi:app
```

**Run as Windows Service:**

Create a `nssm` service to run the app as a Windows service:
```bash
# Install NSSM (Non-Sucking Service Manager)
# Download from https://nssm.cc/

# Create service
nssm install DefenderXDRManager "C:\Python\python.exe" "C:\path\to\app\start_production.bat"
nssm set DefenderXDRManager AppDirectory "C:\path\to\app"
nssm start DefenderXDRManager
```

### Option 2: Local Linux Server

**Using Gunicorn (recommended for Linux):**

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env` file with your credentials

3. Start the production server:
```bash
chmod +x start_production.sh
./start_production.sh
```

**Manual start:**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 wsgi:app
```

**Run as systemd service:**

Create `/etc/systemd/system/defender-xdr.service`:
```ini
[Unit]
Description=Defender XDR Endpoint Policy Manager
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/defender-xdr-manager
Environment="PATH=/opt/defender-xdr-manager/venv/bin"
ExecStart=/opt/defender-xdr-manager/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable defender-xdr
sudo systemctl start defender-xdr
sudo systemctl status defender-xdr
```

### Option 3: Docker Container

**Build and run:**

```bash
# Build image
docker build -t defender-xdr-manager .

# Run with environment file
docker run -d -p 5000:8080 --env-file .env --name defender-xdr defender-xdr-manager

# Or set environment variables directly
docker run -d -p 5000:8080 \
  -e TENANT_ID=your-tenant-id \
  -e CLIENT_ID=your-client-id \
  -e CLIENT_SECRET=your-client-secret \
  -e FLASK_SECRET_KEY=your-secret-key \
  --name defender-xdr \
  defender-xdr-manager
```

**Using Docker Compose:**

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:8080"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker-compose up -d
```

### Option 4: Azure App Service

**Deploy using Azure CLI:**

1. **Create Resource Group and App Service Plan:**
```bash
# Login to Azure
az login

# Create resource group
az group create --name defender-xdr-rg --location eastus

# Create App Service Plan (Linux)
az appservice plan create \
  --name defender-xdr-plan \
  --resource-group defender-xdr-rg \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --resource-group defender-xdr-rg \
  --plan defender-xdr-plan \
  --name defender-xdr-manager \
  --runtime "PYTHON:3.11"
```

2. **Configure Application Settings:**
```bash
az webapp config appsettings set \
  --resource-group defender-xdr-rg \
  --name defender-xdr-manager \
  --settings \
    TENANT_ID="your-tenant-id" \
    CLIENT_ID="your-client-id" \
    CLIENT_SECRET="your-client-secret" \
    FLASK_SECRET_KEY="your-secret-key" \
    FLASK_ENV="production" \
    FLASK_DEBUG="False" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

3. **Configure Startup Command:**
```bash
az webapp config set \
  --resource-group defender-xdr-rg \
  --name defender-xdr-manager \
  --startup-file "gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 wsgi:app"
```

4. **Deploy from local Git or GitHub:**

**Local Git:**
```bash
# Get deployment credentials
az webapp deployment user set --user-name <username> --password <password>

# Get Git URL
az webapp deployment source config-local-git \
  --name defender-xdr-manager \
  --resource-group defender-xdr-rg

# Add remote and push
git remote add azure <deployment-url>
git push azure main
```

**GitHub Actions:**
```bash
# Enable GitHub Actions deployment
az webapp deployment github-actions add \
  --resource-group defender-xdr-rg \
  --name defender-xdr-manager \
  --repo "yourusername/repo" \
  --branch main \
  --login-with-github
```

5. **Access your app:**
```
https://defender-xdr-manager.azurewebsites.net
```

**Deploy using Azure Portal:**

1. Go to Azure Portal → Create a resource → Web App
2. Configure:
   - Name: defender-xdr-manager
   - Runtime: Python 3.11
   - Region: Choose closest to you
   - Pricing Plan: Basic B1 or higher
3. After creation, go to Configuration → Application Settings
4. Add environment variables
5. Go to Deployment Center → Choose deployment source (GitHub/Local Git/ZIP)
6. Deploy your code

## Performance Optimization

### Caching

The app currently doesn't implement caching. For production, consider:
- Redis for session caching
- In-memory caching for API responses (with TTL)
- CDN for static assets

### Scaling

**Horizontal Scaling:**
- Run multiple instances behind a load balancer
- Use session storage (Redis) for multi-instance deployments

**Vertical Scaling:**
- Increase worker/thread count based on server resources
- Monitor memory usage (each worker uses memory)

### Monitoring

**Health Check Endpoint:**
```
GET /api/health
```

Returns configuration status and application health.

**Recommended Monitoring:**
- Application Performance Monitoring (APM)
- Log aggregation (ELK, Splunk, CloudWatch)
- Error tracking (Sentry)
- Uptime monitoring

## Security Considerations

### Enabled Security Headers

The production server (`wsgi.py`) adds these security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### Additional Security

**SSL/TLS:**
- Always use HTTPS in production
- Use a reverse proxy (nginx, Apache, IIS) with SSL termination
- Or use cloud provider SSL (Azure App Gateway, Azure Front Door)

**Firewall:**
- Restrict access to specific IP ranges if possible
- Use Azure AD Conditional Access for additional protection

**Secrets Management:**
- Never commit `.env` file to Git
- Use Azure Key Vault for production secrets
- Rotate client secrets regularly
- Use managed identities when deploying to Azure

## Reverse Proxy Setup

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /static {
        alias /path/to/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Troubleshooting

**Server won't start:**
- Check `.env` file exists and has correct values
- Verify Python version (3.8+)
- Check all dependencies installed: `pip install -r requirements.txt`

**API errors:**
- Verify Azure AD app permissions are granted
- Check TENANT_ID, CLIENT_ID, CLIENT_SECRET are correct
- Ensure app has consent for required API scopes

**Performance issues:**
- Increase worker/thread count
- Check API rate limits
- Enable caching
- Monitor server resources (CPU, memory)

## Support

For issues or questions:
1. Check logs for error messages
2. Verify configuration with `/api/health` endpoint
3. Review Azure AD app permissions
4. Check server resources and scaling
