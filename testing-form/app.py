from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Hello from Bob Test App!",
        "status": "running",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "bob-test-app"
    }), 200

@app.route('/api/info')
def info():
    return jsonify({
        "app": "Bob Test Application",
        "environment": os.environ.get('ENVIRONMENT', 'development'),
        "port": os.environ.get('PORT', '5000')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# Made with Bob
