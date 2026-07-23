import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, CheckCircle, XCircle, Ban, RotateCcw, UserPlus } from 'lucide-react';
import { useTaskStore, useAgentStore } from '../stores';
import { useToast } from '../components/ui/Toast';
import Button from '../components/ui/Button';
import Badge, { statusVariant } from '../components/ui/Badge';
import Card, { CardTitle } from '../components/ui/Card';
import Spinner from '../components/ui/Spinner';

export default function TaskDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { selectedTask: task, fetchTask, taskLogs, fetchTaskLogs, assignTask, autoAssignTask, completeTask, failTask, cancelTask, retryTask, isLoading } = useTaskStore();
  const { agents, fetchAgents } = useAgentStore();
  const { toast } = useToast();

  useEffect(() => {
    if (id) {
      fetchTask(Number(id));
      fetchTaskLogs(Number(id));
      fetchAgents();
    }
  }, [id, fetchTask, fetchTaskLogs, fetchAgents]);

  if (isLoading || !task) {
    return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;
  }

  const handleAction = async (action: () => Promise<void>, msg: string) => {
    try {
      await action();
      toast('success', msg);
      if (id) {
        fetchTask(Number(id));
        fetchTaskLogs(Number(id));
      }
    } catch {
      toast('error', `Failed: ${msg}`);
    }
  };

  const getAgentName = (agentId: number | null) => {
    if (!agentId) return '—';
    const agent = agents.find((a) => a.id === agentId);
    return agent?.name || `#${agentId}`;
  };

  return (
    <div className="page-container">
      <button onClick={() => navigate('/tasks')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> Back to Tasks
      </button>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{task.name}</h1>
          <p className="text-sm text-gray-500">{task.description}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardTitle>Status</CardTitle>
          <div className="mt-3 flex items-center gap-3">
            <Badge variant={statusVariant(task.status)} className="text-sm px-3 py-1">{task.status}</Badge>
            <Badge variant={statusVariant(task.priority)} className="text-sm px-3 py-1">{task.priority}</Badge>
          </div>
          <div className="mt-4">
            <span className="text-sm text-gray-500">Assigned to</span>
            <p className="font-medium text-gray-900">{getAgentName(task.assigned_to)}</p>
          </div>
        </Card>

        <Card>
          <CardTitle>Actions</CardTitle>
          <div className="mt-4 flex flex-wrap gap-2">
            {!task.assigned_to && task.status === 'pending' && (
              <>
                <Button size="sm" onClick={() => handleAction(() => autoAssignTask(task.id), 'Task auto-assigned')}>
                  <UserPlus size={14} className="mr-1" /> Auto-Assign
                </Button>
                {agents.filter((a) => a.is_active && a.status !== 'busy').map((a) => (
                  <Button key={a.id} size="sm" variant="secondary" onClick={() => handleAction(() => assignTask(task.id, a.id), `Assigned to ${a.name}`)}>
                    Assign: {a.name}
                  </Button>
                ))}
              </>
            )}
            {task.status === 'running' && (
              <>
                <Button size="sm" onClick={() => handleAction(() => completeTask(task.id, {}), 'Task completed')}>
                  <CheckCircle size={14} className="mr-1" /> Complete
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleAction(() => failTask(task.id, 'Manual failure'), 'Task failed')}>
                  <XCircle size={14} className="mr-1" /> Fail
                </Button>
              </>
            )}
            {(task.status === 'pending' || task.status === 'running') && (
              <Button size="sm" variant="ghost" onClick={() => handleAction(() => cancelTask(task.id), 'Task cancelled')}>
                <Ban size={14} className="mr-1" /> Cancel
              </Button>
            )}
            {task.status === 'failed' && (
              <Button size="sm" variant="secondary" onClick={() => handleAction(() => retryTask(task.id), 'Task retried')}>
                <RotateCcw size={14} className="mr-1" /> Retry
              </Button>
            )}
          </div>
        </Card>

        <Card>
          <CardTitle>Details</CardTitle>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Retries</span>
              <span className="font-medium text-gray-900">{task.retry_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Created</span>
              <span className="font-medium text-gray-900">{new Date(task.created_at).toLocaleString()}</span>
            </div>
            {task.completed_at && (
              <div className="flex justify-between">
                <span className="text-gray-500">Completed</span>
                <span className="font-medium text-gray-900">{new Date(task.completed_at).toLocaleString()}</span>
              </div>
            )}
            {task.error_message && (
              <div className="mt-2">
                <span className="text-gray-500">Error</span>
                <p className="mt-1 text-red-600 text-xs bg-red-50 rounded-lg p-2">{task.error_message}</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardTitle>Task Logs</CardTitle>
        <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
          {taskLogs.length === 0 ? (
            <p className="text-sm text-gray-500">No logs yet</p>
          ) : (
            taskLogs.map((log) => (
              <div key={log.id} className="flex items-start gap-3 text-sm border-b border-gray-100 pb-3 last:border-0">
                <Badge variant={log.event === 'error' ? 'danger' : log.event === 'completed' ? 'success' : 'info'} className="shrink-0">
                  {log.event}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-700">{log.message}</p>
                  <p className="text-xs text-gray-400 mt-1">{new Date(log.created_at).toLocaleString()}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
