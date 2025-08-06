let currentTab = 'history';

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tab + '-tab').classList.add('active');
    
    currentTab = tab;
    
    // Load data for the active tab
    if (tab === 'history') {
        loadHistory();
    } else if (tab === 'users') {
        loadUsers();
    }
}

function refreshActiveTab() {
    if (currentTab === 'history') {
        loadHistory();
    } else if (currentTab === 'users') {
        loadUsers();
    }
}

async function loadHistory() {
    const loading = document.getElementById('history-loading');
    const table = document.getElementById('history-table');
    const tbody = document.getElementById('history-body');
    
    loading.style.display = 'block';
    table.style.display = 'none';
    
    try {
        const response = await fetch('/admin/history');
        const history = await response.json();
        
        tbody.innerHTML = '';
        
        history.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.first_name} ${record.last_name}</td>
                <td>${record.employee_id}</td>
                <td>${record.table_number}</td>
                <td>${new Date(record.checkin_time).toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
        
        loading.style.display = 'none';
        table.style.display = 'table';
        
    } catch (error) {
        loading.innerHTML = 'Error loading history';
        console.error('Error:', error);
    }
}

async function loadUsers() {
    const loading = document.getElementById('users-loading');
    const table = document.getElementById('users-table');
    const tbody = document.getElementById('users-body');
    
    loading.style.display = 'block';
    table.style.display = 'none';
    
    try {
        const response = await fetch('/admin/users');
        const users = await response.json();
        
        tbody.innerHTML = '';
        
        users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.first_name} ${user.last_name}</td>
                <td>${user.employee_id}</td>
                <td>${user.table_number}</td>
            `;
            tbody.appendChild(row);
        });
        
        loading.style.display = 'none';
        table.style.display = 'table';
        
    } catch (error) {
        loading.innerHTML = 'Error loading users';
        console.error('Error:', error);
    }
}

async function exportExcel() {
    try {
        const response = await fetch('/admin/export');
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'checkin_history.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        alert('Error exporting Excel file');
        console.error('Error:', error);
    }
}

async function importFile() {
    const fileInput = document.getElementById('excel-file');
    const message = document.getElementById('import-message');
    
    if (!fileInput.files[0]) {
        showMessage('Please select an Excel file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    const fileName = file.name.toLowerCase();
    
    if (!fileName.endsWith('.xlsx')) {
        showMessage('Please select an Excel (.xlsx) file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/admin/import', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            let msg = `Successfully imported ${result.imported} users`;
            if (result.errors.length > 0) {
                msg += `\n\nErrors:\n${result.errors.join('\n')}`;
            }
            showMessage(msg, 'success');
            fileInput.value = '';
            // Refresh users tab if it exists
            loadUsers();
        } else {
            showMessage(result.message || 'Import failed', 'error');
        }
        
    } catch (error) {
        showMessage('Error importing file', 'error');
        console.error('Error:', error);
    }
}

function showMessage(text, type) {
    const message = document.getElementById('import-message');
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = 'block';
    
    setTimeout(() => {
        message.style.display = 'none';
    }, 5000);
}

function showDeleteConfirmation() {
    document.getElementById('deleteModal').style.display = 'block';
    document.getElementById('confirmInput').value = '';
    document.getElementById('confirmInput').focus();
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

async function confirmDeleteUsers() {
    const confirmInput = document.getElementById('confirmInput');
    const expectedText = 'DELETE ALL USERS';
    
    if (confirmInput.value !== expectedText) {
        alert(`Please type "${expectedText}" exactly to confirm deletion.`);
        confirmInput.focus();
        return;
    }
    
    try {
        const response = await fetch('/admin/users', {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully deleted ${result.deleted} users`);
            closeDeleteModal();
            // Refresh users tab
            loadUsers();
        } else {
            alert(result.message || 'Failed to delete users');
        }
        
    } catch (error) {
        alert('Error deleting users');
        console.error('Error:', error);
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('deleteModal');
    if (event.target === modal) {
        closeDeleteModal();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Allow Enter key to trigger confirmation in the input field
    document.getElementById('confirmInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            confirmDeleteUsers();
        }
    });
    
    loadHistory();
});