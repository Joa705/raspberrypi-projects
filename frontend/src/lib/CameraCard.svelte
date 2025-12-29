<script>
    import { onDestroy, onMount } from 'svelte';
    import { fetchCameraStatus, API_BASE } from './api.js';
    
    export let camera; // Camera object with config and status

    let videoElement;
    let pc = null;
    let isConnected = false;
    let isConnecting = false;
    let error = null;
    let connectionState = 'disconnected';
    let statusPollInterval;
    

    // Poll status every 3 seconds
    onMount(() => {
        statusPollInterval = setInterval(async () => {
            try {
                const status = await fetchCameraStatus(camera.camera_id);
                // Update only the status, keep camera config unchanged
                camera = { ...camera, status };
            } catch (err) {
                console.error('Failed to fetch status:', err);
            }
        }, 3000); // Poll every 3 seconds
    });


    function getAuthHeaders() {
        const token = localStorage.getItem('token');
        return {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        };
    }
    
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
                console.log(`Camera ${camera.camera_id}: Received video track`);
                if (videoElement) {
                    videoElement.srcObject = event.streams[0];
                }
                isConnected = true;
                isConnecting = false;
            };
            
            // Handle connection state changes
            pc.onconnectionstatechange = () => {
                connectionState = pc.connectionState;
                console.log(`Camera ${camera.camera_id}: Connection state:`, pc.connectionState);
                
                if (pc.connectionState === 'connected') {
                    isConnected = true;
                    isConnecting = false;
                } else if (pc.connectionState === 'failed' || pc.connectionState === 'closed') {
                    isConnected = false;
                    isConnecting = false;
                    error = 'Connection failed or closed';
                }
            };
            
            // Add transceiver for receiving video only
            pc.addTransceiver('video', { direction: 'recvonly' });
            
            // Create offer
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            
            console.log(`Camera ${camera.camera_id}: Sending offer to server...`);
            
            // Send offer to server
            const response = await fetch(`${API_BASE}/cameras/${camera.camera_id}/webrtc/offer`, {
                method: 'POST',
                headers: getAuthHeaders(),
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
            console.log(`Camera ${camera.camera_id}: Received answer from server`);
            
            // Set remote description (server's answer)
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
            
            console.log(`Camera ${camera.camera_id}: WebRTC connection established`);
            
        } catch (err) {
            console.error(`Camera ${camera.camera_id}: Error starting stream:`, err);
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
        if (statusPollInterval) {
            clearInterval(statusPollInterval);
        }
        stopStream();
    });
</script>

<div class="camera-card">
    <div class="camera-header">
        <h3>{camera.name}</h3>
        <div class="camera-info">
            <span class="ip">{camera.ip_address}</span>
            {#if camera.status.is_running}
                <span class="badge badge-success">Stream Active</span>
            {:else}
                <span class="badge badge-inactive">Inactive</span>
            {/if}
        </div>
    </div>
    
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
                ▶ Start Stream
            </button>
        {:else if isConnected}
            <button on:click={stopStream} class="btn btn-danger">
                ⬛ Stop Stream
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
        
        {#if camera.status.viewer_count > 0}
            <span class="viewers">👁 {camera.status.viewer_count}</span>
        {/if}
    </div>
    
    {#if error}
        <div class="error-message">
            <strong>Error:</strong> {error}
        </div>
    {/if}
    
    {#if camera.description}
        <p class="description">{camera.description}</p>
    {/if}
</div>

<style>
    .camera-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: box-shadow 0.3s;
    }
    
    .camera-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .camera-header {
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .camera-header h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
    }
    
    .camera-info {
        display: flex;
        align-items: center;
        gap: 1rem;
        font-size: 0.9rem;
    }
    
    .ip {
        opacity: 0.9;
    }
    
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-success {
        background: rgba(76, 175, 80, 0.3);
        color: #4CAF50;
    }
    
    .badge-inactive {
        background: rgba(255, 255, 255, 0.2);
        color: rgba(255, 255, 255, 0.8);
    }
    
    .video-wrapper {
        position: relative;
        width: 100%;
        background: #000;
        aspect-ratio: 16 / 9;
    }
    
    .video-element {
        width: 100%;
        height: 100%;
        display: block;
        background: #000;
        object-fit: contain;
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
        font-size: 1rem;
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
        padding: 1rem;
        background: #f5f5f5;
    }
    
    .btn {
        padding: 0.5rem 1.5rem;
        border: none;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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
        width: 10px;
        height: 10px;
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
        font-size: 0.85rem;
        color: #666;
    }
    
    .viewers {
        font-size: 0.85rem;
        color: #666;
    }
    
    .error-message {
        margin: 1rem;
        padding: 0.75rem;
        background: #ffebee;
        color: #c62828;
        border-radius: 6px;
        border-left: 4px solid #f44336;
        font-size: 0.9rem;
    }
    
    .description {
        padding: 0 1rem 1rem;
        margin: 0;
        color: #666;
        font-size: 0.9rem;
    }
</style>
