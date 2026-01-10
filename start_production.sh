#!/bin/bash
# Production startup script for Linux/Mac using Gunicorn

echo "Starting Defender XDR Endpoint Policy Manager in PRODUCTION mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create a .env file with your Azure AD credentials"
    exit 1
fi

# Set production environment
export FLASK_ENV=production

# Start Gunicorn with optimal settings
gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --threads 2 \
    --worker-class gthread \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:app
