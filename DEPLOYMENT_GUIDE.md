# OpenShift Deployment Guide - Step by Step

This guide provides detailed step-by-step instructions for deploying the Python Flask application to OpenShift.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] OpenShift cluster access
- [ ] `oc` CLI installed and configured
- [ ] Jenkins instance with required plugins
- [ ] Git repository access
- [ ] Cluster admin permissions (for initial setup)

## 🎯 Deployment Steps

### Phase 1: Initial Setup (One-time)

#### Step 1.1: Login to OpenShift

```bash
# Get your login command from OpenShift web console
# Click on your username → Copy login command
oc login --token=sha256~xxxxx --server=https://api.cluster.example.com:6443

# Verify login
oc whoami
oc cluster-info
```

#### Step 1.2: Create Namespaces

```bash
# Apply namespace configuration
oc apply -f k8s/00-namespaces.yaml

# Verify namespaces
oc get namespaces | grep -E 'production|development'

# Expected output:
# production     Active   1m
# development    Active   1m
```

#### Step 1.3: Setup ServiceAccount and RBAC

```bash
# Apply ServiceAccount and RBAC configuration
oc apply -f k8s/01-serviceaccount-rbac.yaml

# Verify ServiceAccount creation
oc get serviceaccount jenkins-sa -n production
oc get serviceaccount jenkins-sa -n development

# Get ServiceAccount token for Jenkins
TOKEN=$(oc sa get-token jenkins-sa -n production)
echo "Jenkins Token: $TOKEN"

# IMPORTANT: Save this token - you'll need it for Jenkins configuration
echo $TOKEN > jenkins-token.txt

# Verify permissions
oc auth can-i create deployments --as=system:serviceaccount:production:jenkins-sa -n production
# Should return: yes

oc auth can-i create routes --as=system:serviceaccount:production:jenkins-sa -n production
# Should return: yes
```

#### Step 1.4: Apply Configuration (ConfigMap and Secret)

```bash
# Apply ConfigMap and Secret
oc apply -f k8s/02-configmap-secret.yaml -n production

# Verify ConfigMap
oc get configmap python-app-config -n production
oc describe configmap python-app-config -n production

# Verify Secret
oc get secret python-app-secret -n production

# View ConfigMap data
oc get configmap python-app-config -n production -o yaml

# Decode secret (for verification only)
oc get secret python-app-secret -n production -o jsonpath='{.data.API_KEY}' | base64 -d
echo ""
```

### Phase 2: Jenkins Configuration

#### Step 2.1: Install Required Jenkins Plugins

1. Go to Jenkins → Manage Jenkins → Manage Plugins
2. Install these plugins:
   - OpenShift Client Plugin
   - Kubernetes CLI Plugin
   - Pipeline Plugin
   - Git Plugin
   - Credentials Binding Plugin

3. Restart Jenkins after installation

#### Step 2.2: Add OpenShift Credentials to Jenkins

1. Go to Jenkins → Manage Jenkins → Manage Credentials
2. Click on "(global)" domain
3. Click "Add Credentials"
4. Configure:
   - Kind: **Secret text**
   - Scope: **Global**
   - Secret: **[Paste the token from jenkins-token.txt]**
   - ID: **openshift-token**
   - Description: **OpenShift Production ServiceAccount Token**
5. Click "OK"

#### Step 2.3: Configure OpenShift Client Plugin

