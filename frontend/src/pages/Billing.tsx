import { useState, useEffect } from 'react';
import { usageAPI } from '../services/api';
import { UsageSummary, UsageRecord, BillingPlan, Invoice } from '../types';
import { StatsCard } from '../components/StatsCard';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../components/Toast';

interface DailyBucket {
  day: string;
  tokens: number;
}

function formatTokens(n: number): string {
  if (n === -1) return 'Unlimited';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n % 1_000_000 === 0 ? 0 : 1)}M/mo`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K/mo`;
  return `${n}/mo`;
}

function formatLimit(n: number): string {
  if (n === -1) return 'Unlimited';
  return `${n.toLocaleString()}/mo`;
}

function formatFeature(feature: string): string {
  const words = feature.replace(/_/g, ' ');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function formatPeriodLabel(periodStart: string): string {
  try {
    return new Date(periodStart).toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC',
    });
  } catch {
    return 'Monthly';
  }
}

function bucketDailyUsage(records: UsageRecord[]): DailyBucket[] {
  const buckets = new Map<string, number>();
  for (const record of records) {
    if (!record.usage_type.startsWith('token')) continue;
    const key = record.created_at.slice(0, 10);
    buckets.set(key, (buckets.get(key) || 0) + record.quantity);
  }
  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([day, tokens]) => ({ day, tokens }));
}

export function Billing() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [dailyUsage, setDailyUsage] = useState<DailyBucket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showPlans, setShowPlans] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, plansRes, invoicesRes, recordsRes] = await Promise.all([
        usageAPI.summary().catch((e) => { console.error('summary', e); return null; }),
        usageAPI.plans().catch((e) => { console.error('plans', e); return null; }),
        usageAPI.invoices().catch((e) => { console.error('invoices', e); return null; }),
        usageAPI.records().catch((e) => { console.error('records', e); return null; }),
      ]);

      if (summaryRes) setSummary(summaryRes.data);
      if (plansRes) setPlans(plansRes.data || []);
      if (invoicesRes) setInvoices(invoicesRes.data?.invoices || []);
      if (recordsRes) setDailyUsage(bucketDailyUsage(recordsRes.data?.records || []));

      if (!summaryRes) {
        toast('error', 'Failed to load billing data');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const modelEntries = summary
    ? Object.entries(summary.by_model).map(([model, stats]) => ({
        model,
        tokens: stats.input_tokens + stats.output_tokens,
        cost: stats.total_cost,
      }))
    : [];
  const maxModelCost = Math.max(...modelEntries.map((m) => m.cost), 0.000001);
  const maxDailyTokens = Math.max(...dailyUsage.map((d) => d.tokens), 1);

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
          value={`$${(summary?.total_cost ?? 0).toFixed(2)}`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="indigo"
        />
        <StatsCard
          title="Tokens Used"
          value={(summary?.total_tokens ?? 0).toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          }
          color="green"
        />
        <StatsCard
          title="Tasks Run"
          value={(summary?.total_tasks ?? 0).toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
            </svg>
          }
          color="amber"
        />
        <StatsCard
          title="Period"
          value={summary ? formatPeriodLabel(summary.period_start) : 'Monthly'}
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
        {dailyUsage.length === 0 ? (
          <EmptyState
            icon={
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            }
            title="No usage yet"
            description="Token usage will appear here once your agents start running"
          />
        ) : (
          <div className="flex items-end gap-2 h-48 overflow-x-auto">
            {dailyUsage.map((item) => (
              <div key={item.day} className="flex-1 min-w-[2rem] flex flex-col items-center gap-2 group">
                <span className="text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {item.tokens.toLocaleString()}
                </span>
                <div
                  className="w-full rounded-lg bg-gradient-to-t from-[#6366f1] to-[#8b5cf6] transition-all duration-300 group-hover:opacity-80"
                  style={{ height: `${Math.max((item.tokens / maxDailyTokens) * 100, 2)}%` }}
                />
                <span className="text-xs text-gray-500">{item.day.slice(8)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Plans Section */}
      {showPlans && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Compare Plans</h2>
          {plans.length === 0 ? (
            <EmptyState
              title="No plans available"
              description="Billing plans could not be loaded"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plans.map((plan) => (
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
                      <span className="text-gray-200">{plan.agent_limit === -1 ? 'Unlimited' : plan.agent_limit}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Tasks</span>
                      <span className="text-gray-200">{formatLimit(plan.task_limit)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Tokens</span>
                      <span className="text-gray-200">{formatTokens(plan.token_limit)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Members</span>
                      <span className="text-gray-200">{plan.member_limit === -1 ? 'Unlimited' : plan.member_limit}</span>
                    </div>
                  </div>
                  <div className="space-y-2 mb-6">
                    {plan.features.map((feature, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-gray-300">
                        <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                        {formatFeature(feature)}
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => toast('info', 'Plan upgrades are not yet available')}
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
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage by Model */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-6">Usage by Model</h2>
          {modelEntries.length === 0 ? (
            <EmptyState
              title="No model usage"
              description="Model usage will appear once agents run LLM tasks"
            />
          ) : (
            <div className="space-y-4">
              {modelEntries.map((item, i) => (
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
                      style={{ width: `${(item.cost / maxModelCost) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Invoices */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Recent Invoices</h2>
          </div>
          {invoices.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              }
              title="No invoices"
              description="Generate an invoice from your current usage above"
            />
          ) : (
            <div className="space-y-3">
              {invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5"
                >
                  <div>
                    <p className="font-medium">{formatPeriodLabel(inv.period_start)}</p>
                    <p className="text-sm text-gray-400">
                      Issued {new Date(inv.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                      inv.status === 'paid' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {inv.status}
                    </span>
                    <span className="font-medium">${inv.total_cost.toFixed(2)}</span>
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
