# Azure Web Apps Deployment Guide

This guide covers deploying the Defender XDR Endpoint Policy Manager to Azure Web Apps (App Service).

## Prerequisites

- Azure subscription
- Azure CLI installed (`az` command)
- Python 3.8+ locally for testing
- Git repository (optional but recommended)

## Quick Deployment

### Option 1: Azure CLI (Recommended)

#### 1. Login to Azure

```bash
az login
```

#### 2. Create Resource Group

```bash
az group create --name defender-xdr-rg --location eastus
```

#### 3. Create App Service Plan

```bash
az appservice plan create \
  --name defender-xdr-plan \
  --resource-group defender-xdr-rg \
  --sku B1 \
  --is-linux
```

**SKU Options:**
- `F1` - Free (limited, for testing only)
- `B1` - Basic ($13/month) - Recommended minimum
- `B2` - Basic ($26/month)
- `S1` - Standard ($70/month) - Production recommended
- `P1V2` - Premium ($146/month) - High performance

#### 4. Create Web App

```bash
az webapp create \
  --resource-group defender-xdr-rg \
  --plan defender-xdr-plan \
  --name defender-xdr-policies \
  --runtime "PYTHON:3.11"
```

**Note:** The app name must be globally unique. It will be accessible at:
`https://defender-xdr-policies.azurewebsites.net`

#### 5. Configure Application Settings

```bash
# Set Python version
az webapp config set \
  --resource-group defender-xdr-rg \
  --name defender-xdr-policies \
  --linux-fx-version "PYTHON|3.11"

# Configure environment variables
az webapp config appsettings set \
  --resource-group defender-xdr-rg \
  --name defender-xdr-policies \
  --settings \
    TENANT_ID="your-tenant-id" \
    CLIENT_ID="your-client-id" \
    CLIENT_SECRET="your-client-secret" \
    FLASK_SECRET_KEY="$(openssl rand -hex 32)" \
    FLASK_ENV="production" \
    FLASK_DEBUG="False" \
    PORT="8000" \
    REDIRECT_URI="https://defender-xdr-policies.azurewebsites.net/auth/callback" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    WEBSITES_PORT="8000"
```

#### 6. Deploy Application

**Method A: Local Git Deployment**

```bash
# Configure local git deployment
az webapp deployment source config-local-git \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg

# Get deployment credentials
az webapp deployment list-publishing-credentials \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg \
  --query "{username:publishingUserName, password:publishingPassword}" \
  --output table

# Add Azure remote
git remote add azure https://defender-xdr-policies.scm.azurewebsites.net:443/defender-xdr-policies.git

# Deploy
git push azure main
```

**Method B: GitHub Actions (Recommended)**

```bash
# Connect to GitHub repository
az webapp deployment source config \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg \
  --repo-url https://github.com/yourusername/MDE_Endpoint_Pols \
  --branch main \
  --manual-integration
```

**Method C: ZIP Deployment**

```bash
# Create deployment package
zip -r deploy.zip . -x "*.git*" -x "*venv*" -x "*__pycache__*"

# Deploy
az webapp deployment source config-zip \
  --resource-group defender-xdr-rg \
  --name defender-xdr-policies \
  --src deploy.zip
```

#### 7. Configure Custom Domain (Optional)

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name defender-xdr-policies \
  --resource-group defender-xdr-rg \
  --hostname policies.yourdomain.com

# Enable HTTPS
az webapp update \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg \
  --https-only true
```

#### 8. Enable Logging

```bash
# Enable application logs
az webapp log config \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg \
  --application-logging filesystem \
  --level information

# Stream logs
az webapp log tail \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg
```

---

## Option 2: Azure Portal

### 1. Create Web App

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource**
3. Search for **Web App**
4. Click **Create**

### 2. Configure Basics

- **Subscription**: Select your subscription
- **Resource Group**: Create new or select existing
- **Name**: `defender-xdr-policies` (must be unique)
- **Publish**: `Code`
- **Runtime stack**: `Python 3.11`
- **Operating System**: `Linux`
- **Region**: Choose closest to your users
- **Pricing plan**: Select appropriate tier (B1 minimum recommended)

### 3. Configure Deployment

- **GitHub Actions**: If deploying from GitHub, enable continuous deployment
- **FTP**: Alternative deployment method

### 4. Configure Networking (Optional)

- Enable/disable public access
- Configure virtual network integration
- Set up private endpoints

### 5. Configure Monitoring

- Enable Application Insights for monitoring
- Set up alerts

### 6. Review and Create

Click **Create** and wait for deployment to complete.

### 7. Configure Application Settings

After creation:

1. Go to your Web App → **Configuration** → **Application settings**
2. Add the following settings:

```
TENANT_ID = your-tenant-id
CLIENT_ID = your-client-id
CLIENT_SECRET = your-client-secret
FLASK_SECRET_KEY = generate-random-32-char-hex
FLASK_ENV = production
FLASK_DEBUG = False
PORT = 8000
REDIRECT_URI = https://your-app-name.azurewebsites.net/auth/callback
WEBSITES_PORT = 8000
SCM_DO_BUILD_DURING_DEPLOYMENT = true
```

3. Click **Save**

### 8. Deploy Code

**Deployment Center** → Select deployment method:
- GitHub
- Local Git
- Azure Repos
- FTP
- ZIP Deploy

---

## Azure AD Configuration

After deployment, update your Azure AD App Registration:

1. Go to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Select your app → **Authentication**
3. Add redirect URI:
   ```
   https://your-app-name.azurewebsites.net/auth/callback
   ```
4. Click **Save**

---

## Troubleshooting

### Application doesn't start

**Check logs:**
```bash
az webapp log tail --name defender-xdr-policies --resource-group defender-xdr-rg
```

**Common issues:**
- Missing `startup.txt` or incorrect startup command
- Missing environment variables
- Python version mismatch
- Dependencies not installed

### Authentication fails

- Verify `REDIRECT_URI` matches Azure AD exactly
- Check `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` are correct
- Ensure Azure AD redirect URI includes your Azure Web App URL

### Application timeout

- Increase timeout in Azure Portal → Configuration → General settings
- Scale up to higher tier for more resources

### Session issues

- Azure Web Apps uses sticky sessions by default (ARR Affinity)
- For multi-instance deployments, consider Redis session storage

---

## Scaling

### Vertical Scaling (Scale Up)

```bash
az appservice plan update \
  --name defender-xdr-plan \
  --resource-group defender-xdr-rg \
  --sku S1
