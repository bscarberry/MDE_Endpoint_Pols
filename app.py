"""
Defender XDR Endpoint Policy Manager - Web Application
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_caching import Cache
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from modules.policy_manager import PolicyManager
from modules.user_auth import UserAuthManager
from functools import wraps
import os
import secrets

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SESSION_TYPE'] = Config.SESSION_TYPE
app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME

# Trust proxy headers from Azure Web Apps (for HTTPS detection)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure in-memory caching
app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 600  # 10 minutes default
cache = Cache(app)

# Initialize server-side session
Session(app)

# Initialize managers
policy_manager = None


def get_policy_manager():
    """Get or create policy manager instance"""
    global policy_manager
    if policy_manager is None:
        policy_manager = PolicyManager()
    return policy_manager


def get_user_auth_manager():
    """Get user auth manager with dynamic redirect URI based on request"""
    # Build redirect URI dynamically from the request
    redirect_uri = url_for('auth_callback', _external=True)
    return UserAuthManager(redirect_uri=redirect_uri)


def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_auth = get_user_auth_manager()
        if not user_auth.is_authenticated():
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    """Home page - Dashboard"""
    user_auth = get_user_auth_manager()
    user = user_auth.get_user_from_session()
    return render_template('index.html', user=user)


@app.route('/login')
def login():
    """Initiate user login"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(16)
    session['state'] = state
    session['next'] = request.args.get('next', url_for('index'))

    # Get authorization URL with dynamic redirect URI
    user_auth = get_user_auth_manager()
    auth_url = user_auth.get_login_url(state=state)
    return redirect(auth_url)


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Azure AD"""
    # Verify state to prevent CSRF
    if request.args.get('state') != session.get('state'):
        return render_template('error.html', error='Invalid state parameter'), 400

    # Check for errors in the callback
    if 'error' in request.args:
        return render_template('error.html',
                             error=request.args.get('error'),
                             error_description=request.args.get('error_description')), 400

    # Exchange authorization code for tokens
    code = request.args.get('code')
    if not code:
        return render_template('error.html', error='Missing authorization code'), 400

    try:
        user_auth = get_user_auth_manager()
        result = user_auth.get_token_from_code(code)

        if 'error' in result:
            return render_template('error.html',
                                 error=result.get('error'),
                                 error_description=result.get('error_description')), 400

        # Store user information in session
        session['user'] = {
            'name': result.get('id_token_claims', {}).get('name'),
            'username': result.get('id_token_claims', {}).get('preferred_username'),
            'oid': result.get('id_token_claims', {}).get('oid')
        }

        # Redirect to original destination or home
        next_url = session.pop('next', url_for('index'))
        return redirect(next_url)

    except Exception as e:
        return render_template('error.html',
                             error='Authentication failed',
                             error_description=str(e)), 500


@app.route('/logout')
def logout():
    """Log out the current user"""
    user_auth = get_user_auth_manager()
    user_auth.logout()
    logout_url = user_auth.get_logout_url(
        post_logout_redirect_uri=url_for('login', _external=True)
    )
    return redirect(logout_url)


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        Config.validate()
        return jsonify({
            'status': 'healthy',
            'configured': True
        })
    except ValueError as e:
        return jsonify({
            'status': 'unhealthy',
            'configured': False,
            'error': str(e)
        }), 500


@app.route('/api/policies')
@login_required
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_policies():
    """Get all endpoint policies"""
    try:
        pm = get_policy_manager()
        result = pm.get_all_policies()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/policies/<policy_type>/<policy_id>')
@login_required
def get_policy_details(policy_type, policy_id):
    """Get details for a specific policy"""
    try:
        pm = get_policy_manager()
        result = pm.get_policy_details(policy_type, policy_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search')
@login_required
def search_policies():
    """Search policies by term"""
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({
            'success': False,
            'error': 'Search term required'
        }), 400

    try:
        pm = get_policy_manager()
        result = pm.search_policies(search_term)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/defender/machines')
@login_required
def get_machines():
    """Get all machines from Defender XDR"""
    try:
        pm = get_policy_manager()
        result = pm.get_defender_machines()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/defender/alerts')
@login_required
def get_alerts():
    """Get alerts from Defender XDR"""
    filters = request.args.get('filter')
    try:
        pm = get_policy_manager()
        result = pm.get_defender_alerts(filters)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/defender/query', methods=['POST'])
@login_required
def run_query():
    """Run advanced hunting query"""
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({
            'success': False,
            'error': 'Query parameter required'
        }), 400

    try:
        pm = get_policy_manager()
        result = pm.run_advanced_query(data['query'])
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/devices')
@login_required
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_devices():
    """Get all managed devices"""
    try:
        pm = get_policy_manager()
        result = pm.get_managed_devices()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/devices/<device_id>')
@login_required
def get_device_details(device_id):
    """Get device details with assigned policies"""
    try:
        pm = get_policy_manager()
        result = pm.get_device_with_policies(device_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached data"""
    try:
        cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    try:
        # Validate configuration before starting
        Config.validate()
        print("✓ Configuration validated successfully")
        print(f"Starting Defender XDR Endpoint Policy Manager on port {Config.PORT}...")
        app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        exit(1)
