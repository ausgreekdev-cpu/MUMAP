import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import { useToast } from '../components/Toast';

interface Preferences {
  task_completed: boolean;
  task_failed: boolean;
  agent_offline: boolean;
  weekly_summary: boolean;
}

const PREFERENCE_ITEMS: { key: keyof Preferences; label: string; description: string }[] = [
  { key: 'task_completed', label: 'Task completed', description: 'Get notified when a task finishes' },
  { key: 'task_failed', label: 'Task failed', description: 'Get notified when a task fails' },
  { key: 'agent_offline', label: 'Agent offline', description: 'Get notified when an agent goes offline' },
  { key: 'weekly_summary', label: 'Weekly summary', description: 'Receive a weekly platform summary' },
];

export function Settings() {
  const { user, refreshUser } = useAuth();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('profile');

  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSavingPassword, setIsSavingPassword] = useState(false);

  const [prefs, setPrefs] = useState<Preferences | null>(null);

  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setEmail(user.email);
    }
  }, [user]);

  useEffect(() => {
    authAPI
      .getPreferences()
      .then((res) => setPrefs(res.data))
      .catch(() => toast('error', 'Failed to load notification preferences'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const errorDetail = (error: unknown, fallback: string) => {
    const apiErr = error as { response?: { data?: { detail?: unknown } } };
    const detail = apiErr.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d) => d?.msg || d).join(', ');
    return fallback;
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !email.trim()) {
      toast('error', 'Username and email are required');
      return;
    }
    setIsSavingProfile(true);
    try {
      await authAPI.updateProfile({ username: username.trim(), email: email.trim() });
      await refreshUser();
      toast('success', 'Profile updated');
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to update profile'));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast('error', 'New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast('error', 'New passwords do not match');
      return;
    }
    setIsSavingPassword(true);
    try {
      await authAPI.changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast('success', 'Password updated');
    } catch (error) {
      toast('error', errorDetail(error, 'Failed to update password'));
    } finally {
      setIsSavingPassword(false);
    }
  };

  const handleTogglePref = async (key: keyof Preferences, value: boolean) => {
    const previous = prefs;
    setPrefs((p) => (p ? { ...p, [key]: value } : p));
    try {
      const res = await authAPI.updatePreferences({ [key]: value });
      setPrefs(res.data);
    } catch (error) {
      if (previous) setPrefs(previous);
      toast('error', errorDetail(error, 'Failed to save preference'));
    }
  };

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
        <form onSubmit={handleSaveProfile} className="card max-w-2xl">
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
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input"
                  minLength={3}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">Role</label>
              <input type="text" value={user?.role || ''} disabled className="input opacity-50" />
            </div>

            <div className="pt-4">
              <button type="submit" disabled={isSavingProfile} className="btn btn-primary disabled:opacity-50">
                {isSavingProfile ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Security */}
      {activeTab === 'security' && (
        <div className="card max-w-2xl">
          <h2 className="text-lg font-semibold mb-6">Security Settings</h2>

          <form onSubmit={handleChangePassword} className="space-y-6">
            <div>
              <h3 className="font-medium mb-4">Change Password</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">Current Password</label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="input"
                    placeholder="Enter current password"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">New Password</label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="input"
                      placeholder="Enter new password"
                      minLength={8}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">Confirm Password</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="input"
                      placeholder="Confirm new password"
                      required
                    />
                  </div>
                </div>
                <button type="submit" disabled={isSavingPassword} className="btn btn-primary disabled:opacity-50">
                  {isSavingPassword ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Notifications */}
      {activeTab === 'notifications' && (
        <div className="card max-w-2xl">
          <h2 className="text-lg font-semibold mb-6">Notification Preferences</h2>

          {!prefs ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-4">
              {PREFERENCE_ITEMS.map((item) => (
                <div key={item.key} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                  <div>
                    <p className="font-medium">{item.label}</p>
                    <p className="text-sm text-gray-400">{item.description}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={prefs[item.key]}
                      onChange={(e) => handleTogglePref(item.key, e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-indigo-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
