import { useState } from 'react';
import { BookOpen, HelpCircle, Zap, ChevronDown, ChevronRight, ArrowLeft, Bot, ListTodo, Server, Shield, Settings, Activity } from 'lucide-react';
import Card, { CardTitle } from '../components/ui/Card';
import Badge from '../components/ui/Badge';

type Tab = 'walkthrough' | 'faq' | 'howto';

interface FAQItem {
  q: string;
  a: string;
}

interface HowToItem {
  title: string;
  icon: React.ReactNode;
  steps: string[];
  tip?: string;
}

const faqData: FAQItem[] = [
  { q: 'What is MUMAP?', a: 'MUMAP (Multi-Agent Management Platform) is a system for creating, managing, and orchestrating AI agents that work together to complete tasks. Each agent has specialized capabilities and can be assigned tasks automatically or manually.' },
  { q: 'How do agents work?', a: 'Agents are specialized AI workers with defined roles (coder, reviewer, tester, etc.) and capabilities (python, react, sql, etc.). When a task is created, the system can auto-assign it to the best-matching agent based on required capabilities.' },
  { q: 'What is auto-assign?', a: 'Auto-assign uses the task\'s required_capabilities to find the best available agent. It considers the agent\'s capabilities, current status (idle/busy), and health score to make the optimal assignment.' },
  { q: 'What do the agent statuses mean?', a: 'idle = available for new tasks, busy = currently executing a task, active = system is healthy and operational, inactive = manually disabled or shut down.' },
  { q: 'What do the task statuses mean?', a: 'pending = waiting to be assigned, running = being processed by an agent, completed = finished successfully, failed = encountered an error, cancelled = manually stopped.' },
  { q: 'What is the health score?', a: 'A 0-100% metric per agent based on completed vs failed tasks, average response time, and recent performance. Higher means more reliable.' },
  { q: 'Can I create custom agents?', a: 'Yes. Go to Agents > Create Agent. Define the name, role, description, and capabilities. The agent will then be available for task assignments.' },
  { q: 'What is the System page for?', a: 'The System page shows overall platform health, agent/task distribution, and lets you trigger a rebalance to redistribute tasks across agents.' },
  { q: 'How do I retry a failed task?', a: 'Go to the task detail page and click the Retry button. The task will reset to pending and can be reassigned.' },
  { q: 'What is the WebSocket connection?', a: 'The green "Live" indicator in the header means you have a real-time WebSocket connection. This enables instant updates when agents or tasks change status.' },
];

const walkthroughSteps = [
  { title: '1. Login', content: 'Click "Dev Login" on the login page for instant access. This creates a developer account with admin privileges automatically.' },
  { title: '2. Dashboard Overview', content: 'The dashboard shows summary cards: Total Agents, Total Tasks, System Status, and Active Agents. Below that you\'ll see Task Distribution and Recent Tasks. Data refreshes every 30 seconds.' },
  { title: '3. Create an Agent', content: 'Navigate to Agents from the sidebar. Click "Create Agent" and fill in the name, role, description, and capabilities (comma-separated). Roles include: general, coder, reviewer, analyst, tester.' },
  { title: '4. Create a Task', content: 'Navigate to Tasks from the sidebar. Click "Create Task". Set the name, description, priority (low/medium/high/critical), and required capabilities. The system uses these to find the best agent.' },
  { title: '5. Assign Tasks', content: 'On a pending task, click "Auto-Assign" to let the system pick the best agent, or click a specific agent name to assign manually. You can also assign from the task detail page.' },
  { title: '6. Monitor Progress', content: 'Click any task to see its detail page with status, assigned agent, and a live log timeline. Use the filter buttons on the Tasks page to view by status or priority.' },
  { title: '7. Manage Agents', content: 'Click any agent to see its health score, performance stats, and capabilities. Use the activate/deactivate button to take agents offline. Set status manually with the status buttons.' },
  { title: '8. System Health', content: 'Visit the System page to see platform-wide metrics. Click "Rebalance" to redistribute tasks across agents if workload is uneven. Click "Refresh" for the latest data.' },
];

