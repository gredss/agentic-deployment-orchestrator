"""
Example Flask Application
This is a sample app.py to demonstrate the Bob Template Generator

Copy this to app.py in your project directory and customize it!
"""

from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# Get configuration from environment variables
APP_NAME = os.getenv('APP_NAME', 'example-app')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'message': f'Welcome to {APP_NAME}!',
        'environment': ENVIRONMENT,
        'status': 'running'
    })


@app.route('/health')
def health():
    """Health check endpoint - REQUIRED for OpenShift deployment"""
    return jsonify({
        'status': 'healthy',
        'app': APP_NAME,
        'environment': ENVIRONMENT
    })


@app.route('/api/data', methods=['GET'])
def get_data():
    """Example API endpoint"""
    return jsonify({
        'data': [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'},
            {'id': 3, 'name': 'Item 3'}
        ]
    })


@app.route('/api/echo', methods=['POST'])
def echo():
    """Echo endpoint - returns what you send"""
    data = request.get_json()
    return jsonify({
        'received': data,
        'message': 'Echo successful'
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'status': 500
    }), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('APP_PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=(ENVIRONMENT == 'development')
    )

# Made with Bob
