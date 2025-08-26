// API Configuration - Use same host as the webpage
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api`;

// Subject data
const subjectData = {
    tamil: { title: 'Tamil Language & Literature', totalFiles: 0 },
    english: { title: 'English Language & Communication', totalFiles: 0 },
    statistics: { title: 'Statistics & Data Analysis', totalFiles: 0 },
    java: { title: 'Java Programming', totalFiles: 0 },
    html: { title: 'HTML & Web Development', totalFiles: 0 },
    css: { title: 'CSS Styling', totalFiles: 0 },
    javascript: { title: 'JavaScript Programming', totalFiles: 0 },
    python: { title: 'Python Programming', totalFiles: 0 },
    mathematics: { title: 'Mathematics', totalFiles: 0 },
    physics: { title: 'Physics', totalFiles: 0 },
    chemistry: { title: 'Chemistry', totalFiles: 0 },
    other: { title: 'Other Subjects', totalFiles: 0 }
};

// Initialize app
document.addEventListener('DOMContentLoaded', function () {
    console.log('Script loaded');
    loadFilesFromBackend();
    initializeFileUpload();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // File input change
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
    }

    // Upload form submission
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFileUpload);
    }

    // Search functionality
    const filesSearch = document.getElementById('files-search');
    if (filesSearch) {
        filesSearch.addEventListener('input', handleFilesSearch);
    }
}

// File upload initialization
function initializeFileUpload() {
    const uploadArea = document.querySelector('.upload-area');
    if (!uploadArea) return;

    // Click to browse
    uploadArea.addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#4f46e5';
    e.currentTarget.style.background = '#f9fafb';
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#e5e7eb';
    e.currentTarget.style.background = 'transparent';
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#e5e7eb';
    e.currentTarget.style.background = 'transparent';

    const files = Array.from(e.dataTransfer.files);
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.files = e.dataTransfer.files;
        displaySelectedFiles(files);
    }
}

// Handle file selection
function handleFileSelection(event) {
    const files = Array.from(event.target.files);
    displaySelectedFiles(files);
}

function displaySelectedFiles(files) {
    const fileInfo = document.getElementById('file-info');
    const selectedFilesDiv = document.getElementById('selected-files');

    if (!fileInfo || !selectedFilesDiv) return;

    if (files.length > 0) {
        fileInfo.classList.add('active');
        selectedFilesDiv.innerHTML = files.map(file =>
            `<div class="selected-file">
                ${file.name} (${formatFileSize(file.size)})
            </div>`
        ).join('');
    } else {
        fileInfo.classList.remove('active');
    }
}

// Handle file upload
async function handleFileUpload(event) {
    event.preventDefault();

    const fileInput = document.getElementById('file-input');
    const title = document.getElementById('file-title')?.value || '';
    const subject = document.getElementById('file-subject')?.value || '';
    const description = document.getElementById('file-description')?.value || '';
    const url = document.getElementById('file-url')?.value || '';

    if (!fileInput.files.length || !title || !subject) {
        showToast('Please fill all required fields and select a file', 'error');
        return;
    }

    const uploadBtn = event.target.querySelector('button[type="submit"]');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<div class="loading"></div> Uploading...';
    }

    try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('title', title);
        formData.append('subject', subject);
        formData.append('description', description);
        formData.append('url', url);

        console.log('Uploading to:', `${API_BASE_URL}/files`);

        const response = await fetch(`${API_BASE_URL}/files`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer dummy-token'
            },
            body: formData
        });

        console.log('Upload response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Upload error response:', errorText);
            throw new Error(`Upload failed: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        console.log('Upload successful:', result);

        // Show success message
        showToast('File uploaded successfully!', 'success');

        const successDiv = document.getElementById('upload-success');
        if (successDiv) {
            successDiv.style.display = 'block';
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 3000);
        }

        // Reset form
        event.target.reset();
        document.getElementById('file-info')?.classList.remove('active');

        // Reload files
        loadFilesFromBackend();
        loadAdminFiles();

    } catch (error) {
        console.error('Upload error:', error);
        showToast(`Failed to upload file: ${error.message}`, 'error');
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = 'Upload File';
        }
    }
}

