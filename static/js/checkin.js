document.addEventListener('DOMContentLoaded', function() {
    const checkinForm = document.getElementById('checkin-form');
    const badgeInput = document.getElementById('badge-input');
    const result = document.getElementById('result');
    
    checkinForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const badgeId = badgeInput.value.trim();
        
        if (!badgeId) return;
        
        try {
            const formData = new FormData();
            formData.append('badge_id', badgeId);
            
            const response = await fetch('/checkin', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                result.className = 'success';
                result.innerHTML = `
                    <div class="user-info">Welcome, ${data.name}!</div>
                    <div class="table-info">Table ${data.table_number}</div>
                    <div>Checked in at ${data.time}</div>
                `;
            } else {
                result.className = 'error';
                result.innerHTML = data.message || 'Checkin failed';
            }
            
            result.style.display = 'block';
            badgeInput.value = '';
            
            setTimeout(() => {
                result.style.display = 'none';
                badgeInput.focus();
            }, 5000);
            
        } catch (error) {
            result.className = 'error';
            result.innerHTML = 'Error processing checkin';
            result.style.display = 'block';
            badgeInput.value = '';
        }
    });
    
    // Focus on the input field when page loads
    badgeInput.focus();
});