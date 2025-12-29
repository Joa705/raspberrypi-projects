/**
 * Authentication store and utilities for Svelte 5
 */

// Create a reactive auth state using Svelte 5 runes
class AuthStore {
  isAuthenticated = $state(false);
  token = $state(null);
  user = $state(null);

  login(token) {
    localStorage.setItem('token', token);
    this.token = token;
    this.isAuthenticated = true;
  }

  logout() {
    localStorage.removeItem('token');
    this.token = null;
    this.isAuthenticated = false;
    this.user = null;
    
    // Redirect to login - use setTimeout to avoid circular dependency
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        window.location.hash = '#/login';
      }, 0);
    }
  }

  init() {
    const token = localStorage.getItem('token');
    if (token) {
      this.token = token;
      this.isAuthenticated = true;
    }
  }
}

export const auth = new AuthStore();

/**
 * Make authenticated API request
 */
export async function apiRequest(url, options = {}) {
  const token = localStorage.getItem('token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  // If unauthorized, logout
  if (response.status === 401) {
    auth.logout();
  }

  return response;
}
