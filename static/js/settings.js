// Apply dynamic settings from data attributes
document.addEventListener('DOMContentLoaded', function() {
    const body = document.body;
    const root = document.documentElement;
    
    // Get settings from data attributes
    const textColor = body.dataset.textColor;
    const foregroundColor = body.dataset.foregroundColor;
    const backgroundColor = body.dataset.backgroundColor;
    const backgroundImage = body.dataset.backgroundImage;
    
    // Debug logging
    console.log('Settings applied:', {
        textColor,
        foregroundColor,
        backgroundColor,
        backgroundImage
    });
    
    // Apply CSS custom properties
    if (textColor) {
        root.style.setProperty('--text-color', textColor);
    }
    
    if (foregroundColor) {
        root.style.setProperty('--foreground-color', foregroundColor);
    }
    
    if (backgroundColor) {
        root.style.setProperty('--background-color', backgroundColor);
    }
    
    if (backgroundImage && backgroundImage.trim() !== '') {
        const bgUrl = `url("${backgroundImage}")`;
        root.style.setProperty('--background-image', bgUrl);
        console.log('Background image set to:', bgUrl);
    } else {
        root.style.setProperty('--background-image', 'none');
        console.log('Background image set to: none');
    }
});