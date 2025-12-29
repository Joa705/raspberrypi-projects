<script>
  import { push } from 'svelte-spa-router';
  import { auth } from './auth.svelte.js';

  let username = '';
  let password = '';
  let error = '';
  let loading = false;

  const API_URL = 'http://localhost:8000';

  async function handleLogin(e) {
    e.preventDefault();
    error = '';
    loading = true;

    try {
      // OAuth2 password flow requires form data
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        auth.login(data.access_token);
        push('/home');
      } else {
        error = data.detail || 'Login failed';
      }
    } catch (err) {
      error = 'Network error. Please check your connection.';
      console.error('Login error:', err);
    } finally {
      loading = false;
    }
  }
</script>

<div class="login-container">
  <div class="login-card">
    <div class="login-header">
      <h1>🥧 Raspberry Pi</h1>
      <h2>Camera Dashboard</h2>
    </div>

    <form on:submit={handleLogin} class="login-form">
      {#if error}
        <div class="error-message">
          {error}
        </div>
      {/if}

      <div class="form-group">
        <label for="username">Username</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          placeholder="Enter username"
          disabled={loading}
          required
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          bind:value={password}
          placeholder="Enter password"
          disabled={loading}
          required
        />
      </div>

      <button type="submit" class="login-button" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>

    <div class="login-footer">
      <p>Default admin credentials: admin / admin</p>
    </div>
  </div>
</div>

<style>
  .login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
  }

  .login-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    padding: 3rem;
    width: 100%;
    max-width: 400px;
  }

  .login-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .login-header h1 {
    font-size: 3rem;
    margin: 0 0 0.5rem 0;
  }

  .login-header h2 {
    font-size: 1.5rem;
    color: #667eea;
    margin: 0;
    font-weight: 600;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .error-message {
    background: #fee;
    color: #c33;
    padding: 0.75rem;
    border-radius: 8px;
    border-left: 4px solid #c33;
    font-size: 0.9rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    font-weight: 600;
    color: #333;
    font-size: 0.9rem;
  }

  .form-group input {
    padding: 0.75rem;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.3s ease;
  }

  .form-group input:focus {
    outline: none;
    border-color: #667eea;
  }

  .form-group input:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }

  .login-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 1rem;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .login-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .login-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .login-footer {
    margin-top: 2rem;
    text-align: center;
    color: #666;
    font-size: 0.85rem;
  }

  .login-footer p {
    margin: 0;
  }

  @media (max-width: 768px) {
    .login-card {
      padding: 2rem;
    }

    .login-header h1 {
      font-size: 2.5rem;
    }

    .login-header h2 {
      font-size: 1.25rem;
    }
  }
</style>
