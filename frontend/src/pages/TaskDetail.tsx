import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tasksAPI } from '../services/api';
import { Task, TaskLog } from '../types';
import { useToast } from '../components/Toast';

export function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [task, setTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<TaskLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const errorDetail = (error: unknown, fallback: string) => {
    const apiErr = error as { response?: { data?: { detail?: string } } };
    return apiErr.response?.data?.detail || fallback;
  };

  useEffect(() => {
    loadTask();
  }, [id]);

  const loadTask = async () => {
    try {
      const [taskRes, logsRes] = await Promise.all([
        tasksAPI.get(Number(id)),
        tasksAPI.getLogs(Number(id)),
      ]);
      setTask(taskRes.data);
      setLogs(logsRes.data);
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to load task'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAutoAssign = async () => {
    try {
      await tasksAPI.autoAssign(Number(id));
      toast('success', 'Task assigned');
      loadTask();
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to auto-assign'));
    }
  };

  const handleCancel = async () => {
    try {
      await tasksAPI.cancel(Number(id));
      toast('success', 'Task cancelled');
      loadTask();
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to cancel'));
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      await tasksAPI.delete(Number(id));
      toast('success', 'Task deleted');
      navigate('/tasks');
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to delete'));
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400">Loading task...</span>
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Task not found</p>
        <button onClick={() => navigate('/tasks')} className="mt-4 btn btn-primary">
          Back to Tasks
        </button>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'in_progress': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'failed': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'pending': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'assigned': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500/20 text-red-400';
      case 'high': return 'bg-orange-500/20 text-orange-400';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/tasks')}
            className="p-2 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold">{task.name}</h1>
            <p className="text-gray-400 truncate">{task.description || 'No description'}</p>
          </div>
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium border ${getStatusColor(task.status)}`}>
            {task.status.replace('_', ' ')}
          </span>
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${getPriorityColor(task.priority)}`}>
            {task.priority}
          </span>
        </div>
        <div className="flex gap-2">
          {task.status === 'pending' && (
            <button onClick={handleAutoAssign} className="btn btn-primary">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
              Auto Assign
            </button>
          )}
          {['pending', 'assigned'].includes(task.status) && (
            <button onClick={handleCancel} className="btn btn-secondary">Cancel</button>
          )}
          {['pending', 'cancelled', 'failed'].includes(task.status) && (
            <button onClick={handleDelete} className="btn btn-danger">Delete</button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Details</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-400">Description</p>
                <p className="mt-1">{task.description || 'No description'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Assigned To</p>
                <p className="mt-1">
                  {task.assigned_to ? (
                    <button 
                      onClick={() => navigate(`/agents/${task.assigned_to}`)}
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Agent #{task.assigned_to}
                    </button>
                  ) : 'Not assigned'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Required Capabilities</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {task.required_capabilities.length === 0 ? (
                    <span className="text-gray-500">None specified</span>
                  ) : (
                    task.required_capabilities.map((cap) => (
                      <span key={cap} className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-sm">
                        {cap}
                      </span>
                    ))
                  )}
                </div>
              </div>
              {task.error_message && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                  <p className="text-sm text-gray-400 mb-1">Error</p>
                  <p className="text-red-400">{task.error_message}</p>
                </div>
              )}
            </div>
          </div>

          {/* Input/Output Data */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Input Data</h2>
              <pre className="p-4 bg-[#0a0a0f] rounded-xl text-sm overflow-auto max-h-48 text-gray-300 border border-white/5">
                {JSON.stringify(task.input_data, null, 2) || '{}'}
              </pre>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Output Data</h2>
              <pre className="p-4 bg-[#0a0a0f] rounded-xl text-sm overflow-auto max-h-48 text-gray-300 border border-white/5">
                {JSON.stringify(task.output_data, null, 2) || '{}'}
              </pre>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Timestamps */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Timeline</h2>
            <div className="space-y-4 text-sm">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-indigo-400 mt-1.5" />
                <div>
                  <p className="text-gray-300">Created</p>
                  <p className="text-gray-400">{new Date(task.created_at).toLocaleString()}</p>
                </div>
              </div>
              {task.assigned_at && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-purple-400 mt-1.5" />
                  <div>
                    <p className="text-gray-300">Assigned</p>
                    <p className="text-gray-400">{new Date(task.assigned_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
              {task.started_at && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5" />
                  <div>
                    <p className="text-gray-300">Started</p>
                    <p className="text-gray-400">{new Date(task.started_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
              {task.completed_at && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5" />
                  <div>
                    <p className="text-gray-300">Completed</p>
                    <p className="text-gray-400">{new Date(task.completed_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Activity Log */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Activity Log</h2>
            {logs.length === 0 ? (
              <p className="text-gray-400 text-sm">No activity yet</p>
            ) : (
              <div className="space-y-3">
                {logs.map((log) => (
                  <div key={log.id} className="text-sm">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        log.event === 'completed' ? 'bg-emerald-400' :
                        log.event === 'failed' ? 'bg-red-400' :
                        'bg-blue-400'
                      }`} />
                      <span className="font-medium">{log.event}</span>
                    </div>
                    <p className="text-gray-400 ml-3.5 mt-1">{log.message}</p>
                    <p className="text-gray-500 text-xs ml-3.5">
                      {new Date(log.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
