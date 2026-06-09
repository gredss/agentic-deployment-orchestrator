from flask import Flask, request, jsonify
import logging
import os
import yaml
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenShift Configuration
OPENSHIFT_API_URL = os.getenv("OPENSHIFT_API_URL", "https://kubernetes.default.svc")
OPENSHIFT_TOKEN_FILE = "/var/run/secrets/kubernetes.io/serviceaccount/token"
OPENSHIFT_TOKEN = os.getenv("OPENSHIFT_TOKEN")
DEFAULT_NAMESPACE = os.getenv("DEFAULT_NAMESPACE", "production")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "/app/templates")

# Default deployment parameters
DEFAULT_REPLICAS = "2"
DEFAULT_PORT = "5000"


def get_openshift_token():
    """Get OpenShift token from service account or environment"""
    if os.path.exists(OPENSHIFT_TOKEN_FILE):
        try:
            with open(OPENSHIFT_TOKEN_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read service account token: {e}")
    return OPENSHIFT_TOKEN


def get_openshift_headers(content_type="application/json"):
    """Build headers for OpenShift API requests"""
    token = get_openshift_token()
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": content_type
    }


def load_template(template_name):
    """Load a YAML template from the templates directory"""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.yaml")
    try:
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Template not found: {template_path}")
        return None


def render_template(template_content, params):
    """Render template with parameters"""
    try:
        return template_content.format(**params)
    except KeyError as e:
        logger.error(f"Missing parameter in template: {e}")
        return None


def apply_manifest(manifest_yaml, resource_type):
    """Apply a Kubernetes manifest via OpenShift API"""
    try:
        manifest = yaml.safe_load(manifest_yaml)
        headers = get_openshift_headers()
        
        if not headers:
            return False, "No authentication token available"
        
        namespace = manifest['metadata']['namespace']
        name = manifest['metadata']['name']
        
        # Determine API endpoint based on resource type
        if resource_type == "deployment":
            api_path = f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}"
            create_path = f"/apis/apps/v1/namespaces/{namespace}/deployments"
        elif resource_type == "service":
            api_path = f"/api/v1/namespaces/{namespace}/services/{name}"
            create_path = f"/api/v1/namespaces/{namespace}/services"
        elif resource_type == "route":
            api_path = f"/apis/route.openshift.io/v1/namespaces/{namespace}/routes/{name}"
            create_path = f"/apis/route.openshift.io/v1/namespaces/{namespace}/routes"
        else:
            return False, f"Unknown resource type: {resource_type}"
        
        # Try to get existing resource
        get_url = f"{OPENSHIFT_API_URL}{api_path}"
        response = requests.get(get_url, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            # Resource exists, update it
            logger.info(f"Updating existing {resource_type}: {name}")
            patch_headers = get_openshift_headers("application/strategic-merge-patch+json")
            response = requests.patch(
                get_url,
                json=manifest,
                headers=patch_headers,
                verify=False,
                timeout=REQUEST_TIMEOUT
            )
        elif response.status_code == 404:
            # Resource doesn't exist, create it
            logger.info(f"Creating new {resource_type}: {name}")
            create_url = f"{OPENSHIFT_API_URL}{create_path}"
            response = requests.post(
                create_url,
                json=manifest,
                headers=headers,
                verify=False,
                timeout=REQUEST_TIMEOUT
            )
        else:
            return False, f"Failed to check resource: {response.status_code} - {response.text}"
        
        if response.status_code in [200, 201]:
            return True, f"{resource_type.capitalize()} {name} applied successfully"
        else:
            return False, f"Failed to apply {resource_type}: {response.status_code} - {response.text[:200]}"
            
    except Exception as e:
        logger.exception(f"Error applying manifest")
        return False, str(e)


def parse_deployment_command(text):
    """Parse deployment command: /deploy <namespace> <app-name> <image> [replicas] [port]"""
    normalized = " ".join((text or "").strip().lower().split())
    if not normalized:
        return None
    
    tokens = normalized.split()
    if not tokens:
        return None
    
    if tokens[0].startswith("/"):
        tokens[0] = tokens[0][1:]
    
    if tokens[0] != "deploy":
        return None
    
    # Parse parameters
    namespace = tokens[1] if len(tokens) > 1 else DEFAULT_NAMESPACE
    app_name = tokens[2] if len(tokens) > 2 else None
    image = tokens[3] if len(tokens) > 3 else None
    replicas = tokens[4] if len(tokens) > 4 else DEFAULT_REPLICAS
    port = tokens[5] if len(tokens) > 5 else DEFAULT_PORT
    
    if not app_name or not image:
        return None
    
    return {
        "action": "deploy",
        "namespace": namespace,
        "app_name": app_name,
        "image": image,
        "replicas": replicas,
        "port": port,
        "raw_text": normalized,
    }


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    token = get_openshift_token()
    status = "healthy" if token else "degraded"
    return jsonify({
        "status": status,
        "service": "bob-orchestrator-v2",
        "mode": "declarative-templates",
        "templates_dir": TEMPLATES_DIR,
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for deployment commands"""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    command = parse_deployment_command(text)
    
    if not command:
        return jsonify({
            "status": "ignored",
            "message": "Supported format: /deploy <namespace> <app-name> <image> [replicas] [port]",
            "example": "/deploy production my-app python:3.9-slim 2 5000"
        }), 400
    
    result, status_code = deploy_application(command)
    return jsonify(result), status_code


def deploy_application(params):
    """Deploy application using declarative templates"""
    try:
        logger.info(f"Deploying application: {params['app_name']} to {params['namespace']}")
        
        # Template parameters
        template_params = {
            "APP_NAME": params["app_name"],
            "NAMESPACE": params["namespace"],
            "IMAGE": params["image"],
            "REPLICAS": params["replicas"],
            "PORT": params["port"],
        }
        
        results = []
        
        # Apply Deployment
        deployment_template = load_template("deployment")
        if deployment_template:
            deployment_yaml = render_template(deployment_template, template_params)
            if deployment_yaml:
                success, message = apply_manifest(deployment_yaml, "deployment")
                results.append({"resource": "deployment", "success": success, "message": message})
        
        # Apply Service
        service_template = load_template("service")
        if service_template:
            service_yaml = render_template(service_template, template_params)
            if service_yaml:
                success, message = apply_manifest(service_yaml, "service")
                results.append({"resource": "service", "success": success, "message": message})
        
        # Apply Route
        route_template = load_template("route")
        if route_template:
            route_yaml = render_template(route_template, template_params)
            if route_yaml:
                success, message = apply_manifest(route_yaml, "route")
                results.append({"resource": "route", "success": success, "message": message})
        
        # Check if all succeeded
        all_success = all(r["success"] for r in results)
        
        if all_success:
            return {
                "status": "success",
                "message": f"Application {params['app_name']} deployed successfully",
                "app_name": params["app_name"],
                "namespace": params["namespace"],
                "image": params["image"],
                "method": "declarative-templates",
                "results": results
            }, 200
        else:
            return {
                "status": "partial",
                "message": f"Some resources failed to deploy",
                "app_name": params["app_name"],
                "namespace": params["namespace"],
                "results": results
            }, 207
            
    except Exception as e:
        logger.exception("Error deploying application")
        return {
            "status": "error",
            "message": "Failed to deploy application",
            "details": str(e)
        }, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# Bob Orchestrator V2 - Declarative Template Engine
# Industry Best Practice Implementation

# Made with Bob
