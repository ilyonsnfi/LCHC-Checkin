document.addEventListener('DOMContentLoaded', function() {
    const result = document.getElementById('result');
    let hideTimeout = null; // Track the current timeout
    let badgeInput = ''; // Store the current input
    
    // Listen for all keypress events on the document
    document.addEventListener('keypress', function(e) {
        // Ignore keypresses when typing in admin link area or if Ctrl/Alt/Cmd is pressed
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || 
            e.ctrlKey || e.altKey || e.metaKey) {
            return;
        }
        
        const char = e.key;
        
        // Handle Enter key as submission
        if (char === 'Enter') {
            if (badgeInput.trim()) {
                processCheckin(badgeInput.trim());
                badgeInput = ''; // Clear input
            }
            return;
        }
        
        // Ignore non-printable characters
        if (char.length !== 1) {
            return;
        }
        
        // Add character to input
        badgeInput += char;
    });
    
    // Handle backspace separately since it's a keydown event
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || 
            e.ctrlKey || e.altKey || e.metaKey) {
            return;
        }
        
        if (e.key === 'Backspace') {
            badgeInput = badgeInput.slice(0, -1);
            e.preventDefault(); // Prevent browser back navigation
        }
    });
    
    async function processCheckin(badgeId) {
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
                `;
                // Play success sound
                playSound('success-sound');
            } else {
                result.className = 'error';
                result.innerHTML = data.message || 'Checkin failed';
                // Play error sound
                playSound('error-sound');
            }
            
            // Clear any existing timeout
            if (hideTimeout) {
                clearTimeout(hideTimeout);
            }
            
            // Set a new timeout
            hideTimeout = setTimeout(() => {
                result.classList.remove('success', 'error');
                hideTimeout = null; // Clear the reference
            }, 5000);
            
        } catch (error) {
            result.className = 'error';
            result.innerHTML = 'Error processing checkin';
            // Play error sound for network/processing errors
            playSound('error-sound');
            
            // Clear any existing timeout
            if (hideTimeout) {
                clearTimeout(hideTimeout);
            }
            
            // Set a new timeout for error case too
            hideTimeout = setTimeout(() => {
                result.classList.remove('success', 'error');
                hideTimeout = null; // Clear the reference
            }, 5000);
        }
    }
});

function playSound(soundId) {
    try {
        const audio = document.getElementById(soundId);
        if (audio) {
            audio.currentTime = 0; // Reset to beginning
            audio.play().catch(e => {
                // Silently handle autoplay restrictions
                console.log('Audio playback prevented:', e);
            });
        }
    } catch (error) {
        console.log('Error playing sound:', error);
    }
}