# Bob Orchestrator V2 - Test Application

## Overview

This folder contains a **declarative template-based deployment system** for testing Bob's automation pipeline with new applications. This is an industry best practice implementation that separates infrastructure templates from application logic.

---

## Folder Structure

```
bob-test-app/
├── templates/              # Parameterized Kubernetes manifests
│   ├── deployment.yaml     # Generic deployment template
│   ├── service.yaml        # Generic service template
│   └── route.yaml          # Generic route template
├── test-app/               # Sample Flask application
│   ├── app.py              # Simple Flask app
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Container image definition
├── orchestrator-v2.py      # Enhanced Bob with template support
├── requirements.txt        # Bob V2 dependencies
└── README.md              # This file
```

---

## Key Features

### ✅ Declarative Templates
- **Parameterized YAML** files with placeholders like `{APP_NAME}`, `{NAMESPACE}`, `{IMAGE}`
- **Reusable** for any application without code changes
- **Separation of concerns**: Templates define infrastructure, code handles logic

### ✅ Dynamic Deployment
- Deploy **any application** by providing parameters
- **Create or update** resources automatically
- **Multi-tenant** support for different namespaces

### ✅ Industry Best Practice
- Follows Kubernetes/OpenShift standards
- Uses OpenShift API directly (no hardcoded values)
- Template-driven approach (like Helm/Kustomize)

---

## How It Works

### Command Format
```bash
/deploy <namespace> <app-name> <image> [replicas] [port]
```

### Example
```bash
/deploy production hello-world python:3.9-slim 2 5000
```

This will:
1. Load templates from `templates/` folder
2. Replace placeholders with provided values
3. Apply deployment, service, and route to OpenShift
4. Create or update resources as needed

---

## Testing the System

### Step 1: Build Test Application Image

First, build and push the test application to a registry:

```bash
# Navigate to test-app folder
cd bob-test-app/test-app

# Build the image
docker build -t <your-registry>/test-app:v1 .

# Push to registry (or use OpenShift internal registry)
docker push <your-registry>/test-app:v1
```

**OR use OpenShift BuildConfig:**

```bash
# Create BuildConfig for test app
oc new-build --name=test-app \
  --binary \
  --strategy=docker \
  -n production

# Start build from local directory
oc start-build test-app \
  --from-dir=bob-test-app/test-app \
  --follow \
  -n production
```

### Step 2: Deploy Bob V2 (Optional - for testing)

If you want to test Bob V2 separately from the current Bob:

```bash
# Create ConfigMap with templates
oc create configmap bob-v2-templates \
  --from-file=bob-test-app/templates/ \
  -n production

# Create ConfigMap with orchestrator code
oc create configmap bob-v2-code \
  --from-file=orchestrator.py=bob-test-app/orchestrator-v2.py \
  -n production

# Deploy Bob V2 (similar to current Bob deployment)
# ... (deployment manifest needed)
```

### Step 3: Test Deployment via Bob

**Using the test application image:**

```bash
# Deploy test app via Bob
curl -k -X POST \
  https://bob-orchestrator-production.apps.itz-gkg33y.infra01-lb.tok04.techzone.ibm.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "text": "/deploy production test-app image-registry.openshift-image-registry.svc:5000/production/test-app:latest 2 5000"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Application test-app deployed successfully",
  "app_name": "test-app",
  "namespace": "production",
  "image": "image-registry.openshift-image-registry.svc:5000/production/test-app:latest",
  "method": "declarative-templates",
  "results": [
    {"resource": "deployment", "success": true, "message": "..."},
    {"resource": "service", "success": true, "message": "..."},
    {"resource": "route", "success": true, "message": "..."}
  ]
}
```

### Step 4: Verify Deployment

```bash
# Check deployment
oc get deployment test-app -n production

# Check pods
oc get pods -l app=test-app -n production

# Check service
oc get svc test-app -n production

# Check route
oc get route test-app -n production

# Get application URL
TEST_APP_URL=$(oc get route test-app -n production -o jsonpath='{.spec.host}')
echo "Test App URL: https://$TEST_APP_URL"

# Test the application
curl -k https://$TEST_APP_URL/
curl -k https://$TEST_APP_URL/health
```

### Step 5: Test with Different Applications

Deploy another app with different parameters:

```bash
curl -k -X POST \
  https://bob-orchestrator-production.apps.itz-gkg33y.infra01-lb.tok04.techzone.ibm.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "text": "/deploy production my-nginx nginx:alpine 3 80"
  }'
```

---

## Cleanup

To remove the test application:

```bash
# Delete all resources
oc delete deployment test-app -n production
oc delete service test-app -n production
oc delete route test-app -n production

# Or delete the entire folder
cd ..
rm -rf bob-test-app
```

---

## Advantages Over Hardcoded Approach

### ❌ Old Way (Hardcoded)
```python
deployment_name = "python-app"  # Fixed!
# Can only deploy one specific app
```

### ✅ New Way (Template-Based)
```python
# Load template
template = load_template("deployment")
# Inject any app name
manifest = render_template(template, {"APP_NAME": "any-app"})
# Deploy any application!
```

---

## Architecture Benefits

1. **Scalability**: Deploy unlimited apps without code changes
2. **Maintainability**: Update templates, not Python code
3. **Reusability**: Same templates for all applications
4. **Flexibility**: Easy to add new resource types
5. **Best Practice**: Industry-standard declarative approach

---

## Next Steps

1. ✅ Test with the sample application
2. ✅ Verify all resources are created
3. ✅ Test with different images/parameters
4. ✅ Integrate into main Bob if successful
5. ✅ Add more templates (ConfigMap, Secret, etc.)

---

## Notes

- This is a **safe test environment** - can be deleted without affecting current Bob
- Templates follow **OpenShift/Kubernetes standards**
- Code follows **industry best practices** for orchestration
- Ready for **production use** after testing

---

**Created by Bob - Industry Best Practice Implementation** 🚀