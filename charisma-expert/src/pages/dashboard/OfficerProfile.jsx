import { useState, useEffect } from 'react';
import { User, Briefcase, Mail, Key, Phone, Building, Hash, Loader2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { getProfile, updateProfile, changePassword } from '../../api/auth';
import { getSubscriptionStatus, listPlans } from '../../api/subscriptions';
import { useNavigate } from 'react-router-dom';
import { formatLimit } from '../../utils/format';

export default function OfficerProfile() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState('');

  const [isChangingPass, setIsChangingPass] = useState(false);
  const [passForm, setPassForm] = useState({ old_password: '', new_password: '' });
  const [savingPass, setSavingPass] = useState(false);
  const [passError, setPassError] = useState('');
  const [passSuccess, setPassSuccess] = useState('');

  const [defaultPlan, setDefaultPlan] = useState(null);

  useEffect(() => {
    // We catch the subscription error individually so that a missing subscription
    // doesn't cause the entire Profile promise array to reject.
    const fetchSub = getSubscriptionStatus().catch(() => ({ data: null }));
    const fetchPlans = listPlans().catch(() => ({ data: [] }));
    
    Promise.all([getProfile(), fetchSub, fetchPlans])
      .then(([profRes, subRes, plansRes]) => {
        setProfile(profRes.data);
        setEditForm(profRes.data);
        setSubscription(subRes.data);
        
        // If there is no active subscription, we figure out the default plan from the plans list
        if (!subRes.data && plansRes.data && plansRes.data.length > 0) {
          // Sort by price or sort_order to find the "Free Tier" or lowest tier
          const sorted = [...plansRes.data].sort((a, b) => parseFloat(a.price_monthly) - parseFloat(b.price_monthly));
          setDefaultPlan(sorted[0]);
        }
      })
      .catch(() => setProfileError('Failed to load profile data.'))
      .finally(() => setLoading(false));
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileError('');
    try {
      const { data } = await updateProfile(editForm);
      setProfile(data);
      updateUser(data); // update Context
      setIsEditing(false);
    } catch (err) {
      setProfileError('Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSave = async (e) => {
    e.preventDefault();
    setSavingPass(true);
    setPassError('');
    setPassSuccess('');
    try {
      await changePassword(passForm);
      setPassSuccess('Password changed successfully.');
      setIsChangingPass(false);
      setPassForm({ old_password: '', new_password: '' });
    } catch (err) {
      setPassError(err?.response?.data?.old_password?.[0] || 'Failed to change password.');
    } finally {
      setSavingPass(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  if (!profile) return <div className="p-8 text-red-600">Failed to load profile.</div>;

  const plan = subscription?.plan || defaultPlan || profile.subscription || {};

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 font-serif">Officer Profile</h1>
        <p className="text-gray-500 mt-1">Manage your professional credentials and account security.</p>
      </div>

      {profile.export_readiness && (
        <div className={`rounded-xl border p-4 ${profile.export_readiness.ready ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-amber-50 border-amber-200 text-amber-950'}`}>
          <p className="font-semibold">
            {profile.export_readiness.ready ? 'Ready for export' : profile.export_readiness.status === 'agency_assignment_pending' ? 'Agency assignment pending' : 'Complete your profile to export'}
          </p>
          {!profile.export_readiness.ready && (
            <p className="text-sm mt-1">
              {profile.export_readiness.status === 'agency_assignment_pending'
                ? 'Your profile is complete. A KLYVOREK administrator must assign your agency before PDF or DOCX export.'
                : `Required information: ${profile.export_readiness.missing_fields.join(', ')}.`}
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col: Credentials & Password */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Credentials Card */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg text-blue-700">
                  <User size={20} />
                </div>
                <h2 className="text-xl font-bold text-gray-900 font-serif">Official Credentials</h2>
              </div>
              <button 
                onClick={() => { setIsEditing(!isEditing); setEditForm(profile); setProfileError(''); }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {isEditing ? 'Cancel' : 'Edit Credentials'}
              </button>
            </div>
            
            <div className="p-6">
              {profileError && <p className="text-red-600 text-sm mb-4">{profileError}</p>}
              
              {!isEditing ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-y-6 gap-x-8">
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Full Name</div>
                    <div className="text-gray-900 font-medium flex items-center gap-2">
                      {profile.first_name} {profile.last_name}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Badge Number</div>
                    <div className="text-gray-900 font-medium">{profile.badge_number}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Rank / Title</div>
                    <div className="text-gray-900 font-medium">{profile.rank}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Division</div>
                    <div className="text-gray-900 font-medium">{profile.division || 'N/A'}</div>
                  </div>
                  <div className="md:col-span-2 pt-4 border-t border-gray-100">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Department</div>
                    <div className="text-gray-900 font-medium">{profile.department_name}</div>
                    <div className="text-gray-500 text-sm mt-1">{profile.department_address}, {profile.department_state}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">ORI Number</div>
                    <div className="text-gray-900 font-medium font-mono text-sm">{profile.ori || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Phone Number</div>
                    <div className="text-gray-900 font-medium">{profile.phone_number || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Contact Email</div>
                    <div className="text-gray-900 font-medium">{profile.email}</div>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleProfileSave} className="grid grid-cols-1 md:grid-cols-2 gap-y-5 gap-x-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                    <input type="text" value={editForm.first_name || ''} onChange={e => setEditForm({...editForm, first_name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                    <input type="text" value={editForm.last_name || ''} onChange={e => setEditForm({...editForm, last_name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Badge Number</label>
                    <input type="text" value={editForm.badge_number || ''} onChange={e => setEditForm({...editForm, badge_number: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Rank / Title</label>
                    <input type="text" value={editForm.rank || ''} onChange={e => setEditForm({...editForm, rank: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Division</label>
                    <input type="text" value={editForm.division || ''} onChange={e => setEditForm({...editForm, division: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                    <input type="text" value={editForm.phone_number || ''} onChange={e => setEditForm({...editForm, phone_number: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department Name</label>
                    <input type="text" value={editForm.department_name || ''} onChange={e => setEditForm({...editForm, department_name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department Address</label>
                    <textarea value={editForm.department_address || ''} onChange={e => setEditForm({...editForm, department_address: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" rows={2} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department State</label>
                    <input type="text" value={editForm.department_state || ''} onChange={e => setEditForm({...editForm, department_state: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ORI Number</label>
                    <input type="text" value={editForm.ori || ''} onChange={e => setEditForm({...editForm, ori: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div className="md:col-span-2 pt-4 flex justify-end gap-3 border-t border-gray-100">
                    <button type="submit" disabled={savingProfile} className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-70">
                      {savingProfile ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>

          {/* Security & Password */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg text-gray-700">
                  <Key size={20} />
                </div>
                <h2 className="text-xl font-bold text-gray-900 font-serif">Security Settings</h2>
              </div>
              <button 
                onClick={() => { setIsChangingPass(!isChangingPass); setPassError(''); setPassSuccess(''); }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {isChangingPass ? 'Cancel' : 'Change Password'}
              </button>
            </div>
            
            <div className="p-6">
              {passSuccess && <div className="mb-4 p-3 bg-green-50 text-green-700 border border-green-200 rounded-lg text-sm">{passSuccess}</div>}
              {passError && <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm">{passError}</div>}
              
              {!isChangingPass ? (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-900 font-medium">Account Password</p>
                    <p className="text-gray-500 text-sm mt-1">Last changed: Unknown</p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handlePasswordSave} className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                    <input type="password" value={passForm.old_password} onChange={e => setPassForm({...passForm, old_password: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                    <input type="password" value={passForm.new_password} onChange={e => setPassForm({...passForm, new_password: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                  </div>
                  <button type="submit" disabled={savingPass} className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-70">
                    {savingPass ? 'Updating...' : 'Update Password'}
                  </button>
                </form>
              )}
            </div>
          </div>

        </div>

        {/* Right Col: Subscription Status */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden h-fit">
          <div className="p-6 border-b border-gray-100 bg-gray-50/50">
            <h2 className="text-xl font-bold text-gray-900 font-serif flex items-center gap-2">
              <Briefcase size={20} className="text-blue-600" /> Subscription Plan
            </h2>
          </div>
          
          <div className="p-6">
            <div className="mb-6">
              <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-1">Current Tier</p>
              <h3 className="text-2xl font-bold text-gray-900">{plan.display_name || plan.plan_display || 'Free Tier'}</h3>
              <p className="text-sm text-gray-500 mt-1">Billed {subscription?.billing_cycle || 'monthly'}</p>
            </div>

            <div className="space-y-4 mb-8">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100 pb-2">Module Access</p>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div> Incident Reports
                  </span>
                  <span className="font-semibold text-gray-900">Included</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${plan.can_search_warrant ? 'bg-blue-500' : 'bg-gray-300'}`}></div> Search Warrants
                  </span>
                  {plan.can_search_warrant ? <span className="font-semibold text-gray-900">Included</span> : <span className="text-gray-400">Locked</span>}
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${plan.can_arrest_warrant ? 'bg-blue-500' : 'bg-gray-300'}`}></div> Arrest Warrants
                  </span>
                  {plan.can_arrest_warrant ? <span className="font-semibold text-gray-900">Included</span> : <span className="text-gray-400">Locked</span>}
                </div>
              </div>
            </div>

            <div className="space-y-4 mb-6">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 font-medium">Incident Reports</span>
                  <span className="text-gray-900 font-bold">
                    {subscription?.documents_generated_this_month || 0} / {formatLimit(plan.document_limit)}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: plan.document_limit == null ? '0%' : `${Math.min((subscription?.documents_generated_this_month || 0) / plan.document_limit * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
              {(plan.can_search_warrant || plan.can_arrest_warrant) && (
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 font-medium">Warrants</span>
                    <span className="text-gray-900 font-bold">
                      {subscription?.warrants_generated_this_month || 0} / {formatLimit(plan.warrant_document_limit)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: plan.warrant_document_limit == null ? '0%' : `${Math.min((subscription?.warrants_generated_this_month || 0) / plan.warrant_document_limit * 100, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
              <p className="text-xs text-gray-500 text-center mt-2">Resets next billing cycle</p>
            </div>

            <button onClick={() => navigate('/pricing')} className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-sm font-semibold hover:bg-gray-800 transition-colors">
              Manage Billing
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