1. Go to Manage Jenkins → Configure System
2. Scroll to "OpenShift Client Plugin" section
3. Click "Add OpenShift Cluster"
4. Configure:
   - Cluster Name: **production-cluster**
   - API Server URL: **[Your OpenShift API URL, e.g., https://api.cluster.example.com:6443]**
   - Credentials: **Select "openshift-token"**
   - Skip TLS Verify: **Check this if using self-signed certificates**
5. Click "Test Connection" to verify
6. Click "Save"

#### Step 2.4: Create Jenkins Pipeline Job

1. From Jenkins dashboard, click "New Item"
2. Enter name: **python-app-deployment**
3. Select: **Pipeline**
4. Click "OK"
5. Configure the job:

   **General Section:**
   - Description: `CI/CD pipeline for Python Flask application deployment to OpenShift`
   - Check "Discard old builds"
   - Strategy: Log Rotation
   - Max # of builds to keep: 10

   **Build Triggers Section:**
   - Check "GitHub hook trigger for GITScm polling" (if using GitHub webhooks)
   - Or check "Poll SCM" with schedule: `H/5 * * * *` (polls every 5 minutes)

   **Pipeline Section:**
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: **https://github.com/gredss/agentic-deployment-orchestrator**
   - Credentials: **None** (for public repo) or add credentials for private repo
   - Branch Specifier: ***/main**
   - Script Path: **Jenkinsfile**

6. Click "Save"

### Phase 3: First Deployment

#### Step 3.1: Manual Test Deployment (Optional but Recommended)

Before running the Jenkins pipeline, test manual deployment:

```bash
# Switch to production namespace
oc project production

# Apply all manifests
oc apply -f k8s/02-configmap-secret.yaml -n production
oc apply -f k8s/03-deployment.yaml -n production
oc apply -f k8s/04-service.yaml -n production
oc apply -f k8s/05-route.yaml -n production

# Wait for deployment
oc rollout status deployment/python-app -n production

# Check pods
oc get pods -n production -l app=python-app

# Get route URL
ROUTE_URL=$(oc get route python-app -n production -o jsonpath='{.spec.host}')
echo "Application URL: https://$ROUTE_URL"

# Test the application
curl -k https://$ROUTE_URL/
curl -k https://$ROUTE_URL/health

# If successful, delete the manual deployment to let Jenkins manage it
oc delete deployment python-app -n production
oc delete service python-app -n production
oc delete route python-app -n production
```

#### Step 3.2: Run Jenkins Pipeline

1. Go to Jenkins → python-app-deployment job
2. Click "Build Now"
3. Watch the build progress in "Build History"
4. Click on the build number (e.g., #1)
5. Click "Console Output" to see detailed logs

**Expected Pipeline Stages:**
1. ✓ Initialize
2. ✓ Checkout
3. ✓ Build Image
4. ✓ Push to Registry
5. ✓ Deploy to OpenShift
6. ✓ Wait for Rollout
7. ✓ Health Check
8. ✓ Output Information

#### Step 3.3: Verify Deployment

```bash
# Check all resources
oc get all -n production

# Check deployment status
oc get deployment python-app -n production

# Check pods
oc get pods -n production -l app=python-app

# Check service
oc get svc python-app -n production

# Check route
oc get route python-app -n production

# Get application URL
ROUTE_URL=$(oc get route python-app -n production -o jsonpath='{.spec.host}')
echo "Application URL: https://$ROUTE_URL"

# Test endpoints
curl -k https://$ROUTE_URL/
curl -k https://$ROUTE_URL/health
curl -k https://$ROUTE_URL/ready
curl -k https://$ROUTE_URL/info

# View logs
oc logs -f deployment/python-app -n production
```

### Phase 4: Integration with Slack/Bob (Optional)

#### Step 4.1: Configure Jenkins Remote Trigger

1. Go to python-app-deployment job → Configure
2. Under "Build Triggers", check "Trigger builds remotely"
3. Authentication Token: Enter a secure token (e.g., `my-secure-token-123`)
4. Save

#### Step 4.2: Get Jenkins Trigger URL

```bash
# Jenkins trigger URL format:
# http://JENKINS_URL/job/python-app-deployment/build?token=YOUR_TOKEN

# Example:
# http://jenkins.example.com/job/python-app-deployment/build?token=my-secure-token-123

# With authentication:
# http://USERNAME:API_TOKEN@jenkins.example.com/job/python-app-deployment/build?token=my-secure-token-123
```

#### Step 4.3: Test Remote Trigger

```bash
# Test the trigger URL
curl -X POST "http://jenkins.example.com/job/python-app-deployment/build?token=my-secure-token-123"

# With authentication
curl -X POST "http://USERNAME:API_TOKEN@jenkins.example.com/job/python-app-deployment/build?token=my-secure-token-123"
```

#### Step 4.4: Configure Bob to Trigger Jenkins

Update Bob's configuration to call the Jenkins trigger URL when receiving Slack commands.

### Phase 5: Ongoing Operations

#### Monitoring Deployment

```bash
# Watch pods
watch oc get pods -n production

# Stream logs
oc logs -f deployment/python-app -n production

# Check events
oc get events -n production --sort-by='.lastTimestamp'

# Check resource usage
oc adm top pods -n production
```

#### Updating Application

```bash
# Make code changes and push to Git
git add .
git commit -m "Update application"
git push origin main

# Trigger Jenkins pipeline (automatic if webhook configured)
# Or manually trigger from Jenkins UI
```

#### Rollback if Needed

```bash
# View rollout history
oc rollout history deployment/python-app -n production

# Rollback to previous version
oc rollout undo deployment/python-app -n production

# Check rollout status
oc rollout status deployment/python-app -n production
```

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Namespaces created (production, development)
- [ ] ServiceAccount exists with proper RBAC
- [ ] ConfigMap and Secret applied
- [ ] Deployment running with 2 replicas
- [ ] Pods in Running state
- [ ] Service created and has endpoints
- [ ] Route created and accessible
- [ ] Application responds on all endpoints (/, /health, /ready, /info)
- [ ] Jenkins pipeline runs successfully
- [ ] Logs are accessible

## 🚨 Troubleshooting Common Issues

### Issue 1: Pods Not Starting

```bash
# Check pod status
oc get pods -n production

# Describe pod
oc describe pod <pod-name> -n production

# Check logs
oc logs <pod-name> -n production

# Common fixes:
# - Check image pull policy
# - Verify ConfigMap/Secret exists
# - Check resource limits
```

### Issue 2: Jenkins Cannot Connect to OpenShift

```bash
# Verify token is valid
oc whoami --show-token

# Test from Jenkins node
oc login --token=<token> --server=<server-url>
oc project production

# Check ServiceAccount permissions
oc auth can-i create deployments --as=system:serviceaccount:production:jenkins-sa -n production
```

### Issue 3: Route Not Accessible

```bash
# Check route
oc get route python-app -n production
oc describe route python-app -n production

# Check service endpoints
oc get endpoints python-app -n production

# Test service internally
oc run test --image=curlimages/curl --rm -it -- curl http://python-app:8080/health
```

## 📊 Success Criteria

Your deployment is successful when:

1. ✅ Jenkins pipeline completes all stages without errors
2. ✅ Application pods are running (2/2 replicas)
3. ✅ Route is accessible from external network
4. ✅ All endpoints return expected responses:
   - `/` returns "Deployment successful"
   - `/health` returns `{"status": "healthy"}`
   - `/ready` returns `{"status": "ready"}`
   - `/info` returns application metadata
5. ✅ Logs show no errors
6. ✅ Health checks pass consistently

## 🎓 Next Steps

After successful deployment:

1. Configure monitoring and alerting
2. Set up horizontal pod autoscaling
3. Implement blue-green or canary deployments
4. Configure backup and disaster recovery
5. Set up CI/CD for multiple environments
6. Integrate with Slack/Bob for automated deployments

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review Jenkins console output
3. Check OpenShift events and logs
4. Consult the main README.md
5. Contact the DevOps team

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-05-23