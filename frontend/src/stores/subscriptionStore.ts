import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type SubscriptionTier = 'free' | 'pro' | 'team';

export interface SubscriptionPlan {
  id: string;
  tier: SubscriptionTier;
  name: string;
  price: string;
  period: string;
  features: string[];
  limits: {
    maxAgents: number;
    maxTasksPerDay: number;
    templatesAccess: 'basic' | 'all';
    analytics: boolean;
    apiAccess: boolean;
    teamFeatures: boolean;
    prioritySupport: boolean;
  };
}

export const PLANS: SubscriptionPlan[] = [
  {
    id: 'free',
    tier: 'free',
    name: 'Community',
    price: 'Free',
    period: 'forever',
    features: [
      'Up to 3 agents',
      '10 tasks per day',
      '2 industry templates',
      'Basic monitoring',
      'Community support',
    ],
    limits: {
      maxAgents: 3,
      maxTasksPerDay: 10,
      templatesAccess: 'basic',
      analytics: false,
      apiAccess: false,
      teamFeatures: false,
      prioritySupport: false,
    },
  },
  {
    id: 'pro',
    tier: 'pro',
    name: 'Pro',
    price: '$14.99',
    period: '/mo',
    features: [
      'Up to 15 agents',
      'Unlimited tasks',
      'All 10 industry templates',
      'Advanced analytics',
      'Real-time monitoring',
      'Priority support',
      'No ads',
    ],
    limits: {
      maxAgents: 15,
      maxTasksPerDay: Infinity,
      templatesAccess: 'all',
      analytics: true,
      apiAccess: false,
      teamFeatures: false,
      prioritySupport: true,
    },
  },
  {
    id: 'team',
    tier: 'team',
    name: 'Team',
    price: '$39.99',
    period: '/mo',
    features: [
      'Up to 50 agents',
      'Everything in Pro',
      'Team collaboration',
      'Shared workflows',
      'Role-based access',
      'Full API access',
      'Dedicated support',
    ],
    limits: {
      maxAgents: 50,
      maxTasksPerDay: Infinity,
      templatesAccess: 'all',
      analytics: true,
      apiAccess: true,
      teamFeatures: true,
      prioritySupport: true,
    },
  },
];

interface SubscriptionState {
  currentTier: SubscriptionTier;
  subscriptionId: string | null;
  expiresAt: number | null;
  setTier: (tier: SubscriptionTier, subscriptionId?: string) => void;
  clearSubscription: () => void;
  canCreateAgent: (currentCount: number) => boolean;
  canCreateTask: (todayCount: number) => boolean;
  hasTemplatesAccess: () => boolean;
  hasAnalytics: () => boolean;
  hasApiAccess: () => boolean;
  hasTeamFeatures: () => boolean;
  getLimits: () => typeof PLANS[0]['limits'];
}

export const useSubscriptionStore = create<SubscriptionState>()(
  persist(
    (set, get) => ({
      currentTier: 'free',
      subscriptionId: null,
      expiresAt: null,

      setTier: (tier, subscriptionId) => {
        const plan = PLANS.find((p) => p.tier === tier);
        set({
          currentTier: tier,
          subscriptionId: subscriptionId || null,
          expiresAt: tier === 'free' ? null : Date.now() + 30 * 24 * 60 * 60 * 1000,
        });
      },

      clearSubscription: () => set({ currentTier: 'free', subscriptionId: null, expiresAt: null }),

      canCreateAgent: (currentCount) => {
        const limits = get().getLimits();
        return currentCount < limits.maxAgents;
      },

      canCreateTask: (todayCount) => {
        const limits = get().getLimits();
        return todayCount < limits.maxTasksPerDay;
      },

      hasTemplatesAccess: () => get().getLimits().templatesAccess === 'all',
      hasAnalytics: () => get().getLimits().analytics,
      hasApiAccess: () => get().getLimits().apiAccess,
      hasTeamFeatures: () => get().getLimits().teamFeatures,

      getLimits: () => {
        const plan = PLANS.find((p) => p.tier === get().currentTier);
        return plan?.limits || PLANS[0].limits;
      },
    }),
    { name: 'mumap-subscription' }
  )
);
