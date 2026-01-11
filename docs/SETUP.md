# Setup Guide

This comprehensive guide will walk you through setting up the Defender XDR Endpoint Policy Manager from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure AD Configuration](#azure-ad-configuration)
3. [Application Setup](#application-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Verification](#verification)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.8 or higher**
  - Download from [python.org](https://www.python.org/downloads/)
  - Verify installation: `python --version`

- **pip** (Python package installer)
  - Usually included with Python
  - Verify installation: `pip --version`

- **Git** (optional, for cloning repository)
  - Download from [git-scm.com](https://git-scm.com/)

### Required Access

- **Azure AD Global Administrator** or **Application Administrator** role (for app registration)
- **Intune Administrator** role (to view policies)
- **Security Administrator** role (to access Defender data)
- Active **Microsoft 365** subscription with:
  - Microsoft Intune
  - Microsoft Defender for Endpoint

## Azure AD Configuration

### Step 1: Create Azure AD App Registration

1. Sign in to the [Azure Portal](https://portal.azure.com)

2. Navigate to **Azure Active Directory**

3. Click **App registrations** in the left menu

4. Click **+ New registration**

5. Configure the application:
   - **Name**: `Defender XDR Policy Manager`
   - **Supported account types**: Select "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank
   - Click **Register**

6. **Record the following values** (you'll need these later):
   - **Application (client) ID**
   - **Directory (tenant) ID**

### Step 2: Create Client Secret

1. In your app registration, click **Certificates & secrets** in the left menu

2. Under **Client secrets**, click **+ New client secret**

3. Configure the secret:
   - **Description**: `Policy Manager Secret`
   - **Expires**: Select appropriate expiration (24 months recommended)
   - Click **Add**

4. **IMPORTANT**: Copy the secret **Value** immediately (you cannot retrieve it later)
   - Do NOT copy the "Secret ID"
   - Copy the value shown in the "Value" column

### Step 3: Configure API Permissions

#### Microsoft Graph Permissions

1. Click **API permissions** in the left menu

2. Click **+ Add a permission**

3. Select **Microsoft Graph**

4. Select **Application permissions**

5. Add the following permissions:
   - `DeviceManagementConfiguration.Read.All`
   - `DeviceManagementManagedDevices.Read.All`
   - `DeviceManagementServiceConfig.Read.All`
   - `Group.Read.All`

6. Click **Add permissions**

#### Microsoft Defender Permissions

1. Click **+ Add a permission** again

2. Select **APIs my organization uses**

3. Search for and select **WindowsDefenderATP** (or "Microsoft Defender for Endpoint")

4. Select **Application permissions**

5. Add the following permissions:
   - `AdvancedQuery.Read.All`
   - `Machine.Read.All`
   - `Alert.Read.All`

6. Click **Add permissions**

### Step 4: Grant Admin Consent

1. Still in the **API permissions** page

2. Click **Grant admin consent for [Your Organization]**

3. Click **Yes** to confirm

4. Verify all permissions show a green checkmark under "Status"

**Your Azure AD configuration is now complete!**

## Application Setup

### Step 1: Download the Application

#### Option A: Clone from Git
```bash
git clone https://github.com/yourusername/MDE_Endpoint_Pols.git
cd MDE_Endpoint_Pols
```

#### Option B: Download ZIP
1. Download the repository as ZIP
2. Extract to your desired location
3. Open terminal/command prompt in that directory

### Step 2: Create Virtual Environment

Creating a virtual environment isolates the application dependencies.

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

### Step 3: Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- Flask-Caching (in-memory caching for performance)
- MSAL (Microsoft authentication)
- Requests (HTTP library)
- python-dotenv (environment variables)
- Gunicorn & Waitress (production WSGI servers)

## Configuration

### Step 1: Create Environment File

1. Copy the example environment file:

   **Windows:**
   ```bash
   copy .env.example .env
   ```

   **macOS/Linux:**
   ```bash
   cp .env.example .env
   ```

### Step 2: Configure Environment Variables

Open the `.env` file in a text editor and configure the following:

```env
# Azure AD Application Configuration
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here

# Application Configuration
FLASK_SECRET_KEY=your-random-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
```

#### Required Variables:

- **TENANT_ID**: Your Azure AD Directory (tenant) ID from Step 1
- **CLIENT_ID**: Your Application (client) ID from Step 1
- **CLIENT_SECRET**: The secret value from Step 2

#### Generate Flask Secret Key:

Generate a secure random key using Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your `FLASK_SECRET_KEY`.

### Step 3: Verify Configuration

The application will validate your configuration on startup. You can verify it's correct:

```bash
python -c "from config import Config; Config.validate(); print('Configuration is valid!')"
```

If successful, you'll see: `Configuration is valid!`

## Running the Application

### Development Mode

1. Ensure your virtual environment is activated

2. Run the application:
   ```bash
   python app.py
   ```

3. You should see output similar to:
   ```
   ✓ Configuration validated successfully
   Starting Defender XDR Endpoint Policy Manager on port 5000...
   * Running on http://0.0.0.0:5000
   ```

4. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

### First-Time Access

When you first access the application:

1. The dashboard will load
2. Policy statistics will appear (may take 10-30 seconds on first load)
3. Recent policies will be displayed
4. Subsequent page loads will be much faster due to caching

**Note on Performance:**
- **First load**: Takes longer as data is fetched from Microsoft APIs and cached
- **Subsequent loads**: Near-instant (<1 second) as data is served from cache
- **Cache duration**: 10 minutes for policies, 5 minutes for devices
- **Manual refresh**: Use `POST /api/cache/clear` to force fresh data

If you see an error, check the [Troubleshooting](#troubleshooting) section.

## Verification

### Test 1: Health Check

Navigate to: `http://localhost:5000/api/health`

Expected response:
```json
{
    "status": "healthy",
    "configured": true
}
```

### Test 2: View Policies

1. Click **Endpoint Policies** in the sidebar
2. Policies should load and display
3. Click on a policy to view details

### Test 3: Search

1. Use the search bar at the top
2. Type a policy name or keyword
3. Press Enter
4. Results should appear

### Test 4: Advanced Hunting

1. Click **Advanced Hunting** in the sidebar
2. Enter a simple query:
   ```kql
   DeviceInfo
   | limit 5
   ```
3. Click **Run Query**
4. Results should appear in a table

## Production Deployment

### Security Enhancements

1. **Use HTTPS**: Configure SSL/TLS certificates
2. **Set environment to production**:
   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```
3. **Secure the .env file**: Set appropriate file permissions
   ```bash
   chmod 600 .env  # Linux/Mac only
   ```
4. **Use a secrets manager**: Consider Azure Key Vault for credentials

### Using Gunicorn (Linux/Mac)

1. Install Gunicorn (already in requirements.txt):
   ```bash
   pip install gunicorn
   ```

2. Run with Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

   Where:
   - `-w 4` = 4 worker processes
   - `-b 0.0.0.0:5000` = bind to all interfaces on port 5000

### Using Nginx (Reverse Proxy)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t defender-policy-manager .
docker run -p 5000:5000 --env-file .env defender-policy-manager
```

## Troubleshooting

### Issue: "Missing required environment variables"

**Solution:**
1. Verify `.env` file exists in the project root
2. Check that `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` are set
3. Ensure no extra spaces around the `=` sign
4. Verify the file is named exactly `.env` (not `.env.txt`)

### Issue: "Authentication failed"

**Possible causes and solutions:**

1. **Incorrect credentials**
   - Double-check your `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET`
   - Ensure you copied the secret VALUE, not the ID

2. **Expired client secret**
   - Create a new client secret in Azure Portal
   - Update `.env` file with new secret

3. **Missing admin consent**
   - Go to Azure Portal > App registration > API permissions
   - Click "Grant admin consent"

### Issue: "API request failed: 403"

**Solution:**
- Your app doesn't have the required permissions
- Review the permissions in Azure Portal
- Ensure admin consent has been granted
- Wait a few minutes after granting consent for it to propagate

### Issue: "No policies found"

**Possible causes:**

1. **No policies in tenant**
   - Verify you have policies in Intune
   - Log in to [Endpoint Manager](https://endpoint.microsoft.com)

2. **Insufficient permissions**
   - Ensure your account has access to view policies
   - Check API permissions are correctly configured

### Issue: Port 5000 already in use

**Solution:**

Change the port in `.env`:
```env
PORT=8080
```

Or specify when running:
```bash
export PORT=8080  # Linux/Mac
set PORT=8080     # Windows
python app.py
```

### Issue: Advanced Hunting queries fail

**Possible causes:**

1. **Invalid KQL syntax**
   - Verify your query syntax
   - Test in Microsoft 365 Defender portal first

2. **Missing Defender license**
   - Ensure you have Defender for Endpoint licenses
   - Verify Defender is properly configured

### Issue: Seeing stale data or changes not appearing

**Solution:**

The application caches data for performance. If you need to see fresh data immediately:

1. **Manual cache clear**:
   ```bash
   curl -X POST http://localhost:5000/api/cache/clear
   ```

2. **Wait for automatic expiry**:
   - Policy data expires after 10 minutes
   - Device data expires after 5 minutes

3. **Browser console**:
   ```javascript
   fetch('/api/cache/clear', { method: 'POST' }).then(r => r.json()).then(console.log)
   ```

### Getting Help

If you encounter issues not covered here:

1. Check the application logs in the terminal
2. Review the [API Documentation](API.md)
3. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Your environment (OS, Python version)

## Next Steps

After successful setup:

1. **Explore the features**: Try all navigation items
2. **Customize**: Modify the theme or add features
3. **Automate**: Use the API endpoints for automation
4. **Monitor**: Set up logging and monitoring
5. **Secure**: Implement production security best practices

## Additional Resources

- [Main README](../README.md)
- [API Documentation](API.md)
- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/)
- [Microsoft Defender API Documentation](https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/api/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)

---

**Congratulations! Your Defender XDR Endpoint Policy Manager is now set up and ready to use!**
