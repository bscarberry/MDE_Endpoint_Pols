"""
WSGI entry point for production deployment
"""
import os
from app import app

# Production configuration
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Security headers are now set in app.py via @app.after_request
# so they apply regardless of entry point (VULN-12 fix)

if __name__ == '__main__':
    # This won't be called in production, but useful for testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
