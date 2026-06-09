# Agentic Deployment Orchestrator

AI-driven CI/CD orchestration system for automated Python application deployments to OpenShift. This platform provides multiple deployment methods including AI orchestration via Bob, web UI, and template generation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Deployment Methods                        │
├─────────────────────────────────────────────────────────────┤
│  1. Web UI          2. Bob Orchestrator    3. Templates     │
│  (User-friendly)    (AI-driven)            (CLI-based)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Jenkins CI/CD   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  OpenShift/K8s   │
                    └──────────────────┘
```

## Repository Structure

```
.
├── app.py                          # Sample Flask application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image definition
├── Jenkinsfile                     # CI/CD pipeline
├── SECRETS.md                      # Security configuration guide
│
├── bob/                            # Bob AI Orchestrator
│   ├── orchestrator.py             # Main orchestrator service
│   ├── jenkins.py                  # Jenkins integration
│   ├── requirements.txt
│   ├── Dockerfile
│   └── k8s/                        # Bob deployment manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── route.yaml
│       ├── buildconfig.yaml
│       └── secret.yaml.example     # Template for secrets
│
├── web-ui/                         # Web-based Deployment UI
│   ├── app.py                      # Flask web application
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── README.md                   # Detailed web UI documentation
│   ├── QUICKSTART.md
│   ├── templates/                  # HTML templates
│   │   ├── index.html
│   │   └── status.html
│   ├── static/                     # CSS, JS, images
│   │   ├── css/style.css
│   │   └── js/
│   ├── deployment-templates/       # Generated file templates
│   │   ├── Dockerfile.template
│   │   ├── Jenkinsfile.template
│   │   ├── buildconfig.yaml.template
│   │   ├── deployment.yaml.template
│   │   ├── service.yaml.template
│   │   └── route.yaml.template
│   └── k8s/                        # Web UI deployment manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── route.yaml
│       └── secret.yaml.example
│
├── bob-template-generator/         # CLI Template Generator
│   ├── generate.py                 # Template generation script
│   ├── example-app.py              # Sample application
│   ├── quick-start.sh              # Quick setup script
│   ├── .env.example                # Configuration template
│   ├── README.md                   # Generator documentation
│   └── templates/                  # Deployment templates
│       ├── Dockerfile.template
│       ├── Jenkinsfile.template
│       ├── buildconfig.yaml.template
│       └── k8s/
│
├── bob-test-app/                   # Testing & Examples
│   ├── orchestrator-v2.py          # Enhanced orchestrator
│   ├── requirements.txt
│   ├── README.md
│   ├── templates/                  # Kubernetes templates
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── route.yaml
│   └── test-app/                   # Sample test application
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── k8s/                            # Base Kubernetes manifests
│   ├── 00-namespaces.yaml
│   ├── 01-serviceaccount-rbac.yaml
│   ├── 02-configmap-secret.yaml.example
│   ├── 03-deployment.yaml
│   ├── 03-deployment-simple.yaml
│   ├── 04-service.yaml
│   └── 05-route.yaml
│
└── testing-form/                   # Additional testing utilities
    └── app.py
```

## Deployment Methods

### 1. Web UI (Recommended for Beginners)

User-friendly web interface for deploying applications with drag-and-drop support.

**Features:**
- Visual form-based deployment
- Real-time progress tracking
- Automatic dependency detection
- GitHub integration
- No CLI knowledge required

**Quick Start:**
```bash
cd web-ui
pip install -r requirements.txt
python app.py
```

Access at `http://localhost:8080`

See [web-ui/README.md](web-ui/README.md) for detailed documentation.

### 2. Bob AI Orchestrator (Recommended for Automation)

AI-driven orchestrator that interprets deployment commands and manages the CI/CD pipeline.

**Features:**
- Natural language deployment commands
- Jenkins integration
- OpenShift API automation
- Webhook-based triggers
- Event-driven architecture

**Quick Start:**
```bash
# Deploy Bob
oc apply -f bob/k8s/

# Trigger deployment
curl -X POST https://bob-orchestrator-production.apps.../webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"/deploy production"}'
```

**Bob Commands:**
- `/deploy <environment>` - Deploy application
- `/pipeline <pipeline-name> <environment>` - Trigger specific pipeline

### 3. Template Generator (Recommended for Developers)

CLI tool that generates all deployment files from your application code.

**Features:**
- Auto-detect dependencies
- Generate complete CI/CD pipeline
- Customizable templates
- Multi-environment support

**Quick Start:**
```bash
cd bob-template-generator
cp .env.example .env
# Edit .env with your configuration
python generate.py
```

See [bob-template-generator/README.md](bob-template-generator/README.md) for detailed documentation.

## Prerequisites

- Python 3.9+
- OpenShift cluster access with `oc` CLI
- Jenkins server (integrated with OpenShift)
- GitHub account with personal access token
- Docker (for local development)

## Quick Start Guide

### Step 1: Clone Repository

```bash
git clone https://github.com/gredss/agentic-deployment-orchestrator.git
cd agentic-deployment-orchestrator
```

### Step 2: Configure Secrets

