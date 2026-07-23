import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Power, PowerOff, Trash2 } from 'lucide-react';
import { useAgentStore } from '../stores';
import { useToast } from '../components/ui/Toast';
import Button from '../components/ui/Button';
import Badge, { statusVariant } from '../components/ui/Badge';
import Card, { CardTitle } from '../components/ui/Card';
import Spinner from '../components/ui/Spinner';

export default function AgentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { selectedAgent: agent, fetchAgent, updateStatus, activateAgent, deactivateAgent, deleteAgent, isLoading } = useAgentStore();
  const { toast } = useToast();
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (id) fetchAgent(Number(id));
  }, [id, fetchAgent]);

  useEffect(() => {
    if (agent) {
      useAgentStore.getState().fetchStats(agent.id).then(setStats).catch(() => {});
    }
  }, [agent]);

  if (isLoading || !agent) {
    return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;
  }

  const handleStatusChange = async (status: string) => {
    try {
      await updateStatus(agent.id, status);
      toast('success', `Status updated to ${status}`);
    } catch {
      toast('error', 'Failed to update status');
    }
  };

  const handleToggleActive = async () => {
    try {
      if (agent.is_active) {
        await deactivateAgent(agent.id);
        toast('success', 'Agent deactivated');
      } else {
        await activateAgent(agent.id);
        toast('success', 'Agent activated');
      }
      fetchAgent(agent.id);
    } catch {
      toast('error', 'Failed to update agent');
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete agent "${agent.name}"?`)) return;
    try {
      await deleteAgent(agent.id);
      toast('success', 'Agent deleted');
      navigate('/agents');
    } catch {
      toast('error', 'Failed to delete agent');
    }
  };

  return (
    <div className="page-container">
      <button onClick={() => navigate('/agents')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> Back to Agents
      </button>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
          <p className="text-sm text-gray-500">{agent.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={handleToggleActive}>
            {agent.is_active ? <><PowerOff size={16} className="mr-2" /> Deactivate</> : <><Power size={16} className="mr-2" /> Activate</>}
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            <Trash2 size={16} className="mr-2" /> Delete
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardTitle>Status</CardTitle>
          <div className="mt-3 flex items-center gap-3">
            <Badge variant={statusVariant(agent.status)} className="text-sm px-3 py-1">{agent.status}</Badge>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {['idle', 'busy', 'error', 'offline', 'maintenance'].map((s) => (
              <button
                key={s}
                onClick={() => handleStatusChange(s)}
                disabled={agent.status === s}
                className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
                  agent.status === s
                    ? 'bg-brand-600 text-white border-brand-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <CardTitle>Health Score</CardTitle>
          <div className="mt-4">
            <div className="text-3xl font-bold text-gray-900">{Math.round(agent.health_score * 100)}%</div>
            <div className="mt-2 w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${agent.health_score > 0.7 ? 'bg-green-500' : agent.health_score > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${agent.health_score * 100}%` }}
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardTitle>Performance</CardTitle>
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Completed</span>
              <span className="font-medium text-green-600">{agent.completed_tasks_count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Failed</span>
              <span className="font-medium text-red-600">{agent.failed_tasks_count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Avg Time</span>
              <span className="font-medium text-gray-900">{agent.average_task_time.toFixed(1)}s</span>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <CardTitle>Details</CardTitle>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Role</span>
            <p className="font-medium text-gray-900">{agent.role}</p>
          </div>
          <div>
            <span className="text-gray-500">Created</span>
            <p className="font-medium text-gray-900">{new Date(agent.created_at).toLocaleString()}</p>
          </div>
          <div className="col-span-2">
            <span className="text-gray-500">Capabilities</span>
            <div className="mt-1 flex flex-wrap gap-2">
              {agent.capabilities.map((cap) => (
                <Badge key={cap} variant="info">{cap}</Badge>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