```

### Horizontal Scaling (Scale Out)

```bash
az appservice plan update \
  --name defender-xdr-plan \
  --resource-group defender-xdr-rg \
  --number-of-workers 3
```

### Auto-scaling

Configure in Azure Portal → Scale out (App Service plan) → Custom autoscale

---

## Monitoring

### Application Insights

Enable in Azure Portal → Application Insights → Enable

**Features:**
- Performance monitoring
- Request tracking
- Dependency tracking
- Exception tracking
- Custom metrics

### Health Check

Configure health check endpoint:

```bash
az webapp config set \
  --resource-group defender-xdr-rg \
  --name defender-xdr-policies \
  --health-check-path "/api/health"
```

---

## Security

### Managed Identity

Enable managed identity to avoid storing credentials:

```bash
az webapp identity assign \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg
```

### Key Vault Integration

Store secrets in Azure Key Vault:

```bash
# Reference Key Vault secret in app settings
az webapp config appsettings set \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg \
  --settings CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/client-secret)"
```

### Network Security

- Enable virtual network integration
- Configure private endpoints
- Set up NSG rules
- Enable DDoS protection

---

## Cost Optimization

### Development Environment

- Use **F1** (Free) or **B1** ($13/month) tier
- Use single instance
- Disable Application Insights or use sampling

### Production Environment

- **S1** ($70/month) for standard workloads
- Enable auto-scaling based on CPU/memory
- Use Application Insights with sampling
- Configure alerts for cost management

### Estimated Costs

| Tier | Monthly Cost | Instances | Memory | CPU |
|------|-------------|-----------|--------|-----|
| F1   | Free        | 1         | 1 GB   | Shared |
| B1   | ~$13        | 1-3       | 1.75 GB | 1 core |
| B2   | ~$26        | 1-3       | 3.5 GB  | 2 cores |
| S1   | ~$70        | 1-10      | 1.75 GB | 1 core |
| P1V2 | ~$146       | 1-20      | 3.5 GB  | 1 core |

---

## Maintenance

### Update Application

**Method 1: Git Push**
```bash
git push azure main
```

**Method 2: ZIP Deploy**
```bash
az webapp deployment source config-zip \
  --resource-group defender-xdr-rg \
  --name defender-xdr-policies \
  --src deploy.zip
```

**Method 3: Continuous Deployment**
- Automatically deploys on git push if GitHub Actions configured

### Restart Application

```bash
az webapp restart \
  --name defender-xdr-policies \
  --resource-group defender-xdr-rg
```

### View Logs

```bash
# Stream logs
az webapp log tail --name defender-xdr-policies --resource-group defender-xdr-rg

# Download logs
az webapp log download --name defender-xdr-policies --resource-group defender-xdr-rg
```

---

## Backup and Recovery

### Enable Backup

```bash
az webapp config backup update \
  --resource-group defender-xdr-rg \
  --webapp-name defender-xdr-policies \
  --backup-name daily-backup \
  --container-url "https://yourstorageaccount.blob.core.windows.net/backups?sv=..."
```

### Restore from Backup

Available in Azure Portal → Backups → Restore

---

## Best Practices

1. **Use deployment slots** for zero-downtime deployments
2. **Enable Application Insights** for monitoring
3. **Use Key Vault** for sensitive configuration
4. **Enable auto-scaling** for production
5. **Configure health checks** for monitoring
6. **Use managed identity** instead of service principal where possible
7. **Enable HTTPS only** and use custom domains with SSL
8. **Set up alerts** for errors and performance issues
9. **Regular backups** of configuration and data
10. **Use deployment slots** for staging before production

---

## Additional Resources

- [Azure Web Apps Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Python on Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/webapp)
- [App Service Pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/)
