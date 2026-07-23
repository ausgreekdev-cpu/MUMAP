import { Crown, Lock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from './Button';

interface PaywallProps {
  feature: string;
  description?: string;
  requiredTier?: 'pro' | 'team';
}

export default function Paywall({ feature, description, requiredTier = 'pro' }: PaywallProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-indigo-100 flex items-center justify-center mb-4">
        <Lock size={28} className="text-indigo-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{feature} requires {requiredTier === 'pro' ? 'Pro' : 'Team'}</h3>
      <p className="text-sm text-gray-500 mb-6 max-w-sm">
        {description || `Upgrade to ${requiredTier === 'pro' ? 'Pro' : 'Team'} to unlock ${feature}.`}
      </p>
      <Button onClick={() => navigate('/pricing')}>
        <Crown size={16} className="mr-2" />
        Upgrade to {requiredTier === 'pro' ? 'Pro' : 'Team'}
      </Button>
    </div>
  );
}
