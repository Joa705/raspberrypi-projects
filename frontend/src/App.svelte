<script>
  import Navigation from './lib/Navigation.svelte'
  import SystemInfo from './lib/SystemInfo.svelte'
  import Cameras from './lib/Cameras.svelte'
  import Webrtc from './lib/Webrtc.svelte'

  let currentPage = 'home';

  function handleNavigate(page) {
    currentPage = page;
  }
</script>

<div class="app">
  <Navigation {currentPage} onNavigate={handleNavigate} />
  
  <main>
    {#if currentPage === 'home'}
      <SystemInfo />
    {:else if currentPage === 'cameras'}
      <Cameras />
    {:else if currentPage === 'stream'}
      <div class="page-container">
        <h2>Camera Stream</h2>
        <Webrtc cameraId={1} apiUrl="http://localhost:8000" />
      </div>
    {/if}
  </main>
</div>

<style>
  .app {
    min-height: 100vh;
    background: #f5f5f5;
  }

  main {
    min-height: calc(100vh - 80px);
  }

  .page-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  .page-container h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #333;
  }
</style>
