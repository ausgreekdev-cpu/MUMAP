import { create } from 'zustand';
import { Agent, agentsApi } from '../lib/api';

interface AgentState {
  agents: Agent[];
  total: number;
  selectedAgent: Agent | null;
  isLoading: boolean;
  error: string | null;
  fetchAgents: (params?: { status?: string; role?: string }) => Promise<void>;
  fetchAgent: (id: number) => Promise<void>;
  createAgent: (data: Partial<Agent>) => Promise<Agent>;
  updateAgent: (id: number, data: Partial<Agent>) => Promise<void>;
  deleteAgent: (id: number) => Promise<void>;
  updateStatus: (id: number, status: string) => Promise<void>;
  activateAgent: (id: number) => Promise<void>;
  deactivateAgent: (id: number) => Promise<void>;
  fetchStats: (id: number) => Promise<Record<string, unknown>>;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  total: 0,
  selectedAgent: null,
  isLoading: false,
  error: null,

  fetchAgents: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await agentsApi.list(params);
      set({
        agents: response.data.agents,
        total: response.data.total,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false, error: 'Failed to fetch agents' });
    }
  },

  fetchAgent: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await agentsApi.get(id);
      set({ selectedAgent: response.data, isLoading: false });
    } catch (error) {
      set({ isLoading: false, error: 'Failed to fetch agent' });
    }
  },

  createAgent: async (data) => {
    const response = await agentsApi.create(data);
    const agent = response.data;
    set((state) => ({
      agents: [...state.agents, agent],
      total: state.total + 1,
    }));
    return agent;
  },

  updateAgent: async (id, data) => {
    const response = await agentsApi.update(id, data);
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? response.data : a)),
      selectedAgent: state.selectedAgent?.id === id ? response.data : state.selectedAgent,
    }));
  },

  deleteAgent: async (id) => {
    await agentsApi.delete(id);
    set((state) => ({
      agents: state.agents.filter((a) => a.id !== id),
      total: state.total - 1,
    }));
  },

  updateStatus: async (id, status) => {
    await agentsApi.updateStatus(id, status);
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    }));
  },

  activateAgent: async (id) => {
    await agentsApi.activate(id);
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, is_active: true } : a)),
    }));
  },

  deactivateAgent: async (id) => {
    await agentsApi.deactivate(id);
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, is_active: false } : a)),
    }));
  },

  fetchStats: async (id) => {
    const response = await agentsApi.getStats(id);
    return response.data;
  },
}));
