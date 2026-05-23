# Agentic Deployment Orchestrator

AI-driven CI/CD orchestration system using Slack, Bob (AI orchestrator), Jenkins, and OpenShift for automated Python application deployments.

## Architecture

```
Slack → Bob Orchestrator → Jenkins → OpenShift
```

**Components:**
- **Slack**: Human interaction layer for deployment commands
- **Bob**: AI orchestrator that interprets requests and triggers Jenkins
- **Jenkins**: CI/CD engine executing deployment pipelines
- **OpenShift**: Container platform running the Python Flask application

## Repository Structure

```
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container image definition
├── Jenkinsfile              # CI/CD pipeline
├── k8s/                     # OpenShift manifests for Python app
│   ├── 01-serviceaccount-rbac.yaml
│   ├── 02-configmap-secret.yaml
│   ├── 03-deployment-simple.yaml
│   ├── 04-service.yaml
│   └── 05-route.yaml
└── bob/                     # Bob orchestrator
    ├── orchestrator.py      # Flask webhook server
    ├── requirements.txt
    ├── Dockerfile
    └── k8s/                 # OpenShift manifests for Bob
        ├── deployment.yaml
        ├── service.yaml
        ├── route.yaml
        └── secret.yaml
```

## Quick Start

### 1. Deploy Python Application
```bash
oc apply -f k8s/
```

### 2. Deploy Bob Orchestrator
```bash
# Create secret with Jenkins token
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: bob-secrets
  namespace: production
stringData:
  jenkins-token: "YOUR_JENKINS_TOKEN"
EOF

oc apply -f bob/k8s/
```

### 3. Trigger Deployment via Bob
```bash
curl -X POST https://bob-orchestrator-production.apps.../webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"deploy to production"}'
```

## Application Endpoints

- **Python App**: `https://python-app-production.apps.../`
- **Health Check**: `https://python-app-production.apps.../health`
- **Bob Webhook**: `https://bob-orchestrator-production.apps.../webhook`

## Features

- Event-driven deployment automation
- AI-powered request interpretation
- Zero-downtime rolling updates
- Automated health checks
- Slack integration ready
- RBAC-secured deployments

## Technologies

Python 3.9 | Flask | Gunicorn | Jenkins | OpenShift | Kubernetes | Docker
