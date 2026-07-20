import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, username: string, password: string) =>
    api.post('/auth/register', { email, username, password }),
  getMe: () => api.get('/auth/me'),
};

// Agents API
export const agentsAPI = {
  list: (params?: { status?: string; role?: string }) =>
    api.get('/agents/', { params }),
  get: (id: number) => api.get(`/agents/${id}`),
  create: (data: { name: string; description?: string; role?: string; capabilities?: string[] }) =>
    api.post('/agents/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/agents/${id}`, data),
  delete: (id: number) => api.delete(`/agents/${id}`),
  updateStatus: (id: number, status: string) =>
    api.post(`/agents/${id}/status`, null, { params: { status } }),
  chat: (id: number, data: { message: string; system_prompt?: string; temperature?: number; max_tokens?: number }) =>
    api.post(`/agents/${id}/chat`, data),
  execute: (id: number, data: { task_id?: number; description: string }) =>
    api.post(`/agents/${id}/execute`, data),
};

// Tasks API
export const tasksAPI = {
  list: (params?: { status?: string; priority?: string; assigned_to?: number }) =>
    api.get('/tasks/', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
  create: (data: { name: string; description?: string; priority?: string; required_capabilities?: string[]; input_data?: Record<string, unknown> }) =>
    api.post('/tasks/', data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/tasks/${id}`, data),
  delete: (id: number) => api.delete(`/tasks/${id}`),
  assign: (taskId: number, agentId: number) =>
    api.post(`/tasks/${taskId}/assign`, { agent_id: agentId }),
  autoAssign: (taskId: number) =>
    api.post(`/tasks/${taskId}/auto-assign`),
  complete: (taskId: number, outputData: Record<string, unknown>) =>
    api.post(`/tasks/${taskId}/complete`, outputData),
  fail: (taskId: number, errorMessage: string) =>
    api.post(`/tasks/${taskId}/fail`, null, { params: { error_message: errorMessage } }),
  cancel: (taskId: number) =>
    api.post(`/tasks/${taskId}/cancel`),
  getLogs: (taskId: number) =>
    api.get(`/tasks/${taskId}/logs`),
};

export const orgsAPI = {
  list: () => api.get('/orgs/'),
  create: (data: { name: string; description?: string }) => api.post('/orgs/', data),
  get: (id: number) => api.get(`/orgs/${id}`),
  update: (id: number, data: Record<string, unknown>) => api.put(`/orgs/${id}`, data),
  delete: (id: number) => api.delete(`/orgs/${id}`),
  listMembers: (id: number) => api.get(`/orgs/${id}/members`),
  invite: (id: number, data: { email: string; role: string }) => api.post(`/orgs/${id}/members/invite`, data),
  removeMember: (orgId: number, userId: number) => api.delete(`/orgs/${orgId}/members/${userId}`),
  updateRole: (orgId: number, userId: number, role: string) => api.put(`/orgs/${orgId}/members/${userId}/role`, null, { params: { role } }),
};

export const usageAPI = {
  summary: () => api.get('/usage/summary'),
  records: (params?: { usage_type?: string; start_date?: string; end_date?: string }) => api.get('/usage/records', { params }),
  check: () => api.get('/usage/check'),
  costsByModel: () => api.get('/usage/costs/by-model'),
  plans: () => api.get('/usage/billing/plans'),
  invoices: () => api.get('/usage/billing/invoices'),
  generateInvoice: () => api.post('/usage/billing/invoices/generate'),
};

export const executionAPI = {
  execute: (agentId: number, taskId: number) => api.post(`/execution/agents/${agentId}/execute`, null, { params: { task_id: taskId } }),
  chat: (agentId: number, message: string) => api.post(`/execution/agents/${agentId}/chat`, { message }),
  executionLog: (taskId: number) => api.get(`/execution/tasks/${taskId}/execution-log`),
};

export default api;
