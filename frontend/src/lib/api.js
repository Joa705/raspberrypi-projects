const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
}

export async function fetchSystemInfo() {
  const response = await fetch(`${API_BASE}/system-info`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error('Failed to fetch system info');
  }
  return response.json();
}

export async function fetchCamerasStatuses() {
  const response = await fetch(`${API_BASE}/cameras/statuses`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error('Failed to fetch cameras statuses');
  }
  return response.json();
}

export async function fetchCameraStatus(cameraId) {
  const response = await fetch(`${API_BASE}/cameras/${cameraId}/status`, {
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error('Failed to fetch camera status');
  }
  return response.json();
}

export async function cleanupCamera(cameraId) {
  const response = await fetch(`${API_BASE}/camera/${cameraId}/cleanup`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!response.ok) {
    throw new Error('Failed to cleanup camera');
  }
  return response.json();
}
