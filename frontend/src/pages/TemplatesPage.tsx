import { useEffect, useState } from 'react';
import { Code, Heart, DollarSign, ShoppingCart, Megaphone, Scale, GraduationCap, Factory, Building, Users, Rocket, Check } from 'lucide-react';
import { templatesApi, IndustryTemplate } from '../lib/api';
import { useToast } from '../components/ui/Toast';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Spinner from '../components/ui/Spinner';

const iconMap: Record<string, React.ReactNode> = {
  Code: <Code size={28} />,
  Heart: <Heart size={28} />,
  DollarSign: <DollarSign size={28} />,
  ShoppingCart: <ShoppingCart size={28} />,
  Megaphone: <Megaphone size={28} />,
  Scale: <Scale size={28} />,
  GraduationCap: <GraduationCap size={28} />,
  Factory: <Factory size={28} />,
  Building: <Building size={28} />,
  Users: <Users size={28} />,
};

const colorMap: Record<string, string> = {
  blue: 'bg-blue-50 text-blue-600',
  red: 'bg-red-50 text-red-600',
  green: 'bg-green-50 text-green-600',
  orange: 'bg-orange-50 text-orange-600',
  purple: 'bg-purple-50 text-purple-600',
  slate: 'bg-slate-50 text-slate-600',
  cyan: 'bg-cyan-50 text-cyan-600',
  amber: 'bg-amber-50 text-amber-600',
  teal: 'bg-teal-50 text-teal-600',
  indigo: 'bg-indigo-50 text-indigo-600',
};

export default function TemplatesPage() {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<IndustryTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState<IndustryTemplate | null>(null);
  const [deploying, setDeploying] = useState(false);
  const [deployed, setDeployed] = useState<Record<string, boolean>>({});

  useEffect(() => {
    templatesApi.list().then((r) => {
      setTemplates(r.data.templates);
      setIsLoading(false);
    }).catch(() => setIsLoading(false));
  }, []);

  const handleDeploy = async (template: IndustryTemplate) => {
    setDeploying(true);
    try {
      const r = await templatesApi.deploy(template.id);
      setDeployed((prev) => ({ ...prev, [template.id]: true }));
      toast('success', `${template.industry}: ${r.data.agents_created} agents, ${r.data.tasks_created} tasks created`);
      setSelected(null);
    } catch {
      toast('error', 'Failed to deploy template');
    }
    setDeploying(false);
  };

  if (isLoading) {
    return <div className="flex justify-center py-12"><Spinner size="lg" /></div>;
  }

  return (
    <div className="page-container">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Industry Templates</h1>
        <p className="text-sm text-gray-500">Pre-configured agent teams and tasks for specific industries. Deploy with one click.</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((t) => (
          <Card key={t.id} className="hover:shadow-md transition-shadow cursor-pointer" padding={false}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorMap[t.color] || 'bg-gray-50 text-gray-600'}`}>
                  {iconMap[t.icon] || <Code size={28} />}
                </div>
                {deployed[t.id] ? (
                  <Badge variant="success"><Check size={12} className="mr-1" /> Deployed</Badge>
                ) : (
                  <Badge variant="default">{t.agents.length} agents</Badge>
                )}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{t.industry}</h3>
              <p className="text-sm text-gray-500 mb-4">{t.description}</p>
              <div className="flex flex-wrap gap-1 mb-4">
                {t.agents.slice(0, 3).map((a) => (
                  <Badge key={a.name} variant="info" className="text-[10px]">{a.name}</Badge>
                ))}
                {t.agents.length > 3 && (
                  <Badge variant="default" className="text-[10px]">+{t.agents.length - 3} more</Badge>
                )}
              </div>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>{t.tasks.length} sample tasks</span>
                <span>{t.agents.reduce((sum, a) => sum + a.capabilities.length, 0)} capabilities</span>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100">
              <Button
                size="sm"
                className="w-full"
                onClick={() => setSelected(t)}
                disabled={deployed[t.id]}
              >
                {deployed[t.id] ? 'Already Deployed' : 'View & Deploy'}
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title={selected?.industry || ''}>
        {selected && (
          <div className="space-y-6">
            <p className="text-sm text-gray-600">{selected.description}</p>

            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Agents ({selected.agents.length})</h4>
              <div className="space-y-2">
                {selected.agents.map((a) => (
                  <div key={a.name} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-8 h-8 rounded bg-white border border-gray-200 flex items-center justify-center text-xs font-bold text-gray-600">
                      {a.role[0].toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900">{a.name}</div>
                      <div className="text-xs text-gray-500">{a.description}</div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {a.capabilities.map((c) => (
                          <Badge key={c} variant="default" className="text-[10px]">{c}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Sample Tasks ({selected.tasks.length})</h4>
              <div className="space-y-1">
                {selected.tasks.map((t) => (
                  <div key={t.name} className="flex items-center justify-between text-sm py-1.5">
                    <span className="text-gray-700">{t.name}</span>
                    <Badge variant={t.priority === 'critical' ? 'danger' : t.priority === 'high' ? 'warning' : 'info'} className="text-[10px]">
                      {t.priority}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2 border-t border-gray-200">
              <Button variant="secondary" onClick={() => setSelected(null)}>Cancel</Button>
              <Button
                onClick={() => handleDeploy(selected)}
                disabled={deploying || deployed[selected.id]}
              >
                <Rocket size={16} className="mr-2" />
                {deploying ? 'Deploying...' : deployed[selected.id] ? 'Deployed' : 'Deploy Template'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
