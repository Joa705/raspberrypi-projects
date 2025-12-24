<script>
  import { onMount, onDestroy } from 'svelte';
  import { fetchCameras, cleanupCamera } from './api.js';

  let cameras = {};
  let loading = true;
  let error = null;
  let activeStreams = new Map(); // Map<cameraId, WebSocket>
  let canvasRefs = new Map(); // Map<cameraId, canvas element>
  let intentionalCloses = new Set(); // Track intentional closes by cameraId
  let statusInterval;

  // Action to bind canvas element to Map
  function bindCanvas(node, cameraId) {
    canvasRefs.set(cameraId, node);
    return {
      destroy() {
        canvasRefs.delete(cameraId);
      }
    };
  }

  async function loadCameras() {
    try {
      const data = await fetchCameras();
      cameras = data.cameras;
      error = null;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function startStream(cameraId) {
    // Prevent duplicate connections
    if (activeStreams.has(cameraId)) {
      console.log(`Stream ${cameraId} already active`);
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/camera/${cameraId}/ws`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      console.log(`Camera ${cameraId}: WebSocket connected`);
      activeStreams.set(cameraId, ws);
      activeStreams = activeStreams; // Trigger reactivity
    };

    ws.onmessage = async (event) => {
      // Draw frame directly to canvas (no blob URL needed!)
      const canvas = canvasRefs.get(cameraId);
      if (!canvas) return;
      
      try {
        const blob = new Blob([event.data], { type: 'image/jpeg' });
        const imageBitmap = await createImageBitmap(blob);
        
        const ctx = canvas.getContext('2d');
        canvas.width = imageBitmap.width;
        canvas.height = imageBitmap.height;
        ctx.drawImage(imageBitmap, 0, 0);
        
        imageBitmap.close(); // Free memory
      } catch (err) {
        console.error(`Camera ${cameraId}: Error drawing frame`, err);
      }
    };

    ws.onerror = (err) => {
      // Only show error if not an intentional close
      if (!intentionalCloses.has(cameraId) && ws.readyState !== WebSocket.CLOSED) {
        console.error(`Camera ${cameraId}: WebSocket error`, err);
        error = `Connection error for camera ${cameraId}`;
      }
    };

    ws.onclose = () => {
      console.log(`Camera ${cameraId}: WebSocket closed`);
      activeStreams.delete(cameraId);
      intentionalCloses.delete(cameraId); // Clean up tracking
      activeStreams = activeStreams; // Trigger reactivity
      
      // Clear canvas
      const canvas = canvasRefs.get(cameraId);
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    };
  }

  function stopStream(cameraId) {
    const ws = activeStreams.get(cameraId);
    if (ws) {
      console.log(`Camera ${cameraId}: Closing WebSocket`);
      
      // Mark as intentional close to prevent error logging
      intentionalCloses.add(cameraId);
      
      // Only close if not already closed/closing
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      
      // Cleanup happens in ws.onclose handler
    }
  }

  function toggleStream(cameraId) {
    if (activeStreams.has(cameraId)) {
      stopStream(cameraId);
    } else {
      startStream(cameraId);
    }
  }

  async function forceCleanup(cameraId) {
    try {
      stopStream(cameraId); // Close WebSocket first
      await cleanupCamera(cameraId);
      await loadCameras();
    } catch (e) {
      error = `Failed to cleanup ${cameraId}: ${e.message}`;
    }
  }

  onMount(() => {
    loadCameras();
    // Poll for camera status updates
    statusInterval = setInterval(loadCameras, 2000);
  });

  onDestroy(() => {
    if (statusInterval) clearInterval(statusInterval);
    
    // Close all WebSocket connections
    activeStreams.forEach((ws, cameraId) => {
      console.log(`Cleanup: Closing WebSocket for ${cameraId}`);
      ws.close();
    });
    activeStreams.clear();
    canvasRefs.clear();
  });
</script>

<div class="cameras">
  <div class="header">
    <h2>🎥 Camera Monitor</h2>
    <div class="info-box">
      Streams start when you click "Start Stream" and stop when you click "Stop Stream".
      Multiple viewers can watch the same camera without creating duplicate streams.
    </div>
  </div>

  {#if error}
    <div class="error-box">
      ❌ Error: {error}
      <button on:click={loadCameras}>Retry</button>
    </div>
  {/if}

  {#if loading}
    <div class="loading">Loading cameras...</div>
  {:else}
    <div class="camera-grid">
      {#each Object.entries(cameras) as [cameraId, camera]}
        <div class="camera-card">
          <h3>{camera.camera_name}</h3>
          
          <div class="stream-container">
            {#if activeStreams.has(cameraId)}
              <canvas 
                use:bindCanvas={cameraId}
                class="stream-canvas"
              ></canvas>
            {:else}
              <div class="placeholder">Stream not started</div>
            {/if}
          </div>

          <div class="button-group">
            <button 
              class="stream-btn"
              class:stop={activeStreams.has(cameraId)}
              on:click={() => toggleStream(cameraId)}
            >
              {activeStreams.has(cameraId) ? '⏹️ Stop Stream' : '▶️ Start Stream'}
            </button>
            
            {#if camera.is_running}
              <button 
                class="cleanup-btn"
                on:click={() => forceCleanup(cameraId)}
                title="Force stop the stream completely on the backend"
              >
                🗑️ Force Cleanup
              </button>
            {/if}
          </div>

          <div class="status">
            <div class="status-item">
              <span class="label">Status:</span>
              <span 
                class="value" 
                class:running={camera.is_running}
                class:stopped={!camera.is_running}
              >
                {camera.is_running ? 'Running' : 'Stopped'}
              </span>
            </div>
            <div class="status-item">
              <span class="label">Viewers:</span>
              <span class="value">{camera.viewer_count}</span>
            </div>
            <div class="status-item">
              <span class="label">IP:</span>
              <span class="value">{camera.ip_address}</span>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .cameras {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .header {
    margin-bottom: 2rem;
  }

  .header h2 {
    margin: 0 0 1rem 0;
    color: #333;
  }

  .info-box {
    background: #e3f2fd;
    border-left: 4px solid #2196f3;
    padding: 1rem;
    border-radius: 4px;
    color: #0d47a1;
  }

  .error-box {
    background: #ffebee;
    border-left: 4px solid #f44336;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    color: #c62828;
  }

  .error-box button {
    margin-left: 1rem;
    padding: 0.5rem 1rem;
    background: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .loading {
    text-align: center;
    padding: 3rem;
    font-size: 1.2rem;
    color: #666;
  }

  .camera-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 2rem;
  }

  .camera-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .camera-card h3 {
    margin: 0 0 1rem 0;
    color: #667eea;
  }

  .stream-container {
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
  }

  .stream-container img,
  .stream-container canvas {
    width: 100%;
    height: auto;
    display: block;
  }

  .connecting {
    color: #2196f3;
    padding: 2rem;
    font-size: 1.1rem;
  }

  .placeholder {
    color: #999;
    padding: 2rem;
  }

  .button-group {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .stream-btn {
    flex: 1;
    padding: 0.75rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s;
  }

  .stream-btn:hover {
    background: #5568d3;
    transform: translateY(-2px);
  }

  .stream-btn.stop {
    background: #f44336;
  }

  .stream-btn.stop:hover {
    background: #d32f2f;
  }

  .cleanup-btn {
    padding: 0.75rem 1rem;
    background: #ff9800;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s;
    white-space: nowrap;
  }

  .cleanup-btn:hover {
    background: #f57c00;
    transform: translateY(-2px);
  }

  .status {
    background: #f9f9f9;
    padding: 1rem;
    border-radius: 8px;
  }

  .status-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .status-item:last-child {
    margin-bottom: 0;
  }

  .label {
    color: #666;
    font-weight: bold;
  }

  .value {
    color: #333;
  }

  .value.running {
    color: #4caf50;
    font-weight: bold;
  }

  .value.stopped {
    color: #999;
  }

  @media (max-width: 768px) {
    .cameras {
      padding: 1rem;
    }

    .camera-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
