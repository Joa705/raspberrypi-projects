<script>
    import { onMount } from 'svelte';
    import { fetchCamerasStatuses } from './api.js';
    import CameraCard from './CameraCard.svelte';
    
    let cameras = [];
    let loading = true;
    let error = null;
    
    async function loadCameras() {
        try {
            loading = true;
            error = null;
            cameras = await fetchCamerasStatuses();
        } catch (err) {
            console.error('Error loading cameras:', err);
            error = err.message;
        } finally {
            loading = false;
        }
    }
    
    onMount(() => {
        loadCameras();
    });
</script>

<div class="cameras-container">
    <div class="header">
        <h2>Camera Streams</h2>
        <button on:click={loadCameras} class="btn-refresh" disabled={loading}>
            {loading ? '🔄 Loading...' : '🔄 Refresh'}
        </button>
    </div>
    
    {#if loading}
        <div class="loading">
            <div class="spinner-large"></div>
            <p>Loading cameras...</p>
        </div>
    {:else if error}
        <div class="error-box">
            <strong>Error loading cameras:</strong> {error}
            <button on:click={loadCameras} class="btn-retry">Try Again</button>
        </div>
    {:else if cameras.length === 0}
        <div class="empty-state">
            <p>No cameras configured yet.</p>
            <p class="hint">Add cameras to start streaming.</p>
        </div>
    {:else}
        <div class="cameras-grid">
            {#each cameras as camera (camera.camera_id)}
                <CameraCard {camera} />
            {/each}
        </div>
    {/if}
</div>

<style>
    .cameras-container {
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
        font-size: 2rem;
        color: #333;
        margin: 0;
    }
    
    .btn-refresh {
        padding: 0.5rem 1rem;
        background: white;
        border: 2px solid #667eea;
        color: #667eea;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .btn-refresh:hover:not(:disabled) {
        background: #667eea;
        color: white;
    }
    
    .btn-refresh:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        color: #666;
    }
    
    .spinner-large {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .error-box {
        padding: 2rem;
        background: #ffebee;
        color: #c62828;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        text-align: center;
    }
    
    .btn-retry {
        margin-top: 1rem;
        padding: 0.5rem 1.5rem;
        background: #f44336;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
    }
    
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #666;
    }
    
    .empty-state p {
        margin: 0.5rem 0;
        font-size: 1.1rem;
    }
    
    .hint {
        color: #999;
        font-size: 0.9rem !important;
    }
    
    .cameras-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
        gap: 2rem;
    }
    
    @media (max-width: 768px) {
        .cameras-grid {
            grid-template-columns: 1fr;
        }
        
        .header {
            flex-direction: column;
            gap: 1rem;
            align-items: stretch;
        }
    }
</style>
