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

### 2. Build and Deploy Bob Orchestrator
```bash
# Build the Bob container image
docker build -t bob-orchestrator:latest ./bob

# Create secret with Jenkins credentials
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: bob-secrets
  namespace: production
type: Opaque
stringData:
  jenkins-token: "SET_THIS_LOCALLY"
  jenkins-user: "admin"
EOF

oc apply -f bob/k8s/
```

### 3. Trigger Deployment via Bob
```bash
curl -X POST https://bob-orchestrator-production.apps.../webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"/deploy production"}'
```

## Application Endpoints

- **Python App**: `https://python-app-production.apps.../`
- **Health Check**: `https://python-app-production.apps.../health`
- **Bob Webhook**: `https://bob-orchestrator-production.apps.../webhook`

## Features

- Event-driven deployment automation
- Slack-style deployment command parsing
- Jenkins parameterized remote trigger via `buildWithParameters`
- Zero-downtime rolling updates
- Automated health checks
- Secret-based Jenkins authentication
- RBAC-secured deployments

## Technologies

Python 3.9 | Flask | Gunicorn | Jenkins | OpenShift | Kubernetes | Docker

## Bob → Jenkins Integration Notes

Bob now expects Jenkins configuration entirely from environment variables or Kubernetes secrets.

Required variables for [`bob/orchestrator.py`](bob/orchestrator.py):
- `JENKINS_URL`
- `JENKINS_TOKEN`
- `JENKINS_JOB`
- `JENKINS_USER` (optional, for basic auth username)
- `DEFAULT_DEPLOY_ENV` (optional, defaults to `production`)

Supported webhook payload example:
```json
{
  "text": "/deploy production"
}
```

When Bob receives that command, it triggers the Jenkins endpoint:

```text
POST https://jenkins-production.apps.itz-gkg33y.infra01-lb.tok04.techzone.ibm.com/job/python-app-deployment/buildWithParameters?ENV=production
```

That line is an HTTP request description, not a shell command. If you want to test Jenkins directly from a terminal, use [`curl`](README.md:111):

```bash
curl -X POST \
  -u 'kube:admin:YOUR_JENKINS_TOKEN' \
  'https://jenkins-production.apps.itz-gkg33y.infra01-lb.tok04.techzone.ibm.com/job/python-app-deployment/buildWithParameters?ENV=production'
```

If your username contains a colon, prefer using [`--user`](README.md:117) with environment variables or a netrc file to avoid shell parsing issues:

```bash
JENKINS_USER='kube:admin'
JENKINS_TOKEN='YOUR_JENKINS_TOKEN'

curl -X POST \
  --user "${JENKINS_USER}:${JENKINS_TOKEN}" \
  'https://jenkins-production.apps.itz-gkg33y.infra01-lb.tok04.techzone.ibm.com/job/python-app-deployment/buildWithParameters?ENV=production'
```

To test through Bob instead of Jenkins directly:

```bash
curl -X POST https://bob-orchestrator-production.apps.../webhook \
  -H 'Content-Type: application/json' \
  -d '{"text":"/deploy production"}'
```

Response behavior:
- Returns `202 Accepted` when Jenkins accepts the deployment request
- Returns the Jenkins job URL
- Returns the Jenkins queue URL when Jenkins provides it in the `Location` header

Security notes:
- Do not hardcode Jenkins tokens in source files
- Store Jenkins credentials only in the OpenShift secret [`bob/k8s/secret.yaml`](bob/k8s/secret.yaml)
- Prefer applying the secret directly from your terminal instead of committing real values
