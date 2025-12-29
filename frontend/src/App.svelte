<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import Router from 'svelte-spa-router';
  import { auth } from './lib/auth.svelte.js';
  import Login from './lib/Login.svelte';
  import Navigation from './lib/Navigation.svelte'
  import SystemInfo from './lib/SystemInfo.svelte'
  import Webrtc from './lib/Webrtc.svelte'

  // Initialize auth from localStorage on mount
  onMount(() => {
    auth.init();
    // Redirect to login if not authenticated
    if (!auth.isAuthenticated && window.location.hash !== '#/login') {
      push('/login');
    }
  });

  // Route guard - redirect to login if not authenticated
  function conditionsFailed(event) {
    if (!auth.isAuthenticated) {
      push('/login');
    }
  }

  // Routes definition
  const routes = {
    '/': SystemInfo,
    '/home': SystemInfo,
    '/stream': Webrtc,
    '/login': Login,
    '*': SystemInfo // 404 fallback
  };
</script>

{#if auth.isAuthenticated}
  <div class="app">
    <Navigation />
    
    <main>
      <Router {routes} on:conditionsFailed={conditionsFailed} />
    </main>
  </div>
{:else}
  <Login />
{/if}

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
