import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, ListTodo, Server, LayoutTemplate, HelpCircle, Crown } from 'lucide-react';
import { useSubscriptionStore } from '../../stores/subscriptionStore';

const links = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/tasks', icon: ListTodo, label: 'Tasks' },
  { to: '/templates', icon: LayoutTemplate, label: 'Templates' },
  { to: '/system', icon: Server, label: 'System' },
  { to: '/help', icon: HelpCircle, label: 'Help' },
];

export default function Sidebar() {
  const tier = useSubscriptionStore((s) => s.currentTier);

  return (
    <aside className="fixed left-0 top-0 h-full w-16 bg-gray-900 flex flex-col items-center py-4 gap-1 z-30">
      <div className="text-brand-400 font-bold text-lg mb-6">M</div>
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.to === '/'}
          className={({ isActive }) =>
            `flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${
              isActive ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`
          }
          title={link.label}
        >
          <link.icon size={20} />
        </NavLink>
      ))}

      <div className="mt-auto flex flex-col items-center gap-1">
        <NavLink
          to="/pricing"
          className={({ isActive }) =>
            `flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${
              isActive
                ? 'bg-indigo-600 text-white'
                : tier === 'free'
                  ? 'text-amber-400 hover:text-amber-300 hover:bg-gray-800'
                  : 'text-indigo-400 hover:text-indigo-300 hover:bg-gray-800'
            }`
          }
          title={tier === 'free' ? 'Upgrade to Pro' : `Plan: ${tier}`}
        >
          <Crown size={20} />
        </NavLink>
      </div>
    </aside>
  );
}