```bash
# Copy example files
cp bob/k8s/secret.yaml.example bob/k8s/secret.yaml
cp web-ui/k8s/secret.yaml.example web-ui/k8s/secret.yaml
cp k8s/02-configmap-secret.yaml.example k8s/02-configmap-secret.yaml

# Edit with your credentials
nano bob/k8s/secret.yaml
```

See [SECRETS.md](SECRETS.md) for detailed security configuration.

### Step 3: Deploy Components

**Deploy Bob Orchestrator:**
```bash
oc apply -f bob/k8s/
```

**Deploy Web UI:**
```bash
oc apply -f web-ui/k8s/
```

**Deploy Sample Application:**
```bash
oc apply -f k8s/
```

### Step 4: Access Services

```bash
# Get Bob URL
oc get route bob-orchestrator -n production

# Get Web UI URL
oc get route bob-web-ui -n production

# Get Application URL
oc get route python-app -n production
```

## Application Endpoints

- **Web UI**: `https://bob-web-ui-production.apps.../`
- **Bob Webhook**: `https://bob-orchestrator-production.apps.../webhook`
- **Sample App**: `https://python-app-production.apps.../`
- **Health Check**: `https://python-app-production.apps.../health`

## Key Features

### Security
- Secret-based credential management
- RBAC-secured deployments
- Service account authentication
- No hardcoded credentials

### Automation
- Event-driven deployment triggers
- Automated health checks
- Zero-downtime rolling updates
- Automatic rollback on failure

### Flexibility
- Multiple deployment methods
- Template-based configuration
- Multi-environment support
- Customizable pipelines

### Monitoring
- Real-time deployment status
- Progress tracking
- Build and deployment logs
- Health check verification

## Technology Stack

**Backend:**
- Python 3.9+
- Flask
- Gunicorn

**CI/CD:**
- Jenkins
- OpenShift BuildConfig
- Kubernetes

**Infrastructure:**
- OpenShift/Kubernetes
- Docker
- Git/GitHub

## Configuration

### Environment Variables

**Bob Orchestrator:**
- `JENKINS_URL` - Jenkins server URL
- `JENKINS_TOKEN` - Jenkins API token
- `JENKINS_JOB` - Jenkins job name
- `JENKINS_USER` - Jenkins username
- `OPENSHIFT_TOKEN` - OpenShift API token
- `DEFAULT_DEPLOY_ENV` - Default deployment environment

**Web UI:**
- `SECRET_KEY` - Flask secret key
- `PORT` - Server port (default: 8080)
- `OPENSHIFT_TOKEN` - OpenShift API token (optional)
- `OPENSHIFT_API_URL` - OpenShift API endpoint

See [SECRETS.md](SECRETS.md) for complete configuration guide.

## Usage Examples

### Deploy via Web UI

1. Open Web UI in browser
2. Fill in application details
3. Upload your `app.py`
4. Click "Deploy Now"
5. Monitor progress in real-time

### Deploy via Bob Orchestrator

```bash
# Deploy to production
curl -X POST https://bob-orchestrator-production.apps.../webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"/deploy production"}'

# Trigger specific pipeline
curl -X POST https://bob-orchestrator-production.apps.../webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"/pipeline my-app-pipeline production"}'
```

### Deploy via Template Generator

```bash
cd bob-template-generator
cp .env.example .env
# Configure .env
python generate.py
oc apply -f buildconfig.yaml
```

## Testing

### Test Bob Orchestrator

```bash
cd bob-test-app
# Follow instructions in bob-test-app/README.md
```

### Test Web UI

```bash
cd web-ui
python app.py
# Access http://localhost:8080
```

### Test Template Generator

```bash
cd bob-template-generator
python generate.py
# Review generated files
```

## Troubleshooting

### Common Issues

**Bob not responding:**
- Check Bob pod logs: `oc logs -f deployment/bob-orchestrator`
- Verify Jenkins credentials in secret
- Ensure OpenShift token is valid

**Web UI deployment fails:**
- Check build logs: `oc logs -f build/bob-web-ui-1`
- Verify GitHub token permissions
- Check OpenShift RBAC permissions

**Template generation fails:**
- Verify `.env` configuration
- Check Python dependencies
- Ensure templates directory exists

### Debug Commands

```bash
# Check pod status
oc get pods -n production

# View logs
oc logs -f deployment/<app-name>

# Describe resources
oc describe deployment <app-name>

# Check events
oc get events -n production --sort-by='.lastTimestamp'
```

## Security Best Practices

1. Never commit secrets to version control
2. Use `.example` templates for configuration
3. Rotate credentials regularly
4. Use RBAC for access control
5. Enable HTTPS for all endpoints
6. Implement rate limiting in production
7. Monitor and audit deployments

See [SECRETS.md](SECRETS.md) for detailed security guidelines.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Documentation

- [Web UI Documentation](web-ui/README.md)
- [Template Generator Guide](bob-template-generator/README.md)
- [Test Application Guide](bob-test-app/README.md)
- [Security Configuration](SECRETS.md)
- [Web UI Quick Start](web-ui/QUICKSTART.md)

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/gredss/agentic-deployment-orchestrator/issues)
- Documentation: Review component-specific README files

## Acknowledgments

Built with:
- Flask web framework
- OpenShift container platform
- Jenkins CI/CD
- Kubernetes orchestration
