// Bob Web UI - Deployment Status Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO connection
    const socket = io();

    // Elements
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const logsContainer = document.getElementById('logsContainer');
    const resultSection = document.getElementById('resultSection');
    const resultCard = document.getElementById('resultCard');
    const resultIcon = document.getElementById('resultIcon');
    const resultTitle = document.getElementById('resultTitle');
    const resultMessage = document.getElementById('resultMessage');
    const resultDetails = document.getElementById('resultDetails');
    const appUrl = document.getElementById('appUrl');
    const healthUrl = document.getElementById('healthUrl');
    const copyUrlBtn = document.getElementById('copyUrlBtn');

    // Status tracking
    let currentStatus = 'initializing';
    let deploymentData = null;

    // Step mapping
    const stepMapping = {
        'initializing': 'analyzing',
        'analyzing': 'analyzing',
        'generating': 'generating',
        'committing': 'committing',
        'configuring': 'configuring',
        'building': 'building',
        'deploying': 'deploying',
        'completed': 'deploying',
        'failed': null
    };

    // Connect to WebSocket
    socket.on('connect', () => {
        console.log('Connected to server');
        // Fetch initial status
        fetchStatus();
    });

    // Listen for deployment updates
    socket.on('deployment_update', (data) => {
        console.log('Deployment update:', data);
        
        if (data.deployment_id === DEPLOYMENT_ID) {
            updateProgress(data.progress);
            updateStatus(data.status);
            addLogEntry(data.log);
        }
    });

    // Fetch deployment status
    async function fetchStatus() {
        try {
            const response = await fetch(`/api/status/${DEPLOYMENT_ID}`);
            const data = await response.json();
            
            deploymentData = data;
            currentStatus = data.status;
            
            // Update UI with current state
            updateProgress(data.progress);
            updateStatus(data.status);
            
            // Add existing logs
            if (data.logs && data.logs.length > 0) {
                logsContainer.innerHTML = '';
                data.logs.forEach(log => {
                    addLogEntry(log.message, log.timestamp);
                });
            }
            
            // If completed or failed, show result
            if (data.status === 'completed' || data.status === 'failed') {
                showResult(data);
            }
            
            // Poll for updates if not using WebSocket
            if (!socket.connected && data.status !== 'completed' && data.status !== 'failed') {
                setTimeout(fetchStatus, 2000);
            }
        } catch (error) {
            console.error('Failed to fetch status:', error);
            addLogEntry('Error: Failed to fetch deployment status');
        }
    }

    // Update progress bar
    function updateProgress(progress) {
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
    }

    // Update status steps
    function updateStatus(status) {
        currentStatus = status;
        
        // Update step indicators
        const steps = {
            'analyzing': ['analyzing'],
            'generating': ['analyzing', 'generating'],
            'committing': ['analyzing', 'generating', 'committing'],
            'configuring': ['analyzing', 'generating', 'committing', 'configuring'],
            'building': ['analyzing', 'generating', 'committing', 'configuring', 'building'],
            'deploying': ['analyzing', 'generating', 'committing', 'configuring', 'building', 'deploying'],
            'completed': ['analyzing', 'generating', 'committing', 'configuring', 'building', 'deploying'],
            'failed': []
        };
        
        const completedSteps = steps[status] || [];
        const activeStep = stepMapping[status];
        
        // Update all steps
        ['analyzing', 'generating', 'committing', 'configuring', 'building', 'deploying'].forEach(step => {
            const stepElement = document.getElementById(`step-${step}`);
            const stepIcon = stepElement.querySelector('.step-icon');
            const stepStatus = stepElement.querySelector('.step-status');
            
            // Remove all classes
            stepElement.classList.remove('active', 'completed', 'failed');
            
            if (status === 'failed' && step === activeStep) {
                // Failed step
                stepElement.classList.add('failed');
                stepIcon.textContent = '❌';
                stepStatus.textContent = '✗';
            } else if (completedSteps.includes(step) && step !== activeStep) {
                // Completed step
                stepElement.classList.add('completed');
                stepIcon.textContent = '✅';
                stepStatus.textContent = '✓';
            } else if (step === activeStep) {
                // Active step
                stepElement.classList.add('active');
                stepIcon.textContent = '⏳';
                stepStatus.textContent = '⏳';
            } else {
                // Pending step
                stepIcon.textContent = '⏳';
                stepStatus.textContent = '⏳';
            }
        });
    }

    // Add log entry
    function addLogEntry(message, timestamp = null) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        logEntry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">${escapeHtml(message)}</span>
        `;
        
        logsContainer.appendChild(logEntry);
        
        // Auto-scroll to bottom
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    // Show result (success or failure)
    function showResult(data) {
        resultSection.style.display = 'block';
        
        if (data.status === 'completed') {
            // Success
            resultCard.classList.add('success');
            resultIcon.textContent = '🎉';
            resultTitle.textContent = 'Deployment Complete!';
            resultMessage.textContent = 'Your application is now live and accessible.';
            
            // Show app URLs
            if (data.url) {
                resultDetails.style.display = 'block';
                appUrl.href = data.url;
                appUrl.textContent = data.url;
                
                const healthCheckPath = deploymentData?.config?.health_check_path || '/health';
                const healthCheckUrl = data.url + healthCheckPath;
                healthUrl.href = healthCheckUrl;
                healthUrl.textContent = healthCheckUrl;
            }
        } else {
            // Failure
            resultCard.classList.add('error');
            resultIcon.textContent = '❌';
            resultTitle.textContent = 'Deployment Failed';
            resultMessage.textContent = 'Something went wrong during deployment. Please check the logs above.';
            resultDetails.style.display = 'none';
        }
        
        // Scroll to result
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Copy URL to clipboard
    if (copyUrlBtn) {
        copyUrlBtn.addEventListener('click', async () => {
            const url = appUrl.textContent;
            
            try {
                await navigator.clipboard.writeText(url);
                showToast('URL copied to clipboard!', 'success');
                copyUrlBtn.textContent = '✓';
                
                setTimeout(() => {
                    copyUrlBtn.textContent = '📋';
                }, 2000);
            } catch (error) {
                showToast('Failed to copy URL', 'error');
            }
        });
    }

    // View logs button
    const viewLogsBtn = document.getElementById('viewLogsBtn');
    if (viewLogsBtn) {
        viewLogsBtn.addEventListener('click', () => {
            logsContainer.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Toast notification system
    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
        
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-message">${message}</div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                container.removeChild(toast);
            }, 300);
        }, 5000);
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Handle connection errors
    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        addLogEntry('Warning: Real-time updates disconnected. Polling for updates...');
        
        // Fallback to polling
        if (currentStatus !== 'completed' && currentStatus !== 'failed') {
            setTimeout(fetchStatus, 2000);
        }
    });

    // Handle disconnection
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        addLogEntry('Warning: Connection lost. Attempting to reconnect...');
    });

    // Reconnection
    socket.on('reconnect', () => {
        console.log('Reconnected to server');
        addLogEntry('Info: Connection restored. Resuming real-time updates.');
        fetchStatus();
    });

    // Auto-refresh status every 5 seconds as backup
    setInterval(() => {
        if (currentStatus !== 'completed' && currentStatus !== 'failed') {
            fetchStatus();
        }
    }, 5000);

    // Show initial message
    setTimeout(() => {
        showToast('Monitoring deployment progress...', 'info');
    }, 500);

    // Prevent page unload during deployment
    window.addEventListener('beforeunload', (e) => {
        if (currentStatus !== 'completed' && currentStatus !== 'failed') {
            e.preventDefault();
            e.returnValue = 'Deployment is in progress. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
});

// Made with Bob
