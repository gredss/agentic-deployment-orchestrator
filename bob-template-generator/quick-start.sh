#!/bin/bash

# Bob Template Generator - Quick Start Script
# This script helps you get started quickly with a new application

set -e

echo "============================================================"
echo "🚀 Bob Template Generator - Quick Start"
echo "============================================================"
echo ""

# Check if app.py exists
if [ -f "app.py" ]; then
    echo "✓ Found app.py"
else
    echo "❌ app.py not found!"
    echo ""
    echo "Would you like to create an example app.py? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        cp example-app.py app.py
        echo "✓ Created app.py from example"
        echo "  You can now customize it for your needs"
    else
        echo "Please create an app.py file first"
        exit 1
    fi
fi

# Check if .env exists
if [ -f ".env" ]; then
    echo "✓ Found .env configuration"
else
    echo "❌ .env not found!"
    echo ""
    if [ -f ".env.example" ]; then
        echo "Copying .env.example to .env..."
        cp .env.example .env
        echo "✓ Created .env from example"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env and fill in your values:"
        echo "   - APP_NAME"
        echo "   - GITHUB_REPO"
        echo "   - OPENSHIFT_NAMESPACE"
        echo "   - OPENSHIFT_CLUSTER"
        echo ""
        echo "Press Enter when you're done editing .env..."
        read -r
    else
        echo "Please create a .env file with your configuration"
        exit 1
    fi
fi

# Run the generator
echo ""
echo "============================================================"
echo "📦 Generating deployment files..."
echo "============================================================"
echo ""

python3 generate.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Success! Your deployment files are ready"
    echo "============================================================"
    echo ""
    echo "📋 Generated files:"
    echo "   ✓ Dockerfile"
    echo "   ✓ Jenkinsfile"
    echo "   ✓ buildconfig.yaml"
    echo "   ✓ requirements.txt"
    echo "   ✓ k8s/deployment.yaml"
    echo "   ✓ k8s/service.yaml"
    echo "   ✓ k8s/route.yaml"
    echo ""
    echo "🚀 Next steps:"
    echo ""
    echo "1. Review the generated files"
    echo "2. Initialize git repository (if not already done):"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo ""
    echo "3. Push to GitHub:"
    echo "   git remote add origin YOUR_GITHUB_REPO"
    echo "   git push -u origin main"
    echo ""
    echo "4. Apply BuildConfig to OpenShift:"
    echo "   oc apply -f buildconfig.yaml"
    echo ""
    echo "5. Trigger deployment via Bob:"
    echo "   curl -k -X POST https://bob-orchestrator-production.apps.your-cluster.com/webhook \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"text\": \"/pipeline YOUR_APP_NAME-pipeline production\"}'"
    echo ""
    echo "============================================================"
else
    echo ""
    echo "❌ Generation failed. Please check the error messages above."
    exit 1
fi

# Made with Bob
