from flask import Flask, request, jsonify
import logging
import os
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Import Jenkins pipeline trigger module
from jenkins import trigger_jenkins_via_openshift

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenShift Configuration
OPENSHIFT_API_URL = os.getenv("OPENSHIFT_API_URL", "https://kubernetes.default.svc")
OPENSHIFT_TOKEN_FILE = "/var/run/secrets/kubernetes.io/serviceaccount/token"
OPENSHIFT_TOKEN = os.getenv("OPENSHIFT_TOKEN")  # Fallback to env var
OPENSHIFT_NAMESPACE = os.getenv("OPENSHIFT_NAMESPACE", "production")
DEFAULT_ENV = os.getenv("DEFAULT_DEPLOY_ENV", "production")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Deployment manifests paths
DEPLOYMENT_MANIFEST = os.getenv("DEPLOYMENT_MANIFEST", "k8s/03-deployment-simple.yaml")
SERVICE_MANIFEST = os.getenv("SERVICE_MANIFEST", "k8s/04-service.yaml")
ROUTE_MANIFEST = os.getenv("ROUTE_MANIFEST", "k8s/05-route.yaml")


def get_openshift_token():
    """Get OpenShift token from service account or environment"""
    # Try to read from service account token file first
    if os.path.exists(OPENSHIFT_TOKEN_FILE):
        try:
            with open(OPENSHIFT_TOKEN_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read service account token: {e}")
    
    # Fallback to environment variable
    return OPENSHIFT_TOKEN


def get_openshift_headers(content_type="application/strategic-merge-patch+json"):
    """Build headers for OpenShift API requests"""
    token = get_openshift_token()
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": content_type
    }


def validate_configuration():
    """Check if required configuration is present"""
    missing_vars = []
    token = get_openshift_token()
    if not token:
        missing_vars.append("OPENSHIFT_TOKEN or ServiceAccount")
    if not OPENSHIFT_API_URL:
        missing_vars.append("OPENSHIFT_API_URL")
    return missing_vars


