import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { tasksAPI } from '../services/api';
import { Task } from '../types';
import { Modal } from '../components/Modal';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../components/Toast';

export function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filter, setFilter] = useState({ status: '', priority: '' });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    priority: 'medium',
    required_capabilities: '',
    input_data: '',
  });
  const navigate = useNavigate();
  const { toast } = useToast();

  const errorDetail = (error: unknown, fallback: string) => {
    const apiErr = error as { response?: { data?: { detail?: string } } };
    return apiErr.response?.data?.detail || fallback;
  };

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    try {
      const params: Record<string, string> = {};
      if (filter.status) params.status = filter.status;
      if (filter.priority) params.priority = filter.priority;
      
      const response = await tasksAPI.list(params);
      setTasks(response.data.tasks);
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to load tasks'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let input_data = {};
      if (formData.input_data) {
        try {
          input_data = JSON.parse(formData.input_data);
        } catch {
          toast('warning', 'Invalid JSON in input data');
          return;
        }
      }

      await tasksAPI.create({
        name: formData.name,
        description: formData.description,
        priority: formData.priority,
        required_capabilities: formData.required_capabilities.split(',').map((c) => c.trim()).filter(Boolean),
        input_data,
      });
      setShowCreateModal(false);
      setFormData({ name: '', description: '', priority: 'medium', required_capabilities: '', input_data: '' });
      toast('success', 'Task created');
      loadTasks();
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to create task'));
    }
  };

  const handleAutoAssign = async (taskId: number) => {
    try {
      await tasksAPI.autoAssign(taskId);
      toast('success', 'Task assigned');
      loadTasks();
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to auto-assign task'));
    }
  };

  const handleCancel = async (taskId: number) => {
    try {
      await tasksAPI.cancel(taskId);
      toast('success', 'Task cancelled');
      loadTasks();
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to cancel task'));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 12.75l6 6 9-13.5" /></svg>;
      case 'failed':
        return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>;
      case 'in_progress':
        return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>;
      default:
        return <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'in_progress': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'failed': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'pending': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'assigned': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'cancelled': return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-emerald-500/20 text-emerald-400';
      case 'in_progress': return 'bg-blue-500/20 text-blue-400';
      case 'failed': return 'bg-red-500/20 text-red-400';
      case 'assigned': return 'bg-purple-500/20 text-purple-400';
      default: return 'bg-yellow-500/20 text-yellow-400';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400">Loading tasks...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Tasks</h1>
          <p className="text-gray-400">Create and manage tasks for your agents</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Task
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="input w-auto"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={filter.priority}
          onChange={(e) => setFilter({ ...filter, priority: e.target.value })}
          className="input w-auto"
        >
          <option value="">All Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      {/* Tasks List */}
      {tasks.length === 0 ? (
        <EmptyState
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          }
          title="No tasks yet"
          description="Create your first task to assign work to your agents"
          action={
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              Create Task
            </button>
          }
        />
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => navigate(`/tasks/${task.id}`)}
              className="card group cursor-pointer hover:border-indigo-500/30 transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                {/* Status Icon */}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${getStatusBg(task.status)}`}>
                  {getStatusIcon(task.status)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <h3 className="font-semibold mb-1">{task.name}</h3>
                      <p className="text-sm text-gray-400 truncate">{task.description || 'No description'}</p>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className={`px-2.5 py-1 text-xs rounded-full font-medium border ${getStatusColor(task.status)}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                      <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                        task.priority === 'critical' ? 'bg-red-500/20 text-red-400' :
                        task.priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
                        task.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {task.priority}
                      </span>
                    </div>
                  </div>

                  {/* Capabilities and Actions */}
                  <div className="flex items-center justify-between mt-3">
                    <div className="flex flex-wrap gap-2">
                      {task.required_capabilities?.slice(0, 3).map((cap, i) => (
                        <span key={i} className="px-2 py-0.5 text-xs rounded bg-white/5 text-gray-300 border border-white/5">
                          {cap}
                        </span>
                      ))}
                      {task.required_capabilities && task.required_capabilities.length > 3 && (
                        <span className="px-2 py-0.5 text-xs rounded bg-white/5 text-gray-400">
                          +{task.required_capabilities.length - 3} more
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {(task.status === 'pending') && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAutoAssign(task.id);
                          }}
                          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30 transition-colors"
                        >
                          Auto-assign
                        </button>
                      )}
                      {(task.status === 'in_progress' || task.status === 'assigned') && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCancel(task.id);
                          }}
                          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create Task"
      >
        <form onSubmit={handleCreate} className="space-y-5">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Task Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Analyze sales data"
              className="input"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Description</label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="What needs to be done?"
              className="input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="input"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Required Capabilities
              </label>
              <input
                type="text"
                value={formData.required_capabilities}
                onChange={(e) => setFormData({ ...formData, required_capabilities: e.target.value })}
                placeholder="e.g., math, analysis"
                className="input"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">
              Input Data
              <span className="text-gray-500 ml-2">(JSON format)</span>
            </label>
            <textarea
              value={formData.input_data}
              onChange={(e) => setFormData({ ...formData, input_data: e.target.value })}
              placeholder='{"key": "value"}'
              className="input h-24 font-mono text-sm resize-none"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="btn btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex-1"
            >
              Create Task
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
