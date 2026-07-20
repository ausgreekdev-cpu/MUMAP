import { useState, useEffect } from 'react';
import { orgsAPI } from '../services/api';
import { Organization, OrgMember } from '../types';
import { Modal } from '../components/Modal';
import { EmptyState } from '../components/EmptyState';
import { useToast } from '../components/Toast';

export function OrganizationPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [settingsData, setSettingsData] = useState({ name: '', description: '' });
  const { toast } = useToast();

  const currentUserRole = 'owner';

  useEffect(() => {
    loadOrg();
  }, []);

  const loadOrg = async () => {
    try {
      const orgsRes = await orgsAPI.list();
      const orgsList = orgsRes.data.orgs || orgsRes.data;
      if (orgsList.length > 0) {
        const orgData = orgsList[0];
        setOrg(orgData);
        setSettingsData({ name: orgData.name, description: orgData.description || '' });
        const membersRes = await orgsAPI.listMembers(orgData.id);
        setMembers(membersRes.data.members || membersRes.data);
      }
    } catch (error) {
      console.error('Failed to load organization:', error);
      toast('error', 'Failed to load organization data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    try {
      await orgsAPI.invite(org.id, { email: inviteEmail, role: inviteRole });
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('member');
      toast('success', `Invitation sent to ${inviteEmail}`);
      const membersRes = await orgsAPI.listMembers(org.id);
      setMembers(membersRes.data.members || membersRes.data);
    } catch (error) {
      toast('error', 'Failed to send invitation');
    }
  };

  const handleUpdateSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    try {
      const res = await orgsAPI.update(org.id, settingsData);
      setOrg(res.data.org || res.data);
      setShowSettingsModal(false);
      toast('success', 'Organization settings updated');
    } catch (error) {
      toast('error', 'Failed to update settings');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!org) return;
    if (!confirm('Are you sure you want to remove this member?')) return;
    try {
      await orgsAPI.removeMember(org.id, userId);
      const membersRes = await orgsAPI.listMembers(org.id);
      setMembers(membersRes.data.members || membersRes.data);
      toast('success', 'Member removed');
    } catch (error) {
      toast('error', 'Failed to remove member');
    }
  };

  const handleDeleteOrg = async () => {
    if (!org) return;
    try {
      await orgsAPI.delete(org.id);
      toast('success', 'Organization deleted');
      window.location.reload();
    } catch (error) {
      toast('error', 'Failed to delete organization');
    }
  };

  const getRoleBadge = (role: string) => {
    const styles: Record<string, string> = {
      owner: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      admin: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      member: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      viewer: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    };
    return `px-2.5 py-1 text-xs rounded-full font-medium border ${styles[role] || styles.viewer}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400">Loading organization...</span>
        </div>
      </div>
    );
  }

  if (!org) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Organization</h1>
            <p className="text-gray-400">Manage your team and organization settings</p>
          </div>
        </div>
        <EmptyState
          icon={
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
            </svg>
          }
          title="No organization"
          description="You haven't created or joined an organization yet"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-indigo-500/20">
            {org.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{org.name}</h1>
              <span className={`px-2.5 py-1 text-xs rounded-full font-medium border ${
                org.plan === 'enterprise' ? 'bg-purple-500/20 text-purple-400 border-purple-500/30' :
                org.plan === 'pro' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                'bg-gray-500/20 text-gray-400 border-gray-500/30'
              }`}>
                {org.plan}
              </span>
            </div>
            <p className="text-gray-400">{org.member_count} members</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowInviteModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Invite Member
          </button>
          <button
            onClick={() => setShowSettingsModal(true)}
            className="btn btn-secondary flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Settings
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Members Section */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Members ({members.length})</h2>
          </div>

          {members.length === 0 ? (
            <EmptyState
              icon={
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                </svg>
              }
              title="No members"
              description="Invite members to your organization"
            />
          ) : (
            <div className="space-y-2">
              {members.map((member) => (
                <div
                  key={member.user_id}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#6366f1] to-[#8b5cf6] flex items-center justify-center text-white font-semibold text-sm">
                      {member.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium">{member.username}</p>
                      <p className="text-sm text-gray-400">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={getRoleBadge(member.role)}>{member.role}</span>
                    {currentUserRole === 'owner' && member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        className="p-2 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M22 10.5h-6m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Side Section */}
        <div className="space-y-6">
          {/* Plan Info */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Current Plan</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Plan</span>
                <span className={`px-2.5 py-1 text-xs rounded-full font-medium border ${
                  org.plan === 'enterprise' ? 'bg-purple-500/20 text-purple-400 border-purple-500/30' :
                  org.plan === 'pro' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                  'bg-gray-500/20 text-gray-400 border-gray-500/30'
                } capitalize`}>{org.plan}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Agents</span>
                <span className="text-gray-200">{org.max_agents}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Members</span>
                <span className="text-gray-200">{org.max_members}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Token Limit</span>
                <span className="text-gray-200">{org.monthly_token_limit?.toLocaleString() || 'Unlimited'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Task Limit</span>
                <span className="text-gray-200">{org.monthly_task_limit?.toLocaleString() || 'Unlimited'}</span>
              </div>
              <button className="w-full mt-2 btn btn-primary text-sm">
                Upgrade Plan
              </button>
            </div>
          </div>

          {/* Danger Zone */}
          {currentUserRole === 'owner' && (
            <div className="card border-red-500/20">
              <h2 className="text-lg font-semibold mb-4 text-red-400">Danger Zone</h2>
              <p className="text-sm text-gray-400 mb-4">
                Deleting the organization is irreversible. All data will be lost.
              </p>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full btn bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 rounded-xl py-2.5 text-sm font-medium transition-all"
              >
                Delete Organization
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Invite Modal */}
      <Modal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        title="Invite Member"
        size="sm"
      >
        <form onSubmit={handleInvite} className="space-y-5">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Email Address</label>
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@example.com"
              className="input"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="input"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowInviteModal(false)}
              className="btn btn-secondary flex-1"
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary flex-1">
              Send Invite
            </button>
          </div>
        </form>
      </Modal>

      {/* Settings Modal */}
      <Modal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        title="Organization Settings"
        size="sm"
      >
        <form onSubmit={handleUpdateSettings} className="space-y-5">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Organization Name</label>
            <input
              type="text"
              value={settingsData.name}
              onChange={(e) => setSettingsData({ ...settingsData, name: e.target.value })}
              className="input"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Description</label>
            <textarea
              value={settingsData.description}
              onChange={(e) => setSettingsData({ ...settingsData, description: e.target.value })}
              placeholder="Describe your organization..."
              className="input min-h-[100px] resize-none"
              rows={4}
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowSettingsModal(false)}
              className="btn btn-secondary flex-1"
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary flex-1">
              Save Changes
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Organization"
        size="sm"
      >
        <div className="space-y-5">
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
            <svg className="w-6 h-6 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p className="text-sm text-red-300">
              This action cannot be undone. All data associated with this organization will be permanently deleted.
            </p>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="btn btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              onClick={handleDeleteOrg}
              className="flex-1 bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 rounded-xl py-2.5 text-sm font-medium transition-all"
            >
              Delete Organization
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
