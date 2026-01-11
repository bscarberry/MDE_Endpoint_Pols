# Defender XDR Endpoint Policy Manager

A comprehensive web-based application for managing and monitoring Microsoft Defender XDR endpoint policies using Microsoft Graph API and Defender XDR API.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Features

### Policy Management
- **View All Endpoint Policies**: Access all types of endpoint policies from a single interface
  - Device Compliance Policies
  - Device Configuration Policies
  - Endpoint Security Intents (Antivirus, Firewall, Attack Surface Reduction)
  - Configuration Profiles (Settings Catalog)
  - PowerShell Scripts
  - Device Health Monitoring Scripts

### Policy Details
- **Comprehensive Information**: View detailed settings, configurations, and metadata
- **Assignment Tracking**: See which groups and devices are assigned to each policy
- **Settings Visualization**: Review policy settings in an easy-to-read format

### Device Management
- **Managed Devices**: View all Intune-managed devices
- **Defender Machines**: Access machine inventory from Defender XDR
- **Compliance Status**: Monitor device compliance states

### Security Monitoring
- **Security Alerts**: View and monitor security alerts from Defender XDR
- **Advanced Hunting**: Run custom KQL queries for advanced threat hunting
- **Real-time Data**: Access up-to-date information from Microsoft APIs

### Modern UI
- **Terminal/Hacker Theme**: Professional terminal-style interface with JetBrains Mono font
- **Responsive Design**: Works on desktop and tablet devices
- **Intuitive Navigation**: Easy-to-use sidebar navigation with function-style buttons
- **Interactive Dashboard**: Visual stats and quick access to recent policies
- **Multi-Column Filtering**: Filter policies by category, type, platform, and assignments

## 🏭 Production Deployment

**Ready for production?** This application is production-ready with proper WSGI server configuration.

📘 **See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment instructions**, including:
- Production server setup (Gunicorn/Waitress)
- Cloud deployment guides (Heroku, Azure App Service, Docker)
- Security configuration and SSL/TLS setup
- Performance optimization and scaling
- Nginx reverse proxy configuration
- Environment variable management

**Quick Start for Production:**
```bash
# Linux/Mac
./start_production.sh

# Windows
start_production.bat
```

## 📋 Prerequisites

- Python 3.8 or higher
- Microsoft Azure AD Application Registration with appropriate permissions
- Access to Microsoft 365 tenant with Defender XDR and Intune

## 🔐 Required API Permissions

### Microsoft Graph API Permissions
Your Azure AD app registration needs the following **Application** permissions:

**Required:**
- `DeviceManagementConfiguration.Read.All` - Read device configurations
- `DeviceManagementManagedDevices.Read.All` - Read managed devices
- `DeviceManagementServiceConfig.Read.All` - Read service configuration
- `Group.Read.All` - Read groups (for policy assignments)

**Optional:**
- `DeviceManagementScripts.Read.All` - Read PowerShell scripts and health monitoring scripts (if you want to view scripts)

### Microsoft Defender API Permissions
**Required:**
- `AdvancedQuery.Read.All` - Run advanced hunting queries
- `Machine.Read.All` - Read machine information
- `Alert.Read.All` - Read security alerts

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/MDE_Endpoint_Pols.git
cd MDE_Endpoint_Pols
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your Azure AD application details:

```env
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
FLASK_SECRET_KEY=generate-a-random-secret-key
FLASK_ENV=development
PORT=5000
```

## 🚀 Usage

### Running the Application

```bash
python app.py
```

The application will start on `http://localhost:5000` (or the port you configured).

### Accessing the Web Interface

1. Open your web browser and navigate to `http://localhost:5000`
2. The dashboard will load automatically showing policy statistics
3. Use the sidebar to navigate between different sections:
   - **Dashboard**: Overview and statistics
   - **Endpoint Policies**: View all policies
   - **Managed Devices**: Intune-managed devices
   - **Defender Machines**: Defender XDR machine inventory
   - **Security Alerts**: Active security alerts
   - **Advanced Hunting**: Run KQL queries

### Search Functionality

Use the search bar at the top to quickly find policies by name or description. Press Enter to execute the search.

### Advanced Hunting Queries

Example KQL query to find devices with specific configurations:

```kql
DeviceInfo
| where OSPlatform == "Windows10"
| summarize by DeviceName, OSVersion
| limit 100
```

## 📁 Project Structure

```
MDE_Endpoint_Pols/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── modules/                   # Application modules
│   ├── __init__.py
│   ├── auth.py               # Azure AD authentication
│   ├── graph_client.py       # Microsoft Graph API client
│   ├── defender_client.py    # Defender XDR API client
│   └── policy_manager.py     # Policy management logic
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   └── index.html            # Dashboard page
├── static/                    # Static files
│   ├── css/
│   │   └── style.css         # Application styles
│   └── js/
│       └── app.js            # Client-side JavaScript
└── docs/                      # Documentation
    ├── API.md                # API documentation
    └── SETUP.md              # Setup guide
```

## 🔧 Configuration

### Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Configure:
   - Name: `Defender XDR Policy Manager`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: Not required for this application
5. After creation, note the **Application (client) ID** and **Directory (tenant) ID**
6. Create a client secret:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Add description and select expiration
   - Copy the secret **value** (not the ID)
7. Configure API permissions as listed in the Prerequisites section
8. Click **Grant admin consent** for your organization

### Environment Variables

All configuration is done through environment variables in the `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `TENANT_ID` | Azure AD Tenant ID | Yes |
| `CLIENT_ID` | Azure AD Application ID | Yes |
| `CLIENT_SECRET` | Azure AD Client Secret | Yes |
| `FLASK_SECRET_KEY` | Flask session secret key | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `FLASK_DEBUG` | Enable debug mode | No |
| `PORT` | Application port | No |

## 🔒 Security Considerations

- **Never commit** the `.env` file to version control
- Store credentials securely (consider Azure Key Vault for production)
- Use HTTPS in production environments
- Regularly rotate client secrets
- Follow principle of least privilege for API permissions
- Review and audit access logs regularly

## 🐛 Troubleshooting

### Authentication Errors

If you encounter authentication errors:

1. Verify your `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` are correct
2. Ensure API permissions are granted and admin consent is provided
3. Check that the client secret hasn't expired
4. Verify your Azure AD app has the required permissions

### API Request Failures

- Check your internet connection
- Verify the Microsoft services are operational
- Ensure your token hasn't expired (tokens are auto-refreshed)
- Review API rate limits

### Missing Policies

- Verify your account has access to view policies in Intune
- Check that policies exist in your tenant
- Ensure API permissions include read access

## 📚 Additional Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide (Heroku, Azure, Docker, cloud platforms)
- [API Documentation](docs/API.md) - Detailed API endpoint documentation
- [Setup Guide](docs/SETUP.md) - Step-by-step setup instructions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in the `docs/` folder
- Review Microsoft's API documentation:
  - [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
  - [Microsoft Defender XDR API](https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/api/)

## 🙏 Acknowledgments

- Microsoft Graph API
- Microsoft Defender XDR API
- Flask Framework
- Font Awesome Icons

---

**Note**: This application requires appropriate Microsoft 365 licenses and permissions. Ensure you have the necessary licenses before deployment.
