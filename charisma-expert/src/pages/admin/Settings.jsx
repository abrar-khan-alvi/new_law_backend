import { useState, useEffect } from 'react';
import { User, Shield, Save, Key, Loader2 } from 'lucide-react';
import { getProfile, updateProfile, changePassword } from '../../api/auth';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('profile');

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileForm, setProfileForm] = useState({ first_name: '', last_name: '' });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');

  const [passForm, setPassForm] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [savingPass, setSavingPass] = useState(false);
  const [passError, setPassError] = useState('');
  const [passSuccess, setPassSuccess] = useState('');

  useEffect(() => {
    getProfile()
      .then(({ data }) => {
        setProfile(data);
        setProfileForm({ first_name: data.first_name || '', last_name: data.last_name || '' });
      })
      .catch(() => setProfileError('Failed to load profile.'))
      .finally(() => setLoading(false));
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileError('');
    setProfileSuccess('');
    try {
      const { data } = await updateProfile(profileForm);
      setProfile(data);
      setProfileSuccess('Profile updated.');
    } catch (err) {
      setProfileError('Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSave = async (e) => {
    e.preventDefault();
    setPassError('');
    setPassSuccess('');
    if (passForm.new_password !== passForm.confirm_password) {
      setPassError('New password and confirmation do not match.');
      return;
    }
    setSavingPass(true);
    try {
      await changePassword({ old_password: passForm.old_password, new_password: passForm.new_password });
      setPassSuccess('Password changed successfully.');
      setPassForm({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setPassError(err?.response?.data?.error || 'Failed to change password.');
    } finally {
      setSavingPass(false);
    }
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Admin Settings</h1>

        {activeTab === 'profile' && (
          <button
            type="submit"
            form="profile-settings-form"
            disabled={savingProfile || loading}
            className="flex items-center px-5 py-2.5 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 shadow-sm transition-colors disabled:opacity-70"
          >
            {savingProfile ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : <Save className="w-5 h-5 mr-2" />}
            Save Changes
          </button>
        )}
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar Nav */}
        <div className="w-full md:w-64 flex-shrink-0 space-y-1">
          <button
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'profile'
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <User className="w-5 h-5 mr-3" />
            Profile Settings
          </button>

          <button
            onClick={() => setActiveTab('security')}
            className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'security'
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Shield className="w-5 h-5 mr-3" />
            Security & Access
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1">
          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="animate-spin text-gray-400" size={28} />
            </div>
          ) : (
            <>
              {activeTab === 'profile' && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
                  <div className="mb-8">
                    <h2 className="text-xl font-bold text-gray-900">Profile Information</h2>
                    <p className="text-sm text-gray-500 mt-1">Update your admin account name.</p>
                  </div>

                  <div className="flex items-center mb-8">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center text-gray-600 font-bold text-2xl mr-6 border border-gray-200 shadow-sm">
                      {(profileForm.first_name?.[0] || '') + (profileForm.last_name?.[0] || '') || 'A'}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{profile?.email}</div>
                      <p className="text-xs text-gray-500 mt-1">Email cannot be changed here.</p>
                    </div>
                  </div>

                  {profileError && <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm">{profileError}</div>}
                  {profileSuccess && <div className="mb-4 p-3 bg-green-50 text-green-700 border border-green-200 rounded-lg text-sm">{profileSuccess}</div>}

                  <form id="profile-settings-form" onSubmit={handleProfileSave} className="space-y-6 max-w-2xl">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
                        <input
                          type="text"
                          value={profileForm.first_name}
                          onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
                        <input
                          type="text"
                          value={profileForm.last_name}
                          onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                          required
                        />
                      </div>
                    </div>
                  </form>
                </div>
              )}

              {activeTab === 'security' && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
                  <div className="mb-8">
                    <h2 className="text-xl font-bold text-gray-900">Security Settings</h2>
                    <p className="text-sm text-gray-500 mt-1">Change your account password.</p>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-6 max-w-2xl">
                    <div className="flex items-center mb-6">
                      <Key className="w-5 h-5 text-gray-500 mr-2" />
                      <h3 className="text-base font-bold text-gray-900">Change Password</h3>
                    </div>

                    {passError && <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm">{passError}</div>}
                    {passSuccess && <div className="mb-4 p-3 bg-green-50 text-green-700 border border-green-200 rounded-lg text-sm">{passSuccess}</div>}

                    <form onSubmit={handlePasswordSave} className="space-y-5">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
                        <input
                          type="password"
                          value={passForm.old_password}
                          onChange={(e) => setPassForm({ ...passForm, old_password: e.target.value })}
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
                        <input
                          type="password"
                          value={passForm.new_password}
                          onChange={(e) => setPassForm({ ...passForm, new_password: e.target.value })}
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
                        <input
                          type="password"
                          value={passForm.confirm_password}
                          onChange={(e) => setPassForm({ ...passForm, confirm_password: e.target.value })}
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                          required
                        />
                      </div>

                      <div className="pt-2">
                        <button
                          type="submit"
                          disabled={savingPass}
                          className="flex items-center px-5 py-2.5 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 shadow-sm transition-colors disabled:opacity-70"
                        >
                          {savingPass && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                          Update Password
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
