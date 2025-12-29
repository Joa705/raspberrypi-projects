<script>
  import { link, location } from 'svelte-spa-router';
  import { auth } from './auth.svelte.js';

  function handleLogout() {
    auth.logout();
  }

  // Check if a route is active
  function isActive(path) {
    return $location === path || ($location === '/' && path === '/home');
  }
</script>

<nav class="navbar">
  <div class="nav-container">
    <h1 class="logo">🥧 Raspberry Pi Dashboard</h1>
    <div class="nav-links">
      <a 
        href="/home"
        use:link
        class="nav-link" 
        class:active={isActive('/home') || isActive('/')}
      >
        <span class="icon">🏠</span>
        System Info
      </a>
      <a 
        href="/stream"
        use:link
        class="nav-link" 
        class:active={isActive('/stream')}
      >
        <span class="icon">📹</span>
        Stream
      </a>
      <button 
        class="nav-link logout"
        on:click={handleLogout}
      >
        <span class="icon">🚪</span>
        Logout
      </button>
    </div>
  </div>
</nav>

<style>
  .navbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .nav-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .logo {
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0;
  }

  .nav-links {
    display: flex;
    gap: 1rem;
  }

  .nav-link {
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid transparent;
    color: white;
    padding: 0.5rem 1.5rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.3s ease;
    text-decoration: none;
  }

  .nav-link:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }

  .nav-link.active {
    background: white;
    color: #667eea;
    border-color: white;
  }

  .nav-link.logout:hover {
    background: rgba(255, 100, 100, 0.3);
  }

  .icon {
    font-size: 1.2rem;
  }

  @media (max-width: 768px) {
    .nav-container {
      flex-direction: column;
      gap: 1rem;
    }

    .nav-links {
      width: 100%;
      justify-content: center;
    }
  }
</style>
