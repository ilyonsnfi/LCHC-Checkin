let currentTab = 'users';

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tab + '-tab').classList.add('active');
    
    currentTab = tab;
    
    // Load data for the active tab with current search query
    const globalSearchInput = document.getElementById('global-search-input');
    const searchQuery = globalSearchInput ? globalSearchInput.value.trim() : '';
    
    if (tab === 'history') {
        loadHistory(searchQuery);
    } else if (tab === 'users') {
        loadUsers(searchQuery);
    } else if (tab === 'tables') {
        loadTables(searchQuery);
    }
}

function refreshActiveTab() {
    const globalSearchInput = document.getElementById('global-search-input');
    const searchQuery = globalSearchInput ? globalSearchInput.value.trim() : '';
    
    if (currentTab === 'history') {
        loadHistory(searchQuery);
    } else if (currentTab === 'users') {
        loadUsers(searchQuery);
    } else if (currentTab === 'tables') {
        loadTables(searchQuery);
    }
}

async function loadHistory(searchQuery = '') {
    const loading = document.getElementById('history-loading');
    const table = document.getElementById('history-table');
    const tbody = document.getElementById('history-body');
    
    loading.style.display = 'block';
    table.style.display = 'none';
    
    try {
        const url = searchQuery ? `/admin/history?search=${encodeURIComponent(searchQuery)}` : '/admin/history';
        const response = await fetch(url);
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

async function loadUsers(searchQuery = '') {
    const loading = document.getElementById('users-loading');
    const table = document.getElementById('users-table');
    const tbody = document.getElementById('users-body');
    
    loading.style.display = 'block';
    table.style.display = 'none';
    
    try {
        const url = searchQuery ? `/admin/users?search=${encodeURIComponent(searchQuery)}` : '/admin/users';
        const response = await fetch(url);
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

async function loadTables(searchQuery = '') {
    const loading = document.getElementById('tables-loading');
    const container = document.getElementById('tables-container');
    const grid = document.getElementById('tables-grid');
    
    loading.style.display = 'block';
    container.style.display = 'none';
    
    try {
        const url = searchQuery ? `/admin/tables?search=${encodeURIComponent(searchQuery)}` : '/admin/tables';
        const response = await fetch(url);
        const tables = await response.json();
        
        grid.innerHTML = '';
        
        if (tables.length === 0) {
            const emptyMsg = searchQuery ? `No tables found matching "${searchQuery}"` : 'No tables with users found';
            grid.innerHTML = `<div class="empty-tables">${emptyMsg}</div>`;
        } else {
            tables.forEach(table => {
                const tableCard = document.createElement('div');
                tableCard.className = 'table-card';
                
                const usersList = table.users.map(user => `<li>${user}</li>`).join('');
                
                tableCard.innerHTML = `
                    <div class="table-header">
                        <div class="table-number">Table ${table.table_number}</div>
                        <div class="user-count">${table.user_count} user${table.user_count === 1 ? '' : 's'}</div>
                    </div>
                    <ul class="table-users">
                        ${usersList}
                    </ul>
                `;
                
                grid.appendChild(tableCard);
            });
        }
        
        loading.style.display = 'none';
        container.style.display = 'block';
        
    } catch (error) {
        loading.innerHTML = 'Error loading tables';
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

function showAddUserForm() {
    document.getElementById('add-user-form').style.display = 'block';
    document.getElementById('new-first-name').focus();
}

function hideAddUserForm() {
    document.getElementById('add-user-form').style.display = 'none';
    // Clear form fields
    document.getElementById('new-first-name').value = '';
    document.getElementById('new-last-name').value = '';
    document.getElementById('new-employee-id').value = '';
    document.getElementById('new-table-number').value = '';
    // Clear messages
    document.getElementById('add-user-message').style.display = 'none';
}

async function createUser() {
    const firstName = document.getElementById('new-first-name').value.trim();
    const lastName = document.getElementById('new-last-name').value.trim();
    const employeeId = document.getElementById('new-employee-id').value.trim();
    const tableNumber = parseInt(document.getElementById('new-table-number').value);
    const message = document.getElementById('add-user-message');
    
    // Validation
    if (!firstName || !lastName || !employeeId || !tableNumber) {
        showAddUserMessage('Please fill in all fields', 'error');
        return;
    }
    
    if (tableNumber < 1) {
        showAddUserMessage('Table number must be greater than 0', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                employee_id: employeeId,
                table_number: tableNumber
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAddUserMessage(result.message, 'success');
            // Clear form after successful creation
            setTimeout(() => {
                hideAddUserForm();
                loadUsers(); // Refresh the users list
            }, 1500);
        } else {
            showAddUserMessage(result.message, 'error');
        }
        
    } catch (error) {
        showAddUserMessage('Error creating user', 'error');
        console.error('Error:', error);
    }
}

function showAddUserMessage(text, type) {
    const message = document.getElementById('add-user-message');
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = 'block';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Allow Enter key to trigger confirmation in the input field
    document.getElementById('confirmInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            confirmDeleteUsers();
        }
    });
    
    // Add global search functionality
    const globalSearchInput = document.getElementById('global-search-input');
    let searchTimeout;
    
    globalSearchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = globalSearchInput.value.trim();
            // Apply search to the currently active tab
            if (currentTab === 'history') {
                loadHistory(query);
            } else if (currentTab === 'users') {
                loadUsers(query);
            } else if (currentTab === 'tables') {
                loadTables(query);
            }
        }, 300); // Debounce search
    });
    
    // Load the default tab (users)
    loadUsers();
});