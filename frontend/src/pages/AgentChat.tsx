import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { agentsAPI } from '../services/api';
import { Agent } from '../types';
import { useToast } from '../components/Toast';

interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

const STORAGE_KEY = 'agent_chat_conversations';

function loadConversations(): Record<string, ChatMessage[]> {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : {};
  } catch {
    return {};
  }
}

function saveConversations(convos: Record<string, ChatMessage[]>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(convos));
  } catch {
    console.error('Failed to save conversations');
  }
}

export function AgentChat() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>(id || '');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    if (id) {
      setSelectedAgentId(id);
    }
  }, [id]);

  useEffect(() => {
    if (selectedAgentId && agents.length > 0) {
      const agent = agents.find((a) => a.id === Number(selectedAgentId));
      setSelectedAgent(agent || null);

      const conversations = loadConversations();
      setMessages(conversations[selectedAgentId] || []);
    }
  }, [selectedAgentId, agents]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  useEffect(() => {
    if (selectedAgentId && messages.length > 0) {
      const conversations = loadConversations();
      conversations[selectedAgentId] = messages;
      saveConversations(conversations);
    }
  }, [messages, selectedAgentId]);

  useEffect(() => {
    if (!isThinking && selectedAgent) {
      inputRef.current?.focus();
    }
  }, [isThinking, selectedAgent]);

  const loadAgents = async () => {
    try {
      const response = await agentsAPI.list();
      setAgents(response.data.agents || []);
    } catch (error) {
      toast('error', 'Failed to load agents');
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleSendMessage = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || isThinking || !selectedAgentId) return;

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
      const history = messages.slice(-20).map((m) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content,
      }));
      const response = await agentsAPI.chat(Number(selectedAgentId), {
        message: content,
        history,
      });

      const agentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: response.data.response || response.data.message || 'No response received.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      const apiErr = error as { response?: { data?: { detail?: string } } };
      const detail = apiErr.response?.data?.detail;
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: detail || 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast('error', detail || 'Failed to get agent response');
    } finally {
      setIsThinking(false);
    }
  }, [inputValue, isThinking, selectedAgentId, toast, messages]);

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

  const handleClearChat = () => {
    setMessages([]);
    if (selectedAgentId) {
      const conversations = loadConversations();
      delete conversations[selectedAgentId];
      saveConversations(conversations);
    }
  };

  const handleAgentChange = (agentId: string) => {
    setSelectedAgentId(agentId);
    navigate(agentId ? `/agents/${agentId}/chat` : '/agents', { replace: true });
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

  return (
    <div className="animate-fadeIn" style={{ height: 'calc(100vh - 96px)' }}>
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#12121a]/50 backdrop-blur-sm rounded-t-2xl">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/agents')}
              className="p-2 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>
            <div className="flex items-center gap-3">
              {selectedAgent ? (
                <>
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-lg font-bold">{selectedAgent.name}</h1>
                    <p className="text-xs text-gray-400 capitalize">{selectedAgent.role} agent</p>
                  </div>
                </>
              ) : (
                <h1 className="text-lg font-bold">Agent Chat</h1>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="px-6 py-3 border-b border-white/5 bg-[#12121a]/30">
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-400 whitespace-nowrap">Chat with:</label>
            <select
              value={selectedAgentId}
              onChange={(e) => handleAgentChange(e.target.value)}
              className="input flex-1 max-w-sm"
              disabled={isLoadingAgents}
            >
              <option value="">Select an agent...</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name} ({agent.role}) - {agent.status}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 bg-[#0a0a0f]/50">
          {messages.length === 0 && selectedAgent && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 flex items-center justify-center mb-5">
                <svg className="w-10 h-10 text-[#8b5cf6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold mb-2">Chat with {selectedAgent.name}</h2>
              <p className="text-gray-400 text-sm max-w-md mb-1">
                {selectedAgent.description || `A ${selectedAgent.role} agent ready to help.`}
              </p>
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {selectedAgent.capabilities.slice(0, 5).map((cap) => (
                  <span key={cap} className="px-3 py-1 text-xs rounded-full bg-white/5 border border-white/10 text-gray-300">
                    {cap}
                  </span>
                ))}
              </div>
              <p className="text-gray-500 text-xs mt-6">Type a message below to start the conversation</p>
            </div>
          )}

          {messages.length === 0 && !selectedAgent && !isLoadingAgents && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center mb-5">
                <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold mb-2">Select an agent</h2>
              <p className="text-gray-400 text-sm">Choose an agent from the dropdown above to start chatting</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'agent' && selectedAgent && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center flex-shrink-0 mr-3 mt-1">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                </div>
              )}
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 ${
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
              {selectedAgent && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center flex-shrink-0 mr-3 mt-1">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                </div>
              )}
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

        <div className="px-6 py-4 border-t border-white/5 bg-[#12121a]/50 backdrop-blur-sm rounded-b-2xl">
          <div className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder={selectedAgent ? `Message ${selectedAgent.name}...` : 'Select an agent first...'}
              rows={1}
              disabled={!selectedAgent}
              className="flex-1 p-3 bg-[#0a0a0f] border border-white/10 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#6366f1]/50 resize-none max-h-40 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ minHeight: '44px' }}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isThinking || !selectedAgent}
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
  );
}