// Load files from backend
async function loadFilesFromBackend() {
    try {
        console.log('Loading files from:', `${API_BASE_URL}/files`);

        const response = await fetch(`${API_BASE_URL}/files`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Load files response status:', response.status);

        if (!response.ok) {
            throw new Error(`Failed to load files: ${response.status} ${response.statusText}`);
        }

        const files = await response.json();
        console.log('Loaded files:', files);
        updateDashboardStats(files);
        return files;

    } catch (error) {
        console.error('Error loading files:', error);
        showToast(`Failed to load files: ${error.message}`, 'error');
        return [];
    }
}

// Load files for admin table
async function loadAdminFiles() {
    const files = await loadFilesFromBackend();
    const tableBody = document.getElementById('files-table-body');

    if (!tableBody) return;

    if (files.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="no-files-message">No files uploaded yet</td></tr>';
        return;
    }

    tableBody.innerHTML = files.map(file => `
        <tr>
            <td>${file.title}</td>
            <td>${file.subject}</td>
            <td>${file.type}</td>
            <td>${formatDate(file.uploadDate)}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editFile('${file.id}')">Edit</button>
                <button class="action-btn delete-btn" onclick="deleteFile('${file.id}')">Delete</button>
                <button class="action-btn download-btn" onclick="downloadFile('${file.id}', '${file.originalName}')">Download</button>
            </td>
        </tr>
    `).join('');
}

// Edit file
function editFile(fileId) {
    // This function is called by the HTML, find the file and populate edit form
    loadFilesFromBackend().then(files => {
        const file = files.find(f => f.id === fileId);
        if (!file) return;

        document.getElementById('edit-file-id').value = fileId;
        document.getElementById('edit-title').value = file.title;
        document.getElementById('edit-subject').value = file.subject;
        document.getElementById('edit-description').value = file.description || '';
        document.getElementById('edit-url').value = file.url || '';

        const editModal = document.getElementById('edit-modal-overlay');
        if (editModal) {
            editModal.classList.add('active');
        }
    });
}

// Delete file
async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }

    try {
        console.log('Deleting file:', fileId);

        const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer dummy-token',
                'Content-Type': 'application/json'
            }
        });

        console.log('Delete response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Delete failed: ${response.status} - ${errorText}`);
        }

        showToast('File deleted successfully', 'success');
        loadAdminFiles();
        loadFilesFromBackend();

    } catch (error) {
        console.error('Delete error:', error);
        showToast(`Failed to delete file: ${error.message}`, 'error');
    }
}

// Download file
async function downloadFile(fileId, fileName) {
    try {
        console.log('Downloading file:', fileId, fileName);

        const response = await fetch(`${API_BASE_URL}/files/${fileId}/download`);

        console.log('Download response status:', response.status);

        if (!response.ok) {
            throw new Error(`Download failed: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('Download started', 'success');

    } catch (error) {
        console.error('Download error:', error);
        showToast(`Failed to download file: ${error.message}`, 'error');
    }
}

// Update dashboard stats
function updateDashboardStats(files) {
    const totalFiles = files.length;
    const subjects = [...new Set(files.map(f => f.subject))].length;

    const totalFilesElement = document.getElementById('total-files');
    const totalSubjectsElement = document.getElementById('total-subjects');

    if (totalFilesElement) totalFilesElement.textContent = totalFiles;
    if (totalSubjectsElement) totalSubjectsElement.textContent = subjects;

    // Update subject counts
    Object.keys(subjectData).forEach(subject => {
        subjectData[subject].totalFiles = files.filter(f => f.subject === subject).length;
    });

    // Update subject cards if they exist
    Object.keys(subjectData).forEach(subject => {
        const countElement = document.getElementById(`${subject}-count`);
        if (countElement) {
            countElement.textContent = subjectData[subject].totalFiles;
        }
    });
}

// Search files
function handleFilesSearch(event) {
    const searchTerm = event.target.value.toLowerCase();
    const rows = document.querySelectorAll('#files-table-body tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 5000;
        opacity: 0;
        transform: translateY(-20px);
        transition: all 0.3s ease;
        max-width: 400px;
        word-wrap: break-word;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 100);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 4000);
}

// Test API connection
async function testAPIConnection() {
    try {
        console.log('Testing API connection...');
        const response = await fetch(`${API_BASE_URL}/test`);
        const result = await response.json();
        console.log('API Test Result:', result);
        return result;
    } catch (error) {
        console.error('API Test Failed:', error);
        showToast('API connection failed', 'error');
        return null;
    }
}

// Run API test on load
document.addEventListener('DOMContentLoaded', function () {
    testAPIConnection();
});

// Global functions for HTML onclick handlers
window.editFile = editFile;
window.deleteFile = deleteFile;
window.downloadFile = downloadFile;

console.log('Notes Dock script loaded successfully');