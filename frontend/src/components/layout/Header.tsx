import { useAuthStore } from '../../stores';
import { LogOut, Wifi, WifiOff } from 'lucide-react';

interface HeaderProps {
  wsConnected?: boolean;
}

export default function Header({ wsConnected = false }: HeaderProps) {
  const { user, logout } = useAuthStore();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">Multi-Agent Platform</span>
        <div className="flex items-center gap-1 text-xs">
          {wsConnected ? (
            <>
              <Wifi size={12} className="text-green-500" />
              <span className="text-green-600">Live</span>
            </>
          ) : (
            <>
              <WifiOff size={12} className="text-gray-400" />
              <span className="text-gray-400">Offline</span>
            </>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-700">{user?.username || user?.email}</span>
        <button
          onClick={logout}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
