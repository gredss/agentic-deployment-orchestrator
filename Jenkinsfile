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
        
        stage('Build Image') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 2: Build Docker Image"
                    echo "=========================================="
                    
                    // Login to OpenShift
                    sh """
                        oc project ${OPENSHIFT_PROJECT}
                        echo "✓ Switched to project: ${OPENSHIFT_PROJECT}"
                    """
                    
                    echo "Building image from Dockerfile using oc new-app from Git..."
                    sh """
                        # Clean up existing resources
                        oc delete all -l app=${APP_NAME} -n ${OPENSHIFT_PROJECT} 2>/dev/null || true
                        sleep 3
                        
                        # Create app from Git repository (this handles the build properly)
                        oc new-app ${GIT_REPO} \
                            --name=${APP_NAME} \
                            --strategy=docker \
                            -n ${OPENSHIFT_PROJECT} || true
                        
                        # Wait for build to start
                        sleep 10
                        
                        # Follow the build logs
                        oc logs -f bc/${APP_NAME} -n ${OPENSHIFT_PROJECT} || true
                    """
                    
                    echo "✓ Image built successfully"
                }
            }
        }
        
        stage('Wait for Build') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 3: Wait for Build Completion"
                    echo "=========================================="
                    
                    // Wait for build to complete
                    timeout(time: 10, unit: 'MINUTES') {
                        sh """
                            # Wait for the build to complete
                            BUILD_NAME=\$(oc get builds -n ${OPENSHIFT_PROJECT} -l app=${APP_NAME} --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
                            echo "Waiting for build: \$BUILD_NAME"
                            
                            # Wait for build completion
                            oc wait --for=condition=Complete build/\$BUILD_NAME -n ${OPENSHIFT_PROJECT} --timeout=600s || \
                            oc wait --for=condition=Failed build/\$BUILD_NAME -n ${OPENSHIFT_PROJECT} --timeout=10s
                            
                            # Check build status
                            BUILD_STATUS=\$(oc get build \$BUILD_NAME -n ${OPENSHIFT_PROJECT} -o jsonpath='{.status.phase}')
                            echo "Build status: \$BUILD_STATUS"
                            
                            if [ "\$BUILD_STATUS" != "Complete" ]; then
                                echo "Build failed with status: \$BUILD_STATUS"
                                oc logs build/\$BUILD_NAME -n ${OPENSHIFT_PROJECT}
                                exit 1
                            fi
                        """
                    }
                    
                    echo "✓ Build completed successfully"
                }
            }
        }
        
        stage('Deploy to OpenShift') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 4: Deploy to OpenShift"
                    echo "=========================================="
                    
                    // Check if deployment exists
                    def deploymentExists = sh(
                        script: "oc get deployment ${APP_NAME} -n ${OPENSHIFT_PROJECT} 2>/dev/null",
                        returnStatus: true
                    ) == 0
                    
                    if (!deploymentExists) {
                        echo "Creating new deployment..."
                        
                        // Apply ConfigMap and Secret
                        sh """
                            oc apply -f k8s/02-configmap-secret.yaml -n ${OPENSHIFT_PROJECT}
                        """
                        
                        // Apply Deployment
                        sh """
                            oc apply -f k8s/03-deployment.yaml -n ${OPENSHIFT_PROJECT}
                        """
                        
                        // Apply Service
                        sh """
                            oc apply -f k8s/04-service.yaml -n ${OPENSHIFT_PROJECT}
                        """
                        
                        // Apply Route
                        sh """
                            oc apply -f k8s/05-route.yaml -n ${OPENSHIFT_PROJECT}
                        """
                    } else {
                        echo "Updating existing deployment..."
                        
                        // Update image in deployment
                        sh """
                            oc set image deployment/${APP_NAME} \
                                ${APP_NAME}=${IMAGE_NAME}:${IMAGE_TAG} \
                                -n ${OPENSHIFT_PROJECT}
                        """
                        
                        // Update ConfigMap if changed
                        sh """
                            oc apply -f k8s/02-configmap-secret.yaml -n ${OPENSHIFT_PROJECT}
                        """
                    }
                    
                    echo "✓ Deployment configuration applied"
                }
            }
        }
        
        stage('Wait for Rollout') {
            steps {
                script {
                    echo "=========================================="
                    echo "Stage 5: Wait for Deployment Rollout"
                    echo "=========================================="
                    
                    // Wait for rollout to complete
                    timeout(time: 5, unit: 'MINUTES') {
                        sh """
                            oc rollout status deployment/${APP_NAME} \
                                -n ${OPENSHIFT_PROJECT} \
                                --timeout=5m
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
                    echo "Stage 6: Verify Deployment Health"
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
                    echo "Stage 7: Deployment Information"
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
                    ║ Version:         ${IMAGE_TAG}                              
                    ║ Namespace:       ${OPENSHIFT_PROJECT}                      
                    ║ Replicas:        ${REPLICAS}                               
                    ║                                                            
                    ║ Application URL: https://${routeUrl}
                    ║ Health Check:    https://${routeUrl}/health
                    ║ Info Endpoint:   https://${routeUrl}/info
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
