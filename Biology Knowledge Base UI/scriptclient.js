// Dropdown functionality
function selectOption(element) {
    const dropdown = document.getElementById('resolutionDropdown');
    const button = dropdown.querySelector('.dropdown-button');
    const buttonText = button.childNodes[0];
    
    // Update button text (keep the SVG)
    buttonText.textContent = element.textContent + ' ';
    
    // Close dropdown
    dropdown.classList.remove('open');
}

// Close dropdown when clicking outsideS
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('resolutionDropdown');
    if (dropdown && !dropdown.contains(event.target)) {
        dropdown.classList.remove('open');
    }
});

// Chat functionality
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const chatContainer = document.querySelector('.chat-container');
    
    if (!messageInput || !sendButton || !chatContainer) return;
    
    function createUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${escapeHtml(text)}
            </div>
            <div class="user-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
            </div>
        `;
        return messageDiv;
    }
    
    function createAssistantMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${escapeHtml(text)}
            </div>
            <div class="avatar">
                <svg viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="9" cy="10" r="1.5" fill="#5a5a5a"/>
                    <circle cx="15" cy="10" r="1.5" fill="#5a5a5a"/>
                    <path d="M12 17c-2 0-3.5-1-4-2h8c-0.5 1-2 2-4 2z" fill="#5a5a5a"/>
                </svg>
            </div>
        `;
        return messageDiv;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function sendMessage() {
        const text = messageInput.value.trim();
        
        if (!text) return;
        
        // Add user message
        const userMessage = createUserMessage(text);
        chatContainer.appendChild(userMessage);
        
        // Clear input
        messageInput.value = '';
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Send bot reply after a short delay
        setTimeout(() => {
            const botMessage = createAssistantMessage('default');
            chatContainer.appendChild(botMessage);
            
            // Scroll to bottom again
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 500);
    }
    
    // Send button click
    sendButton.addEventListener('click', sendMessage);
    
    // Enter key press
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});