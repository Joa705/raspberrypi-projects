<script>
    import { onMount, onDestroy } from 'svelte';
    
    export let cameraId = 1; // Camera ID to stream
    export let apiUrl = 'http://localhost:8000'; // Backend URL
    
    let videoElement;
    let pc = null;
    let isConnected = false;
    let isConnecting = false;
    let error = null;
    let connectionState = 'disconnected';
    
    async function startStream() {
        try {
            error = null;
            isConnecting = true;
            connectionState = 'connecting';
            
            // Create peer connection
            pc = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' }
                ]
            });
            
            // Handle incoming video track
            pc.ontrack = (event) => {
                console.log('Received video track');
                if (videoElement) {
                    videoElement.srcObject = event.streams[0];
                }
                isConnected = true;
                isConnecting = false;
            };
            
            // Handle connection state changes
            pc.onconnectionstatechange = () => {
                connectionState = pc.connectionState;
                console.log('Connection state:', pc.connectionState);
                
                if (pc.connectionState === 'connected') {
                    isConnected = true;
                    isConnecting = false;
                } else if (pc.connectionState === 'failed' || pc.connectionState === 'closed') {
                    isConnected = false;
                    isConnecting = false;
                    error = 'Connection failed or closed';
                }
            };
            
            // Handle ICE connection state
            pc.oniceconnectionstatechange = () => {
                console.log('ICE connection state:', pc.iceConnectionState);
            };
            
            // Add transceiver for receiving video only
            pc.addTransceiver('video', { direction: 'recvonly' });
            
            // Create offer
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            
            console.log('Sending offer to server...');
            
            // Send offer to server
            const response = await fetch(`${apiUrl}/cameras/${cameraId}/webrtc/offer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sdp: pc.localDescription.sdp,
                    type: pc.localDescription.type
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            const answer = await response.json();
            console.log('Received answer from server');
            
            // Set remote description (server's answer)
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
            
            console.log('WebRTC connection established');
            
        } catch (err) {
            console.error('Error starting stream:', err);
            error = err.message;
            isConnecting = false;
            isConnected = false;
            
            if (pc) {
                pc.close();
                pc = null;
            }
        }
    }
    
    async function stopStream() {
        isConnecting = true;
        
        if (pc) {
            // Close peer connection gracefully
            pc.close();
            pc = null;
        }
        
        if (videoElement) {
            videoElement.srcObject = null;
        }
        
        isConnected = false;
        isConnecting = false;
        connectionState = 'disconnected';
        error = null;
    }
        
    // Cleanup on component destroy
    onDestroy(() => {
        stopStream();
    });
</script>

<div class="webrtc-container">
    <div class="video-wrapper">
        <video 
            bind:this={videoElement}
            autoplay 
            playsinline
            muted={false} 
            controls
            class="video-element"
        >
            <track kind="captions" />
        </video>
        
        {#if !isConnected && !isConnecting}
            <div class="video-overlay">
                <p>Click "Start Stream" to begin</p>
            </div>
        {/if}
        
        {#if isConnecting}
            <div class="video-overlay">
                <div class="spinner"></div>
                <p>Connecting...</p>
            </div>
        {/if}
    </div>
    
    <div class="controls">
        {#if !isConnected && !isConnecting}
            <button on:click={startStream} class="btn btn-primary">
                Start Stream
            </button>
        {:else if isConnected}
            <button on:click={stopStream} class="btn btn-danger">
                Stop Stream
            </button>
        {/if}
        
        <div class="status">
            <span class="status-indicator status-{connectionState}"></span>
            <span class="status-text">
                {#if isConnecting}
                    Connecting...
                {:else if isConnected}
                    Connected
                {:else}
                    Disconnected
                {/if}
            </span>
        </div>
    </div>
    
    {#if error}
        <div class="error-message">
            <strong>Error:</strong> {error}
        </div>
    {/if}
</div>

<style>
    .webrtc-container {
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
    }
    
    .video-wrapper {
        position: relative;
        width: 100%;
        background: #000;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .video-element {
        width: 100%;
        height: auto;
        display: block;
        background: #000;
    }
    
    .video-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.2rem;
    }
    
    .spinner {
        border: 4px solid rgba(255, 255, 255, 0.3);
        border-top: 4px solid white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .controls {
        display: flex;
        gap: 1rem;
        align-items: center;
        margin-top: 1rem;
        padding: 1rem;
        background: #f5f5f5;
        border-radius: 8px;
    }
    
    .btn {
        padding: 0.5rem 1.5rem;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
        transition: opacity 0.2s;
    }
    
    .btn:hover {
        opacity: 0.8;
    }
    
    .btn-primary {
        background: #4CAF50;
        color: white;
    }
    
    .btn-danger {
        background: #f44336;
        color: white;
    }
    
    .status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-left: auto;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #999;
    }
    
    .status-indicator.status-connecting {
        background: #FFC107;
        animation: pulse 1.5s infinite;
    }
    
    .status-indicator.status-connected {
        background: #4CAF50;
    }
    
    .status-indicator.status-disconnected {
        background: #999;
    }
    
    .status-indicator.status-failed,
    .status-indicator.status-closed {
        background: #f44336;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .status-text {
        font-size: 0.9rem;
        color: #666;
    }
    
    .error-message {
        margin-top: 1rem;
        padding: 1rem;
        background: #ffebee;
        color: #c62828;
        border-radius: 4px;
        border-left: 4px solid #f44336;
    }
</style>
