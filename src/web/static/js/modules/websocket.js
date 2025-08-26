// Catalynx WebSocket Module
// Real-time communication module extracted from monolithic app.js

class CatalynxWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 5000; // 5 seconds
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.listeners = new Map();
        this.isConnecting = false;
        this.isManualClose = false;
        this.heartbeatInterval = null;
        this.heartbeatTimeout = 30000; // 30 seconds
    }
    
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
            console.log('WebSocket already connected or connecting');
            return;
        }
        
        this.isConnecting = true;
        this.isManualClose = false;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('WebSocket connected successfully');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            this.emit('connected', { event });
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data.type, data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error, event.data);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            this.isConnecting = false;
            this.stopHeartbeat();
            
            if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
                this.scheduleReconnect();
            }
            
            this.emit('disconnected', { event });
        };
        
        this.ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            this.emit('error', { event });
        };
    }
    
    handleMessage(data) {
        const { type } = data;
        
        switch (type) {
            case 'connection_established':
                this.emit('connection_established', data);
                break;
            case 'progress_update':
                this.emit('progress_update', data);
                break;
            case 'system_status':
                this.emit('system_status', data);
                break;
            case 'pong':
                this.emit('pong', data);
                break;
            case 'error':
                this.emit('ws_error', data);
                break;
            default:
                this.emit('message', data);
        }
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                const message = typeof data === 'string' ? data : JSON.stringify(data);
                this.ws.send(message);
                return true;
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
                return false;
            }
        } else {
            console.warn('WebSocket is not connected. Message not sent:', data);
            return false;
        }
    }
    
    subscribeToProgress(workflowId) {
        return this.send({
            type: 'subscribe_progress',
            workflow_id: workflowId
        });
    }
    
    ping() {
        return this.send({
            type: 'ping'
        });
    }
    
    getStatus() {
        return this.send({
            type: 'get_status'
        });
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.ping();
        }, this.heartbeatTimeout);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    scheduleReconnect() {
        if (this.isManualClose) return;
        
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);
        
        setTimeout(() => {
            if (!this.isManualClose) {
                this.connect();
            }
        }, delay);
    }
    
    disconnect() {
        console.log('Manually disconnecting WebSocket');
        this.isManualClose = true;
        this.stopHeartbeat();
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    // Event system
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
        
        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(event);
            if (callbacks) {
                const index = callbacks.indexOf(callback);
                if (index > -1) {
                    callbacks.splice(index, 1);
                }
            }
        };
    }
    
    off(event, callback) {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in WebSocket event callback for '${event}':`, error);
                }
            });
        }
    }
    
    getConnectionState() {
        if (!this.ws) return 'CLOSED';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'CONNECTING';
            case WebSocket.OPEN:
                return 'OPEN';
            case WebSocket.CLOSING:
                return 'CLOSING';
            case WebSocket.CLOSED:
                return 'CLOSED';
            default:
                return 'UNKNOWN';
        }
    }
    
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Create global WebSocket instance
const websocket = new CatalynxWebSocket();
window.CatalynxWebSocket = websocket;

// Auto-connect when module is loaded
document.addEventListener('DOMContentLoaded', () => {
    websocket.connect();
});

// Reconnect when page becomes visible (handles laptop sleep/wake)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !websocket.isConnected()) {
        console.log('Page became visible, checking WebSocket connection...');
        websocket.connect();
    }
});

export default websocket;