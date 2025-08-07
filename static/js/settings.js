// Apply dynamic settings from data attributes
document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const root = document.documentElement;
    
    // Get settings from data attributes
    const containerColor = body.dataset.containerColor;
    const textColor = body.dataset.textColor;
    const backgroundImage = body.dataset.backgroundImage;
    
    // Apply CSS custom properties
    if (containerColor) {
        root.style.setProperty('--container-color', containerColor);
    }
    
    if (textColor) {
        root.style.setProperty('--text-color', textColor);
    }
    
    if (backgroundImage) {
        root.style.setProperty('--background-image', `url("${backgroundImage}")`);
    } else {
        root.style.setProperty('--background-image', 'none');
    }
});