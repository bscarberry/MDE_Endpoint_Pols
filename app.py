"""
Defender XDR Endpoint Policy Manager - Web Application
"""
from flask import Flask, render_template, request, jsonify
from config import Config
from modules.policy_manager import PolicyManager
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize Policy Manager
policy_manager = None


def get_policy_manager():
    """Get or create policy manager instance"""
    global policy_manager
    if policy_manager is None:
        policy_manager = PolicyManager()
    return policy_manager


@app.route('/')
def index():
    """Home page - Dashboard"""
    return render_template('index.html')


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
