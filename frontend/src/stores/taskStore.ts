import { create } from 'zustand';
import { Task, TaskLog, tasksApi } from '../lib/api';

interface TaskState {
  tasks: Task[];
  total: number;
  selectedTask: Task | null;
  taskLogs: TaskLog[];
  isLoading: boolean;
  error: string | null;
  fetchTasks: (params?: { status?: string; priority?: string; assigned_to?: number }) => Promise<void>;
  fetchTask: (id: number) => Promise<void>;
  createTask: (data: Partial<Task>) => Promise<Task>;
  updateTask: (id: number, data: Partial<Task>) => Promise<void>;
  deleteTask: (id: number) => Promise<void>;
  assignTask: (id: number, agentId: number) => Promise<void>;
  autoAssignTask: (id: number) => Promise<void>;
  completeTask: (id: number, outputData: Record<string, unknown>) => Promise<void>;
  failTask: (id: number, errorMessage: string) => Promise<void>;
  cancelTask: (id: number) => Promise<void>;
  retryTask: (id: number) => Promise<void>;
  fetchTaskLogs: (id: number) => Promise<void>;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  total: 0,
  selectedTask: null,
  taskLogs: [],
  isLoading: false,
  error: null,

  fetchTasks: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await tasksApi.list(params);
      set({
        tasks: response.data.tasks,
        total: response.data.total,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false, error: 'Failed to fetch tasks' });
    }
  },

  fetchTask: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await tasksApi.get(id);
      set({ selectedTask: response.data, isLoading: false });
    } catch (error) {
      set({ isLoading: false, error: 'Failed to fetch task' });
    }
  },

  createTask: async (data) => {
    const response = await tasksApi.create(data);
    const task = response.data;
    set((state) => ({
      tasks: [task, ...state.tasks],
      total: state.total + 1,
    }));
    return task;
  },

  updateTask: async (id, data) => {
    const response = await tasksApi.update(id, data);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
      selectedTask: state.selectedTask?.id === id ? response.data : state.selectedTask,
    }));
  },

  deleteTask: async (id) => {
    await tasksApi.delete(id);
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== id),
      total: state.total - 1,
    }));
  },

  assignTask: async (id, agentId) => {
    const response = await tasksApi.assign(id, agentId);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
    }));
  },

  autoAssignTask: async (id) => {
    const response = await tasksApi.autoAssign(id);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
    }));
  },

  completeTask: async (id, outputData) => {
    const response = await tasksApi.complete(id, outputData);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
    }));
  },

  failTask: async (id, errorMessage) => {
    const response = await tasksApi.fail(id, errorMessage);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
    }));
  },

  cancelTask: async (id) => {
    const response = await tasksApi.cancel(id);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
    }));
  },

  retryTask: async (id) => {
    const response = await tasksApi.retry(id);
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
    }));
  },

  fetchTaskLogs: async (id) => {
    try {
      const response = await tasksApi.getLogs(id);
      set({ taskLogs: response.data });
    } catch (error) {
      set({ error: 'Failed to fetch task logs' });
    }
  },
}));
