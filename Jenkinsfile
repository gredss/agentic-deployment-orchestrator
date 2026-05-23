#!/usr/bin/env groovy

/**
 * Jenkins Pipeline for Python Flask Application Deployment to OpenShift
 * 
 * This pipeline implements a complete CI/CD workflow:
 * 1. Checkout source code from Git
 * 2. Build Docker image
 * 3. Push image to OpenShift internal registry
 * 4. Deploy to OpenShift production namespace
 * 5. Verify deployment health
 * 6. Rollback on failure
 */

pipeline {
    agent any
    
    // Environment variables
    environment {
        // OpenShift configuration
        OPENSHIFT_PROJECT = 'production'
        OPENSHIFT_DEV_PROJECT = 'development'
        
        // Application configuration
        APP_NAME = 'python-app'
        APP_VERSION = "${env.BUILD_NUMBER}"
        
        // Git repository
        GIT_REPO = 'https://github.com/gredss/agentic-deployment-orchestrator'
        GIT_BRANCH = 'main'
        
        // Image registry
        IMAGE_REGISTRY = 'image-registry.openshift-image-registry.svc:5000'
        IMAGE_NAME = "${IMAGE_REGISTRY}/${OPENSHIFT_PROJECT}/${APP_NAME}"
        IMAGE_TAG = "v${APP_VERSION}"
        
        // Deployment configuration
        REPLICAS = '2'
        HEALTH_CHECK_TIMEOUT = '300'
        
        // Rollback flag
        DEPLOYMENT_SUCCESSFUL = 'false'
    }
    
    // Pipeline options
    options {
        // Keep only last 10 builds
        buildDiscarder(logRotator(numToKeepStr: '10'))
        
        // Timeout for entire pipeline
        timeout(time: 30, unit: 'MINUTES')
        
        // Disable concurrent builds
        disableConcurrentBuilds()
    }
    
    // Pipeline stages
    stages {
        
        stage('Initialize') {
            steps {
                script {
                    echo "=========================================="
                    echo "Pipeline Initialization"
                    echo "=========================================="
                    echo "Build Number: ${env.BUILD_NUMBER}"
                    echo "Build ID: ${env.BUILD_ID}"
                    echo "Job Name: ${env.JOB_NAME}"
                    echo "Workspace: ${env.WORKSPACE}"
                    echo "OpenShift Project: ${OPENSHIFT_PROJECT}"
                    echo "Application: ${APP_NAME}"
                    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
                    echo "=========================================="
                }
            }
        }
        
        stage('Checkout') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 1: Checkout Source Code"
                    echo "=========================================="
                    
                    // Clean workspace using deleteDir
                    deleteDir()
                    
                    // Checkout code from Git
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "*/${GIT_BRANCH}"]],
                        userRemoteConfigs: [[url: "${GIT_REPO}"]]
                    ])
                    
                    echo "✓ Source code checked out successfully"
                    
                    // List files
                    sh 'ls -la'
                }
            }
        }
        
        stage('Deploy to OpenShift') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 2: Deploy to OpenShift (No Build Required)"
                    echo "=========================================="
                    
                    // Switch to production namespace
                    sh """
                        oc project ${OPENSHIFT_PROJECT}
                        echo "✓ Switched to project: ${OPENSHIFT_PROJECT}"
                    """
                    
                    echo "Applying ConfigMap (production only)..."
                    sh """
                        oc apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: python-app-config
  namespace: production
data:
  APP_VERSION: "1.0.0"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
EOF
                    """
                    
                    echo "Deploying application..."
                    sh """
                        oc apply -f k8s/03-deployment-simple.yaml -n ${OPENSHIFT_PROJECT}
                    """
                    
                    echo "Applying Service..."
                    sh """
                        oc apply -f k8s/04-service.yaml -n ${OPENSHIFT_PROJECT}
                    """
                    
                    echo "Applying Route..."
                    sh """
                        oc apply -f k8s/05-route.yaml -n ${OPENSHIFT_PROJECT}
                    """
                    
                    echo "✓ Deployment configuration applied"
                }
            }
        }
        
        stage('Wait for Rollout') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 3: Wait for Deployment Rollout"
                    echo "=========================================="
                    
                    // Wait for rollout to complete (longer timeout for image pull + pip install)
                    timeout(time: 15, unit: 'MINUTES') {
                        sh """
                            oc rollout status deployment/${APP_NAME} \
                                -n ${OPENSHIFT_PROJECT} \
                                --timeout=15m
                        """
                    }
                    
                    echo "✓ Rollout completed successfully"
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 4: Verify Deployment Health"
                    echo "=========================================="
                    
                    // Get pod status
                    sh """
                        echo "=== Pod Status ==="
                        oc get pods -l app=${APP_NAME} -n ${OPENSHIFT_PROJECT}
                    """
                    
                    // Get deployment status
                    sh """
                        echo "=== Deployment Status ==="
                        oc get deployment ${APP_NAME} -n ${OPENSHIFT_PROJECT}
                    """
                    
                    // Get service
                    sh """
                        echo "=== Service ==="
                        oc get svc ${APP_NAME} -n ${OPENSHIFT_PROJECT}
                    """
                    
                    // Get route URL
                    def routeUrl = sh(
                        script: "oc get route ${APP_NAME} -n ${OPENSHIFT_PROJECT} -o jsonpath='{.spec.host}'",
                        returnStdout: true
                    ).trim()
                    
                    echo "=== Route URL ==="
                    echo "Application URL: https://${routeUrl}"
                    
                    // Wait for pods to be ready
                    sleep(time: 15, unit: 'SECONDS')
                    
                    // Health check
                    echo "=== Health Check ==="
                    def healthCheckPassed = false
                    def maxRetries = 10
                    def retryCount = 0
                    
                    while (!healthCheckPassed && retryCount < maxRetries) {
                        try {
                            sh """
                                curl -f -k https://${routeUrl}/health
                            """
                            healthCheckPassed = true
                            echo "✓ Health check passed"
                        } catch (Exception e) {
                            retryCount++
                            echo "Health check attempt ${retryCount}/${maxRetries} failed, retrying..."
                            sleep(time: 10, unit: 'SECONDS')
                        }
                    }
                    
                    if (!healthCheckPassed) {
                        error("Health check failed after ${maxRetries} attempts")
                    }
                    
                    // Mark deployment as successful
                    env.DEPLOYMENT_SUCCESSFUL = 'true'
                    
                    echo "✓ All health checks passed"
                }
            }
        }
        
        stage('Output Information') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 5: Deployment Information"
                    echo "=========================================="
                    
                    def routeUrl = sh(
                        script: "oc get route ${APP_NAME} -n ${OPENSHIFT_PROJECT} -o jsonpath='{.spec.host}'",
                        returnStdout: true
                    ).trim()
                    
                    echo """
                    ╔════════════════════════════════════════════════════════════╗
                    ║           DEPLOYMENT COMPLETED SUCCESSFULLY                ║
                    ╠════════════════════════════════════════════════════════════╣
                    ║ Application:     ${APP_NAME}
                    ║ Version:         Build ${APP_VERSION}
                    ║ Namespace:       ${OPENSHIFT_PROJECT}
                    ║ Replicas:        ${REPLICAS}
                    ║ Note:            Using public Python image (no registry)
                    ║
                    ║ Application URL: https://${routeUrl}
                    ║ Health Check:    https://${routeUrl}/health
                    ║                                                            
                    ║ Build Number:    ${env.BUILD_NUMBER}                       
                    ║ Build Time:      ${new Date()}                             
                    ╚════════════════════════════════════════════════════════════╝
                    """
                }
            }
        }
    }
    
    // Post-build actions
    post {
        success {
            script {
                echo "=========================================="
                echo "Pipeline Completed Successfully! ✓"
                echo "=========================================="
                
                // Optional: Send notification
                // slackSend(
                //     color: 'good',
                //     message: "Deployment successful: ${APP_NAME} v${IMAGE_TAG} to ${OPENSHIFT_PROJECT}"
                // )
            }
        }
        
        failure {
            script {
                echo "=========================================="
                echo "Pipeline Failed! ✗"
                echo "=========================================="
                
                // Rollback if deployment was started but failed
                if (env.DEPLOYMENT_SUCCESSFUL != 'true') {
                    echo "Attempting rollback..."
                    
                    try {
                        sh """
                            oc rollout undo deployment/${APP_NAME} -n ${OPENSHIFT_PROJECT}
                            oc rollout status deployment/${APP_NAME} -n ${OPENSHIFT_PROJECT}
                        """
                        echo "✓ Rollback completed"
                    } catch (Exception e) {
                        echo "✗ Rollback failed: ${e.message}"
                    }
                }
                
                // Get logs for debugging
                sh """
                    echo "=== Recent Pod Logs ==="
                    oc logs -l app=${APP_NAME} --tail=50 -n ${OPENSHIFT_PROJECT} || true
                """
                
                // Optional: Send notification
                // slackSend(
                //     color: 'danger',
                //     message: "Deployment failed: ${APP_NAME} v${IMAGE_TAG} to ${OPENSHIFT_PROJECT}"
                // )
            }
        }
        
        always {
            script {
                echo "=========================================="
                echo "Pipeline Cleanup"
                echo "=========================================="
                
                // Archive build artifacts
                // archiveArtifacts artifacts: '**/target/*.jar', allowEmptyArchive: true
                
                // Clean workspace
                // cleanWs()
            }
        }
    }
}

// Made with Bob
