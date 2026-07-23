import { Link } from 'react-router-dom';
import { Bot, Zap, Shield, BarChart3, Users, ArrowRight, Check, Sparkles, Workflow, GitBranch } from 'lucide-react';
import Button from '../components/ui/Button';

const features = [
  {
    icon: Bot,
    title: 'Smart Agent Matching',
    description: 'Tasks are automatically assigned to the best-suited agent based on capabilities, health score, and availability.',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
  },
  {
    icon: Workflow,
    title: 'Orchestration Engine',
    description: 'Coordinate complex multi-agent workflows with dependency management, retries, and automatic failover.',
    color: 'text-purple-600',
    bg: 'bg-purple-50',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Monitoring',
    description: 'Track agent health, task throughput, and system performance with live dashboards and instant alerts.',
    color: 'text-green-600',
    bg: 'bg-green-50',
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'JWT authentication, API key management, audit logging, and role-based access control out of the box.',
    color: 'text-red-600',
    bg: 'bg-red-50',
  },
  {
    icon: GitBranch,
    title: 'Task Lifecycle',
    description: 'Full task lifecycle management with assign, complete, fail, cancel, retry, and priority queuing.',
    color: 'text-orange-600',
    bg: 'bg-orange-50',
  },
  {
    icon: Sparkles,
    title: 'Extensible Architecture',
    description: 'Clean layered architecture with domain events, repository pattern, and pluggable middleware.',
    color: 'text-pink-600',
    bg: 'bg-pink-50',
  },
];

const stats = [
  { value: '10x', label: 'Faster Task Routing' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '<50ms', label: 'Assignment Latency' },
  { value: '∞', label: 'Scalable Agents' },
];

const steps = [
  { step: '1', title: 'Define Your Agents', description: 'Create specialized agents with roles, capabilities, and system prompts.' },
  { step: '2', title: 'Submit Tasks', description: 'Create tasks with required capabilities and priority levels.' },
  { step: '3', title: 'Auto-Assign & Execute', description: 'The orchestration engine matches tasks to the best agents automatically.' },
  { step: '4', title: 'Monitor & Optimize', description: 'Track performance, rebalance workloads, and scale as needed.' },
];

const testimonials = [
  { name: 'Engineering Team', role: 'At Scale', quote: 'Reduced our task routing overhead by 80%. Agents handle themselves now.' },
  { name: 'DevOps Lead', role: 'Startup', quote: 'The auto-assign feature alone saved us 20 hours per week.' },
  { name: 'CTO', role: 'Enterprise', quote: 'Clean architecture, easy to extend. We added 5 custom agent types in a day.' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">M</div>
            <span className="text-lg font-bold text-gray-900">MUMAP</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/pricing">
              <Button variant="ghost" size="sm">Pricing</Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-brand-50 text-brand-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Sparkles size={14} /> Multi-Agent Orchestration Platform
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight mb-6">
            Orchestrate AI Agents<br />
            <span className="text-brand-600">That Work Together</span>
          </h1>
          <p className="text-xl text-gray-500 mb-8 max-w-2xl mx-auto">
            Create specialized agents, submit tasks, and let MUMAP automatically route work to the best-suited agent. Monitor everything in real time.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg">
                Start Free <ArrowRight size={18} className="ml-2" />
              </Button>
            </Link>
            <a href="#features">
              <Button variant="secondary" size="lg">Learn More</Button>
            </a>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-brand-600">{stat.value}</div>
              <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Everything You Need</h2>
            <p className="text-gray-500 max-w-xl mx-auto">A complete platform for managing AI agent workflows at any scale.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
                <div className={`w-10 h-10 rounded-lg ${f.bg} flex items-center justify-center mb-4`}>
                  <f.icon size={20} className={f.color} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">How It Works</h2>
            <p className="text-gray-500">Four steps from zero to a fully orchestrated agent system.</p>
          </div>
          <div className="grid md:grid-cols-4 gap-8">
            {steps.map((s) => (
              <div key={s.step} className="text-center">
                <div className="w-12 h-12 rounded-full bg-brand-600 text-white flex items-center justify-center text-lg font-bold mx-auto mb-4">
                  {s.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Trusted by Teams</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t) => (
              <div key={t.name} className="bg-white border border-gray-200 rounded-xl p-6">
                <p className="text-gray-600 text-sm mb-4 italic">"{t.quote}"</p>
                <div>
                  <div className="font-medium text-gray-900 text-sm">{t.name}</div>
                  <div className="text-xs text-gray-500">{t.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 bg-brand-600">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Orchestrate?</h2>
          <p className="text-brand-100 mb-8 text-lg">Start managing your AI agents in minutes. Free to get started.</p>
          <div className="flex items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" className="bg-white text-brand-600 hover:bg-brand-50">
                Create Free Account <ArrowRight size={18} className="ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="ghost" className="text-white border-white hover:bg-brand-700">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-gray-200">
        <div className="max-w-5xl mx-auto flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-brand-600 rounded flex items-center justify-center text-white text-xs font-bold">M</div>
            <span>MUMAP</span>
          </div>
          <div>Multi-Agent Orchestration Platform</div>
        </div>
      </footer>
    </div>
  );
}
