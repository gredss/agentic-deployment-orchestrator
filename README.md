# Python Flask Application - OpenShift CI/CD Deployment

Complete OpenShift deployment configuration for a Python Flask application with Jenkins-based CI/CD pipeline.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Jenkins Pipeline](#jenkins-pipeline)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## 🎯 Overview

This project implements a complete CI/CD pipeline for deploying a Python Flask application to OpenShift. The pipeline automates:

- Source code checkout from Git
- Docker image building
- Image pushing to OpenShift internal registry
- Deployment to production namespace
- Health check verification
- Automatic rollback on failure

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Slack     │─────▶│     Bob      │─────▶│    Jenkins      │
│  (Trigger)  │      │ (Orchestrator)│      │   (CI/CD)       │
└─────────────┘      └──────────────┘      └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │   OpenShift     │
                                            │   (Runtime)     │
                                            └────────┬────────┘
                                                     │
                                            ┌────────▼────────┐
                                            │  Python Flask   │
                                            │  Application    │
                                            └─────────────────┘
                                                     │
                                            ┌────────▼────────┐
                                            │  Public Route   │
                                            │  (HTTPS)        │
                                            └─────────────────┘
```

## ✅ Prerequisites

### Required Tools

1. **OpenShift CLI (oc)**
   ```bash
   # Download from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/
   # Verify installation
   oc version
   ```

2. **Jenkins** with plugins:
   - OpenShift Client Plugin
   - Kubernetes CLI Plugin
   - Pipeline Plugin
   - Git Plugin

3. **Git**
   ```bash
   git --version
   ```

4. **Access Requirements**
   - OpenShift cluster access
   - Jenkins instance with OpenShift connectivity
   - Git repository access

### OpenShift Cluster Requirements

- OpenShift 4.x or later
- Cluster admin access (for initial setup)
- Internal image registry enabled

## 📁 Project Structure

```
agentic-deployment-orchestrator/
├── app.py                          # Flask application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image definition
├── Jenkinsfile                     # CI/CD pipeline definition
├── README.md                       # This file
└── k8s/                           # Kubernetes/OpenShift manifests
    ├── 00-namespaces.yaml         # Namespace definitions
    ├── 01-serviceaccount-rbac.yaml # ServiceAccount and RBAC
    ├── 02-configmap-secret.yaml   # Configuration and secrets
    ├── 03-deployment.yaml         # Deployment configuration
    ├── 04-service.yaml            # Service definition
    └── 05-route.yaml              # Route for external access
```

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/gredss/agentic-deployment-orchestrator.git
cd agentic-deployment-orchestrator
```

### 2. Login to OpenShift

```bash
# Login to your OpenShift cluster
oc login --token=<your-token> --server=<your-server-url>
```

### 3. Create Namespaces

```bash
# Create production and development namespaces
oc apply -f k8s/00-namespaces.yaml

# Verify
oc get namespaces | grep -E 'production|development'
```

### 4. Setup ServiceAccount and RBAC

```bash
# Create ServiceAccount and configure RBAC
oc apply -f k8s/01-serviceaccount-rbac.yaml

# Get token for Jenkins
oc sa get-token jenkins-sa -n production

# Save this token - you'll need it for Jenkins configuration
```

### 5. Apply Configuration

```bash
# Apply ConfigMap and Secret
oc apply -f k8s/02-configmap-secret.yaml -n production

# Verify
oc get configmap,secret -n production
```

### 6. Configure Jenkins

See [Jenkins Pipeline](#jenkins-pipeline) section below.

## 🔧 Detailed Setup

### Step 1: Namespace Creation

```bash
# Create namespaces
oc apply -f k8s/00-namespaces.yaml

# Switch to production namespace
oc project production

# Verify current project
oc project
```

### Step 2: ServiceAccount Configuration

```bash
# Apply ServiceAccount and RBAC
oc apply -f k8s/01-serviceaccount-rbac.yaml

# Verify ServiceAccount
oc get serviceaccount jenkins-sa -n production

# Get ServiceAccount token
TOKEN=$(oc sa get-token jenkins-sa -n production)
echo $TOKEN

# Verify permissions
oc auth can-i create deployments --as=system:serviceaccount:production:jenkins-sa -n production
oc auth can-i create routes --as=system:serviceaccount:production:jenkins-sa -n production
```

### Step 3: Application Configuration

```bash
# Apply ConfigMap and Secret
oc apply -f k8s/02-configmap-secret.yaml -n production

# View ConfigMap
oc get configmap python-app-config -o yaml -n production

# View Secret (base64 encoded)
oc get secret python-app-secret -o yaml -n production

# Decode secret values
oc get secret python-app-secret -o jsonpath='{.data.API_KEY}' -n production | base64 -d
```

### Step 4: Manual Deployment (Optional)

For testing before Jenkins automation:

```bash
# Apply all manifests
oc apply -f k8s/03-deployment.yaml -n production
oc apply -f k8s/04-service.yaml -n production
oc apply -f k8s/05-route.yaml -n production

# Check deployment status
oc rollout status deployment/python-app -n production

# Get route URL
oc get route python-app -n production -o jsonpath='{.spec.host}'
```

## 🔄 Jenkins Pipeline

### Jenkins Configuration

#### 1. Add OpenShift Credentials

1. Go to Jenkins → Manage Jenkins → Manage Credentials
2. Add new credential:
   - Kind: Secret text
   - Secret: `<token from oc sa get-token jenkins-sa -n production>`
   - ID: `openshift-token`
   - Description: OpenShift ServiceAccount Token

#### 2. Configure OpenShift Plugin

1. Go to Manage Jenkins → Configure System
2. Find "OpenShift Client Plugin" section
3. Add cluster:
   - Cluster Name: `production-cluster`
   - API Server URL: `<your-openshift-api-url>`
   - Credentials: Select `openshift-token`
   - Skip TLS Verify: Check if using self-signed certificates

#### 3. Create Pipeline Job

1. New Item → Pipeline
2. Name: `python-app-deployment`
3. Pipeline section:
   - Definition: Pipeline script from SCM
   - SCM: Git
   - Repository URL: `https://github.com/gredss/agentic-deployment-orchestrator`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
4. Save

#### 4. Configure OpenShift Context in Jenkinsfile

The Jenkinsfile uses `oc` commands. Ensure Jenkins has:

```groovy
// In Jenkinsfile, add at the beginning if needed:
withCredentials([string(credentialsId: 'openshift-token', variable: 'OC_TOKEN')]) {
    sh """
        oc login --token=\${OC_TOKEN} --server=<your-server-url> --insecure-skip-tls-verify
        oc project production
    """
}
```

### Pipeline Stages

The Jenkinsfile implements these stages:

1. **Initialize** - Setup environment variables
2. **Checkout** - Clone Git repository
3. **Build Image** - Build Docker image using OpenShift BuildConfig
4. **Push to Registry** - Verify image in OpenShift registry
5. **Deploy to OpenShift** - Apply Kubernetes manifests
6. **Wait for Rollout** - Wait for deployment completion
7. **Health Check** - Verify application health
8. **Output Information** - Display deployment details

### Triggering the Pipeline

#### Manual Trigger
```bash
# From Jenkins UI
Click "Build Now" on the pipeline job
```

#### Webhook Trigger (for Slack/Bob integration)
```bash
# Configure webhook in Jenkins job
# Build Triggers → Trigger builds remotely
# Authentication Token: <your-token>

# Trigger URL:
curl -X POST http://jenkins-url/job/python-app-deployment/build?token=<your-token>
```

#### Git Webhook
```bash
# Configure in GitHub/GitLab
# Webhook URL: http://jenkins-url/github-webhook/
# or: http://jenkins-url/project/python-app-deployment
```

## ✔️ Verification

### Check Deployment Status

```bash
# Check all resources
oc get all -n production

# Check pods
oc get pods -n production -l app=python-app

# Check deployment
oc get deployment python-app -n production

# Check service
oc get svc python-app -n production

# Check route
oc get route python-app -n production
```

### Get Application URL

```bash
# Get route URL
ROUTE_URL=$(oc get route python-app -n production -o jsonpath='{.spec.host}')
echo "Application URL: https://${ROUTE_URL}"
```

### Test Endpoints

```bash
# Home endpoint
curl -k https://${ROUTE_URL}/

# Health check
curl -k https://${ROUTE_URL}/health

# Readiness check
curl -k https://${ROUTE_URL}/ready

# Info endpoint
curl -k https://${ROUTE_URL}/info
```

### View Logs

```bash
# View pod logs
oc logs -f deployment/python-app -n production

# View logs from specific pod
POD_NAME=$(oc get pods -n production -l app=python-app -o jsonpath='{.items[0].metadata.name}')
oc logs -f $POD_NAME -n production

# View previous pod logs (if pod restarted)
oc logs $POD_NAME --previous -n production
```

### Check Events

```bash
# View recent events
oc get events -n production --sort-by='.lastTimestamp'

# View deployment events
oc describe deployment python-app -n production
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
oc get pods -n production

# Describe pod for events
oc describe pod <pod-name> -n production

# Check pod logs
oc logs <pod-name> -n production

# Common causes:
# - Image pull errors
# - Resource limits
# - ConfigMap/Secret not found
# - Health check failures
```

#### 2. Image Pull Errors

```bash
# Check ImageStream
oc get imagestream python-app -n production
oc describe imagestream python-app -n production

# Check BuildConfig
oc get buildconfig python-app -n production

# Trigger new build
oc start-build python-app -n production --follow
```

#### 3. Route Not Accessible

```bash
# Check route
oc get route python-app -n production

# Describe route
oc describe route python-app -n production

# Check service endpoints
oc get endpoints python-app -n production

# Test service internally
oc run test-pod --image=curlimages/curl --rm -it -- curl http://python-app:8080/health
```

#### 4. Health Check Failures

```bash
# Check liveness probe
oc get deployment python-app -n production -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}'

# Check readiness probe
oc get deployment python-app -n production -o jsonpath='{.spec.template.spec.containers[0].readinessProbe}'

# Temporarily disable probes for debugging
oc set probe deployment/python-app --liveness --readiness --remove=true -n production
```

#### 5. Jenkins Pipeline Failures

```bash
# Check Jenkins logs
# View in Jenkins UI: Build → Console Output

# Verify OpenShift connectivity from Jenkins
oc whoami
oc project

# Check ServiceAccount permissions
oc auth can-i create deployments --as=system:serviceaccount:production:jenkins-sa -n production
```

### Debug Commands

```bash
# Get all resources
oc get all -n production

# Describe deployment
oc describe deployment python-app -n production

# Get pod details
oc get pods -n production -o wide

# Execute command in pod
oc exec -it <pod-name> -n production -- /bin/sh

# Port forward for local testing
oc port-forward deployment/python-app 8080:8080 -n production

# View resource usage
oc adm top pods -n production
oc adm top nodes
```

### Rollback Deployment

```bash
# View rollout history
oc rollout history deployment/python-app -n production

# Rollback to previous version
oc rollout undo deployment/python-app -n production

# Rollback to specific revision
oc rollout undo deployment/python-app --to-revision=2 -n production

# Check rollout status
oc rollout status deployment/python-app -n production
```

## 🔐 Security Best Practices

### 1. Use Secrets for Sensitive Data

```bash
# Create secret from literal
oc create secret generic app-secret \
  --from-literal=api-key=your-api-key \
  -n production

# Create secret from file
oc create secret generic app-secret \
  --from-file=credentials.json \
  -n production
```

### 2. Limit ServiceAccount Permissions

```yaml
# Use least privilege principle
# Only grant necessary permissions in Role
```

### 3. Use Security Context

```yaml
# Already configured in deployment.yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  allowPrivilegeEscalation: false
```

### 4. Enable Network Policies

```bash
# Create network policy to restrict traffic
oc apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: python-app-netpol
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: python-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 8080
EOF
```

## 📊 Monitoring and Observability

### View Metrics

```bash
# Pod metrics
oc adm top pods -n production

# Node metrics
oc adm top nodes

# Resource quotas
oc get resourcequota -n production
```

### Application Logs

```bash
# Stream logs
oc logs -f deployment/python-app -n production

# Logs from all pods
oc logs -l app=python-app -n production --all-containers=true

# Export logs
oc logs deployment/python-app -n production > app.log
```

## 🚀 Advanced Configuration

### Horizontal Pod Autoscaling

```bash
# Create HPA
oc autoscale deployment python-app \
  --min=2 \
  --max=10 \
  --cpu-percent=80 \
  -n production

# Check HPA status
oc get hpa -n production
```

### Resource Quotas

```bash
# Create resource quota
oc apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
EOF
```

### Persistent Storage

```bash
# Create PVC
oc apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: python-app-data
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
EOF

# Mount in deployment (add to volumes and volumeMounts)
```

## 📚 Additional Resources

- [OpenShift Documentation](https://docs.openshift.com/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 👥 Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the DevOps team

---

**Last Updated:** 2026-05-23
**Version:** 1.0.0