# 🚀 Bob Web UI - OpenShift Deployment Generator

A beautiful, user-friendly web interface for deploying Python applications to OpenShift with just a few clicks!

## ✨ Features

- **🎨 Modern UI**: Clean, intuitive interface with real-time progress tracking
- **📤 Drag & Drop**: Easy file upload with drag-and-drop support
- **🔄 Real-time Updates**: Live deployment status via WebSockets
- **🤖 Auto-Detection**: Automatically detects Python dependencies
- **📝 Template Generation**: Generates all deployment files automatically
- **🔗 GitHub Integration**: Commits files directly to your repository
- **☁️ OpenShift Native**: Full OpenShift API integration
- **📊 Progress Tracking**: Visual progress bar and step-by-step status
- **📱 Responsive**: Works on desktop, tablet, and mobile

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
│  (User UI)  │
└──────┬──────┘
       │ HTTP/WebSocket
       ▼
┌─────────────┐
│  Flask App  │
│  (Backend)  │
└──────┬──────┘
       │
       ├──► GitHub API (Commit files)
       ├──► OpenShift API (Apply configs)
       └──► Jenkins (Trigger pipeline)
```

## 📋 Prerequisites

- Python 3.9+
- OpenShift cluster access
- GitHub account with personal access token
- Jenkins integrated with OpenShift

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd web-ui
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export SECRET_KEY="your-secret-key-here"
export OPENSHIFT_TOKEN="your-openshift-token"  # Optional for local testing
export OPENSHIFT_API_URL="https://api.your-cluster.com:6443"
```

### 3. Run Locally

```bash
python app.py
```

The application will be available at `http://localhost:8080`

### 4. Deploy to OpenShift

```bash
# Build and deploy
oc new-app python:3.11~https://github.com/your-org/bob-jenkins-os.git \
  --context-dir=web-ui \
  --name=bob-web-ui

# Expose the service
oc expose svc/bob-web-ui

# Get the URL
oc get route bob-web-ui
```

## 📁 Project Structure

```
web-ui/
├── app.py                          # Flask backend server
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── Dockerfile                      # Container image definition
├── .gitignore                      # Git ignore rules
│
├── templates/                      # HTML templates
│   ├── index.html                  # Main form page
│   └── status.html                 # Deployment status page
│
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css              # Styling
│   ├── js/
│   │   ├── app.js                 # Form handling
│   │   └── deploy.js              # Status page logic
│   └── img/
│       └── logo.png               # Logo (optional)
│
├── deployment-templates/           # Deployment file templates
│   ├── Dockerfile.template
│   ├── Jenkinsfile.template
│   ├── buildconfig.yaml.template
│   ├── deployment.yaml.template
│   ├── service.yaml.template
│   └── route.yaml.template
│
└── k8s/                           # Kubernetes manifests for web-ui itself
    ├── deployment.yaml
    ├── service.yaml
    └── route.yaml
```

## 🎯 How It Works

### User Workflow

1. **Fill Form**: User enters application details
2. **Upload File**: User uploads their `app.py`
3. **Submit**: User clicks "Deploy Now"
4. **Watch Progress**: Real-time status updates
5. **Get URL**: Application URL when deployment completes

### Backend Process

1. **Analyze**: Parse `app.py` to detect dependencies
2. **Generate**: Create all deployment files from templates
3. **Commit**: Push files to GitHub repository
4. **Configure**: Apply BuildConfig to OpenShift
5. **Build**: Trigger Jenkins pipeline
6. **Deploy**: Jenkins builds and deploys the application
7. **Verify**: Health check confirms deployment success

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `PORT` | Server port | No | 8080 |
| `OPENSHIFT_TOKEN` | OpenShift API token | No* | Auto-detected from service account |
| `OPENSHIFT_API_URL` | OpenShift API endpoint | No | `https://kubernetes.default.svc` |

*Not required when running in OpenShift with service account

### Form Fields

