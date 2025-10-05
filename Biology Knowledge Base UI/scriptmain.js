const toggleOptions = document.querySelectorAll('.toggle-option');
const iframe = document.getElementById('contentFrame');

toggleOptions.forEach(option => {
    option.addEventListener('click', function() {
        // Remove active class from all options
        toggleOptions.forEach(opt => opt.classList.remove('active'));
        
        // Add active class to clicked option
        this.classList.add('active');
        
        // Get the page to load
        const page = this.getAttribute('data-page');
        
        // Update iframe src
        iframe.src = page + '.html';
    });
});