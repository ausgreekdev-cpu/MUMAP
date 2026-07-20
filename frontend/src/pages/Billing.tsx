import { useState, useEffect } from 'react';
import { usageAPI } from '../services/api';
import { UsageSummary, BillingPlan } from '../types';
import { StatsCard } from '../components/StatsCard';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../components/Toast';

const mockDailyUsage = [
  { day: 'Jun 1', tokens: 12500, tasks: 8 },
  { day: 'Jun 5', tokens: 18400, tasks: 12 },
  { day: 'Jun 10', tokens: 9800, tasks: 6 },
  { day: 'Jun 15', tokens: 22100, tasks: 15 },
  { day: 'Jun 20', tokens: 15600, tasks: 10 },
  { day: 'Jun 25', tokens: 27200, tasks: 18 },
  { day: 'Jun 30', tokens: 14300, tasks: 9 },
];

const mockPlans: BillingPlan[] = [
  {
    id: 1, name: 'free', display_name: 'Free', price_monthly: 0, price_yearly: 0,
    token_limit: 100000, task_limit: 100, agent_limit: 3, member_limit: 1,
    features: ['Up to 3 agents', '100 tasks/month', '100K tokens/month', 'Basic analytics', 'Community support'],
    is_active: true,
  },
  {
    id: 2, name: 'pro', display_name: 'Pro', price_monthly: 49, price_yearly: 490,
    token_limit: 1000000, task_limit: 1000, agent_limit: 10, member_limit: 5,
    features: ['Up to 10 agents', '1000 tasks/month', '1M tokens/month', 'Advanced analytics', 'Priority support', 'Custom integrations', 'Team collaboration'],
    is_active: true,
  },
  {
    id: 3, name: 'enterprise', display_name: 'Enterprise', price_monthly: 199, price_yearly: 1990,
    token_limit: 10000000, task_limit: 10000, agent_limit: 50, member_limit: 50,
    features: ['Up to 50 agents', 'Unlimited tasks', '10M tokens/month', 'Custom models', 'Dedicated support', 'SLA guarantee', 'SSO & SAML', 'Audit logs', 'API access'],
    is_active: true,
  },
];

const mockInvoices = [
  { id: 1, period: 'June 2026', amount: 49, status: 'paid', issued_at: '2026-06-01' },
  { id: 2, period: 'May 2026', amount: 49, status: 'paid', issued_at: '2026-05-01' },
  { id: 3, period: 'April 2026', amount: 49, status: 'paid', issued_at: '2026-04-01' },
];

const modelCosts = [
  { model: 'GPT-4o', tokens: 450000, cost: 4.50 },
  { model: 'GPT-4o-mini', tokens: 890000, cost: 1.78 },
  { model: 'Claude 3.5 Sonnet', tokens: 320000, cost: 4.80 },
  { model: 'Claude 3 Haiku', tokens: 560000, cost: 0.56 },
  { model: 'Custom Fine-tuned', tokens: 120000, cost: 0.60 },
];

