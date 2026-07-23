import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, ListTodo, Server, Activity } from 'lucide-react';
import { useAgentStore, useTaskStore, useSystemStore } from '../stores';
import Card, { CardTitle } from '../components/ui/Card';
import Badge, { statusVariant } from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { useInterval } from '../hooks/useWebSocket';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { agents, total: agentTotal, fetchAgents, isLoading: agentsLoading } = useAgentStore();
  const { tasks, total: taskTotal, fetchTasks, isLoading: tasksLoading } = useTaskStore();
  const { status, fetchStatus, isLoading: systemLoading } = useSystemStore();

  useEffect(() => {
    fetchAgents();
    fetchTasks();
    fetchStatus();
  }, [fetchAgents, fetchTasks, fetchStatus]);

  useInterval(() => {
    fetchAgents();
    fetchTasks();
    fetchStatus();
  }, 30000);

  const loading = agentsLoading || tasksLoading || systemLoading;

  const stats = [
    {
      label: 'Total Agents',
      value: agentTotal,
      icon: Bot,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      link: '/agents',
    },
    {
      label: 'Total Tasks',
      value: taskTotal,
      icon: ListTodo,
      color: 'text-green-600',
      bg: 'bg-green-50',
      link: '/tasks',
    },
    {
      label: 'System Status',
      value: (status as Record<string, string>)?.status || 'Unknown',
      icon: Server,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      link: '/system',
    },
    {
      label: 'Active Agents',
      value: agents.filter((a) => a.status === 'active' || a.status === 'idle').length,
      icon: Activity,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      link: '/agents',
    },
  ];

  const taskStatusCounts = tasks.reduce(
    (acc, t) => {
      acc[t.status] = (acc[t.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const recentTasks = [...tasks].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5);

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {loading && agents.length === 0 ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {stats.map((s) => (
              <Card key={s.label} className="cursor-pointer hover:shadow-md transition-shadow" padding={false}>
                <div className="p-5" onClick={() => navigate(s.link)}>
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-lg ${s.bg}`}>
                      <s.icon size={24} className={s.color} />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">{s.label}</p>
                      <p className="text-2xl font-bold text-gray-900">{s.value}</p>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardTitle>Task Distribution</CardTitle>
              <div className="mt-4 space-y-3">
                {Object.entries(taskStatusCounts).length === 0 ? (
                  <p className="text-sm text-gray-500">No tasks yet</p>
                ) : (
                  Object.entries(taskStatusCounts).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={statusVariant(status)}>{status}</Badge>
                      </div>
                      <span className="text-sm font-medium text-gray-700">{count}</span>
                    </div>
                  ))
                )}
              </div>
            </Card>

            <Card>
              <CardTitle>Recent Tasks</CardTitle>
              <div className="mt-4 space-y-3">
                {recentTasks.length === 0 ? (
                  <p className="text-sm text-gray-500">No recent tasks</p>
                ) : (
                  recentTasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 cursor-pointer hover:bg-gray-50 rounded px-2 -mx-2"
                      onClick={() => navigate(`/tasks/${task.id}`)}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{task.name}</p>
                        <p className="text-xs text-gray-500">{new Date(task.created_at).toLocaleDateString()}</p>
                      </div>
                      <Badge variant={statusVariant(task.status)}>{task.status}</Badge>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
