# 🚀 Bob Template Generator

**Auto-generate all deployment files from just your `app.py` and a simple `.env` configuration!**

This template generator creates a complete CI/CD pipeline for deploying Python applications to OpenShift via Jenkins, triggered by Bob orchestrator.

---

## ✨ Features

- **Zero Boilerplate**: Write only your application logic
- **Auto-Dependency Detection**: Automatically detects Python packages from imports
- **One Config File**: All settings in `.env`
- **Complete Pipeline**: Generates Dockerfile, Jenkinsfile, Kubernetes manifests, and BuildConfig
- **Best Practices**: Production-ready templates with health checks, resource limits, and proper labels
- **Bob Integration**: Ready to deploy via Bob orchestrator webhook

---

## 📋 Prerequisites

- Python 3.7+
- OpenShift CLI (`oc`) installed and logged in
- Bob orchestrator deployed on OpenShift
- GitHub repository for your application
- Your Python application (`app.py`)

---

## 🚀 Quick Start

### Step 1: Create Your Application

```bash
# Create your app directory
mkdir my-awesome-app
cd my-awesome-app

# Write your Flask application
cat > app.py << 'EOF'
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({'message': 'Hello from My Awesome App!'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
```

### Step 2: Download Template Generator

```bash
# Download the generator
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/generate.py
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/.env.example

# Download templates directory
mkdir -p templates/k8s
cd templates
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/templates/Dockerfile.template
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/templates/Jenkinsfile.template
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/templates/buildconfig.yaml.template
cd k8s
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/templates/k8s/deployment.yaml.template
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/templates/k8s/service.yaml.template
curl -O https://raw.githubusercontent.com/your-org/bob-template-generator/main/templates/k8s/route.yaml.template
cd ../..
```

**OR** clone the entire repository:

```bash
git clone https://github.com/your-org/bob-template-generator.git
cp -r bob-template-generator/templates .
cp bob-template-generator/generate.py .
cp bob-template-generator/.env.example .env
```

### Step 3: Configure Your Application

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your values
nano .env
```

**Example `.env`:**

```bash
# Application Configuration
APP_NAME=my-awesome-app
APP_PORT=5000
REPLICAS=2
HEALTH_CHECK_PATH=/health

# GitHub Configuration
GITHUB_REPO=https://github.com/myuser/my-awesome-app.git
GITHUB_BRANCH=main

# OpenShift Configuration
OPENSHIFT_NAMESPACE=production
OPENSHIFT_CLUSTER=apps.my-cluster.com

# Python Configuration
PYTHON_VERSION=3.11
```

### Step 4: Generate All Files

```bash
# Run the generator
python generate.py
```

**Output:**
```
============================================================
🚀 Bob Template Generator
============================================================
📖 Loading configuration from .env...
✓ Configuration loaded successfully
  App Name: my-awesome-app
  Namespace: production
  GitHub: https://github.com/myuser/my-awesome-app.git

🔍 Analyzing app.py for dependencies...
✓ Found 1 external dependencies:
  - Flask==3.0.0

📝 Generating requirements.txt...
✓ Created requirements.txt

📦 Generating deployment files...
📝 Generating Dockerfile...
✓ Created Dockerfile
📝 Generating Jenkinsfile...
✓ Created Jenkinsfile
📝 Generating buildconfig.yaml...
✓ Created buildconfig.yaml
📝 Generating k8s/deployment.yaml...
✓ Created k8s/deployment.yaml
📝 Generating k8s/service.yaml...
✓ Created k8s/service.yaml
📝 Generating k8s/route.yaml...
✓ Created k8s/route.yaml

============================================================
✅ All files generated successfully!
============================================================
```

### Step 5: Review Generated Files

Your directory now contains:

```
my-awesome-app/
├── app.py                    # Your application (you wrote this)
├── .env                      # Configuration (you filled this)
├── requirements.txt          # Auto-generated dependencies
├── Dockerfile               # Auto-generated container image
├── Jenkinsfile              # Auto-generated CI/CD pipeline
├── buildconfig.yaml         # Auto-generated OpenShift config
└── k8s/
    ├── deployment.yaml      # Auto-generated Kubernetes deployment
    ├── service.yaml         # Auto-generated Kubernetes service
    └── route.yaml           # Auto-generated OpenShift route
```

### Step 6: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit with deployment configuration"
git remote add origin https://github.com/myuser/my-awesome-app.git
git push -u origin main
```

### Step 7: Deploy to OpenShift

```bash
# Apply the BuildConfig
oc apply -f buildconfig.yaml

# Trigger deployment via Bob
curl -k -X POST https://bob-orchestrator-production.apps.my-cluster.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"text": "/pipeline my-awesome-app-pipeline production"}'
```

