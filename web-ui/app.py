#!/usr/bin/env python3
"""
Bob Web UI - Flask Backend Server
Provides web interface for automated OpenShift deployments
"""

import os
import ast
import json
import uuid
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import requests
from github import Github
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = '/tmp/bob-uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory deployment tracking (use Redis in production)
deployments = {}


class DeploymentGenerator:
    """Handles template generation and deployment automation"""
    
    def __init__(self, config, app_file_path):
        self.config = config
        self.app_file_path = app_file_path
        self.deployment_id = str(uuid.uuid4())[:8]
        self.templates_dir = Path(__file__).parent / 'deployment-templates'
        
    def analyze_dependencies(self):
        """Analyze Python file to detect dependencies"""
        logger.info(f"Analyzing dependencies for {self.app_file_path}")
        
        with open(self.app_file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        # Map common imports to pip packages
        package_mapping = {
            'flask': 'Flask',
            'requests': 'requests',
            'sqlalchemy': 'SQLAlchemy',
            'psycopg2': 'psycopg2-binary',
            'pymongo': 'pymongo',
            'redis': 'redis',
            'celery': 'celery',
            'jwt': 'PyJWT',
            'yaml': 'PyYAML',
            'dotenv': 'python-dotenv',
        }
        
        packages = []
        for imp in imports:
            if imp in package_mapping:
                packages.append(package_mapping[imp])
        
        logger.info(f"Detected packages: {packages}")
        return packages
    
    def render_template(self, template_name, **kwargs):
        """Render a template file with provided variables"""
        template_path = self.templates_dir / template_name
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace all {{VARIABLE}} with actual values
        for key, value in kwargs.items():
            content = content.replace(f'{{{{{key}}}}}', str(value))
        
        return content
    
    def generate_dockerfile(self, dependencies):
        """Generate Dockerfile"""
        requirements = '\n'.join(dependencies)
        
        return self.render_template(
            'Dockerfile.template',
            PYTHON_VERSION=self.config['python_version'],
            APP_PORT=self.config['app_port'],
            HEALTH_CHECK_PATH=self.config['health_check_path'],
            REQUIREMENTS=requirements
        )
    
    def generate_jenkinsfile(self):
        """Generate Jenkinsfile"""
        return self.render_template(
            'Jenkinsfile.template',
            APP_NAME=self.config['app_name'],
            OPENSHIFT_NAMESPACE=self.config['openshift_namespace'],
            HEALTH_CHECK_PATH=self.config['health_check_path']
        )
    
    def generate_buildconfig(self):
        """Generate BuildConfig YAML"""
        return self.render_template(
            'buildconfig.yaml.template',
            APP_NAME=self.config['app_name'],
            GITHUB_REPO=self.config['github_repo'],
            GITHUB_BRANCH=self.config['github_branch'],
            OPENSHIFT_NAMESPACE=self.config['openshift_namespace'],
            DOCKER_USERNAME=self.config['docker_username']
        )
    
    def generate_deployment(self):
        """Generate Deployment YAML"""
        return self.render_template(
            'deployment.yaml.template',
            APP_NAME=self.config['app_name'],
            REPLICAS=self.config['replicas'],
            APP_PORT=self.config['app_port'],
            HEALTH_CHECK_PATH=self.config['health_check_path'],
            OPENSHIFT_NAMESPACE=self.config['openshift_namespace'],
            DOCKER_USERNAME=self.config['docker_username']
        )
    
    def generate_service(self):
        """Generate Service YAML"""
        return self.render_template(
            'service.yaml.template',
            APP_NAME=self.config['app_name'],
            APP_PORT=self.config['app_port'],
            OPENSHIFT_NAMESPACE=self.config['openshift_namespace']
        )
    
    def generate_route(self):
        """Generate Route YAML"""
        return self.render_template(
            'route.yaml.template',
            APP_NAME=self.config['app_name'],
            OPENSHIFT_CLUSTER=self.config['openshift_cluster'],
            OPENSHIFT_NAMESPACE=self.config['openshift_namespace']
        )
    
    def generate_all_files(self):
        """Generate all deployment files"""
        logger.info("Generating all deployment files")
        
        # Analyze dependencies
        dependencies = self.analyze_dependencies()
        
        # Generate all files
        files = {
            'app.py': open(self.app_file_path, 'r').read(),
            'requirements.txt': '\n'.join(dependencies),
            'Dockerfile': self.generate_dockerfile(dependencies),
            'Jenkinsfile': self.generate_jenkinsfile(),
            'buildconfig.yaml': self.generate_buildconfig(),
            'k8s/deployment.yaml': self.generate_deployment(),
            'k8s/service.yaml': self.generate_service(),
            'k8s/route.yaml': self.generate_route(),
        }
        
        logger.info(f"Generated {len(files)} files")
        return files
    
    def commit_to_github(self, files):
        """Commit generated files to GitHub"""
        logger.info(f"Committing to GitHub: {self.config['github_repo']}")
        
        try:
            # Initialize GitHub client
            g = Github(self.config['github_token'])
            
            # Get repository
            repo_name = self.config['github_repo'].replace('https://github.com/', '').replace('.git', '')
            repo = g.get_repo(repo_name)
            
            # Use the user's specified branch directly (no new branch creation)
            branch_name = self.config['github_branch']
            logger.info(f"Committing to branch: {branch_name}")
            
            # Commit files directly to the specified branch
            for file_path, content in files.items():
                try:
                    # Try to get existing file
                    existing_file = repo.get_contents(file_path, ref=branch_name)
                    repo.update_file(
                        file_path,
                        f"Bob: Update {file_path}",
                        content,
                        existing_file.sha,
                        branch=branch_name
                    )
                    logger.info(f"Updated: {file_path}")
                except:
                    # File doesn't exist, create it
                    repo.create_file(
                        file_path,
                        f"Bob: Create {file_path}",
                        content,
                        branch=branch_name
                    )
                    logger.info(f"Created: {file_path}")
            
            return {
                'success': True,
                'branch': branch_name,
                'repo': repo_name
            }
            
        except Exception as e:
            logger.error(f"GitHub commit failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_dockerhub_secret(self):
        """Create Docker Hub secret in OpenShift"""
        logger.info("Creating Docker Hub secret")
        
        try:
            # Get OpenShift token
            token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token = f.read().strip()
            else:
                token = os.environ.get('OPENSHIFT_TOKEN')
            
            if not token:
                raise Exception("OpenShift token not found")
            
            # Get OpenShift API URL
            api_url = os.environ.get('OPENSHIFT_API_URL', 'https://kubernetes.default.svc')
            
            # Create Docker config JSON
            import base64
            import json
            
            auth_string = f"{self.config['docker_username']}:{self.config['docker_password']}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            
            docker_config = {
                "auths": {
                    "https://index.docker.io/v1/": {
                        "username": self.config['docker_username'],
                        "password": self.config['docker_password'],
                        "auth": auth_b64
                    }
                }
            }
            
            docker_config_json = base64.b64encode(json.dumps(docker_config).encode()).decode()
            
            # Create secret manifest
            secret_data = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": "dockerhub-secret",
                    "namespace": self.config['openshift_namespace']
                },
                "type": "kubernetes.io/dockerconfigjson",
                "data": {
                    ".dockerconfigjson": docker_config_json
                }
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{api_url}/api/v1/namespaces/{self.config['openshift_namespace']}/secrets"
            
            # Try to create the secret
            response = requests.post(url, headers=headers, json=secret_data, verify=False)
            
            if response.status_code in [200, 201]:
                logger.info("Docker Hub secret created successfully")
                return {'success': True}
            elif response.status_code == 409:
                # Secret already exists, update it
                logger.info("Docker Hub secret already exists, updating...")
                update_url = f"{url}/dockerhub-secret"
                
                # Get existing secret to preserve resourceVersion
                get_response = requests.get(update_url, headers=headers, verify=False)
                if get_response.status_code == 200:
                    existing = get_response.json()
                    secret_data['metadata']['resourceVersion'] = existing['metadata']['resourceVersion']
                    
                    # Update the secret
                    update_response = requests.put(update_url, headers=headers, json=secret_data, verify=False)
                    if update_response.status_code == 200:
                        logger.info("Docker Hub secret updated successfully")
                        return {'success': True}
                    else:
                        logger.error(f"Failed to update secret: {update_response.text}")
                        return {'success': False, 'error': update_response.text}
            else:
                logger.error(f"Failed to create secret: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Docker Hub secret creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def apply_buildconfig(self):
        """Apply BuildConfig to OpenShift"""
        logger.info("Applying BuildConfig to OpenShift")
        
        try:
            # First, create Docker Hub secret
            secret_result = self.create_dockerhub_secret()
            if not secret_result['success']:
                return secret_result
            
            # Get OpenShift token from service account
            token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token = f.read().strip()
            else:
                # Fallback to environment variable for local testing
                token = os.environ.get('OPENSHIFT_TOKEN')
            
            if not token:
                raise Exception("OpenShift token not found")
            
            # Get OpenShift API URL
            api_url = os.environ.get('OPENSHIFT_API_URL', 'https://kubernetes.default.svc')
            
            # Generate BuildConfig
            buildconfig_yaml = self.generate_buildconfig()
            
            # Parse YAML - handle multiple documents
            import yaml
            buildconfig_docs = list(yaml.safe_load_all(buildconfig_yaml))
            
            # Apply each document separately
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            applied_resources = []
            
            for doc in buildconfig_docs:
                if not doc:  # Skip empty documents
                    continue
                
                # Determine the correct API endpoint based on resource kind
                kind = doc.get('kind', '')
                api_version = doc.get('apiVersion', '')
                
                if kind == 'BuildConfig':
                    url = f"{api_url}/apis/build.openshift.io/v1/namespaces/{self.config['openshift_namespace']}/buildconfigs"
                elif kind == 'ImageStream':
                    url = f"{api_url}/apis/image.openshift.io/v1/namespaces/{self.config['openshift_namespace']}/imagestreams"
                else:
                    logger.warning(f"Unknown resource kind: {kind}")
                    continue
                
                response = requests.post(url, headers=headers, json=doc, verify=False)
                
                if response.status_code in [200, 201]:
                    logger.info(f"{kind} '{doc['metadata']['name']}' applied successfully")
                    applied_resources.append(f"{kind}/{doc['metadata']['name']}")
                elif response.status_code == 409:
                    # Resource already exists, try to update it
                    logger.info(f"{kind} '{doc['metadata']['name']}' already exists, updating...")
                    resource_name = doc['metadata']['name']
                    update_url = f"{url}/{resource_name}"
                    
                    # Get existing resource to preserve resourceVersion
                    get_response = requests.get(update_url, headers=headers, verify=False)
                    if get_response.status_code == 200:
                        existing = get_response.json()
                        doc['metadata']['resourceVersion'] = existing['metadata']['resourceVersion']
                        
                        # Update the resource
                        update_response = requests.put(update_url, headers=headers, json=doc, verify=False)
                        if update_response.status_code == 200:
                            logger.info(f"{kind} '{resource_name}' updated successfully")
                            applied_resources.append(f"{kind}/{resource_name} (updated)")
                        else:
                            logger.error(f"Failed to update {kind} '{resource_name}': {update_response.text}")
                            return {'success': False, 'error': f"Failed to update {kind}: {update_response.text}"}
                else:
                    logger.error(f"Failed to apply {kind} '{doc['metadata']['name']}': {response.text}")
                    return {'success': False, 'error': f"Failed to apply {kind}: {response.text}"}
            
            logger.info(f"Applied resources: {', '.join(applied_resources)}")
            return {'success': True, 'resources': applied_resources}
                
        except Exception as e:
            logger.error(f"BuildConfig apply failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def apply_deployment_resources(self):
        """Apply Deployment, Service, and Route to OpenShift"""
        logger.info("Applying Deployment resources to OpenShift")
        
        try:
            # Get OpenShift token
            token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token = f.read().strip()
            else:
                token = os.environ.get('OPENSHIFT_TOKEN')
            
            if not token:
                raise Exception("OpenShift token not found")
            
            # Get OpenShift API URL
            api_url = os.environ.get('OPENSHIFT_API_URL', 'https://kubernetes.default.svc')
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            import yaml
            applied_resources = []
            
            # Apply Deployment
            logger.info("Applying Deployment...")
            deployment_yaml = self.generate_deployment()
            deployment_doc = yaml.safe_load(deployment_yaml)
            url = f"{api_url}/apis/apps/v1/namespaces/{self.config['openshift_namespace']}/deployments"
            response = requests.post(url, headers=headers, json=deployment_doc, verify=False)
            
            if response.status_code in [200, 201]:
                logger.info("Deployment created successfully")
                applied_resources.append("Deployment")
            elif response.status_code == 409:
                # Update existing deployment
                logger.info("Deployment already exists, updating...")
                deployment_name = deployment_doc['metadata']['name']
                update_url = f"{url}/{deployment_name}"
                get_response = requests.get(update_url, headers=headers, verify=False)
                if get_response.status_code == 200:
                    existing = get_response.json()
                    deployment_doc['metadata']['resourceVersion'] = existing['metadata']['resourceVersion']
                    update_response = requests.put(update_url, headers=headers, json=deployment_doc, verify=False)
                    if update_response.status_code == 200:
                        logger.info("Deployment updated successfully")
                        applied_resources.append("Deployment (updated)")
                    else:
                        logger.error(f"Failed to update Deployment: {update_response.text}")
                        return {'success': False, 'error': f"Failed to update Deployment: {update_response.text}"}
            else:
                logger.error(f"Failed to create Deployment: {response.text}")
                return {'success': False, 'error': f"Failed to create Deployment: {response.text}"}
            
            # Apply Service
            logger.info("Applying Service...")
            service_yaml = self.generate_service()
            service_doc = yaml.safe_load(service_yaml)
            url = f"{api_url}/api/v1/namespaces/{self.config['openshift_namespace']}/services"
            response = requests.post(url, headers=headers, json=service_doc, verify=False)
            
            if response.status_code in [200, 201]:
                logger.info("Service created successfully")
                applied_resources.append("Service")
            elif response.status_code == 409:
                logger.info("Service already exists")
                applied_resources.append("Service (already exists)")
            else:
                logger.error(f"Failed to create Service: {response.text}")
                return {'success': False, 'error': f"Failed to create Service: {response.text}"}
            
            # Apply Route
            logger.info("Applying Route...")
            route_yaml = self.generate_route()
            route_doc = yaml.safe_load(route_yaml)
            url = f"{api_url}/apis/route.openshift.io/v1/namespaces/{self.config['openshift_namespace']}/routes"
            response = requests.post(url, headers=headers, json=route_doc, verify=False)
            
            if response.status_code in [200, 201]:
                logger.info("Route created successfully")
                applied_resources.append("Route")
            elif response.status_code == 409:
                logger.info("Route already exists")
                applied_resources.append("Route (already exists)")
            else:
                logger.error(f"Failed to create Route: {response.text}")
                return {'success': False, 'error': f"Failed to create Route: {response.text}"}
            
            logger.info(f"Applied resources: {', '.join(applied_resources)}")
            return {'success': True, 'resources': applied_resources}
            
        except Exception as e:
            logger.error(f"Deployment resources apply failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def trigger_pipeline(self):
        """Trigger Jenkins pipeline via OpenShift API"""
        logger.info("Triggering Jenkins pipeline")
        
        try:
            # Get OpenShift token
            token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token = f.read().strip()
            else:
                token = os.environ.get('OPENSHIFT_TOKEN')
            
            if not token:
                raise Exception("OpenShift token not found")
            
            # Get OpenShift API URL
            api_url = os.environ.get('OPENSHIFT_API_URL', 'https://kubernetes.default.svc')
            
            # Trigger build
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            build_config_name = f"{self.config['app_name']}-pipeline"
            url = f"{api_url}/apis/build.openshift.io/v1/namespaces/{self.config['openshift_namespace']}/buildconfigs/{build_config_name}/instantiate"
            
            build_request = {
                "kind": "BuildRequest",
                "apiVersion": "build.openshift.io/v1",
                "metadata": {
                    "name": build_config_name
                }
            }
            
            response = requests.post(url, headers=headers, json=build_request, verify=False)
            
            if response.status_code in [200, 201]:
                build_data = response.json()
                logger.info(f"Pipeline triggered: {build_data.get('metadata', {}).get('name')}")
                return {
                    'success': True,
                    'build_name': build_data.get('metadata', {}).get('name')
                }
            else:
                logger.error(f"Pipeline trigger failed: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Pipeline trigger failed: {str(e)}")
            return {'success': False, 'error': str(e)}


# Routes
@app.route('/')
def index():
    """Main page with deployment form"""
    return render_template('index.html')


@app.route('/status/<deployment_id>')
def status(deployment_id):
    """Deployment status page"""
    return render_template('status.html', deployment_id=deployment_id)


@app.route('/api/deploy', methods=['POST'])
def deploy():
    """Handle deployment request"""
    try:
        # Log received form data for debugging
        logger.info(f"Received form keys: {list(request.form.keys())}")
        logger.info(f"Received files: {list(request.files.keys())}")
        
        # Get form data
        config = {
            'app_name': request.form.get('app_name'),
            'app_port': request.form.get('app_port'),
            'health_check_path': request.form.get('health_check_path', '/health'),
            'replicas': request.form.get('replicas', '2'),
            'github_repo': request.form.get('github_repo'),
            'github_branch': request.form.get('github_branch', 'main'),
            'github_token': request.form.get('github_token'),
            'openshift_namespace': request.form.get('openshift_namespace'),
            'openshift_cluster': request.form.get('openshift_cluster'),
            'python_version': request.form.get('python_version', '3.11'),
            'docker_username': request.form.get('docker_username'),
            'docker_password': request.form.get('docker_password'),
        }
        
        # Validate required fields
        required_fields = ['app_name', 'app_port', 'github_repo', 'github_token', 'openshift_namespace', 'openshift_cluster', 'docker_username', 'docker_password']
        for field in required_fields:
            if not config.get(field):
                logger.error(f"Missing required field: {field}")
                logger.error(f"Config values: {config}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get uploaded file
        if 'app_py' not in request.files:
            return jsonify({'error': 'No app.py file uploaded'}), 400
        
        file = request.files['app_py']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        # Create deployment generator
        generator = DeploymentGenerator(config, file_path)
        deployment_id = generator.deployment_id
        
        # Store deployment info
        deployments[deployment_id] = {
            'id': deployment_id,
            'config': config,
            'status': 'initializing',
            'progress': 0,
            'logs': [],
            'created_at': datetime.now().isoformat(),
            'url': None
        }
        
        # Start deployment in background
        socketio.start_background_task(run_deployment, generator, deployment_id)
        
        return jsonify({
            'deployment_id': deployment_id,
            'status': 'started'
        })
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


def run_deployment(generator, deployment_id):
    """Run deployment process in background"""
    
    def update_status(status, progress, log_message):
        """Update deployment status and emit to client"""
        deployments[deployment_id]['status'] = status
        deployments[deployment_id]['progress'] = progress
        deployments[deployment_id]['logs'].append({
            'timestamp': datetime.now().isoformat(),
            'message': log_message
        })
        
        socketio.emit('deployment_update', {
            'deployment_id': deployment_id,
            'status': status,
            'progress': progress,
            'log': log_message
        }, namespace='/')
    
    try:
        # Step 1: Analyze dependencies
        update_status('analyzing', 10, 'Analyzing app.py for dependencies...')
        socketio.sleep(1)
        
        # Step 2: Generate files
        update_status('generating', 20, 'Generating deployment files...')
        files = generator.generate_all_files()
        update_status('generating', 30, f'Generated {len(files)} files successfully')
        socketio.sleep(1)
        
        # Step 3: Commit to GitHub
        update_status('committing', 40, 'Committing files to GitHub...')
        github_result = generator.commit_to_github(files)
        
        if not github_result['success']:
            update_status('failed', 40, f"GitHub commit failed: {github_result.get('error')}")
            return
        
        update_status('committing', 50, f"Committed to branch: {github_result['branch']}")
        socketio.sleep(1)
        
        # Step 4: Apply BuildConfig
        update_status('configuring', 60, 'Applying BuildConfig to OpenShift...')
        buildconfig_result = generator.apply_buildconfig()
        
        if not buildconfig_result['success']:
            update_status('failed', 60, f"BuildConfig apply failed: {buildconfig_result.get('error')}")
            return
        
        update_status('configuring', 70, 'BuildConfig applied successfully')
        socketio.sleep(1)
        
        # Step 4.5: Apply Deployment Resources
        update_status('deploying', 75, 'Applying Deployment, Service, and Route...')
        deploy_result = generator.apply_deployment_resources()
        
        if not deploy_result['success']:
            update_status('failed', 75, f"Deployment apply failed: {deploy_result.get('error')}")
            return
        
        update_status('deploying', 78, f"Applied: {', '.join(deploy_result['resources'])}")
        socketio.sleep(1)
        
        # Step 5: Trigger pipeline
        update_status('building', 80, 'Triggering Jenkins pipeline...')
        pipeline_result = generator.trigger_pipeline()
        
        if not pipeline_result['success']:
            update_status('failed', 80, f"Pipeline trigger failed: {pipeline_result.get('error')}")
            return
        
        update_status('building', 90, f"Pipeline started: {pipeline_result.get('build_name')}")
        socketio.sleep(2)
        
        # Step 6: Complete
        app_url = f"https://{generator.config['app_name']}-{generator.config['openshift_namespace']}.{generator.config['openshift_cluster']}"
        deployments[deployment_id]['url'] = app_url
        
        update_status('completed', 100, f'Deployment complete! App URL: {app_url}')
        
    except Exception as e:
        logger.error(f"Deployment {deployment_id} failed: {str(e)}")
        update_status('failed', deployments[deployment_id]['progress'], f'Error: {str(e)}')


@app.route('/api/status/<deployment_id>')
def get_deployment_status(deployment_id):
    """Get deployment status"""
    if deployment_id not in deployments:
        return jsonify({'error': 'Deployment not found'}), 404
    
    return jsonify(deployments[deployment_id])


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)

# Made with Bob
