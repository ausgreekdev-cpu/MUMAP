import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { agentsAPI, tasksAPI } from '../services/api';
import { Agent, Task } from '../types';
import { Modal } from '../components/Modal';
import { useToast } from '../components/Toast';

interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

type DetailTab = 'info' | 'chat' | 'tools';

const defaultTools = [
  { name: 'web_search', description: 'Search the internet for information', paramCount: 2 },
  { name: 'code_exec', description: 'Execute code in a sandboxed environment', paramCount: 3 },
  { name: 'file_read', description: 'Read contents of a file', paramCount: 1 },
  { name: 'file_write', description: 'Write content to a file', paramCount: 2 },
  { name: 'api_call', description: 'Make an HTTP API request', paramCount: 4 },
  { name: 'data_transform', description: 'Transform and process data', paramCount: 3 },
];

export function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<DetailTab>('info');
  const [pendingTasks, setPendingTasks] = useState<Task[]>([]);
  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [executeTaskId, setExecuteTaskId] = useState<string>('');
  const [executeDescription, setExecuteDescription] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executeResult, setExecuteResult] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const [modelProvider] = useState('openai');
  const [modelName] = useState('gpt-4');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    loadAgent();
  }, [id]);

  useEffect(() => {
    if (activeTab === 'info') {
      loadPendingTasks();
    }
  }, [activeTab]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const loadAgent = async () => {
    try {
      const response = await agentsAPI.get(Number(id));
      setAgent(response.data);
    } catch (error) {
      toast('error', 'Failed to load agent');
    } finally {
      setIsLoading(false);
    }
  };

  const loadPendingTasks = async () => {
    try {
      const response = await tasksAPI.list({ status: 'pending' });
      setPendingTasks(response.data.tasks || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await agentsAPI.updateStatus(Number(id), newStatus);
      loadAgent();
      toast('success', `Agent is now ${newStatus}`);
    } catch (error) {
      toast('error', 'Failed to update agent status');
    }
  };

  const handleExecute = async () => {
    if (!executeDescription.trim() && !executeTaskId) return;
    setIsExecuting(true);
    setExecuteResult('');
    try {
      if (executeTaskId) {
        await tasksAPI.assign(Number(executeTaskId), Number(id));
        const response = await tasksAPI.get(Number(executeTaskId));
        setExecuteResult(JSON.stringify(response.data, null, 2));
        toast('success', 'Task assigned to agent successfully');
      } else {
        const taskResponse = await tasksAPI.create({
          name: `Execute: ${executeDescription.slice(0, 50)}`,
          description: executeDescription,
          priority: 'medium',
        });
        await tasksAPI.assign(taskResponse.data.id, Number(id));
        const response = await tasksAPI.get(taskResponse.data.id);
        setExecuteResult(JSON.stringify(response.data, null, 2));
        toast('success', 'Task created and assigned successfully');
      }
      loadPendingTasks();
    } catch (error) {
      toast('error', 'Failed to execute task');
      setExecuteResult(JSON.stringify({ error: 'Execution failed' }, null, 2));
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSendMessage = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || isThinking) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await agentsAPI.chat(Number(id), {
        message: content,
        system_prompt: systemPrompt || undefined,
        temperature,
        max_tokens: maxTokens,
      });

      const agentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: response.data.response || response.data.message || 'No response received.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast('error', 'Failed to get agent response');
    } finally {
      setIsThinking(false);
    }
  }, [inputValue, isThinking, systemPrompt, temperature, maxTokens, id, toast]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
  };

  const renderMessageContent = (content: string) => {
    const parts = content.split(/(```[\s\S]*?```)/g);
    return parts.map((part, i) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3).replace(/^\w+\n/, '');
        return (
          <pre key={i} className="mt-2 p-3 bg-[#0a0a0f] rounded-lg text-sm overflow-x-auto border border-white/5">
            <code>{code}</code>
          </pre>
        );
      }
      const formatted = part.split(/(\*\*.*?\*\*)/g).map((segment, j) => {
        if (segment.startsWith('**') && segment.endsWith('**')) {
          return <strong key={j} className="font-semibold">{segment.slice(2, -2)}</strong>;
        }
        return segment;
      });
      return <span key={i}>{formatted}</span>;
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'busy': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'error': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const tabs: { key: DetailTab; label: string; icon: JSX.Element }[] = [
    {
      key: 'info',
      label: 'Details',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      key: 'chat',
      label: 'Live Chat',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
        </svg>
      ),
    },
    {
      key: 'tools',
      label: 'Tools',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.42 15.17l-5.384 5.384a2.025 2.025 0 01-2.864-2.864l5.384-5.384m2.864 2.864L18.5 6.5a2.121 2.121 0 013 3l-8.08 8.08" />
        </svg>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#6366f1] border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400">Loading agent...</span>
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Agent not found</p>
        <button onClick={() => navigate('/agents')} className="mt-4 btn btn-primary">
          Back to Agents
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/agents')}
            className="p-2 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold">{agent.name}</h1>
            <p className="text-gray-400 capitalize">{agent.role}</p>
          </div>
          <span className={`px-2.5 py-1 text-xs rounded-full font-medium border ${getStatusColor(agent.status)}`}>
            {agent.status}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate(`/agents/${id}/chat`)}
            className="btn btn-secondary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
            Chat
          </button>
          <button
            onClick={() => setShowExecuteModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
            </svg>
            Execute
          </button>
          {agent.status === 'idle' && (
            <button onClick={() => handleStatusChange('offline')} className="btn btn-secondary">
              Take Offline
            </button>
          )}
          {agent.status === 'offline' && (
            <button onClick={() => handleStatusChange('idle')} className="btn btn-primary">
              Bring Online
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.key
                ? 'bg-[#6366f1]/20 text-[#8b5cf6] shadow-sm'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'info' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Agent Configuration</h2>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Role</p>
                  <p className="mt-1 capitalize">{agent.role}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Max Concurrent Tasks</p>
                  <p className="mt-1">{agent.max_concurrent_tasks}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Model Provider</p>
                  <p className="mt-1 capitalize">{modelProvider}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Model</p>
                  <p className="mt-1">{modelName}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-400">Description</p>
                  <p className="mt-1">{agent.description || 'No description'}</p>
                </div>
              </div>
            </div>

            <div className="card">
              <button
                onClick={() => setShowSystemPrompt(!showSystemPrompt)}
                className="flex items-center justify-between w-full"
              >
                <h2 className="text-lg font-semibold">System Prompt</h2>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform ${showSystemPrompt ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showSystemPrompt && (
                <div className="mt-4">
                  <textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    placeholder="Enter a system prompt for this agent..."
                    className="w-full h-32 p-3 bg-[#0a0a0f] border border-white/10 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#6366f1]/50 resize-none"
                  />
                </div>
              )}
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Model Parameters</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm text-gray-400">Temperature</label>
                    <span className="text-sm font-mono text-[#8b5cf6]">{temperature.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.01"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Precise</span>
                    <span>Creative</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm text-gray-400">Max Tokens</label>
                    <span className="text-sm font-mono text-[#8b5cf6]">{maxTokens}</span>
                  </div>
                  <input
                    type="range"
                    min="256"
                    max="8192"
                    step="256"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>256</span>
                    <span>8192</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Capabilities</h2>
              <div className="flex flex-wrap gap-2">
                {agent.capabilities.length === 0 ? (
                  <p className="text-gray-400">No capabilities assigned</p>
                ) : (
                  agent.capabilities.map((cap) => (
                    <span key={cap} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm">
                      {cap}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Statistics</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 rounded-lg bg-emerald-500/10">
                  <span className="text-gray-300">Completed Tasks</span>
                  <span className="font-semibold text-emerald-400 text-lg">{agent.completed_tasks_count}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-red-500/10">
                  <span className="text-gray-300">Failed Tasks</span>
                  <span className="font-semibold text-red-400 text-lg">{agent.failed_tasks_count}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-white/5">
                  <span className="text-gray-300">Current Task</span>
                  <span>{agent.current_task_id ? `#${agent.current_task_id}` : 'None'}</span>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Timestamps</h2>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-400">Created: </span>
                  {new Date(agent.created_at).toLocaleString()}
                </div>
                {agent.updated_at && (
                  <div>
                    <span className="text-gray-400">Updated: </span>
                    {new Date(agent.updated_at).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'chat' && (
        <div className="card p-0 overflow-hidden" style={{ height: 'calc(100vh - 280px)', minHeight: '400px' }}>
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-sm">{agent.name}</p>
                  <p className="text-xs text-gray-400">Live chat session</p>
                </div>
              </div>
              {messages.length > 0 && (
                <button
                  onClick={() => setMessages([])}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Clear chat
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-[#8b5cf6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold mb-1">Start a conversation</h3>
                  <p className="text-gray-400 text-sm max-w-sm">
                    Send a message to {agent.name} to begin a live chat session.
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-[#6366f1] text-white'
                        : 'bg-white/10 text-gray-200'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap break-words">
                      {message.role === 'agent' ? renderMessageContent(message.content) : message.content}
                    </div>
                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/50' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}

              {isThinking && (
                <div className="flex justify-start">
                  <div className="bg-white/10 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-xs text-gray-400">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            <div className="px-6 py-4 border-t border-white/5">
              <div className="flex items-end gap-3">
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={handleTextareaInput}
                  onKeyDown={handleKeyDown}
                  placeholder={`Message ${agent.name}...`}
                  rows={1}
                  className="flex-1 p-3 bg-[#0a0a0f] border border-white/10 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#6366f1]/50 resize-none max-h-40"
                  style={{ minHeight: '44px' }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isThinking}
                  className="p-3 rounded-xl bg-[#6366f1] hover:bg-[#5558e6] disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                >
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                  </svg>
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'tools' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {defaultTools.map((tool) => (
              <div key={tool.name} className="card hover:border-[#6366f1]/30 transition-all">
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-[#6366f1]/10 flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-[#8b5cf6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.42 15.17l-5.384 5.384a2.025 2.025 0 01-2.864-2.864l5.384-5.384m2.864 2.864L18.5 6.5a2.121 2.121 0 013 3l-8.08 8.08" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold font-mono text-sm">{tool.name}</h3>
                    <p className="text-xs text-gray-400 mt-1">{tool.description}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-white/5">
                  <span className="text-xs text-gray-500">{tool.paramCount} parameters</span>
                  <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Available
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <Modal
        isOpen={showExecuteModal}
        onClose={() => {
          setShowExecuteModal(false);
          setExecuteResult('');
          setExecuteTaskId('');
          setExecuteDescription('');
        }}
        title="Execute Task"
        size="lg"
      >
        <div className="space-y-5">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Select Pending Task</label>
            <select
              value={executeTaskId}
              onChange={(e) => {
                setExecuteTaskId(e.target.value);
                if (e.target.value) setExecuteDescription('');
              }}
              className="input"
            >
              <option value="">Choose a pending task...</option>
              {pendingTasks.map((task) => (
                <option key={task.id} value={task.id}>
                  #{task.id} - {task.name}
                </option>
              ))}
            </select>
          </div>

          <div className="text-center text-gray-500 text-sm">— or —</div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Task Description</label>
            <textarea
              value={executeDescription}
              onChange={(e) => {
                setExecuteDescription(e.target.value);
                if (e.target.value) setExecuteTaskId('');
              }}
              placeholder="Describe the task for this agent..."
              className="w-full h-28 p-3 bg-[#0a0a0f] border border-white/10 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#6366f1]/50 resize-none"
            />
          </div>

          {executeResult && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Result</label>
              <pre className="p-4 bg-[#0a0a0f] rounded-xl text-sm overflow-auto max-h-64 text-gray-300 border border-white/5 whitespace-pre-wrap">
                {executeResult}
              </pre>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setShowExecuteModal(false);
                setExecuteResult('');
                setExecuteTaskId('');
                setExecuteDescription('');
              }}
              className="btn btn-secondary flex-1"
            >
              Close
            </button>
            <button
              onClick={handleExecute}
              disabled={isExecuting || (!executeTaskId && !executeDescription.trim())}
              className="btn btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {isExecuting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                  </svg>
                  Execute
                </>
              )}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
