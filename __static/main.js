// Basic JavaScript for Status Page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Status Page loaded successfully');
    
    // Add some basic interactivity
    const statusCards = document.querySelectorAll('.status-card');
    statusCards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.transform = this.style.transform === 'scale(1.02)' ? 'scale(1)' : 'scale(1.02)';
            this.style.transition = 'transform 0.3s ease';
        });
    });
    
    // Auto-refresh status (example)
    setInterval(function() {
        console.log('Status check...');
    }, 60000);
});
