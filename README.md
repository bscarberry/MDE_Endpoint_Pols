# Defender XDR Endpoint Policy Manager

A web-based application for managing and monitoring Microsoft Defender XDR endpoint policies with user authentication.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)

## ✨ Features

- **Policy Management**: View and search all endpoint policies (Compliance, Configuration, Security Intents, Scripts)
- **Device Monitoring**: Track managed devices and Defender XDR machines
- **Security Alerts**: Monitor security alerts from Defender XDR
- **Advanced Hunting**: Run custom KQL queries for threat hunting
- **User Authentication**: Microsoft Azure AD OAuth 2.0 login required
- **Performance**: In-memory caching (10-min TTL) for fast page loads
- **Modern UI**: Terminal-style theme with responsive design

## 🚀 Quick Start (Localhost)

### Prerequisites

- Python 3.8+
- Azure AD App Registration
- Microsoft 365 with Defender XDR and Intune

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/MDE_Endpoint_Pols.git
cd MDE_Endpoint_Pols

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure AD credentials
```

### Configuration

Create `.env` file with your Azure AD app details:

```env
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
FLASK_SECRET_KEY=your-random-secret-key
REDIRECT_URI=http://localhost:5000/auth/callback
```

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Azure AD Setup

**1. App Registration Permissions:**

Add these **Application** permissions to your Azure AD app:

**Microsoft Graph:**
- `DeviceManagementConfiguration.Read.All`
- `DeviceManagementManagedDevices.Read.All`
- `DeviceManagementServiceConfig.Read.All`
- `Group.Read.All`

**Microsoft Defender:**
- `AdvancedQuery.Read.All`
- `Machine.Read.All`
- `Alert.Read.All`

**User Authentication (Delegated):**
- `User.Read`

**2. Authentication Configuration:**

In Azure Portal → App Registration → Authentication:
- Add platform: **Web**
- Redirect URI: `http://localhost:5000/auth/callback`
- Enable: **ID tokens** ✅

**3. Grant Admin Consent**

Click "Grant admin consent" for all permissions.

### Run Application

```bash
# Development mode
python app.py

# Access at http://localhost:5000
```

## 🌐 Production Deployment (Azure Web Apps)

Deploy to Azure Web Apps for production use.

### Quick Deploy

```bash
# Login to Azure
az login

# Create resources
az group create --name defender-xdr-rg --location eastus

az appservice plan create \
  --name defender-xdr-plan \
  --resource-group defender-xdr-rg \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group defender-xdr-rg \
  --plan defender-xdr-plan \
  --name your-app-name \
  --runtime "PYTHON:3.11"

# Configure settings
az webapp config appsettings set \
  --resource-group defender-xdr-rg \
  --name your-app-name \
  --settings \
    TENANT_ID="your-tenant-id" \
    CLIENT_ID="your-client-id" \
    CLIENT_SECRET="your-client-secret" \
    FLASK_SECRET_KEY="$(openssl rand -hex 32)" \
    REDIRECT_URI="https://your-app-name.azurewebsites.net/auth/callback" \
    PORT="8000" \
    WEBSITES_PORT="8000"

# Deploy code
az webapp deployment source config-zip \
  --resource-group defender-xdr-rg \
  --name your-app-name \
  --src deploy.zip
```

**Update Azure AD redirect URI:**
Add `https://your-app-name.azurewebsites.net/auth/callback` to your app registration.

📘 **See [docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md) for complete deployment guide.**

## 📖 Documentation

- **[docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md)** - Azure Web Apps deployment guide
- **[docs/SETUP.md](docs/SETUP.md)** - Detailed setup instructions
- **[docs/API.md](docs/API.md)** - API endpoint documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - General deployment options (Docker, systemd, etc.)

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TENANT_ID` | Azure AD Tenant ID | Required |
| `CLIENT_ID` | Azure AD Application ID | Required |
| `CLIENT_SECRET` | Azure AD Client Secret | Required |
| `FLASK_SECRET_KEY` | Session encryption key | Required |
| `REDIRECT_URI` | OAuth callback URL | `http://localhost:5000/auth/callback` |
| `PORT` | Application port | `5000` |
| `FLASK_ENV` | Environment | `production` |

## 🛠️ Troubleshooting

### Authentication fails
- Verify Azure AD credentials in `.env`
- Check redirect URI matches exactly (including http/https)
- Ensure all API permissions granted with admin consent
- Verify client secret hasn't expired

### Stale data
```bash
# Clear cache
curl -X POST http://localhost:5000/api/cache/clear
```

### Missing policies
- Verify Intune administrator permissions
- Check API permissions include required scopes
- Ensure policies exist in your tenant

## 🔒 Security

- Never commit `.env` file to version control
- Use Azure Key Vault for production secrets
- Rotate client secrets regularly
- Enable HTTPS in production
- Review access logs periodically

## 📦 Requirements

See `requirements.txt`:
- Flask 3.0+
- Flask-Caching (performance)
- Flask-Session (server-side sessions)
- MSAL (Microsoft authentication)
- Gunicorn (production server)

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Credits

Built with:
- Microsoft Graph API
- Microsoft Defender XDR API
- Flask Framework
- MSAL Python

---

**Note**: Requires Microsoft 365 licenses with Defender XDR and Intune.
