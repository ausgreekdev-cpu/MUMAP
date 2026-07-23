import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Power, PowerOff } from 'lucide-react';
import { useAgentStore } from '../stores';
import { useToast } from '../components/ui/Toast';
import Button from '../components/ui/Button';
import Badge, { statusVariant } from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import EmptyState from '../components/ui/EmptyState';
import Spinner from '../components/ui/Spinner';
import { Agent } from '../lib/api';

export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, total, fetchAgents, createAgent, deleteAgent, activateAgent, deactivateAgent, isLoading } = useAgentStore();
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState('');
  const [form, setForm] = useState({ name: '', description: '', role: 'general', capabilities: '' });

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createAgent({
        ...form,
        capabilities: form.capabilities.split(',').map((s) => s.trim()).filter(Boolean),
      });
      setShowCreate(false);
      setForm({ name: '', description: '', role: 'general', capabilities: '' });
      toast('success', 'Agent created');
    } catch {
      toast('error', 'Failed to create agent');
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete agent "${name}"?`)) return;
    try {
      await deleteAgent(id);
      toast('success', 'Agent deleted');
    } catch {
      toast('error', 'Failed to delete agent');
    }
  };

  const handleToggleActive = async (agent: Agent) => {
    try {
      if (agent.is_active) {
        await deactivateAgent(agent.id);
        toast('success', 'Agent deactivated');
      } else {
        await activateAgent(agent.id);
        toast('success', 'Agent activated');
      }
    } catch {
      toast('error', 'Failed to update agent');
    }
  };

  const filtered = filter
    ? agents.filter((a) => a.status === filter || a.role.includes(filter))
    : agents;

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
          <p className="text-sm text-gray-500">{total} total</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus size={16} className="mr-2" /> Create Agent
        </Button>
      </div>

      <div className="mb-4 flex gap-2">
        {['', 'idle', 'busy', 'active', 'inactive'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              filter === f ? 'bg-brand-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {f || 'All'}
          </button>
        ))}
      </div>

      {isLoading && agents.length === 0 ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No agents"
          description="Create your first agent to get started"
          action={<Button onClick={() => setShowCreate(true)}>Create Agent</Button>}
        />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Health</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasks</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/agents/${agent.id}`)}>
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-xs text-gray-500 truncate max-w-[200px]">{agent.description}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{agent.role}</td>
                  <td className="px-6 py-4"><Badge variant={statusVariant(agent.status)}>{agent.status}</Badge></td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${agent.health_score > 0.7 ? 'bg-green-500' : agent.health_score > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{ width: `${agent.health_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{Math.round(agent.health_score * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <span className="text-green-600">{agent.completed_tasks_count}</span>
                    {' / '}
                    <span className="text-red-600">{agent.failed_tasks_count}</span>
                  </td>
                  <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleToggleActive(agent)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                        title={agent.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {agent.is_active ? <PowerOff size={16} /> : <Power size={16} />}
                      </button>
                      <button
                        onClick={() => handleDelete(agent.id, agent.name)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Agent">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required placeholder="e.g. Code Assistant" />
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="What does this agent do?" />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Role</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="general">General</option>
              <option value="coder">Coder</option>
              <option value="reviewer">Reviewer</option>
              <option value="analyst">Analyst</option>
              <option value="tester">Tester</option>
            </select>
          </div>
          <Input label="Capabilities" value={form.capabilities} onChange={(e) => setForm({ ...form, capabilities: e.target.value })} placeholder="python, javascript, debugging" />
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