export function Billing() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showPlans, setShowPlans] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const summaryRes = await usageAPI.summary().catch(() => null);
      if (summaryRes) setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to load billing data:', error);
      toast('error', 'Failed to load billing data');
    } finally {
      setIsLoading(false);
    }
  };

  const maxTokens = Math.max(...mockDailyUsage.map((d) => d.tokens));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400">Loading billing...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Billing & Usage</h1>
          <p className="text-gray-400">Monitor your usage and manage your subscription</p>
        </div>
        <button
          onClick={() => setShowPlans(!showPlans)}
          className="btn btn-primary flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
          </svg>
          {showPlans ? 'Hide Plans' : 'View Plans'}
        </button>
      </div>

      {/* Usage Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Cost"
          value={`$${(summary?.total_cost || 12.34).toFixed(2)}`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="indigo"
        />
        <StatsCard
          title="Tokens Used"
          value={(summary?.total_tokens || 89450).toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          }
          color="green"
        />
        <StatsCard
          title="Tasks Run"
          value={summary?.total_tasks || 64}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
            </svg>
          }
          color="amber"
        />
        <StatsCard
          title="Period"
          value={summary?.period || 'Monthly'}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
          }
          color="purple"
        />
      </div>

      {/* Usage Bar Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-6">Daily Token Usage</h2>
        <div className="flex items-end gap-3 h-48">
          {mockDailyUsage.map((item) => (
            <div key={item.day} className="flex-1 flex flex-col items-center gap-2 group">
              <span className="text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                {item.tokens.toLocaleString()}
              </span>
              <div
                className="w-full rounded-lg bg-gradient-to-t from-[#6366f1] to-[#8b5cf6] transition-all duration-300 group-hover:opacity-80"
                style={{ height: `${(item.tokens / maxTokens) * 100}%` }}
              />
              <span className="text-xs text-gray-500">{item.day.split(' ')[1]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Plans Section */}
      {showPlans && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Compare Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {mockPlans.map((plan) => (
              <div key={plan.id} className={`card relative ${plan.name === 'pro' ? 'border-[#6366f1]/50 ring-1 ring-[#6366f1]/20' : ''}`}>
                {plan.name === 'pro' && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] text-xs font-medium text-white">
                    Popular
                  </div>
                )}
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold">{plan.display_name}</h3>
                  <div className="mt-3">
                    <span className="text-3xl font-bold">${plan.price_monthly}</span>
                    <span className="text-gray-400 text-sm">/mo</span>
                  </div>
                  {plan.price_yearly > 0 && (
                    <p className="text-sm text-gray-500 mt-1">${plan.price_yearly}/year</p>
                  )}
                </div>
                <div className="space-y-3 mb-6">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Agents</span>
                    <span className="text-gray-200">{plan.agent_limit}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Tasks</span>
                    <span className="text-gray-200">{plan.task_limit === 10000 ? 'Unlimited' : `${plan.task_limit}/mo`}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Tokens</span>
                    <span className="text-gray-200">{(plan.token_limit / 1000000).toFixed(0)}M/mo</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Members</span>
                    <span className="text-gray-200">{plan.member_limit}</span>
                  </div>
                </div>
                <div className="space-y-2 mb-6">
                  {plan.features.map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-gray-300">
                      <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                      {feature}
                    </div>
                  ))}
                </div>
                <button
                  className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all ${
                    plan.name === 'free'
                      ? 'bg-white/5 text-gray-300 border border-white/10 hover:bg-white/10'
                      : plan.name === 'pro'
                      ? 'bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] text-white hover:opacity-90'
                      : 'bg-white/5 text-gray-300 border border-white/10 hover:bg-white/10'
                  }`}
                >
                  {plan.name === 'free' ? 'Current Plan' : plan.name === 'pro' ? 'Upgrade to Pro' : 'Contact Sales'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage by Model */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-6">Usage by Model</h2>
          <div className="space-y-4">
            {modelCosts.map((item, i) => {
              const maxCost = Math.max(...modelCosts.map((m) => m.cost));
              return (
                <div key={i} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-300">{item.model}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-gray-400">{item.tokens.toLocaleString()} tokens</span>
                      <span className="text-gray-200 font-medium">${item.cost.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] transition-all"
                      style={{ width: `${(item.cost / maxCost) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Invoices */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Recent Invoices</h2>
            <button className="text-sm text-[#8b5cf6] hover:text-[#a855f7] transition-colors">
              View all
            </button>
          </div>
          {mockInvoices.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              }
              title="No invoices"
              description="Invoices will appear once you upgrade to a paid plan"
            />
          ) : (
            <div className="space-y-3">
              {mockInvoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5"
                >
                  <div>
                    <p className="font-medium">{inv.period}</p>
                    <p className="text-sm text-gray-400">Issued {inv.issued_at}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                      inv.status === 'paid' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {inv.status}
                    </span>
                    <span className="font-medium">${inv.amount.toFixed(2)}</span>
                    <button className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-all">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
