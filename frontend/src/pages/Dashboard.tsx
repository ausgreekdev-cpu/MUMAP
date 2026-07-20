import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { agentsAPI, tasksAPI } from '../services/api';
import { Stats } from '../types';
import { StatsCard } from '../components/StatsCard';
import { EmptyState } from '../components/EmptyState';
import { BarChart } from '../components/Charts';
import { useToast } from '../components/Toast';

export function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentTasks, setRecentTasks] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsRes, tasksRes] = await Promise.all([
        agentsAPI.list(),
        tasksAPI.list({}),
      ]);

      const agents = agentsRes.data.agents;
      const tasks = tasksRes.data.tasks;

      setStats({
        agents: {
          total: agents.length,
          idle: agents.filter((a: { status: string }) => a.status === 'idle').length,
          busy: agents.filter((a: { status: string }) => a.status === 'busy').length,
        },
        tasks: {
          total: tasksRes.data.total,
          pending: tasks.filter((t: { status: string }) => t.status === 'pending').length,
          completed: tasks.filter((t: { status: string }) => t.status === 'completed').length,
          failed: tasks.filter((t: { status: string }) => t.status === 'failed').length,
        },
      });

      setRecentTasks(tasks.slice(0, 5));
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast('error', 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
          <span className="text-[#94a3b8]">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-400">Welcome back! Here's what's happening with your agents.</p>
        </div>
        <button onClick={() => navigate('/tasks')} className="btn btn-primary flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Task
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Agents"
          value={stats?.agents.total || 0}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
          }
          color="indigo"
        />
        <StatsCard
          title="Active Agents"
          value={stats?.agents.idle || 0}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="green"
        />
        <StatsCard
          title="Pending Tasks"
          value={stats?.tasks.pending || 0}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="amber"
        />
        <StatsCard
          title="Completed"
          value={stats?.tasks.completed || 0}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3l1.664 1.664M21 21l-1.5-1.5m-5.523-2.121a2.25 2.25 0 01-3.182 0l-4.95-4.95a2.25 2.25 0 010-3.182l3.182-3.182a2.25 2.25 0 013.182 0l4.95 4.95a2.25 2.25 0 010 3.182z" />
            </svg>
          }
          color="purple"
        />
      </div>

      {/* Task Distribution Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-6">Task Overview</h2>
        <BarChart
          data={[
            { label: 'Pending', value: stats?.tasks.pending || 0, color: '#f59e0b' },
            { label: 'Completed', value: stats?.tasks.completed || 0, color: '#22c55e' },
            { label: 'Failed', value: stats?.tasks.failed || 0, color: '#ef4444' },
            { label: 'Total', value: stats?.tasks.total || 0, color: '#6366f1' },
          ]}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Tasks */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Recent Tasks</h2>
            <button onClick={() => navigate('/tasks')} className="text-sm text-[#8b5cf6] hover:text-[#a855f7] transition-colors">
              View all
            </button>
          </div>
          
          {recentTasks.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              }
              title="No tasks yet"
              description="Create your first task to get started"
            />
          ) : (
            <div className="space-y-3">
              {recentTasks.map((task: any) => (
                <div
                  key={task.id}
                  onClick={() => navigate(`/tasks/${task.id}`)}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer transition-all duration-200"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      task.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
                      task.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      task.status === 'in_progress' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {task.status === 'completed' ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 12.75l6 6 9-13.5" />
                        </svg>
                      ) : task.status === 'failed' ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      ) : task.status === 'in_progress' ? (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium truncate">{task.name}</p>
                      <p className="text-sm text-gray-400 truncate">{task.description || 'No description'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                      task.priority === 'critical' ? 'bg-red-500/20 text-red-400' :
                      task.priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
                      task.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {task.priority}
                    </span>
                    <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          {/* Quick Actions Card */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/agents')}
                className="w-full flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-200 text-left group"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-indigo-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium">Create Agent</p>
                  <p className="text-sm text-gray-400">Add a new AI agent</p>
                </div>
              </button>
              
              <button
                onClick={() => navigate('/tasks')}
                className="w-full flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-200 text-left group"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 6.878V6a2.25 2.25 0 012.25-2.25h7.5A2.25 2.25 0 0118 6v.878m-12 0c.235-.083.487-.128.75-.128h10.5c.263 0 .515.045.75.128m-12 0A2.25 2.25 0 004.5 9v.878m13.5-3A2.25 2.25 0 0119.5 9v.878m0 0a2.246 2.246 0 00-.75-.128H5.25c-.263 0-.515.045-.75.128m15 0A2.25 2.25 0 0121 12v6a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 18v-6c0-1.243 1.007-2.25 2.25-2.25h13.5" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium">Create Task</p>
                  <p className="text-sm text-gray-400">Assign work to agents</p>
                </div>
              </button>

              <button
                onClick={() => navigate('/settings')}
                className="w-full flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-200 text-left group"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium">Settings</p>
                  <p className="text-sm text-gray-400">Configure your platform</p>
                </div>
              </button>
            </div>
          </div>

          {/* Platform Status */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Platform Status</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-sm text-gray-300">API Server</span>
                </div>
                <span className="text-xs text-emerald-400 font-medium">Operational</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-sm text-gray-300">WebSocket</span>
                </div>
                <span className="text-xs text-emerald-400 font-medium">Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-sm text-gray-300">Task Queue</span>
                </div>
                <span className="text-xs text-emerald-400 font-medium">Healthy</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
