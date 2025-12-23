<script>
  import Navigation from './lib/Navigation.svelte'
  import SystemInfo from './lib/SystemInfo.svelte'
  import Cameras from './lib/Cameras.svelte'

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
</style>
