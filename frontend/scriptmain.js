// Global storage for chat history in parent window
window.persistentChatHistory = {
    messages: [],
    sessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
};

const toggleOptions = document.querySelectorAll('.toggle-option');
const iframe = document.getElementById('contentFrame');

// Function to save chat history from iframe to parent
function saveChatHistoryFromIframe() {
    if (iframe.contentWindow && typeof iframe.contentWindow.chatHistory !== 'undefined') {
        const iframeHistory = iframe.contentWindow.chatHistory;
        if (iframeHistory && iframeHistory.messages) {
            window.persistentChatHistory.messages = [...iframeHistory.messages];
            window.persistentChatHistory.sessionId = iframeHistory.sessionId;
        }
    }
}

// Function to restore chat history to iframe after page load
function restoreChatHistoryToIframe() {
    if (iframe.contentWindow && typeof iframe.contentWindow.chatHistory !== 'undefined') {
        const iframeHistory = iframe.contentWindow.chatHistory;
        if (iframeHistory && window.persistentChatHistory.messages.length > 0) {
            iframeHistory.messages = [...window.persistentChatHistory.messages];
            iframeHistory.sessionId = window.persistentChatHistory.sessionId;
            
            // Restore visual messages in the chat container
            if (typeof iframe.contentWindow.restoreMessagesUI === 'function') {
                iframe.contentWindow.restoreMessagesUI();
            }
        }
    }
}

// Listen for iframe load event to restore history
iframe.addEventListener('load', function() {
    // Wait a bit for the iframe's scripts to initialize
    setTimeout(() => {
        restoreChatHistoryToIframe();
    }, 100);
});

toggleOptions.forEach(option => {
    option.addEventListener('click', function() {
        // Save chat history before navigating away
        saveChatHistoryFromIframe();

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

// Also save history periodically (every 5 seconds) as a backup
setInterval(() => {
    saveChatHistoryFromIframe();
}, 5000);

// Save history before page unload
window.addEventListener('beforeunload', () => {
    saveChatHistoryFromIframe();
});