from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

APP_NAME = os.getenv('APP_NAME', 'test-app')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'unknown')
HOSTNAME = socket.gethostname()

@app.route('/')
def home():
    return jsonify({
        'message': f'Hello from {APP_NAME}!',
        'app': APP_NAME,
        'environment': ENVIRONMENT,
        'hostname': HOSTNAME,
        'status': 'running'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'app': APP_NAME,
        'environment': ENVIRONMENT
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Simple Test Application for Bob Orchestrator

# Made with Bob
