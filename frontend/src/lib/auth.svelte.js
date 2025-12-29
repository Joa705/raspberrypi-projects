/**
 * Authentication store and utilities for Svelte 5
 */

// Create a reactive auth state using Svelte 5 runes
class AuthStore {
  isAuthenticated = $state(false);
  token = $state(null);
  user = $state(null);
  is_admin = $state(false);

  login(token, is_admin) {
    localStorage.setItem('token', token);
    this.token = token;
    this.isAuthenticated = true;
    localStorage.setItem('is_admin', is_admin ? 'true' : 'false');
    this.is_admin = is_admin;
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('is_admin');
    this.token = null;
    this.isAuthenticated = false;
    this.user = null;
    this.is_admin = false;
    
    // Redirect to login - use setTimeout to avoid circular dependency
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        window.location.hash = '#/login';
      }, 0);
    }
  }

  init() {
    const token = localStorage.getItem('token');
    const is_admin = localStorage.getItem('is_admin') === 'true';
    if (token) {
      this.token = token;
      this.isAuthenticated = true;
      this.is_admin = is_admin; 
    }

  }
}

export const auth = new AuthStore();


