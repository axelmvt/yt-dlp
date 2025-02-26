// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Toggle advanced options
    const toggleOptions = document.getElementById('toggle-options');
    const optionsContent = document.getElementById('options-content');
    
    if (toggleOptions && optionsContent) {
        toggleOptions.addEventListener('click', function(e) {
            e.preventDefault();
            optionsContent.classList.toggle('show');
            
            // Update the icon and text
            const icon = toggleOptions.querySelector('i');
            if (optionsContent.classList.contains('show')) {
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
                toggleOptions.textContent = 'Hide Advanced Options ';
                toggleOptions.appendChild(icon);
            } else {
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
                toggleOptions.textContent = 'Advanced Options ';
                toggleOptions.appendChild(icon);
            }
        });
    }
    
    // Handle form submission with loading state
    const downloadForm = document.querySelector('form');
    const downloadBtn = document.querySelector('.download-btn');
    
    if (downloadForm && downloadBtn) {
        downloadForm.addEventListener('submit', function() {
            // Show loading state
            const originalText = downloadBtn.textContent;
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
            downloadBtn.disabled = true;
            
            // Form will submit normally
            // We could also implement AJAX submission here if needed
        });
    }
    
    // Automatically hide alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.5s ease';
                
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 500);
            }, 5000);
        });
    }
    
    // URL input focus effect
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.focus();
        
        // Auto paste from clipboard when focused (if permission is granted)
        urlInput.addEventListener('focus', async function() {
            try {
                const text = await navigator.clipboard.readText();
                if (text && urlInput.value === '' && isValidURL(text)) {
                    urlInput.value = text;
                }
            } catch (err) {
                // Clipboard access denied or other error
                console.log('Could not access clipboard');
            }
        });
    }
});

// Helper function to validate URL
function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
} 