def parse_deployment_command(text):
    """Parse deployment command from text
    
    Supports:
    - /deploy <environment> - Trigger rollout restart
    - /pipeline [build_config_name] - Trigger Jenkins pipeline
    """
    normalized = " ".join((text or "").strip().lower().split())
    if not normalized:
        return None

    tokens = normalized.split()
    if not tokens:
        return None

    if tokens[0].startswith("/"):
        tokens[0] = tokens[0][1:]

    # Handle /deploy command
    if tokens[0] == "deploy":
        environment = tokens[1] if len(tokens) > 1 else DEFAULT_ENV
        return {
            "action": "deploy",
            "environment": environment,
            "raw_text": normalized,
        }
    
    # Handle /pipeline command
    if tokens[0] == "pipeline":
        build_config = tokens[1] if len(tokens) > 1 else "bob-automation-pipeline"
        namespace = tokens[2] if len(tokens) > 2 else "production"
        return {
            "action": "pipeline",
            "build_config": build_config,
            "namespace": namespace,
            "raw_text": normalized,
        }
    
    return None


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    missing_vars = validate_configuration()
    status = "healthy" if not missing_vars else "degraded"
    return jsonify(
        {
            "status": status,
            "service": "bob-orchestrator",
            "mode": "openshift-api",
            "missing_configuration": missing_vars,
        }
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for deployment commands"""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    command = parse_deployment_command(text)

    if not command:
        return (
            jsonify(
                {
                    "status": "ignored",
                    "message": "Supported commands:\n- /deploy <environment>\n- /pipeline [build_config_name] [namespace]",
                }
            ),
            400,
        )

    # Route to appropriate handler
    if command["action"] == "deploy":
        result, status_code = trigger_openshift_deployment(command["environment"])
    elif command["action"] == "pipeline":
        result, status_code = trigger_jenkins_pipeline(
            command["build_config"],
            command["namespace"]
        )
    else:
        result = {"status": "error", "message": "Unknown action"}
        status_code = 400
    
    return jsonify(result), status_code


def trigger_openshift_deployment(environment):
    """Trigger deployment using OpenShift API"""
    missing_vars = validate_configuration()
    if missing_vars:
        logger.error("Missing OpenShift configuration: %s", ", ".join(missing_vars))
        return (
            {
                "status": "error",
                "message": "Bob is missing OpenShift configuration",
                "missing_configuration": missing_vars,
            },
            500,
        )

    headers = get_openshift_headers()
    namespace = OPENSHIFT_NAMESPACE if environment == "production" else environment

    try:
        logger.info(
            "Triggering deployment to namespace '%s' via OpenShift API",
            namespace
        )

        # Step 1: Restart the deployment by patching it
        deployment_name = "python-app"
        patch_url = f"{OPENSHIFT_API_URL}/apis/apps/v1/namespaces/{namespace}/deployments/{deployment_name}"
        
        # Patch to trigger rollout restart
        patch_data = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip()
                        }
                    }
                }
            }
        }

        logger.info(f"Patching deployment at: {patch_url}")
        headers_patch = get_openshift_headers("application/strategic-merge-patch+json")
        response = requests.patch(
            patch_url,
            json=patch_data,
            headers=headers_patch,
            verify=False,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code in [200, 201]:
            logger.info("Deployment rollout triggered successfully")
            
            # Step 2: Get rollout status
            status_url = f"{OPENSHIFT_API_URL}/apis/apps/v1/namespaces/{namespace}/deployments/{deployment_name}/status"
            status_response = requests.get(
                status_url,
                headers=headers,
                verify=False,
                timeout=REQUEST_TIMEOUT,
            )
            
            deployment_status = "unknown"
            if status_response.status_code == 200:
                status_data = status_response.json()
                replicas = status_data.get("status", {}).get("replicas", 0)
                ready_replicas = status_data.get("status", {}).get("readyReplicas", 0)
                deployment_status = f"{ready_replicas}/{replicas} ready"

            return (
                {
                    "status": "success",
                    "message": f"Deployment rollout triggered for {deployment_name} in {namespace}",
                    "deployment": deployment_name,
                    "namespace": namespace,
                    "environment": environment,
                    "deployment_status": deployment_status,
                    "method": "openshift-api",
                },
                200,
            )
        else:
            logger.error(f"Failed to trigger deployment: {response.status_code} - {response.text}")
            return (
                {
                    "status": "error",
                    "message": f"OpenShift API returned {response.status_code}",
                    "deployment": deployment_name,
                    "namespace": namespace,
                    "details": response.text[:500],
                },
                response.status_code,
            )

    except requests.RequestException as exc:
        logger.exception("Error triggering OpenShift deployment")
        return (
            {
                "status": "error",
                "message": "Failed to contact OpenShift API",
                "details": str(exc),
            },
            502,
        )


def trigger_jenkins_pipeline(build_config_name, namespace):
    """Trigger Jenkins pipeline via OpenShift BuildConfig
    
    Args:
        build_config_name (str): Name of the BuildConfig
        namespace (str): OpenShift namespace
    
    Returns:
        tuple: (result_dict, status_code)
    """
    logger.info(
        f"Triggering Jenkins pipeline: {build_config_name} in namespace: {namespace}"
    )
    
    try:
        # Call the jenkins.py module
        result = trigger_jenkins_via_openshift(
            build_config_name=build_config_name,
            namespace=namespace
        )
        
        if result["success"]:
            return (
                {
                    "status": "success",
                    "message": result["message"],
                    "build_id": result.get("build_id"),
                    "build_number": result.get("build_number"),
                    "build_config": build_config_name,
                    "namespace": namespace,
                    "method": "jenkins-pipeline-via-openshift",
                },
                200,
            )
        else:
            return (
                {
                    "status": "error",
                    "message": result["message"],
                    "error": result.get("error"),
                    "build_config": build_config_name,
                    "namespace": namespace,
                },
                result.get("status_code", 500),
            )
    
    except Exception as e:
        logger.exception("Error triggering Jenkins pipeline")
        return (
            {
                "status": "error",
                "message": f"Failed to trigger Jenkins pipeline: {str(e)}",
                "build_config": build_config_name,
                "namespace": namespace,
            },
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# Made with Bob - OpenShift API Integration + Jenkins Pipeline Support
