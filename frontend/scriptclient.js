// NEW - A global variable to hold the latest CSV file content as a string.
var globalCsvFileContent = '';

// Chat History Management with CSV Export
class ChatHistory {
    constructor() {
        this.messages = [];
        this.sessionId = this.generateSessionId();
    }
    
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    addMessage(sender, content) {
        const message = {
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            sender: sender,
            content: content
        };
        this.messages.push(message);
        return message;
    }
    
    getMessages() {
        return this.messages;
    }
    
    clearHistory() {
        this.messages = [];
    }
    
    toCSV() {
        // First, define the header row for the CSV file.
        const headers = 'Timestamp,Session ID,Sender,Message';

        // Then, map each message object to a single CSV row string, which prepares the data.
        const rows = this.messages.map(msg => {
            const escapedContent = this.escapeCSV(msg.content);
            return `${msg.timestamp},${msg.sessionId},${msg.sender},${escapedContent}`;
        });

        // Finally, combine the header with all the message rows to create the final CSV string.
        const csvString = [headers, ...rows].join('\n') + '\n';
        
        // NEW - Update the global variable with the newly generated CSV content.
        globalCsvFileContent = csvString;
        
        // Return the final CSV string.
        return csvString;
    }
    
    escapeCSV(text) {
        if (text.includes(',') || text.includes('\n') || text.includes('"')) {
            return '"' + text.replace(/"/g, '""') + '"';
        }
        return text;
    }
    
    loadFromCSV(file) {
        return new Promise((resolve, reject) => {
            Papa.parse(file, {
                header: true,
                skipEmptyLines: true,
                complete: (results) => {
                    this.messages = results.data.map(row => ({
                        timestamp: row.Timestamp,
                        sessionId: row['Session ID'],
                        sender: row.Sender,
                        content: row.Message
                    }));
                    resolve(this.messages);
                },
                error: (error) => {
                    reject(error);
                }
            });
        });
    }
}

// Helper function for HTML escaping
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Message creation functions (defined globally)
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
        <div class="message-content-container">
            <div class="message-bubble">
                ${escapeHtml(text)}
            </div>
            <div class="message-actions">
                <button class="action_button">Sources</button>
            </div>
        </div>
    `;
    return messageDiv;
}

// NEW FUNCTION: Restore messages to UI
function restoreMessagesUI() {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer || !window.chatHistory) return;
    
    // Clear existing messages
    chatContainer.innerHTML = '';
    
    // Recreate all messages from history
    window.chatHistory.messages.forEach(msg => {
        let messageElement;
        if (msg.sender === 'user') {
            messageElement = createUserMessage(msg.content);
        } else {
            messageElement = createAssistantMessage(msg.content);
        }
        chatContainer.appendChild(messageElement);
    });
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Dropdown functionality
function selectOption(element) {
    const dropdown = document.getElementById('sizeDropdown');
    if (!dropdown) return;
    
    const button = dropdown.querySelector('.dropdown-button');
    if (!button) return;
    
    const buttonText = button.childNodes[0];
    
    buttonText.textContent = element.textContent + ' ';
    dropdown.dataset.selectedSize = element.textContent.toLowerCase(); // Store selected size
    dropdown.classList.remove('open');
}

// Make functions globally accessible
window.restoreMessagesUI = restoreMessagesUI;
window.createUserMessage = createUserMessage;
window.createAssistantMessage = createAssistantMessage;

// Dropdown click handler
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('sizeDropdown');
    if (dropdown && !dropdown.contains(event.target)) {
        dropdown.classList.remove('open');
    }
});

// Chat functionality with history
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const chatContainer = document.querySelector('.chat-container');
    const sizeDropdown = document.getElementById('sizeDropdown');
    
    if (!messageInput || !sendButton || !chatContainer || !sizeDropdown) {
        console.error('Required elements not found');
        return;
    }
    
    // Set default size
    sizeDropdown.dataset.selectedSize = 'light';

    const chatHistory = new ChatHistory();
    window.chatHistory = chatHistory;
    
    // Check if parent window has persistent history and restore it
    try {
        if (window.parent && window.parent !== window && window.parent.persistentChatHistory && window.parent.persistentChatHistory.messages.length > 0) {
            chatHistory.messages = [...window.parent.persistentChatHistory.messages];
            chatHistory.sessionId = window.parent.persistentChatHistory.sessionId;
            
            console.log('Restoring', chatHistory.messages.length, 'messages');
            
            // Restore the UI
            restoreMessagesUI();
        } else {
            console.log('No history to restore');
        }
    } catch (e) {
        console.log('Could not access parent window history:', e);
    }
    
    async function sendMessage() {
        const text = messageInput.value.trim();
        
        if (!text) return;
        
        chatHistory.addMessage('user', text);
        
        const userMessage = createUserMessage(text);
        chatContainer.appendChild(userMessage);
        
        messageInput.value = '';
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Show thinking indicator
        const thinkingMessage = createAssistantMessage('...');
        chatContainer.appendChild(thinkingMessage);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        const selectedSize = sizeDropdown.dataset.selectedSize || 'light';

        try {
            // Get text response from bot
            const chatResponse = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, size: selectedSize })
            });

            if (!chatResponse.ok) {
                throw new Error(`HTTP error! status: ${chatResponse.status}`);
            }

            const chatData = await chatResponse.json();
            const botResponseText = chatData.response;

            // Update thinking message with actual response
            thinkingMessage.querySelector('.message-bubble').innerHTML = escapeHtml(botResponseText);
            chatHistory.addMessage('assistant', botResponseText);

            // Get TTS audio and play it
            const ttsResponse = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: botResponseText })
            });

            if (!ttsResponse.ok) {
                throw new Error(`TTS HTTP error! status: ${ttsResponse.status}`);
            }

            const audioBlob = await ttsResponse.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();

        } catch (error) {
            console.error('Error during bot communication:', error);
            thinkingMessage.querySelector('.message-bubble').innerHTML = 'Sorry, something went wrong.';
            chatHistory.addMessage('assistant', 'Sorry, something went wrong.');
        } finally {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

