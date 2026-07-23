import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8005';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Agent {
  id: number;
  name: string;
  description: string;
  role: string;
  capabilities: string[];
  status: string;
  health_score: number;
  completed_tasks_count: number;
  failed_tasks_count: number;
  average_task_time: number;
  is_active: boolean;
  created_at: string;
}

export interface Task {
  id: number;
  name: string;
  description: string;
  status: string;
  priority: string;
  assigned_to: number | null;
  required_capabilities: string[];
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  completed_at: string | null;
}

export interface TaskLog {
  id: number;
  task_id: number;
  agent_id: number | null;
  event: string;
  message: string;
  data: Record<string, unknown>;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PaginatedResponse<T> {
  total: number;
  [key: string]: T[] | number;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/api/v1/auth/login', { email, password }),
  register: (email: string, username: string, password: string) =>
    api.post<User>('/api/v1/auth/register', { email, username, password }),
  getMe: () => api.get<User>('/api/v1/auth/me'),
  devLogin: () => api.post<TokenResponse>('/api/v1/auth/dev-login'),
};

export const agentsApi = {
  list: (params?: { status?: string; role?: string; skip?: number; limit?: number }) =>
    api.get<{ agents: Agent[]; total: number }>('/api/v1/agents/', { params }),
  get: (id: number) => api.get<Agent>(`/api/v1/agents/${id}`),
  create: (data: Partial<Agent>) => api.post<Agent>('/api/v1/agents/', data),
  update: (id: number, data: Partial<Agent>) => api.put<Agent>(`/api/v1/agents/${id}`, data),
  delete: (id: number) => api.delete(`/api/v1/agents/${id}`),
  updateStatus: (id: number, status: string) =>
    api.post(`/api/v1/agents/${id}/status`, null, { params: { status } }),
  getStats: (id: number) => api.get(`/api/v1/agents/${id}/stats`),
  deactivate: (id: number) => api.post(`/api/v1/agents/${id}/deactivate`),
  activate: (id: number) => api.post(`/api/v1/agents/${id}/activate`),
};

export const tasksApi = {
  list: (params?: { status?: string; priority?: string; assigned_to?: number; skip?: number; limit?: number }) =>
    api.get<{ tasks: Task[]; total: number }>('/api/v1/tasks/', { params }),
  get: (id: number) => api.get<Task>(`/api/v1/tasks/${id}`),
  create: (data: Partial<Task>) => api.post<Task>('/api/v1/tasks/', data),
  update: (id: number, data: Partial<Task>) => api.put<Task>(`/api/v1/tasks/${id}`, data),
  delete: (id: number) => api.delete(`/api/v1/tasks/${id}`),
  assign: (id: number, agentId: number) =>
    api.post<Task>(`/api/v1/tasks/${id}/assign`, null, { params: { agent_id: agentId } }),
  autoAssign: (id: number) => api.post<Task>(`/api/v1/tasks/${id}/auto-assign`),
  complete: (id: number, outputData: Record<string, unknown>) =>
    api.post<Task>(`/api/v1/tasks/${id}/complete`, outputData),
  fail: (id: number, errorMessage: string) =>
    api.post<Task>(`/api/v1/tasks/${id}/fail`, null, { params: { error_message: errorMessage } }),
  cancel: (id: number) => api.post<Task>(`/api/v1/tasks/${id}/cancel`),
  retry: (id: number) => api.post<Task>(`/api/v1/tasks/${id}/retry`),
  getLogs: (id: number, limit?: number) =>
    api.get<TaskLog[]>(`/api/v1/tasks/${id}/logs`, { params: { limit } }),
};

export const systemApi = {
  getStatus: () => api.get('/api/v1/system/status'),
  rebalance: () => api.post('/api/v1/system/rebalance'),
};

export interface IndustryTemplate {
  id: string;
  industry: string;
  icon: string;
  color: string;
  description: string;
  agents: { name: string; role: string; description: string; capabilities: string[] }[];
  tasks: { name: string; priority: string; required_capabilities: string[] }[];
}

export const templatesApi = {
  list: () => api.get<{ templates: IndustryTemplate[] }>('/api/v1/templates/'),
  get: (id: string) => api.get<IndustryTemplate>(`/api/v1/templates/${id}`),
  deploy: (id: string) => api.post<{ message: string; agents_created: number; tasks_created: number }>(`/api/v1/templates/${id}/deploy`),
};
