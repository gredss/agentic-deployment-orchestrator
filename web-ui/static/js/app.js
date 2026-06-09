// Bob Web UI - Main JavaScript for Form Handling

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Elements
    const form = document.getElementById('deploymentForm');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('app_py');
    const browseBtn = document.getElementById('browseBtn');
    const uploadSuccess = document.getElementById('uploadSuccess');
    const uploadContent = uploadArea ? uploadArea.querySelector('.upload-content') : null;
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const changeFileBtn = document.getElementById('changeFileBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Debug: Log all elements
    console.log('Elements found:', {
        form: !!form,
        uploadArea: !!uploadArea,
        fileInput: !!fileInput,
        browseBtn: !!browseBtn,
        uploadSuccess: !!uploadSuccess,
        uploadContent: !!uploadContent,
        fileName: !!fileName,
        fileSize: !!fileSize,
        changeFileBtn: !!changeFileBtn
    });

    // File upload handling
    let selectedFile = null;

    // Browse button click
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });

    // Upload area click
    uploadArea.addEventListener('click', (e) => {
        if (e.target !== changeFileBtn && !selectedFile) {
            fileInput.click();
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        console.log('File input changed:', e.target.files);
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.py')) {
            handleFileSelect(file);
        } else {
            showToast('Please upload a Python (.py) file', 'error');
        }
    });

    // Change file button
    changeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = '';
        uploadContent.style.display = 'flex';
        uploadSuccess.style.display = 'none';
    });

    // Handle file selection
    function handleFileSelect(file) {
        console.log('handleFileSelect called with:', file);
        
        if (!file) {
            console.log('No file provided');
            return;
        }

        console.log('File name:', file.name);
        console.log('File size:', file.size);

        if (!file.name.endsWith('.py')) {
            showToast('Please upload a Python (.py) file', 'error');
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            showToast('File size must be less than 16MB', 'error');
            return;
        }

        selectedFile = file;
        
        // Update UI - Force display changes
        console.log('Updating UI elements');
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        
        if (uploadContent) {
            uploadContent.style.display = 'none';
            console.log('Hidden upload content');
        }
        
        if (uploadSuccess) {
            uploadSuccess.style.display = 'flex';
            console.log('Showing upload success');
        }

        showToast('✓ File uploaded: ' + file.name, 'success');
        console.log('File upload complete');
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }

    // Form validation
    function validateForm() {
        const appName = document.getElementById('app_name').value;
        const appPort = document.getElementById('app_port').value;
        const githubRepo = document.getElementById('github_repo').value;
        const githubToken = document.getElementById('github_token').value;
        const openshiftNamespace = document.getElementById('openshift_namespace').value;
        const openshiftCluster = document.getElementById('openshift_cluster').value;

        // Validate app name (lowercase, numbers, hyphens only)
        const appNameRegex = /^[a-z0-9-]+$/;
        if (!appNameRegex.test(appName)) {
            showToast('App name must contain only lowercase letters, numbers, and hyphens', 'error');
            return false;
        }

        // Validate port
        const port = parseInt(appPort);
        if (isNaN(port) || port < 1 || port > 65535) {
            showToast('Port must be between 1 and 65535', 'error');
            return false;
        }

        // Validate GitHub repo URL
        if (!githubRepo.startsWith('https://github.com/')) {
            showToast('GitHub repository must be a valid GitHub URL', 'error');
            return false;
        }

        // Validate GitHub token
        if (githubToken.length < 20) {
            showToast('GitHub token appears to be invalid', 'error');
            return false;
        }

        // Validate file upload
        if (!selectedFile) {
            showToast('Please upload your app.py file', 'error');
            return false;
        }

        return true;
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validate form
        if (!validateForm()) {
            return;
        }

        // Show loading overlay
        loadingOverlay.style.display = 'flex';

        try {
            // Create FormData
            const formData = new FormData(form);
            
            // Manually append the file since it's stored in selectedFile variable
            if (selectedFile) {
                formData.set('app_py', selectedFile);
            }

            // Send request
            const response = await fetch('/api/deploy', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Redirect to status page
                window.location.href = `/status/${data.deployment_id}`;
            } else {
                throw new Error(data.error || 'Deployment failed');
            }
        } catch (error) {
            console.error('Deployment error:', error);
            showToast(error.message || 'Deployment failed. Please try again.', 'error');
            loadingOverlay.style.display = 'none';
        }
    });

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

    // Add slideOut animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideOut {
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // Real-time validation
    const appNameInput = document.getElementById('app_name');
    appNameInput.addEventListener('input', (e) => {
        const value = e.target.value;
        const isValid = /^[a-z0-9-]*$/.test(value);
        
        if (!isValid && value.length > 0) {
            e.target.style.borderColor = 'var(--danger-color)';
        } else {
            e.target.style.borderColor = '';
        }
    });

    // Port validation
    const portInput = document.getElementById('app_port');
    portInput.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        
        if (value < 1 || value > 65535) {
            e.target.style.borderColor = 'var(--danger-color)';
        } else {
            e.target.style.borderColor = '';
        }
    });

    // GitHub URL validation
    const githubRepoInput = document.getElementById('github_repo');
    githubRepoInput.addEventListener('blur', (e) => {
        const value = e.target.value;
        
        if (value && !value.startsWith('https://github.com/')) {
            e.target.style.borderColor = 'var(--danger-color)';
            showToast('GitHub URL must start with https://github.com/', 'error');
        } else {
            e.target.style.borderColor = '';
        }
    });

    // Auto-format GitHub URL
    githubRepoInput.addEventListener('blur', (e) => {
        let value = e.target.value.trim();
        
        // Add .git if missing
        if (value && !value.endsWith('.git')) {
            value += '.git';
            e.target.value = value;
        }
    });

    // Show initial welcome message
    setTimeout(() => {
        showToast('Welcome to Bob Deployment Generator! Fill in the form to get started.', 'info');
    }, 500);
});

// Made with Bob
