/**
 * Main application JavaScript for Facilities Management AI Agent
 * Following ADK documentation WebSocket pattern exactly
 */

// Import audio worklets
import { startAudioPlayerWorklet } from './audio-player.js';
import { startAudioRecorderWorklet } from './audio-recorder.js';

class FacilitiesAgent {
    constructor() {
        // Generate unique session ID
        this.sessionId = Math.random().toString().substring(10);
        this.websocket = null;
        this.isAudioMode = false;
        this.isConnected = false;
        
        // Audio components
        this.audioPlayerNode = null;
        this.audioPlayerContext = null;
        this.audioRecorderNode = null;
        this.audioRecorderContext = null;
        this.micStream = null;
        
        // UI elements
        this.elements = {
            messagesArea: document.getElementById('messagesArea'),
            messageForm: document.getElementById('messageForm'),
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            startAudioButton: document.getElementById('startAudioButton'),
            audioIndicator: document.getElementById('audioIndicator'),
            connectionStatus: document.getElementById('connectionStatus'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            emergencyBanner: document.getElementById('emergencyBanner')
        };
        
        // Message handling
        this.currentMessageId = null;
        this.isTyping = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        // Form submission
        this.elements.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendTextMessage();
        });
        
        // Audio button
        this.elements.startAudioButton.addEventListener('click', () => {
            this.toggleAudioMode();
        });
        
        // Input focus handling
        this.elements.messageInput.addEventListener('focus', () => {
            this.elements.messageInput.placeholder = 'Type your message...';
        });
        
        this.elements.messageInput.addEventListener('blur', () => {
            if (!this.elements.messageInput.value) {
                this.elements.messageInput.placeholder = 'Type your message here...';
            }
        });
        
