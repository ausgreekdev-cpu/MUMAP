import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuthStore } from '../../stores';
import { ToastProvider } from '../ui/Toast';

export default function AppShell() {
  const token = useAuthStore((s) => s.token);
  const { isConnected } = useWebSocket('', token);

  return (
    <ToastProvider>
      <div className="min-h-screen flex">
        <Sidebar />
        <div className="flex-1 flex flex-col ml-16">
          <Header wsConnected={isConnected} />
          <main className="flex-1 overflow-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}