### Step 8: Monitor and Access

```bash
# Watch the build
oc get builds -n production -w

# Check deployment status
oc get pods -l app=my-awesome-app -n production

# Get the application URL
oc get route my-awesome-app -n production -o jsonpath='{.spec.host}'

# Test your application
curl https://my-awesome-app-production.apps.my-cluster.com/
curl https://my-awesome-app-production.apps.my-cluster.com/health
```

---

## 📁 Generated Files Explained

### `requirements.txt`
Auto-detected Python dependencies from your `app.py` imports.

### `Dockerfile`
Multi-stage Docker build with:
- Python base image
- Dependency installation
- Health checks
- Proper port exposure

### `Jenkinsfile`
Complete CI/CD pipeline with:
- Source checkout
- Image build
- Deployment to OpenShift
- Health verification
- Automatic rollback on failure

### `buildconfig.yaml`
OpenShift BuildConfig with:
- Jenkins Pipeline integration
- Git source configuration
- Image stream definition

### `k8s/deployment.yaml`
Kubernetes Deployment with:
- Configurable replicas
- Resource limits
- Liveness and readiness probes
- Environment variables

### `k8s/service.yaml`
Kubernetes Service for internal routing

### `k8s/route.yaml`
OpenShift Route for external access with TLS

---

## 🔧 Configuration Options

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `APP_NAME` | Application name (lowercase, no spaces) | `my-app` |
| `APP_PORT` | Port your app listens on | `5000` |
| `REPLICAS` | Number of pod replicas | `2` |
| `HEALTH_CHECK_PATH` | Health check endpoint | `/health` |
| `GITHUB_REPO` | Git repository URL | `https://github.com/user/repo.git` |
| `GITHUB_BRANCH` | Git branch to deploy | `main` |
| `OPENSHIFT_NAMESPACE` | OpenShift namespace | `production` |
| `OPENSHIFT_CLUSTER` | OpenShift cluster domain | `apps.my-cluster.com` |
| `PYTHON_VERSION` | Python version | `3.11` |

### Optional: Custom Environment Variables

Add any environment variables your app needs in `.env`:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
API_KEY=your-secret-key
REDIS_URL=redis://redis:6379/0
```

These will be automatically added to your deployment.

---

## 🎯 Use Cases

### Simple Flask API
```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    return jsonify({'data': [1, 2, 3]})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### FastAPI Application
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### Database-Connected App
```python
from flask import Flask
from sqlalchemy import create_engine
import os

app = Flask(__name__)
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

@app.route('/users')
def get_users():
    # Query database
    return {'users': []}

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## 🐛 Troubleshooting

### Dependencies Not Detected

If the generator doesn't detect all your dependencies:

1. Manually edit `requirements.txt` after generation
2. Add missing packages with versions

### Build Fails

Check the build logs:
```bash
oc logs -f build/my-app-1
```

Common issues:
- Missing dependencies in requirements.txt
- Syntax errors in app.py
- Port mismatch in configuration

### Deployment Fails

Check pod logs:
```bash
oc logs -f deployment/my-app
```

Common issues:
- Health check endpoint not responding
- Wrong port configuration
- Missing environment variables

### Health Check Fails

Ensure your app has a `/health` endpoint:
```python
@app.route('/health')
def health():
    return {'status': 'healthy'}
```

---

## 🔄 Updating Your Application

1. Make changes to `app.py`
2. Commit and push to GitHub
3. Trigger new deployment via Bob:
   ```bash
   curl -k -X POST https://bob-orchestrator-production.apps.my-cluster.com/webhook \
     -H "Content-Type: application/json" \
     -d '{"text": "/pipeline my-app-pipeline production"}'
   ```

---

## 📚 Advanced Usage

### Multiple Environments

Create separate `.env` files:
- `.env.dev` - Development
- `.env.staging` - Staging
- `.env.production` - Production

Generate for each environment:
```bash
python generate.py --config .env.dev
python generate.py --config .env.staging
python generate.py --config .env.production
```

### Custom Templates

Modify templates in the `templates/` directory to match your organization's standards.

### CI/CD Integration

Integrate with your existing CI/CD:
```bash
# In your CI pipeline
python generate.py
git add .
git commit -m "Update deployment config"
git push
```

---

## 🤝 Contributing

Contributions welcome! Please submit pull requests or open issues.

---

## 📄 License

MIT License - feel free to use in your projects!

---

## 🎉 Credits

Created for Bob Orchestrator - Making OpenShift deployments simple and automated!

---

**Happy Deploying! 🚀**