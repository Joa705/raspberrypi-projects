const API_BASE = 'http://localhost:8000';

export async function fetchSystemInfo() {
  const response = await fetch(`${API_BASE}/system-info`);
  if (!response.ok) {
    throw new Error('Failed to fetch system info');
  }
  return response.json();
}

export async function fetchCameras() {
  const response = await fetch(`${API_BASE}/cameras`);
  if (!response.ok) {
    throw new Error('Failed to fetch cameras');
  }
  return response.json();
}

export function getCameraStreamUrl(cameraId) {
  const timestamp = new Date().getTime();
  return `${API_BASE}/camera/${cameraId}/stream?t=${timestamp}`;
}

export async function cleanupCamera(cameraId) {
  const response = await fetch(`${API_BASE}/camera/${cameraId}/cleanup`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error('Failed to cleanup camera');
  }
  return response.json();
}
