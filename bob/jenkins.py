"""
Jenkins Pipeline Trigger Module for Bob Orchestrator

This module provides a clean interface to trigger Jenkins pipelines
via OpenShift's native BuildConfig integration. It uses the same
service account authentication that Bob already has, eliminating
the need for separate Jenkins credentials.

Usage:
    from jenkins import trigger_jenkins_via_openshift
    
    result = trigger_jenkins_via_openshift(
        build_config_name="bob-automation-pipeline",
        namespace="production"
    )
"""

import urllib3
from kubernetes import client
from kubernetes.client.rest import ApiException

# Disable SSL warnings for internal cluster communication
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OpenShift internal API endpoint
OPENSHIFT_API_ENDPOINT = "https://kubernetes.default.svc"
TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
CA_CERT_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"


def get_service_account_token():
    """
    Read the service account token from the mounted secret.
    
    Returns:
        str: The service account token
    
    Raises:
        FileNotFoundError: If token file doesn't exist
    """
    try:
        with open(TOKEN_PATH, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Service account token not found at {TOKEN_PATH}. "
            "Ensure Bob is running in OpenShift with a service account."
        )


def configure_kubernetes_client():
    """
    Configure the Kubernetes client with OpenShift service account credentials.
    
    Returns:
        kubernetes.client.Configuration: Configured client
    """
    token = get_service_account_token()
    
    configuration = client.Configuration()
    configuration.host = OPENSHIFT_API_ENDPOINT
    configuration.api_key = {"authorization": f"Bearer {token}"}
    configuration.ssl_ca_cert = CA_CERT_PATH
    configuration.verify_ssl = True
    configuration.assert_hostname = False
    
    client.Configuration.set_default(configuration)
    return configuration


def trigger_jenkins_via_openshift(
    build_config_name="bob-automation-pipeline",
    namespace="production"
):
    """
    Trigger a Jenkins pipeline by creating a BuildRequest in OpenShift.
    
    This function uses OpenShift's native BuildConfig integration with Jenkins.
    When you create a BuildRequest for a JenkinsPipeline BuildConfig, OpenShift
    automatically triggers the corresponding Jenkins job.
    
    Args:
        build_config_name (str): Name of the BuildConfig (default: bob-automation-pipeline)
        namespace (str): OpenShift namespace (default: production)
    
    Returns:
        dict: Response containing:
            - success (bool): Whether the trigger was successful
            - message (str): Human-readable message
            - build_id (str): OpenShift Build ID (if successful)
            - error (str): Error details (if failed)
    
    Example:
        >>> result = trigger_jenkins_via_openshift()
        >>> if result['success']:
        ...     print(f"Pipeline started! Build ID: {result['build_id']}")
        ... else:
        ...     print(f"Failed: {result['error']}")
    """
    try:
        # Configure Kubernetes client
        configure_kubernetes_client()
        
        # Create CustomObjectsApi instance for BuildConfig operations
        custom_api = client.CustomObjectsApi()
        
        # BuildRequest payload
        build_request = {
            "apiVersion": "build.openshift.io/v1",
            "kind": "BuildRequest",
            "metadata": {
                "name": build_config_name
            }
        }
        
        print(f"[Jenkins] Triggering pipeline: {build_config_name} in namespace: {namespace}")
        
        # Get the service account token
        token = get_service_account_token()
        
        # Trigger the build via OpenShift API using requests library directly
        # This is more reliable than the Kubernetes Python client for custom resources
        import requests
        
        api_url = f"{OPENSHIFT_API_ENDPOINT}/apis/build.openshift.io/v1/namespaces/{namespace}/buildconfigs/{build_config_name}/instantiate"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(
            api_url,
            json=build_request,
            headers=headers,
            verify=CA_CERT_PATH,
            timeout=30
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Extract build information
        build_id = response_data.get("metadata", {}).get("name", "Unknown")
        build_number = response_data.get("status", {}).get("buildNumber", "N/A")
        
        success_message = (
            f"✓ Jenkins pipeline triggered successfully!\n"
            f"  Build Config: {build_config_name}\n"
            f"  Build ID: {build_id}\n"
            f"  Build Number: {build_number}\n"
            f"  Namespace: {namespace}"
        )
        
        print(f"[Jenkins] {success_message}")
        
        return {
            "success": True,
            "message": success_message,
            "build_id": build_id,
            "build_number": build_number,
            "namespace": namespace,
            "build_config": build_config_name
        }
        
    except ApiException as e:
        error_message = f"OpenShift API error: {e.reason} (Status: {e.status})"
        
        if e.status == 404:
            error_message = (
                f"BuildConfig '{build_config_name}' not found in namespace '{namespace}'. "
                f"Please apply the BuildConfig first: oc apply -f bob/k8s/buildconfig.yaml"
            )
        elif e.status == 401:
            error_message = (
                "Authentication failed. Ensure Bob's service account has proper RBAC permissions."
            )
        elif e.status == 403:
            error_message = (
                f"Permission denied. Service account needs 'edit' role in namespace '{namespace}'."
            )
        
        print(f"[Jenkins] ✗ {error_message}")
        
        return {
            "success": False,
            "message": error_message,
            "error": str(e),
            "status_code": e.status
        }
        
    except FileNotFoundError as e:
        error_message = str(e)
        print(f"[Jenkins] ✗ {error_message}")
        
        return {
            "success": False,
            "message": error_message,
            "error": "Service account token not found"
        }
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"[Jenkins] ✗ {error_message}")
        
        return {
            "success": False,
            "message": error_message,
            "error": str(e)
        }


def get_build_status(build_name, namespace="production"):
    """
    Get the status of a specific build.
    
    Args:
        build_name (str): Name of the Build resource
        namespace (str): OpenShift namespace
    
    Returns:
        dict: Build status information
    """
    try:
        configure_kubernetes_client()
        custom_api = client.CustomObjectsApi()
        
        build = custom_api.get_namespaced_custom_object(
            group="build.openshift.io",
            version="v1",
            namespace=namespace,
            plural="builds",
            name=build_name
        )
        
        status = build.get("status", {})
        phase = status.get("phase", "Unknown")
        
        return {
            "success": True,
            "build_name": build_name,
            "phase": phase,
            "status": status
        }
        
    except ApiException as e:
        return {
            "success": False,
            "error": f"Failed to get build status: {e.reason}"
        }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Jenkins Pipeline Trigger - Test Mode")
    print("=" * 60)
    
    # Test trigger
    result = trigger_jenkins_via_openshift()
    
    if result["success"]:
        print("\n✓ SUCCESS!")
        print(f"Build ID: {result['build_id']}")
        print(f"Message: {result['message']}")
    else:
        print("\n✗ FAILED!")
        print(f"Error: {result['message']}")
    
    print("=" * 60)

# Made with Bob
