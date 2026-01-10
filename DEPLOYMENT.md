# Production Deployment Guide

This guide explains how to deploy the Defender XDR Endpoint Policy Manager to production.

## Prerequisites

- Python 3.8 or higher
- Azure AD App Registration with appropriate permissions
- Production server (Linux, Windows, or cloud platform)

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

## Cloud Deployment

### Heroku

1. Create a new Heroku app:
```bash
heroku create your-app-name
```

2. Set environment variables:
```bash
heroku config:set TENANT_ID=your-tenant-id
heroku config:set CLIENT_ID=your-client-id
heroku config:set CLIENT_SECRET=your-client-secret
heroku config:set FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

3. Deploy:
```bash
git push heroku main
```

The `Procfile` is already configured for Heroku.

### Docker

Build and run with Docker:

```bash
docker build -t defender-xdr-manager .
docker run -p 5000:5000 --env-file .env defender-xdr-manager
```

### Cloudflare Workers/Pages

For Cloudflare deployment, you'll need to adapt the Flask app to run as a Cloudflare Worker or use Cloudflare Pages Functions. Consider using a Python WSGI adapter for Cloudflare.

### Azure App Service

1. Create an Azure App Service (Python 3.x)
2. Configure application settings (environment variables)
3. Deploy using:
   - Azure CLI
   - GitHub Actions
   - VS Code extension
   - ZIP deployment

Startup command: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 wsgi:app`

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
- Use a reverse proxy (nginx, Apache) with SSL termination
- Or use cloud provider SSL (Cloudflare, AWS ALB, Azure App Gateway)

**Firewall:**
- Restrict access to specific IP ranges if possible
- Use Azure AD Conditional Access for additional protection

**Secrets Management:**
- Never commit `.env` file to Git
- Use secret management services (Azure Key Vault, AWS Secrets Manager)
- Rotate client secrets regularly

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