const howToData: HowToItem[] = [
  {
    title: 'Create a Coding Agent',
    icon: <Bot size={18} className="text-blue-500" />,
    steps: [
      'Go to Agents from the sidebar',
      'Click "Create Agent"',
      'Name: "Python Expert"',
      'Role: Select "coder"',
      'Description: "Specialized in Python backend development"',
      'Capabilities: python, flask, sqlalchemy, rest-api',
      'Click "Create"',
    ],
    tip: 'Use specific capability names that match your task requirements for better auto-assignment.',
  },
  {
    title: 'Submit a Bug Fix Task',
    icon: <ListTodo size={18} className="text-green-500" />,
    steps: [
      'Go to Tasks from the sidebar',
      'Click "Create Task"',
      'Name: "Fix user authentication bug"',
      'Description: Describe the bug and expected behavior',
      'Priority: Select "high" for urgent fixes',
      'Required Capabilities: python, debugging, security',
      'Click "Create"',
      'Click the task, then "Auto-Assign" to find the best agent',
    ],
  },
  {
    title: 'Review Agent Performance',
    icon: <Activity size={18} className="text-orange-500" />,
    steps: [
      'Go to Agents from the sidebar',
      'Click on an agent name',
      'Check the Health Score card (0-100%)',
      'Review completed vs failed task counts',
      'Check average task time for efficiency',
      'Use status buttons to mark busy/idle manually',
    ],
  },
  {
    title: 'Handle a Failed Task',
    icon: <Shield size={18} className="text-red-500" />,
    steps: [
      'Go to Tasks and filter by "failed"',
      'Click the failed task to open details',
      'Read the error message in the Details card',
      'Review the task logs timeline for context',
      'Fix the underlying issue',
      'Click "Retry" to re-queue the task',
    ],
  },
  {
    title: 'Rebalance Workload',
    icon: <Server size={18} className="text-purple-500" />,
    steps: [
      'Go to System from the sidebar',
      'Review the agent status distribution',
      'If too many agents are "busy", click "Rebalance"',
      'The system redistributes pending tasks',
      'Check agent counts to verify balance',
    ],
  },
  {
    title: 'Filter and Search Tasks',
    icon: <Settings size={18} className="text-gray-500" />,
    steps: [
      'Go to Tasks from the sidebar',
      'Use the Status filter buttons (All, pending, running, completed, failed, cancelled)',
      'Use the Priority filter buttons (All, low, medium, high, critical)',
      'Filters can be combined',
      'Click a task row to view full details',
    ],
  },
];

export default function HelpPage() {
  const [tab, setTab] = useState<Tab>('walkthrough');
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="page-container max-w-4xl">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Help & Guide</h1>
      </div>

      <div className="flex gap-2 mb-6">
        {([
          { key: 'walkthrough', label: 'Walkthrough', icon: BookOpen },
          { key: 'faq', label: 'FAQ', icon: HelpCircle },
          { key: 'howto', label: 'How To', icon: Zap },
        ] as const).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key ? 'bg-brand-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'walkthrough' && (
        <div className="space-y-4">
          <Card>
            <CardTitle>Welcome to MUMAP</CardTitle>
            <p className="text-sm text-gray-600 mt-2">
              This walkthrough takes you through the core features of the Multi-Agent Management Platform.
              Follow the steps in order for a complete overview.
            </p>
          </Card>
          {walkthroughSteps.map((step, i) => (
            <Card key={i}>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-sm font-bold">
                  {i + 1}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{step.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{step.content}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {tab === 'faq' && (
        <div className="space-y-3">
          {faqData.map((item, i) => (
            <Card key={i} padding={false}>
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between px-6 py-4 text-left"
              >
                <span className="font-medium text-gray-900 text-sm">{item.q}</span>
                {openFaq === i ? <ChevronDown size={18} className="text-gray-400" /> : <ChevronRight size={18} className="text-gray-400" />}
              </button>
              {openFaq === i && (
                <div className="px-6 pb-4">
                  <p className="text-sm text-gray-600">{item.a}</p>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {tab === 'howto' && (
        <div className="space-y-4">
          {howToData.map((item, i) => (
            <Card key={i}>
              <div className="flex items-center gap-3 mb-3">
                {item.icon}
                <h3 className="font-semibold text-gray-900">{item.title}</h3>
              </div>
              <ol className="space-y-2 ml-8">
                {item.steps.map((step, j) => (
                  <li key={j} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-gray-400 font-mono text-xs mt-0.5">{j + 1}.</span>
                    {step}
                  </li>
                ))}
              </ol>
              {item.tip && (
                <div className="mt-3 ml-8 p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700"><strong>Tip:</strong> {item.tip}</p>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
