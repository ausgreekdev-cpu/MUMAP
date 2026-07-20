import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export function Settings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-400">Manage your account and platform settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-white/5 rounded-xl w-fit">
        {['profile', 'security', 'notifications'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-lg capitalize transition-all ${
              activeTab === tab
                ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-white border border-indigo-500/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Profile */}
      {activeTab === 'profile' && (
        <div className="card max-w-2xl">
          <h2 className="text-lg font-semibold mb-6">Profile Information</h2>
          
          <div className="flex items-center gap-6 mb-8">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-3xl font-bold shadow-lg shadow-indigo-500/20">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="text-xl font-semibold">{user?.username}</h3>
              <p className="text-gray-400">{user?.email}</p>
              <p className="text-sm text-gray-500 mt-1">Member since {new Date(user?.created_at || '').toLocaleDateString()}</p>
            </div>
          </div>

          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">Username</label>
                <input type="text" defaultValue={user?.username} className="input" />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">Email</label>
                <input type="email" defaultValue={user?.email} className="input" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Role</label>
              <input type="text" defaultValue={user?.role} disabled className="input opacity-50" />
            </div>

            <div className="pt-4">
              <button className="btn btn-primary">Save Changes</button>
            </div>
          </div>
        </div>
      )}

      {/* Security */}
      {activeTab === 'security' && (
        <div className="card max-w-2xl">
          <h2 className="text-lg font-semibold mb-6">Security Settings</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-medium mb-4">Change Password</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">Current Password</label>
                  <input type="password" className="input" placeholder="Enter current password" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">New Password</label>
                    <input type="password" className="input" placeholder="Enter new password" />
                  </div>
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">Confirm Password</label>
                    <input type="password" className="input" placeholder="Confirm new password" />
                  </div>
                </div>
                <button className="btn btn-primary">Update Password</button>
              </div>
            </div>

            <div className="border-t border-white/5 pt-6">
              <h3 className="font-medium mb-4">API Keys</h3>
              <p className="text-sm text-gray-400 mb-4">Manage your API keys for programmatic access.</p>
              <button className="btn btn-secondary">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
                </svg>
                Generate API Key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notifications */}
      {activeTab === 'notifications' && (
        <div className="card max-w-2xl">
          <h2 className="text-lg font-semibold mb-6">Notification Preferences</h2>
          
          <div className="space-y-4">
            {[
              { label: 'Task completed', description: 'Get notified when a task finishes', enabled: true },
              { label: 'Task failed', description: 'Get notified when a task fails', enabled: true },
              { label: 'Agent offline', description: 'Get notified when an agent goes offline', enabled: false },
              { label: 'Weekly summary', description: 'Receive a weekly platform summary', enabled: true },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                <div>
                  <p className="font-medium">{item.label}</p>
                  <p className="text-sm text-gray-400">{item.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={item.enabled} className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-indigo-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                </label>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
