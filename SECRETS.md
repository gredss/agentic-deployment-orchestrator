# Secrets Configuration Guide

This document explains how to configure secrets for the Bob Jenkins OS project.

## ⚠️ Important Security Notice

**NEVER commit actual secrets to version control!** This repository includes `.example` template files that should be copied and filled with your actual credentials locally.

## 🔐 Required Secrets

### 1. Bob Service Secrets (`bob/k8s/secret.yaml`)

**Template:** `bob/k8s/secret.yaml.example`

```bash
# Copy the template
cp bob/k8s/secret.yaml.example bob/k8s/secret.yaml

# Edit with your actual credentials
nano bob/k8s/secret.yaml
```

**Required values:**
- `openshift-token`: Your OpenShift service account token
  - Get it by running: `oc whoami -t`
  - Or from OpenShift Console: Click username → Copy login command
- `jenkins-user`: Jenkins username (e.g., `admin`)
- `jenkins-password`: Jenkins password
- `jenkins-token`: Jenkins API token
  - Generate from Jenkins: User → Configure → API Token → Add new Token

### 2. Web UI Secrets (`web-ui/k8s/secret.yaml`)

**Template:** `web-ui/k8s/secret.yaml.example`

```bash
# Copy the template
cp web-ui/k8s/secret.yaml.example web-ui/k8s/secret.yaml

# Edit with your actual secret key
nano web-ui/k8s/secret.yaml
```

**Required values:**
- `secret-key`: Base64 encoded Flask secret key
  ```bash
  # Generate and encode in one command
  echo -n "$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" | base64
  ```

### 3. Application Secrets (`k8s/02-configmap-secret.yaml`)

**Template:** `k8s/02-configmap-secret.yaml.example`

```bash
# Copy the template
cp k8s/02-configmap-secret.yaml.example k8s/02-configmap-secret.yaml

# Edit with your actual credentials
nano k8s/02-configmap-secret.yaml
```

**Required values (base64 encoded):**
- `API_KEY`: Your API key
  ```bash
  echo -n "your-api-key" | base64
  ```
- `DB_PASSWORD`: Database password
  ```bash
  echo -n "your-db-password" | base64
  ```
- `SECRET_TOKEN`: Application secret token
  ```bash
  echo -n "your-secret-token" | base64
  ```

## 📝 Quick Setup Script

```bash
#!/bin/bash
# setup-secrets.sh - Quick setup script for all secrets

echo "Setting up Bob Jenkins OS secrets..."

# 1. Bob service secrets
if [ ! -f bob/k8s/secret.yaml ]; then
    cp bob/k8s/secret.yaml.example bob/k8s/secret.yaml
    echo "✓ Created bob/k8s/secret.yaml - Please edit with your credentials"
else
    echo "⚠ bob/k8s/secret.yaml already exists"
fi

# 2. Web UI secrets
if [ ! -f web-ui/k8s/secret.yaml ]; then
    cp web-ui/k8s/secret.yaml.example web-ui/k8s/secret.yaml
    echo "✓ Created web-ui/k8s/secret.yaml - Please edit with your credentials"
else
    echo "⚠ web-ui/k8s/secret.yaml already exists"
fi

# 3. Application secrets
if [ ! -f k8s/02-configmap-secret.yaml ]; then
    cp k8s/02-configmap-secret.yaml.example k8s/02-configmap-secret.yaml
    echo "✓ Created k8s/02-configmap-secret.yaml - Please edit with your credentials"
else
    echo "⚠ k8s/02-configmap-secret.yaml already exists"
fi

echo ""
echo "Next steps:"
echo "1. Edit bob/k8s/secret.yaml with your OpenShift and Jenkins credentials"
echo "2. Edit web-ui/k8s/secret.yaml with your Flask secret key"
echo "3. Edit k8s/02-configmap-secret.yaml with your application credentials"
echo ""
echo "Remember: NEVER commit these files to git!"
```

## 🔒 Security Best Practices

1. **Never commit secrets to git**
   - The `.gitignore` file is configured to exclude all secret files
   - Only `.example` templates are tracked in version control

2. **Use strong, random values**
   - Generate secrets using cryptographically secure methods
   - Don't reuse passwords across environments

3. **Rotate credentials regularly**
   - Change tokens and passwords periodically
   - Update secrets in Kubernetes after rotation

4. **Use environment-specific secrets**
   - Different credentials for development, staging, and production
   - Never use production credentials in development

5. **Limit access**
   - Only authorized personnel should have access to production secrets
   - Use Kubernetes RBAC to control secret access

## 🚀 Deployment

After configuring your secrets:

```bash
# Apply secrets to your cluster
oc apply -f bob/k8s/secret.yaml
oc apply -f web-ui/k8s/secret.yaml
oc apply -f k8s/02-configmap-secret.yaml

# Verify secrets are created
oc get secrets -n production
```

## 🆘 Troubleshooting

### Secret not found
```bash
# Check if secret exists
oc get secret bob-secrets -n production

# Describe secret (won't show values)
oc describe secret bob-secrets -n production
```

### Invalid base64 encoding
```bash
# Decode to verify
echo "your-base64-string" | base64 -d

# Re-encode if needed
echo -n "your-value" | base64
```

### Token expired
```bash
# Get new OpenShift token
oc whoami -t

# Update secret
oc edit secret bob-secrets -n production
```

## 📚 Additional Resources

- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OpenShift Secrets Guide](https://docs.openshift.com/container-platform/latest/nodes/pods/nodes-pods-secrets.html)
- [Jenkins API Token](https://www.jenkins.io/doc/book/system-administration/authenticating-scripted-clients/)

---

**Made with Bob** 🤖