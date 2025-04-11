class ChatApp {
    constructor() {
        this.socket = null;
        this.roomId = 'default-room';
        this.initializeElements();
        this.setupEventListeners();
        this.connectWebSocket();
    }

    initializeElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.sourceLang = document.getElementById('sourceLang');
        this.targetLang = document.getElementById('targetLang');
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = '8000'; // Match your FastAPI server port
        const wsUrl = `${protocol}//${host}:${port}/ws/chat/${this.roomId}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
            this.addSystemMessage('Connected to chat server');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            this.addSystemMessage('Disconnected from chat server');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addSystemMessage('Connection error occurred');
        };
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.socket || this.socket.readyState !== WebSocket.OPEN) return;

        const data = {
            text: message,
            source_lang: this.sourceLang.value,
            target_lang: this.targetLang.value
        };

        this.socket.send(JSON.stringify(data));
        this.addMessage(message, 'sent');
        this.messageInput.value = '';
    }

    handleMessage(data) {
        if (data.type === 'system') {
            this.addSystemMessage(data.message);
        } else {
            this.addMessage(data.text, 'received', data.translation);
        }
    }

    addMessage(text, type, translation = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;

        if (translation) {
            const translationDiv = document.createElement('div');
            translationDiv.className = 'translation';
            translationDiv.textContent = translation;
            messageDiv.appendChild(translationDiv);
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addSystemMessage(message) {
        const systemDiv = document.createElement('div');
        systemDiv.className = 'message system';
        systemDiv.textContent = message;
        this.chatMessages.appendChild(systemDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the chat application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
