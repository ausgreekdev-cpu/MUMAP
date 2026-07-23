import { useState, useEffect } from 'react';
import { Check, Crown, Users, Zap, Lock, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useSubscriptionStore, PLANS, SubscriptionTier } from '../stores/subscriptionStore';
import { purchaseSubscription, getSubscriptionProducts, restorePurchases } from '../lib/billing';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';

const tierIcons: Record<SubscriptionTier, React.ReactNode> = {
  free: <Zap size={24} />,
  pro: <Crown size={24} />,
  team: <Users size={24} />,
};

const tierColors: Record<SubscriptionTier, string> = {
  free: 'text-gray-600 bg-gray-100',
  pro: 'text-indigo-600 bg-indigo-100',
  team: 'text-purple-600 bg-purple-100',
};

const tierBorder: Record<SubscriptionTier, string> = {
  free: 'border-gray-200',
  pro: 'border-indigo-400 ring-2 ring-indigo-100',
  team: 'border-purple-400 ring-2 ring-purple-100',
};

export default function PricingPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { currentTier, setTier } = useSubscriptionStore();
  const [purchasing, setPurchasing] = useState<SubscriptionTier | null>(null);
  const [annual, setAnnual] = useState(false);

  const handlePurchase = async (tier: SubscriptionTier) => {
    if (tier === 'free') return;
    setPurchasing(tier);
    const ok = await purchaseSubscription(tier, annual ? 'yearly' : 'monthly');
    if (ok) {
      toast('success', `${tier === 'pro' ? 'Pro' : 'Team'} activated!`);
      navigate('/dashboard');
    } else {
      toast('info', 'Purchase cancelled');
    }
    setPurchasing(null);
  };

  const handleRestore = async () => {
    const ok = await restorePurchases();
    toast(ok ? 'success' : 'info', ok ? 'Subscription restored!' : 'No active subscription found');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft size={16} /> Back
        </button>

        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Choose Your Plan</h1>
          <p className="text-gray-500 max-w-lg mx-auto">
            Scale your AI agent fleet. Start free, upgrade when you need more power.
          </p>

          <div className="flex items-center justify-center gap-3 mt-6">
            <span className={`text-sm ${!annual ? 'font-semibold text-gray-900' : 'text-gray-400'}`}>Monthly</span>
            <button
              onClick={() => setAnnual(!annual)}
              className={`relative w-12 h-6 rounded-full transition-colors ${annual ? 'bg-indigo-600' : 'bg-gray-300'}`}
            >
              <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${annual ? 'left-7' : 'left-1'}`} />
            </button>
            <span className={`text-sm ${annual ? 'font-semibold text-gray-900' : 'text-gray-400'}`}>
              Annual <Badge variant="success" className="ml-1">Save 17%</Badge>
            </span>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {PLANS.map((plan) => {
            const isActive = currentTier === plan.tier;
            const price = plan.tier === 'free' ? '$0' : annual
              ? plan.tier === 'pro' ? '$12.49' : '$33.25'
              : plan.price;

            return (
              <Card
                key={plan.id}
                className={`relative border-2 transition-all ${tierBorder[plan.tier]} ${isActive ? 'ring-2 ring-green-400' : ''}`}
                padding={false}
              >
                {plan.tier === 'pro' && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge variant="info" className="px-3 py-1">Most Popular</Badge>
                  </div>
                )}

                <div className="p-6">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${tierColors[plan.tier]}`}>
                    {tierIcons[plan.tier]}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                  <div className="mt-3 mb-6">
                    <span className="text-3xl font-bold text-gray-900">{price}</span>
                    {plan.period !== 'forever' && (
                      <span className="text-gray-400 text-sm">{annual ? '/mo billed annually' : plan.period}</span>
                    )}
                  </div>

                  <ul className="space-y-2.5 mb-6">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                        <Check size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  {isActive ? (
                    <Button variant="secondary" className="w-full" disabled>
                      Current Plan
                    </Button>
                  ) : plan.tier === 'free' ? (
                    <Button variant="secondary" className="w-full" disabled>
                      Free Forever
                    </Button>
                  ) : (
                    <Button
                      className="w-full"
                      onClick={() => handlePurchase(plan.tier)}
                      disabled={purchasing !== null}
                    >
                      {purchasing === plan.tier ? 'Processing...' : `Upgrade to ${plan.name}`}
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>

        <div className="text-center mt-8">
          <button onClick={handleRestore} className="text-sm text-indigo-600 hover:text-indigo-800 underline">
            Restore Purchases
          </button>
        </div>

        <div className="mt-12 text-center">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Compare Plans</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4">Feature</th>
                  <th className="py-3 px-4">Community</th>
                  <th className="py-3 px-4 text-indigo-600">Pro</th>
                  <th className="py-3 px-4 text-purple-600">Team</th>
                </tr>
              </thead>
              <tbody className="text-gray-600">
                <tr className="border-b border-gray-100">
                  <td className="py-3 px-4 text-left">Max Agents</td>
                  <td className="py-3 px-4 text-center">3</td>
                  <td className="py-3 px-4 text-center">15</td>
                  <td className="py-3 px-4 text-center">50</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-3 px-4 text-left">Daily Tasks</td>
                  <td className="py-3 px-4 text-center">10</td>
                  <td className="py-3 px-4 text-center">Unlimited</td>
                  <td className="py-3 px-4 text-center">Unlimited</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-3 px-4 text-left">Industry Templates</td>
                  <td className="py-3 px-4 text-center">2</td>
                  <td className="py-3 px-4 text-center">All 10</td>
                  <td className="py-3 px-4 text-center">All 10</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-3 px-4 text-left">Analytics</td>
                  <td className="py-3 px-4 text-center">-</td>
                  <td className="py-3 px-4 text-center"><Check size={16} className="inline text-green-500" /></td>
                  <td className="py-3 px-4 text-center"><Check size={16} className="inline text-green-500" /></td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-3 px-4 text-left">API Access</td>
                  <td className="py-3 px-4 text-center">-</td>
                  <td className="py-3 px-4 text-center">-</td>
                  <td className="py-3 px-4 text-center"><Check size={16} className="inline text-green-500" /></td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-3 px-4 text-left">Team Collaboration</td>
                  <td className="py-3 px-4 text-center">-</td>
                  <td className="py-3 px-4 text-center">-</td>
                  <td className="py-3 px-4 text-center"><Check size={16} className="inline text-green-500" /></td>
                </tr>
                <tr>
                  <td className="py-3 px-4 text-left">Support</td>
                  <td className="py-3 px-4 text-center">Community</td>
                  <td className="py-3 px-4 text-center">Priority</td>
                  <td className="py-3 px-4 text-center">Dedicated</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
