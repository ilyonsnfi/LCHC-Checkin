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
    } else if (tab === 'settings') {
        loadSettings();
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
    } else if (currentTab === 'settings') {
        loadSettings();
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
            const statusClass = user.is_checked_in ? 'checked-in' : 'not-checked-in';
            const statusText = user.is_checked_in ? 'Checked In' : 'Not Checked In';
            const lastCheckin = user.last_checkin ? new Date(user.last_checkin).toLocaleString() : 'Never';
            
            const buttonText = user.is_checked_in ? 'Check Out' : 'Check In';
            const buttonClass = user.is_checked_in ? 'checkout-button' : 'checkin-button';
            const buttonAction = user.is_checked_in ? 'manualCheckout' : 'manualCheckin';
            
            row.innerHTML = `
                <td>
                    <button onclick="${buttonAction}('${user.employee_id}', this)" 
                            class="${buttonClass}">
                        ${buttonText}
                    </button>
                </td>
                <td>${user.first_name} ${user.last_name}</td>
                <td>${user.employee_id}</td>
                <td>${user.table_number}</td>
                <td><span class="status ${statusClass}">${statusText}</span></td>
                <td>${lastCheckin}</td>
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

function showClearHistoryConfirmation() {
    document.getElementById('clearHistoryModal').style.display = 'block';
    document.getElementById('confirmHistoryInput').value = '';
    document.getElementById('confirmHistoryInput').focus();
}

function closeClearHistoryModal() {
    document.getElementById('clearHistoryModal').style.display = 'none';
}

async function confirmClearHistory() {
    const confirmInput = document.getElementById('confirmHistoryInput');
    const expectedText = 'CLEAR HISTORY';
    
    if (confirmInput.value !== expectedText) {
        alert(`Please type "${expectedText}" exactly to confirm.`);
        confirmInput.focus();
        return;
    }
    
    try {
        const response = await fetch('/admin/clear-history', {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully cleared ${result.deleted} checkin records`);
            closeClearHistoryModal();
            // Refresh history tab if it's active
            if (currentTab === 'history') {
                loadHistory();
            }
        } else {
            alert(result.message || 'Failed to clear checkin history');
        }
        
    } catch (error) {
        alert('Error clearing checkin history');
        console.error('Error:', error);
    }
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const deleteModal = document.getElementById('deleteModal');
    const clearHistoryModal = document.getElementById('clearHistoryModal');
    
    if (event.target === deleteModal) {
        closeDeleteModal();
    } else if (event.target === clearHistoryModal) {
        closeClearHistoryModal();
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
    // Allow Enter key to trigger confirmation in the input fields
    document.getElementById('confirmInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            confirmDeleteUsers();
        }
    });
    
    document.getElementById('confirmHistoryInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            confirmClearHistory();
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

async function loadSettings() {
    const loading = document.getElementById('settings-loading');
    const container = document.getElementById('settings-container');
    
    loading.style.display = 'block';
    container.style.display = 'none';
    
    try {
        const response = await fetch('/admin/settings');
        const settings = await response.json();
        
        // Populate form fields
        document.getElementById('welcome-banner').value = settings.welcome_banner;
        document.getElementById('secondary-banner').value = settings.secondary_banner;
        document.getElementById('text-color').value = settings.text_color;
        document.getElementById('foreground-color').value = settings.foreground_color;
        document.getElementById('background-color').value = settings.background_color;
        
        // Show current background image
        const currentBg = document.getElementById('current-background');
        const removeSection = document.getElementById('remove-background-section');
        if (settings.background_image) {
            currentBg.innerHTML = `<p>Current background image:</p><img src="${settings.background_image}" alt="Current background">`;
            removeSection.style.display = 'block';
        } else {
            currentBg.innerHTML = '<p>No background image set</p>';
            removeSection.style.display = 'none';
        }
        
        loading.style.display = 'none';
        container.style.display = 'block';
        
        // No need to initialize preview - iframe loads automatically
        
        // Add real-time auto-apply listeners
        addAutoApplyListeners();
        
    } catch (error) {
        loading.innerHTML = 'Error loading settings';
        console.error('Error:', error);
    }
}

async function saveSettings() {
    const welcomeBanner = document.getElementById('welcome-banner').value.trim();
    const secondaryBanner = document.getElementById('secondary-banner').value.trim();
    const textColor = document.getElementById('text-color').value;
    const foregroundColor = document.getElementById('foreground-color').value;
    const backgroundColor = document.getElementById('background-color').value;
    
    if (!welcomeBanner || !secondaryBanner) {
        showSettingsMessage('Please fill in all text fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                welcome_banner: welcomeBanner,
                secondary_banner: secondaryBanner,
                text_color: textColor,
                foreground_color: foregroundColor,
                background_color: backgroundColor
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSettingsMessage('Settings saved successfully', 'success');
            // Refresh the preview iframe
            reloadPreview();
        } else {
            showSettingsMessage(result.message, 'error');
        }
        
    } catch (error) {
        showSettingsMessage('Error saving settings', 'error');
        console.error('Error:', error);
    }
}

async function resetSettings() {
    const confirmed = confirm('Are you sure you want to reset all settings to defaults?');
    if (!confirmed) return;
    
    try {
        const response = await fetch('/admin/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                welcome_banner: 'RFID Checkin Station',
                secondary_banner: 'Scan your badge to check in',
                text_color: '#333333',
                foreground_color: '#ffffff',
                background_color: '#f5f5f5',
                background_image: ''
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSettingsMessage('Settings reset to defaults', 'success');
            loadSettings(); // Reload to show updated values
            reloadPreview(); // Refresh preview
        } else {
            showSettingsMessage(result.message, 'error');
        }
        
    } catch (error) {
        showSettingsMessage('Error resetting settings', 'error');
        console.error('Error:', error);
    }
}

async function handleBackgroundUpload() {
    const fileInput = document.getElementById('background-file');
    
    if (!fileInput.files[0]) {
        return;
    }
    
    // Check if there's already a background image
    const currentBg = document.getElementById('current-background');
    const hasExistingImage = currentBg.innerHTML.includes('<img');
    
    if (hasExistingImage) {
        const confirmed = confirm('A background image already exists. Do you want to replace it with the new image?');
        if (!confirmed) {
            fileInput.value = ''; // Clear the file input
            return;
        }
    }
    
    await uploadBackgroundImage();
}

async function uploadBackgroundImage() {
    const fileInput = document.getElementById('background-file');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/admin/upload-background', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBackgroundMessage('Background image uploaded successfully', 'success');
            fileInput.value = '';
            // Update current background display
            const currentBg = document.getElementById('current-background');
            const removeSection = document.getElementById('remove-background-section');
            currentBg.innerHTML = `<p>Current background image:</p><img src="${result.path}" alt="Current background">`;
            removeSection.style.display = 'block';
            // Update preview
            reloadPreview();
        } else {
            showBackgroundMessage(result.message, 'error');
        }
        
    } catch (error) {
        showBackgroundMessage('Error uploading image', 'error');
        console.error('Error:', error);
    }
}

