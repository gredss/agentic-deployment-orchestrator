from flask import Flask, jsonify
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration from environment variables
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

@app.route("/")
def home():
    """
    Home endpoint - returns deployment success message
    """
    logger.info("Home endpoint accessed")
    return jsonify({
        "message": "Deployment successful",
        "version": APP_VERSION,
        "environment": ENVIRONMENT
    })

@app.route("/health")
def health():
    """
    Health check endpoint for Kubernetes liveness/readiness probes
    Returns 200 OK if application is healthy
    """
    logger.info("Health check endpoint accessed")
    return jsonify({
        "status": "healthy",
        "version": APP_VERSION
    }), 200

@app.route("/ready")
def ready():
    """
    Readiness probe endpoint
    Returns 200 OK when application is ready to serve traffic
    """
    logger.info("Readiness check endpoint accessed")
    return jsonify({
        "status": "ready",
        "version": APP_VERSION
    }), 200

@app.route("/info")
def info():
    """
    Application information endpoint
    Returns application metadata and environment details
    """
    logger.info("Info endpoint accessed")
    return jsonify({
        "application": "Python Flask App",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "python_version": os.sys.version,
        "endpoints": {
            "home": "/",
            "health": "/health",
            "ready": "/ready",
            "info": "/info"
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == "__main__":
    logger.info(f"Starting Flask application v{APP_VERSION} in {ENVIRONMENT} environment")
    # Run on all interfaces, port 8080
    app.run(host="0.0.0.0", port=8080, debug=False)