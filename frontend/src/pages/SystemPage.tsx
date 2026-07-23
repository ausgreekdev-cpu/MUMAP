import { useEffect } from 'react';
import { Server, RefreshCw, Activity, Bot, ListTodo } from 'lucide-react';
import { useSystemStore, useAgentStore, useTaskStore } from '../stores';
import { useToast } from '../components/ui/Toast';
import Card, { CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge, { statusVariant } from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { useInterval } from '../hooks/useWebSocket';

export default function SystemPage() {
  const { status, fetchStatus, rebalance, isLoading: systemLoading } = useSystemStore();
  const { agents, fetchAgents, isLoading: agentsLoading } = useAgentStore();
  const { tasks, fetchTasks, isLoading: tasksLoading } = useTaskStore();
  const { toast } = useToast();

  useEffect(() => {
    fetchStatus();
    fetchAgents();
    fetchTasks();
  }, [fetchStatus, fetchAgents, fetchTasks]);

  useInterval(() => {
    fetchStatus();
    fetchAgents();
    fetchTasks();
  }, 15000);

  const handleRebalance = async () => {
    try {
      await rebalance();
      toast('success', 'Rebalance completed');
      fetchAgents();
      fetchTasks();
    } catch {
      toast('error', 'Rebalance failed');
    }
  };

  const loading = systemLoading || agentsLoading || tasksLoading;

  const agentStatusCounts = agents.reduce(
    (acc, a) => {
      acc[a.status] = (acc[a.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const taskStatusCounts = tasks.reduce(
    (acc, t) => {
      acc[t.status] = (acc[t.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const sys = status as Record<string, unknown> | null;

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System</h1>
          <p className="text-sm text-gray-500">Platform health and metrics</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => { fetchStatus(); fetchAgents(); fetchTasks(); }}>
            <RefreshCw size={16} className="mr-2" /> Refresh
          </Button>
          <Button onClick={handleRebalance} disabled={systemLoading}>
            <Activity size={16} className="mr-2" /> Rebalance
          </Button>
        </div>
      </div>

      {loading && !sys ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <div className="flex items-center gap-3 mb-4">
                <Server size={20} className="text-purple-600" />
                <CardTitle>System Status</CardTitle>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Status</span>
                  <Badge variant={sys?.status === 'healthy' ? 'success' : sys?.status === 'degraded' ? 'warning' : 'info'}>
                    {(sys?.status as string) || 'Unknown'}
                  </Badge>
                </div>
                {typeof sys?.version === 'string' && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Version</span>
                    <span className="font-medium text-gray-900">{sys.version}</span>
                  </div>
                )}
                {typeof sys?.environment === 'string' && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Environment</span>
                    <span className="font-medium text-gray-900">{sys.environment}</span>
                  </div>
                )}
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-3 mb-4">
                <Bot size={20} className="text-blue-600" />
                <CardTitle>Agents</CardTitle>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total</span>
                  <span className="font-medium text-gray-900">{agents.length}</span>
                </div>
                {Object.entries(agentStatusCounts).map(([status, count]) => (
                  <div key={status} className="flex justify-between text-sm">
                    <Badge variant={statusVariant(status)}>{status}</Badge>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-3 mb-4">
                <ListTodo size={20} className="text-green-600" />
                <CardTitle>Tasks</CardTitle>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total</span>
                  <span className="font-medium text-gray-900">{tasks.length}</span>
                </div>
                {Object.entries(taskStatusCounts).map(([status, count]) => (
                  <div key={status} className="flex justify-between text-sm">
                    <Badge variant={statusVariant(status)}>{status}</Badge>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {sys?.metrics && (
            <Card>
              <CardTitle>Metrics</CardTitle>
              <pre className="mt-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-4 overflow-auto">
                {JSON.stringify(sys.metrics, null, 2)}
              </pre>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
