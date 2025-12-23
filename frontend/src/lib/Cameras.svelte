<script>
  import { onMount, onDestroy } from 'svelte';
  import { fetchCameras, getCameraStreamUrl, cleanupCamera } from './api.js';

  let cameras = {};
  let loading = true;
  let error = null;
  let activeStreams = new Map();
  let statusInterval;

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
    const streamUrl = getCameraStreamUrl(cameraId);
    activeStreams.set(cameraId, streamUrl);
    activeStreams = activeStreams; // Trigger reactivity
  }

  function stopStream(cameraId) {
    activeStreams.delete(cameraId);
    activeStreams = activeStreams; // Trigger reactivity
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
      await cleanupCamera(cameraId);
      stopStream(cameraId);
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
    // Stop all streams
    activeStreams.clear();
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
              <img 
                src={activeStreams.get(cameraId)} 
                alt={camera.camera_name}
                on:error={() => {
                  error = `Failed to load stream from ${cameraId}`;
                  stopStream(cameraId);
                }}
              />
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

  .stream-container img {
    width: 100%;
    height: auto;
    display: block;
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
