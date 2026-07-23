import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, RotateCcw } from 'lucide-react';
import { useTaskStore, useAgentStore } from '../stores';
import { useToast } from '../components/ui/Toast';
import Button from '../components/ui/Button';
import Badge, { statusVariant } from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import EmptyState from '../components/ui/EmptyState';
import Spinner from '../components/ui/Spinner';
import { Task } from '../lib/api';

export default function TasksPage() {
  const navigate = useNavigate();
  const { tasks, total, fetchTasks, createTask, deleteTask, autoAssignTask, retryTask, isLoading } = useTaskStore();
  const { agents, fetchAgents } = useAgentStore();
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [form, setForm] = useState({ name: '', description: '', priority: 'normal', required_capabilities: '' });

  useEffect(() => {
    fetchTasks();
    fetchAgents();
  }, [fetchTasks, fetchAgents]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTask({
        ...form,
        required_capabilities: form.required_capabilities.split(',').map((s) => s.trim()).filter(Boolean),
      });
      setShowCreate(false);
      setForm({ name: '', description: '', priority: 'normal', required_capabilities: '' });
      toast('success', 'Task created');
    } catch {
      toast('error', 'Failed to create task');
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete task "${name}"?`)) return;
    try {
      await deleteTask(id);
      toast('success', 'Task deleted');
    } catch {
      toast('error', 'Failed to delete task');
    }
  };

  const handleAutoAssign = async (id: number) => {
    try {
      await autoAssignTask(id);
      toast('success', 'Task auto-assigned');
    } catch {
      toast('error', 'Failed to auto-assign');
    }
  };

  const handleRetry = async (id: number) => {
    try {
      await retryTask(id);
      toast('success', 'Task retried');
    } catch {
      toast('error', 'Failed to retry task');
    }
  };

  const filtered = tasks.filter((t) => {
    if (statusFilter && t.status !== statusFilter) return false;
    if (priorityFilter && t.priority !== priorityFilter) return false;
    return true;
  });

  const getAgentName = (agentId: number | null) => {
    if (!agentId) return '—';
    const agent = agents.find((a) => a.id === agentId);
    return agent?.name || `#${agentId}`;
  };

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
          <p className="text-sm text-gray-500">{total} total</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus size={16} className="mr-2" /> Create Task
        </Button>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex gap-1">
          {['', 'pending', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled'].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                statusFilter === f ? 'bg-brand-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f || 'All Status'}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          {['', 'low', 'normal', 'high', 'urgent', 'critical'].map((f) => (
            <button
              key={f}
              onClick={() => setPriorityFilter(f)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                priorityFilter === f ? 'bg-brand-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f || 'All Priority'}
            </button>
          ))}
        </div>
      </div>

      {isLoading && tasks.length === 0 ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No tasks"
          description="Create your first task to get started"
          action={<Button onClick={() => setShowCreate(true)}>Create Task</Button>}
        />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned To</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/tasks/${task.id}`)}>
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{task.name}</div>
                    <div className="text-xs text-gray-500 truncate max-w-[200px]">{task.description}</div>
                  </td>
                  <td className="px-6 py-4"><Badge variant={statusVariant(task.status)}>{task.status}</Badge></td>
                  <td className="px-6 py-4"><Badge variant={statusVariant(task.priority)}>{task.priority}</Badge></td>
                  <td className="px-6 py-4 text-sm text-gray-600">{getAgentName(task.assigned_to)}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{new Date(task.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      {!task.assigned_to && task.status === 'pending' && (
                        <button
                          onClick={() => handleAutoAssign(task.id)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50"
                          title="Auto-assign"
                        >
                          <Plus size={16} />
                        </button>
                      )}
                      {task.status === 'failed' && (
                        <button
                          onClick={() => handleRetry(task.id)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-orange-600 hover:bg-orange-50"
                          title="Retry"
                        >
                          <RotateCcw size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(task.id, task.name)}
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

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Task">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required placeholder="e.g. Refactor auth module" />
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Describe the task..." />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <Input label="Required Capabilities" value={form.required_capabilities} onChange={(e) => setForm({ ...form, required_capabilities: e.target.value })} placeholder="python, api-design" />
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