| Field | Description | Example | Required |
|-------|-------------|---------|----------|
| App Name | Application name (lowercase, hyphens) | `my-api` | Yes |
| App Port | Port your app listens on | `5000` | Yes |
| Health Check Path | Health endpoint | `/health` | No |
| Replicas | Number of pods | `2` | No |
| GitHub Repo | Repository URL | `https://github.com/user/repo.git` | Yes |
| GitHub Branch | Git branch | `main` | No |
| GitHub Token | Personal access token | `ghp_xxx...` | Yes |
| OpenShift Namespace | Target namespace | `production` | Yes |
| OpenShift Cluster | Cluster domain | `apps.cluster.com` | Yes |
| Python Version | Python runtime | `3.11` | No |
| app.py | Your application file | - | Yes |

## 🎨 UI Features

### Main Form (`/`)

- **Smart Validation**: Real-time input validation
- **Drag & Drop**: Upload files by dragging
- **Auto-format**: Automatically formats GitHub URLs
- **Tooltips**: Helpful hints for each field
- **Responsive**: Mobile-friendly design

### Status Page (`/status/<deployment_id>`)

- **Progress Bar**: Visual progress indicator (0-100%)
- **Step Tracking**: Shows current deployment step
- **Live Logs**: Real-time log streaming
- **Success/Failure**: Clear result display
- **Copy URL**: One-click URL copying
- **Auto-refresh**: Polls for updates if WebSocket fails

## 🔌 API Endpoints

### `POST /api/deploy`

Deploy a new application.

**Request**: `multipart/form-data`
- Form fields (see Configuration section)
- File: `app_py`

**Response**:
```json
{
  "deployment_id": "abc12345",
  "status": "started"
}
```

### `GET /api/status/<deployment_id>`

Get deployment status.

**Response**:
```json
{
  "id": "abc12345",
  "status": "building",
  "progress": 75,
  "logs": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "message": "Building Docker image..."
    }
  ],
  "url": "https://my-app-production.apps.cluster.com",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## 🔐 Security

### Best Practices

1. **Never commit tokens**: GitHub tokens are never stored permanently
2. **HTTPS only**: Always use HTTPS in production
3. **Input validation**: All inputs are validated and sanitized
4. **RBAC**: Uses OpenShift service account with minimal permissions
5. **Session management**: Secure session handling
6. **Rate limiting**: Prevent abuse (implement in production)

### GitHub Token Permissions

Required scopes:
- `repo` - Full repository access
- `workflow` - Update GitHub Actions workflows (optional)

### OpenShift Permissions

Required RBAC:
```yaml
rules:
- apiGroups: ["build.openshift.io"]
  resources: ["buildconfigs", "builds"]
  verbs: ["get", "list", "create", "update"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list", "create"]
- apiGroups: ["route.openshift.io"]
  resources: ["routes"]
  verbs: ["get", "list", "create"]
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Connection error" in status page
- **Solution**: Check WebSocket connection, fallback to polling is automatic

**Issue**: "GitHub commit failed"
- **Solution**: Verify GitHub token has `repo` permissions

**Issue**: "BuildConfig apply failed"
- **Solution**: Check OpenShift service account has proper RBAC

**Issue**: "Health check failed"
- **Solution**: Ensure your app has the health endpoint configured

### Debug Mode

Enable debug logging:
```python
# In app.py
app.config['DEBUG'] = True
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Monitoring

### Deployment Status

- `initializing` - Starting deployment
- `analyzing` - Analyzing dependencies
- `generating` - Generating files
- `committing` - Committing to GitHub
- `configuring` - Applying BuildConfig
- `building` - Building Docker image
- `deploying` - Deploying to OpenShift
- `completed` - Deployment successful
- `failed` - Deployment failed

### Logs

All deployment logs are:
- Displayed in real-time in the UI
- Stored in memory (use Redis in production)
- Timestamped for debugging

## 🚀 Production Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "app:app"]
```

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Use production WSGI server (gunicorn)
- [ ] Enable HTTPS
- [ ] Configure rate limiting
- [ ] Set up Redis for session storage
- [ ] Configure logging to external service
- [ ] Set resource limits
- [ ] Enable monitoring/alerting
- [ ] Configure backup strategy
- [ ] Document disaster recovery

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Flask framework
- Socket.IO for real-time updates
- OpenShift for container orchestration
- GitHub for version control

## 📞 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-org/bob-jenkins-os/issues)
- Documentation: [Full docs](https://docs.example.com)
- Email: support@example.com

---

**Made with ❤️ by the Bob Team** 🤖