async function confirmRemoveBackground() {
    const confirmed = confirm('Are you sure you want to remove the background image? The file will be permanently deleted.');
    if (!confirmed) return;
    
    try {
        const response = await fetch('/admin/remove-background', {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBackgroundMessage(result.message, 'success');
            // Show warning if file deletion failed but settings were updated
            if (result.warning) {
                setTimeout(() => {
                    showBackgroundMessage(`Warning: ${result.warning}`, 'error');
                }, 3000);
            }
            // Update display
            const currentBg = document.getElementById('current-background');
            const removeSection = document.getElementById('remove-background-section');
            currentBg.innerHTML = '<p>No background image set</p>';
            removeSection.style.display = 'none';
            // Update preview
            reloadPreview();
        } else {
            showBackgroundMessage(result.message, 'error');
        }
        
    } catch (error) {
        showBackgroundMessage('Error removing background image', 'error');
        console.error('Error:', error);
    }
}

function showSettingsMessage(text, type) {
    const message = document.getElementById('settings-message');
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = 'block';
    
    setTimeout(() => {
        message.style.display = 'none';
    }, 5000);
}

function showBackgroundMessage(text, type) {
    const message = document.getElementById('background-message');
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = 'block';
    
    setTimeout(() => {
        message.style.display = 'none';
    }, 5000);
}

function reloadPreview() {
    const iframe = document.getElementById('checkin-preview');
    if (iframe) {
        // Add timestamp to force reload
        const baseUrl = '/preview';
        const timestamp = new Date().getTime();
        iframe.src = `${baseUrl}?t=${timestamp}`;
    }
}

function addAutoApplyListeners() {
    const welcomeInput = document.getElementById('welcome-banner');
    const secondaryInput = document.getElementById('secondary-banner');
    const textColorInput = document.getElementById('text-color');
    const foregroundColorInput = document.getElementById('foreground-color');
    const backgroundColorInput = document.getElementById('background-color');
    
    let autoSaveTimeout = null;
    
    function autoSaveSettings(immediate = false) {
        // Clear existing timeout
        if (autoSaveTimeout) {
            clearTimeout(autoSaveTimeout);
        }
        
        const delay = immediate ? 0 : 200;
        
        // Set new timeout to save after user stops typing/changing
        autoSaveTimeout = setTimeout(async () => {
            const welcomeBanner = welcomeInput.value.trim();
            const secondaryBanner = secondaryInput.value.trim();
            const textColor = textColorInput.value;
            const foregroundColor = foregroundColorInput.value;
            const backgroundColor = backgroundColorInput.value;
            
            // Skip if text fields are empty
            if (!welcomeBanner || !secondaryBanner) {
                return;
            }
            
            try {
                const response = await fetch('/admin/settings', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        welcome_banner: welcomeBanner,
                        secondary_banner: secondaryBanner,
                        text_color: textColor,
                        foreground_color: foregroundColor,
                        background_color: backgroundColor
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Reload preview to show changes
                    reloadPreview();
                    // Show brief success indicator only for manual saves
                    if (!immediate) {
                        showAutoSaveIndicator();
                    }
                }
                
            } catch (error) {
                console.error('Auto-save error:', error);
            }
        }, delay);
    }
    
    // Immediate save function for colors (no debounce needed)
    function immediateColorSave() {
        autoSaveSettings(true);
    }
    
    // Add event listeners
    if (welcomeInput) welcomeInput.addEventListener('input', autoSaveSettings);
    if (secondaryInput) secondaryInput.addEventListener('input', autoSaveSettings);
    
    // Colors update immediately
    if (textColorInput) textColorInput.addEventListener('input', immediateColorSave);
    if (foregroundColorInput) foregroundColorInput.addEventListener('input', immediateColorSave);
    if (backgroundColorInput) backgroundColorInput.addEventListener('input', immediateColorSave);
}

function showAutoSaveIndicator() {
    // Create or update auto-save indicator
    let indicator = document.getElementById('auto-save-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'auto-save-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        indicator.textContent = '✓ Auto-saved';
        document.body.appendChild(indicator);
    }
    
    // Show and hide the indicator
    indicator.style.opacity = '1';
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
}

async function manualCheckin(employeeId, buttonElement) {
    const originalText = buttonElement.textContent;
    buttonElement.textContent = 'Checking in...';
    buttonElement.disabled = true;
    
    try {
        const response = await fetch(`/admin/checkin/${employeeId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Refresh users list to show updated status
            loadUsers();
        } else {
            alert(result.message || 'Failed to check in user');
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        }
        
    } catch (error) {
        alert('Error checking in user');
        console.error('Error:', error);
        buttonElement.textContent = originalText;
        buttonElement.disabled = false;
    }
}

async function manualCheckout(employeeId, buttonElement) {
    const originalText = buttonElement.textContent;
    buttonElement.textContent = 'Checking out...';
    buttonElement.disabled = true;
    
    try {
        const response = await fetch(`/admin/checkout/${employeeId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Refresh users list to show updated status
            loadUsers();
        } else {
            alert(result.message || 'Failed to check out user');
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        }
        
    } catch (error) {
        alert('Error checking out user');
        console.error('Error:', error);
        buttonElement.textContent = originalText;
        buttonElement.disabled = false;
    }
}