        // Enter key handling
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });
    }
    
    connectWebSocket() {
        // Construct WebSocket URL exactly like ADK docs
        const ws_url = "ws://" + window.location.host + "/ws/" + this.sessionId;
        
        try {
            this.websocket = new WebSocket(ws_url + "?is_audio=" + this.isAudioMode);
            this.setupWebSocketHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus('error', 'Connection failed');
        }
    }
    
    setupWebSocketHandlers() {
        // Handle connection open - Following ADK docs pattern
        this.websocket.onopen = () => {
            console.log('WebSocket connection opened.');
            this.isConnected = true;
            this.updateConnectionStatus('connected', 'Connected');
            this.enableInterface();
        };
        
        // Handle incoming messages - Following ADK docs pattern EXACTLY
        this.websocket.onmessage = (event) => {
            // Parse the incoming message - EXACT pattern from ADK docs
            const message_from_server = JSON.parse(event.data);
            console.log("[AGENT TO CLIENT] ", message_from_server);
            
            // Handle interruption - Clear audio buffer immediately when ADK detects interruption
            if (message_from_server.interrupted === true && this.audioPlayerNode) {
                console.log("Interruption detected - clearing audio buffer");
                this.audioPlayerNode.port.postMessage({ command: 'clear_buffer' });
            }
            
            // Check if the turn is complete - EXACT pattern from ADK docs
            if (
                message_from_server.turn_complete &&
                message_from_server.turn_complete == true
            ) {
                this.currentMessageId = null;
                this.hideTypingIndicator();
                return;
            }
            
            // If it's audio, play it - EXACT pattern from ADK docs
            if (message_from_server.mime_type == "audio/pcm" && this.audioPlayerNode) {
                this.audioPlayerNode.port.postMessage(this.base64ToArray(message_from_server.data));
            }
            
            // If it's a text, print it - EXACT pattern from ADK docs
            if (message_from_server.mime_type == "text/plain") {
                // add a new message for a new turn
                if (this.currentMessageId == null) {
                    this.currentMessageId = Math.random().toString(36).substring(7);
                    const message = document.createElement("p");
                    message.id = this.currentMessageId;
                    message.className = "message agent";
                    // Append the message element to the messagesArea
                    this.elements.messagesArea.appendChild(message);
                }
                
                // Add message text to the existing message element
                const message = document.getElementById(this.currentMessageId);
                message.textContent += message_from_server.data;
                
                // Scroll down to the bottom of the messagesArea
                this.elements.messagesArea.scrollTop = this.elements.messagesArea.scrollHeight;
            }
        };
        
        // Handle connection close - Following ADK docs pattern
        this.websocket.onclose = () => {
            console.log('WebSocket connection closed.');
            this.isConnected = false;
            this.updateConnectionStatus('disconnected', 'Disconnected');
            this.disableInterface();
            
            setTimeout(() => {
                console.log('Reconnecting...');
                this.updateConnectionStatus('connecting', 'Reconnecting...');
                this.connectWebSocket();
            }, 5000);
        };
        
        this.websocket.onerror = (error) => {
            console.log('WebSocket error: ', error);
            this.updateConnectionStatus('error', 'Connection error');
        };
    }
    
    sendTextMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Display user message
        this.displayUserMessage(message);
        
        // Clear input
        this.elements.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Check for emergency keywords
        this.checkForEmergency(message);
        
        // Send message - Following ADK docs pattern EXACTLY
        this.sendMessage({
            mime_type: 'text/plain',
            data: message
        });
        
        console.log('[CLIENT TO AGENT] ' + message);
    }
    
    // Send a message to the server as a JSON string - EXACT pattern from ADK docs
    sendMessage(message) {
        if (this.websocket && this.websocket.readyState == WebSocket.OPEN) {
            const messageJson = JSON.stringify(message);
            this.websocket.send(messageJson);
        }
    }
    
    // Decode Base64 data to Array - EXACT pattern from ADK docs
    base64ToArray(base64) {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }
    
    displayUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        this.elements.messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span>AI Assistant is typing...</span>
        `;
        
        this.elements.messagesArea.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        if (!this.isTyping) return;
        
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        this.isTyping = false;
    }
    
    checkForEmergency(message) {
        const emergencyKeywords = [
            'emergency', 'urgent', 'leak', 'fire', 'flood', 'gas', 
            'electrical', 'water', 'burst', 'overflow', 'dangerous', 'safety', 'help'
        ];
        
        const messageLower = message.toLowerCase();
        const hasEmergencyKeyword = emergencyKeywords.some(keyword => 
            messageLower.includes(keyword)
        );
        
        if (hasEmergencyKeyword) {
            this.showEmergencyBanner();
        }
    }
    
    showEmergencyBanner() {
        this.elements.emergencyBanner.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.elements.emergencyBanner.style.display = 'none';
        }, 10000);
    }
    
    async toggleAudioMode() {
        if (!this.isAudioMode) {
            await this.startAudioMode();
        } else {
            this.stopAudioMode();
        }
    }
    
    async startAudioMode() {
        try {
            this.elements.startAudioButton.disabled = true;
            this.elements.startAudioButton.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
                </svg>
                <span>Initializing...</span>
            `;
            
            // Start audio components
            await this.initializeAudio();
            
            // Switch to audio mode
            this.isAudioMode = true;
            
            // Reconnect WebSocket in audio mode
            if (this.websocket) {
                this.websocket.close();
            }
            
            // Show audio indicator
            this.elements.audioIndicator.style.display = 'flex';
            
            // Update button
            this.elements.startAudioButton.className = 'audio-btn active';
            this.elements.startAudioButton.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z"/>
                </svg>
                <span>Stop Voice</span>
            `;
            
            this.elements.startAudioButton.disabled = false;
            
            // Reconnect with audio mode
            setTimeout(() => {
                this.connectWebSocket();
            }, 1000);
            
        } catch (error) {
            console.error('Error starting audio mode:', error);
            this.elements.startAudioButton.disabled = false;
            alert('Could not access microphone. Please check your browser permissions.');
        }
    }
    
    stopAudioMode() {
        this.isAudioMode = false;
        
        // Stop audio components
        this.cleanupAudio();
        
        // Hide audio indicator
        this.elements.audioIndicator.style.display = 'none';
        
        // Update button
        this.elements.startAudioButton.className = 'audio-btn';
        this.elements.startAudioButton.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
            </svg>
            <span>Start Voice</span>
        `;
        
        // Reconnect in text mode
        if (this.websocket) {
            this.websocket.close();
        }
        
        setTimeout(() => {
            this.connectWebSocket();
        }, 1000);
    }
    
    async initializeAudio() {
        // Start audio output - Following ADK docs pattern
        const [playerNode, playerContext] = await startAudioPlayerWorklet();
        this.audioPlayerNode = playerNode;
        this.audioPlayerContext = playerContext;
        
        // Start audio input - Following ADK docs pattern
        const [recorderNode, recorderContext, micStream] = await startAudioRecorderWorklet(
            (pcmData) => this.audioRecorderHandler(pcmData)
        );
        this.audioRecorderNode = recorderNode;
        this.audioRecorderContext = recorderContext;
        this.micStream = micStream;
    }
    
    // Audio recorder handler - EXACT pattern from ADK docs
    audioRecorderHandler(pcmData) {
        // Send the pcm data as base64
        this.sendMessage({
            mime_type: "audio/pcm",
            data: this.arrayBufferToBase64(pcmData),
        });
        console.log("[CLIENT TO AGENT] sent %s bytes", pcmData.byteLength);
    }
    
    // Encode an array buffer with Base64 - EXACT pattern from ADK docs
    arrayBufferToBase64(buffer) {
        let binary = "";
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }
    
    cleanupAudio() {
        // Stop microphone stream
        if (this.micStream) {
            this.micStream.getTracks().forEach(track => track.stop());
            this.micStream = null;
        }
        
        // Close audio contexts
        if (this.audioPlayerContext) {
            this.audioPlayerContext.close();
            this.audioPlayerContext = null;
        }
        
        if (this.audioRecorderContext) {
            this.audioRecorderContext.close();
            this.audioRecorderContext = null;
        }
        
        // Clear audio nodes
        this.audioPlayerNode = null;
        this.audioRecorderNode = null;
    }
    
    updateConnectionStatus(status, text) {
        this.elements.statusIndicator.className = `status-indicator ${status}`;
        this.elements.statusText.textContent = text;
        
        // Update colors based on status
        switch (status) {
            case 'connected':
                this.elements.statusIndicator.style.color = 'var(--success-color)';
                break;
            case 'disconnected':
            case 'error':
                this.elements.statusIndicator.style.color = 'var(--error-color)';
                break;
            case 'connecting':
                this.elements.statusIndicator.style.color = 'var(--warning-color)';
                break;
        }
    }
    
    enableInterface() {
        this.elements.messageInput.disabled = false;
        this.elements.sendButton.disabled = false;
        this.elements.startAudioButton.disabled = false;
        this.elements.messageInput.placeholder = 'Type your message here...';
    }
    
    disableInterface() {
        this.elements.messageInput.disabled = true;
        this.elements.sendButton.disabled = true;
        this.elements.startAudioButton.disabled = true;
        this.elements.messageInput.placeholder = 'Connecting...';
    }
    
    scrollToBottom() {
        this.elements.messagesArea.scrollTop = this.elements.messagesArea.scrollHeight;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.facilitiesAgent = new FacilitiesAgent();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.facilitiesAgent) {
        window.facilitiesAgent.cleanupAudio();
        if (window.facilitiesAgent.websocket) {
            window.facilitiesAgent.websocket.close();
        }
    }
});