import { create } from 'zustand';
import { systemApi } from '../lib/api';

interface SystemState {
  status: Record<string, unknown> | null;
  isLoading: boolean;
  error: string | null;
  fetchStatus: () => Promise<void>;
  rebalance: () => Promise<void>;
}

export const useSystemStore = create<SystemState>((set) => ({
  status: null,
  isLoading: false,
  error: null,

  fetchStatus: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await systemApi.getStatus();
      set({ status: response.data, isLoading: false });
    } catch {
      set({ isLoading: false, error: 'Failed to fetch system status' });
    }
  },

  rebalance: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await systemApi.rebalance();
      set({ status: response.data, isLoading: false });
    } catch {
      set({ isLoading: false, error: 'Failed to rebalance' });
    }
  },
}));
