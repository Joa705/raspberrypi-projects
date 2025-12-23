<script>
  import { onMount } from 'svelte';
  import { fetchSystemInfo } from './api.js';

  let systemInfo = null;
  let loading = true;
  let error = null;
  let autoRefresh = true;
  let refreshInterval;

  async function loadSystemInfo() {
    try {
      loading = true;
      error = null;
      systemInfo = await fetchSystemInfo();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    if (autoRefresh) {
      refreshInterval = setInterval(loadSystemInfo, 5000);
    }
  }

  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  }

  onMount(() => {
    loadSystemInfo();
    startAutoRefresh();
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });

  $: if (autoRefresh) {
    startAutoRefresh();
  } else if (refreshInterval) {
    clearInterval(refreshInterval);
  }
</script>

<div class="system-info">
  <div class="header">
    <h2>📊 System Information</h2>
    <div class="controls">
      <label class="toggle">
        <input type="checkbox" bind:checked={autoRefresh} on:change={toggleAutoRefresh} />
        Auto-refresh (5s)
      </label>
      <button class="refresh-btn" on:click={loadSystemInfo} disabled={loading}>
        {loading ? '⏳' : '🔄'} Refresh
      </button>
    </div>
  </div>

  {#if loading && !systemInfo}
    <div class="loading">Loading system information...</div>
  {:else if error}
    <div class="error">
      ❌ Error: {error}
      <button on:click={loadSystemInfo}>Retry</button>
    </div>
  {:else if systemInfo}
    <div class="info-grid">
      <!-- CPU Card -->
      <div class="card">
        <h3>🖥️ CPU</h3>
        <div class="metric">
          <span class="label">Overall Usage:</span>
          <span class="value">{systemInfo.cpu.usage_percent}%</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {systemInfo.cpu.usage_percent}%"></div>
          </div>
        </div>
        {#if systemInfo.cpu.per_core}
          <div class="metric-full">
            <span class="label">Per-Core Usage:</span>
            {#each systemInfo.cpu.per_core as coreUsage, index}
              <div class="core-metric">
                <span class="core-label">Core {index}:</span>
                <span class="core-value">{coreUsage}%</span>
                <div class="progress-bar-small">
                  <div class="progress-fill" style="width: {coreUsage}%"></div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
        <div class="metric">
          <span class="label">Cores:</span>
          <span class="value">{systemInfo.cpu.cores}</span>
        </div>
        {#if systemInfo.cpu.frequency_mhz}
          <div class="metric">
            <span class="label">Frequency:</span>
            <span class="value">{systemInfo.cpu.frequency_mhz} MHz</span>
          </div>
        {/if}
        <div class="metric">
          <span class="label">Load Avg (1/5/15 min):</span>
          <span class="value">
            {systemInfo.cpu.load_average['1min']} / 
            {systemInfo.cpu.load_average['5min']} / 
            {systemInfo.cpu.load_average['15min']}
          </span>
        </div>
      </div>

      <!-- Memory Card -->
      <div class="card">
        <h3>💾 Memory</h3>
        <div class="metric">
          <span class="label">Used / Total:</span>
          <span class="value">{systemInfo.memory.used_gb} GB / {systemInfo.memory.total_gb} GB</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {systemInfo.memory.percent}%"></div>
          </div>
        </div>
        <div class="metric">
          <span class="label">Available:</span>
          <span class="value">{systemInfo.memory.available_gb} GB</span>
        </div>
        <div class="metric">
          <span class="label">Usage:</span>
          <span class="value">{systemInfo.memory.percent}%</span>
        </div>
      </div>

      <!-- Temperature Card -->
      {#if systemInfo.temperature}
        <div class="card">
          <h3>🌡️ Temperature</h3>
          <div class="metric">
            <span class="label">CPU Temp:</span>
            <span class="value temp" class:hot={systemInfo.temperature.celsius > 70}>
              {systemInfo.temperature.celsius}°C / {systemInfo.temperature.fahrenheit}°F
            </span>
          </div>
        </div>
      {/if}

      <!-- Disk Card -->
      <div class="card">
        <h3>💿 Disk</h3>
        <div class="metric">
          <span class="label">Used / Total:</span>
          <span class="value">{systemInfo.disk.used_gb} GB / {systemInfo.disk.total_gb} GB</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {systemInfo.disk.percent}%"></div>
          </div>
        </div>
        <div class="metric">
          <span class="label">Free:</span>
          <span class="value">{systemInfo.disk.free_gb} GB</span>
        </div>
        <div class="metric">
          <span class="label">Usage:</span>
          <span class="value">{systemInfo.disk.percent}%</span>
        </div>
      </div>

      <!-- Uptime Card -->
      <div class="card">
        <h3>⏱️ Uptime</h3>
        <div class="metric">
          <span class="label">Hours:</span>
          <span class="value">{systemInfo.uptime.hours}</span>
        </div>
        <div class="metric">
          <span class="label">Boot Time:</span>
          <span class="value">{new Date(systemInfo.uptime.boot_time).toLocaleString()}</span>
        </div>
      </div>

      <!-- Camera Stats Card -->
      <div class="card">
        <h3>🎥 Camera Streams</h3>
        <div class="metric">
          <span class="label">Active Streams:</span>
          <span class="value">{systemInfo.cameras.active_streams}</span>
        </div>
        <div class="metric">
          <span class="label">Total Viewers:</span>
          <span class="value">{systemInfo.cameras.total_viewers}</span>
        </div>
        <div class="metric">
          <span class="label">Total Cameras:</span>
          <span class="value">{systemInfo.cameras.total_cameras}</span>
        </div>
      </div>
    </div>

    <div class="timestamp">
      Last updated: {new Date(systemInfo.timestamp).toLocaleString()}
    </div>
  {/if}
</div>

<style>
  .system-info {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .header h2 {
    margin: 0;
    color: #333;
  }

  .controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #666;
    cursor: pointer;
  }

  .refresh-btn {
    background: #667eea;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.3s;
  }

  .refresh-btn:hover:not(:disabled) {
    background: #5568d3;
  }

  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .loading, .error {
    text-align: center;
    padding: 3rem;
    font-size: 1.2rem;
    color: #666;
  }

  .error {
    color: #d32f2f;
  }

  .error button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #d32f2f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1rem;
  }

  .card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .card h3 {
    margin: 0 0 1rem 0;
    color: #667eea;
    font-size: 1.2rem;
  }

  .metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
  }

  .metric-full {
    margin-bottom: 1rem;
  }

  .metric-full .label {
    display: block;
    margin-bottom: 0.5rem;
  }

  .core-metric {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .core-label {
    color: #666;
    font-size: 0.85rem;
    min-width: 50px;
  }

  .core-value {
    font-weight: bold;
    color: #333;
    min-width: 40px;
    font-size: 0.85rem;
  }

  .label {
    color: #666;
    font-size: 0.9rem;
  }

  .value {
    font-weight: bold;
    color: #333;
  }

  .value.temp.hot {
    color: #d32f2f;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 0.5rem;
  }

  .progress-bar-small {
    flex: 1;
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.3s ease;
  }

  .timestamp {
    text-align: center;
    color: #999;
    font-size: 0.9rem;
    margin-top: 2rem;
  }

  @media (max-width: 768px) {
    .system-info {
      padding: 1rem;
    }

    .header {
      flex-direction: column;
      gap: 1rem;
    }

    .info-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
