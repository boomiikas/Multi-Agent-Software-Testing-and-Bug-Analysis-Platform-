const API_BASE = import.meta.env.VITE_API_URL || '/api';

const TOKEN_KEY = 'agentqa_token';
const REMEMBER_KEY = 'agentqa_remember';

// "Remember me" controls where the token is persisted: localStorage
// survives closing the browser, sessionStorage clears when the tab closes.
export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

export function storeToken(token, rememberMe) {
  clearToken();
  if (rememberMe) localStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(REMEMBER_KEY, rememberMe ? '1' : '0');
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REMEMBER_KEY);
}

let onUnauthorized = null;
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = getStoredToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // no JSON body
  }

  if (res.status === 401 && auth) {
    onUnauthorized?.();
  }

  if (!res.ok) {
    const error = new Error(data?.error || 'Something went wrong. Please try again.');
    error.status = res.status;
    error.errors = data?.errors;
    throw error;
  }

  return data;
}

export const authApi = {
  register: (fullName, email, password) => request('/auth/register', { method: 'POST', body: { fullName, email, password }, auth: false }),
  login: (email, password, rememberMe) => request('/auth/login', { method: 'POST', body: { email, password, rememberMe }, auth: false }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  forgotPassword: (email) => request('/auth/forgot-password', { method: 'POST', body: { email }, auth: false }),
  resetPassword: (token, password) => request('/auth/reset-password', { method: 'POST', body: { token, password }, auth: false }),
  changePassword: (currentPassword, password) => request('/auth/change-password', { method: 'PUT', body: { currentPassword, password } }),
};

export const userApi = {
  getProfile: () => request('/users/profile'),
  updateProfile: (updates) => request('/users/profile', { method: 'PUT', body: updates }),
};

export const adminApi = {
  listUsers: () => request('/admin/users'),
  createUser: (payload) => request('/admin/users', { method: 'POST', body: payload }),
  updateUser: (id, updates) => request(`/admin/users/${id}`, { method: 'PUT', body: updates }),
  deleteUser: (id) => request(`/admin/users/${id}`, { method: 'DELETE' }),
};
