# 🚀 Bob Web UI - Quick Start Guide

Get the Bob Web UI up and running in 5 minutes!

## 📋 Prerequisites

- OpenShift cluster with Jenkins
- GitHub account with personal access token
- `oc` CLI tool installed and logged in

## ⚡ Quick Deploy to OpenShift

### Step 1: Create Secret

```bash
# Generate a random secret key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Create secret in OpenShift
oc create secret generic bob-web-ui-secret \
  --from-literal=secret-key="$SECRET_KEY" \
  -n production
```

### Step 2: Deploy the Application

```bash
# Navigate to web-ui directory
cd web-ui

# Apply all Kubernetes manifests
oc apply -f k8s/

# Wait for deployment to be ready
oc rollout status deployment/bob-web-ui -n production
```

### Step 3: Get the URL

```bash
# Get the route URL
oc get route bob-web-ui -n production -o jsonpath='{.spec.host}'
```

### Step 4: Access the UI

Open the URL in your browser and start deploying! 🎉

## 🧪 Local Development

### Step 1: Install Dependencies

```bash
cd web-ui
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

```bash
export SECRET_KEY="dev-secret-key"
export OPENSHIFT_TOKEN="your-token-here"  # Get from: oc whoami -t
export OPENSHIFT_API_URL="https://api.your-cluster.com:6443"
```

### Step 3: Run the Server

```bash
python app.py
```

Visit `http://localhost:8080` in your browser.

## 📝 First Deployment

### 1. Prepare Your App

Create a simple Flask app (`app.py`):

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Hello from Bob!"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 2. Get GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Copy the token (starts with `ghp_`)

### 3. Fill the Form

Open Bob Web UI and fill in:

- **App Name**: `my-first-app`
- **App Port**: `5000`
- **Health Check Path**: `/health`
- **Replicas**: `2`
- **GitHub Repo**: `https://github.com/your-username/your-repo.git`
- **GitHub Branch**: `main`
- **GitHub Token**: `ghp_your_token_here`
- **OpenShift Namespace**: `production`
- **OpenShift Cluster**: `apps.your-cluster.com`
- **Python Version**: `3.11`
- **Upload**: Your `app.py` file

### 4. Deploy!

Click "Deploy Now" and watch the magic happen! ✨

## 🎯 What Happens Next?

1. **Analyzing** (10%) - Bob analyzes your app.py for dependencies
2. **Generating** (30%) - Creates Dockerfile, Jenkinsfile, K8s manifests
3. **Committing** (50%) - Pushes files to your GitHub repo
4. **Configuring** (70%) - Applies BuildConfig to OpenShift
5. **Building** (90%) - Jenkins builds your Docker image
6. **Deploying** (100%) - App is deployed and health checked

Total time: ~2-3 minutes ⚡

## 🔍 Verify Deployment

```bash
# Check pods
oc get pods -n production -l app=my-first-app

# Check service
oc get svc my-first-app -n production

# Check route
oc get route my-first-app -n production

# Test the app
curl https://my-first-app-production.apps.your-cluster.com/health
```

## 🐛 Troubleshooting

### Issue: "GitHub commit failed"

**Solution**: Check your GitHub token has `repo` permissions

```bash
# Test token
curl -H "Authorization: token ghp_your_token" https://api.github.com/user
```

### Issue: "BuildConfig apply failed"

**Solution**: Ensure service account has proper RBAC

```bash
# Grant permissions
oc adm policy add-role-to-user edit system:serviceaccount:production:jenkins-sa -n production
```

### Issue: "Cannot connect to OpenShift API"

**Solution**: Check service account token

```bash
# Verify token exists
oc get secret -n production | grep jenkins-sa
```

### Issue: "Health check failed"

**Solution**: Ensure your app has the health endpoint

```python
@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200
```

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [example apps](../examples/) for more complex deployments
- Join our community for support

## 🎉 Success!

Your app should now be live at:
```
https://my-first-app-production.apps.your-cluster.com
```

Happy deploying! 🚀

---

**Need help?** Open an issue on GitHub or contact support.