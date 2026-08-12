import { useState, useEffect } from 'react';
import { Download, DollarSign, Users, ChevronDown, Plus, Pencil, Trash2, Loader2, X, Check } from 'lucide-react';
import { listAdminPlans, createPlan, updatePlan, deletePlan, getStats, listAdminUsers, updateAdminUser } from '../../api/adminPanel';
import { formatLimit } from '../../utils/format';

const Billing = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [userPage, setUserPage] = useState(1);
  const [hasMoreUsers, setHasMoreUsers] = useState(false);
  const [updatingUserId, setUpdatingUserId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);

  const initialFormState = {
    name: '',
    display_name: '',
    description: '',
    price_monthly: '0.00',
    price_yearly: '0.00',
    document_limit: 5,
    warrant_document_limit: '',
    can_incident_report: true,
    can_search_warrant: false,
    can_arrest_warrant: false,
    can_save_history: true,
    is_active: true,
    sort_order: 0
  };

  const [formData, setFormData] = useState(initialFormState);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchPlans = () => {
    setLoading(true);
    listAdminPlans()
      .then(({ data }) => setPlans(data))
      .catch((err) => console.error("Failed to fetch plans", err))
      .finally(() => setLoading(false));
  };

  const fetchStats = () => {
    setStatsLoading(true);
    getStats()
      .then(({ data }) => setStats(data))
      .catch((err) => console.error("Failed to fetch stats", err))
      .finally(() => setStatsLoading(false));
  };

  const fetchUsers = (page) => {
    setUsersLoading(true);
    listAdminUsers({ page })
      .then(({ data }) => {
        setUsers(data.results || data);
        setHasMoreUsers(!!data.next);
      })
      .catch((err) => console.error("Failed to fetch users", err))
      .finally(() => setUsersLoading(false));
  };

  const calculateMRR = () => {
    if (!stats?.subscriptions?.by_plan || plans.length === 0) return 0;
    let total = 0;
    stats.subscriptions.by_plan.forEach(item => {
      const planName = item.plan__name;
      const count = item.count || 0;
      const matchedPlan = plans.find(p => p.name === planName);
      if (matchedPlan) {
        const price = parseFloat(matchedPlan.price_monthly) || 0;
        total += price * count;
      }
    });
    return total;
  };

  const getPlanPrice = (planName) => {
    const matchedPlan = plans.find(p => p.name === planName);
    return matchedPlan ? `$ ${parseFloat(matchedPlan.price_monthly).toFixed(2)}` : '$ 0.00';
  };

  const handleChangeUserPlan = async (userId, planName) => {
    setUpdatingUserId(userId);
    try {
      await updateAdminUser(userId, { plan: planName });
      fetchUsers(userPage);
      fetchStats();
    } catch (err) {
      alert('Failed to update user subscription plan.');
    } finally {
      setUpdatingUserId(null);
    }
  };

  useEffect(() => {
    fetchPlans();
    fetchStats();
  }, []);

  useEffect(() => {
    fetchUsers(userPage);
  }, [userPage]);

  const openCreateModal = () => {
    setEditingPlan(null);
    setFormData(initialFormState);
    setError('');
    setIsModalOpen(true);
  };

  const openEditModal = (plan) => {
    setEditingPlan(plan);
    setFormData({
      name: plan.name || '',
      display_name: plan.display_name || '',
      description: plan.description || '',
      price_monthly: plan.price_monthly || '0.00',
      price_yearly: plan.price_yearly || '0.00',
      // null/undefined means "unlimited" on the backend — represent that as a
      // blank input rather than a magic number.
      document_limit: plan.document_limit ?? '',
      warrant_document_limit: plan.warrant_document_limit ?? '',
      can_incident_report: plan.can_incident_report ?? true,
      can_search_warrant: plan.can_search_warrant ?? false,
      can_arrest_warrant: plan.can_arrest_warrant ?? false,
      can_save_history: plan.can_save_history ?? true,
      is_active: plan.is_active ?? true,
      sort_order: plan.sort_order ?? 0
    });
    setError('');
    setIsModalOpen(true);
  };

  const handleDelete = async (pk) => {
    if (!window.confirm("Are you sure you want to delete this plan?")) return;
    try {
      await deletePlan(pk);
      fetchPlans();
    } catch (err) {
      alert("Failed to delete plan. It might have active subscriptions.");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      // Blank means unlimited (null on the backend) — never send an empty
      // string, and never let a stray "-1" or similar sneak through.
      const payload = {
        ...formData,
        document_limit: formData.document_limit === '' ? null : Number(formData.document_limit),
        warrant_document_limit: formData.warrant_document_limit === '' ? null : Number(formData.warrant_document_limit),
      };
      if (editingPlan) {
        await updatePlan(editingPlan.id, payload);
      } else {
        await createPlan(payload);
      }
      setIsModalOpen(false);
      fetchPlans();
    } catch (err) {
      // Validation errors might be an object mapping fields to array of messages
      if (err?.response?.data && typeof err.response.data === 'object' && !err.response.data.error) {
         const msgs = Object.entries(err.response.data).map(([k, v]) => `${k}: ${v}`).join(', ');
         setError(msgs || "Failed to save plan");
      } else {
         setError(err?.response?.data?.error?.detail || err?.response?.data?.detail || "Failed to save plan");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Subscriptions & Billing</h1>
        <button className="flex items-center px-4 py-2.5 bg-white border border-gray-300 rounded-md font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors">
          <Download className="w-5 h-5 mr-2" />
          Export Report
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex items-center gap-6">
          <div className="w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0">
            <DollarSign className="w-7 h-7 text-emerald-500" />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500 mb-1">Monthly Recurring Revenue</div>
            <div className="text-3xl font-bold text-gray-900">
              {statsLoading || loading ? (
                <Loader2 className="animate-spin text-gray-400 h-6 w-6" />
              ) : (
                `$${calculateMRR().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex items-center gap-6">
          <div className="w-14 h-14 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
            <Users className="w-7 h-7 text-blue-500" />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500 mb-1">Active Subscriptions</div>
            <div className="text-3xl font-bold text-gray-900">
              {statsLoading ? (
                <Loader2 className="animate-spin text-gray-400 h-6 w-6" />
              ) : (
                stats?.subscriptions?.active ?? 0
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex items-center gap-6">
          <div className="w-14 h-14 rounded-full bg-purple-50 flex items-center justify-center flex-shrink-0">
            <Users className="w-7 h-7 text-purple-500" />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500 mb-1">Total Platform Users</div>
            <div className="text-3xl font-bold text-gray-900">
              {statsLoading ? (
                <Loader2 className="animate-spin text-gray-400 h-6 w-6" />
              ) : (
                stats?.users?.total ?? 0
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* Subscription Plans Management */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full xl:col-span-1">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-1">Subscription Plans</h2>
              <p className="text-sm text-gray-500">Manage pricing & access rules globally.</p>
            </div>
            <button onClick={openCreateModal} className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors">
              <Plus size={20} />
            </button>
          </div>

          <div className="space-y-4 flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex justify-center py-10"><Loader2 className="animate-spin text-gray-400" size={24} /></div>
            ) : plans.length === 0 ? (
              <div className="text-center py-10 text-gray-400 text-sm">No plans found. Create one.</div>
            ) : (
              plans.map(plan => (
                <div key={plan.id} className="border border-gray-200 rounded-lg p-5 hover:border-gray-300 transition-colors">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-md font-bold text-gray-900">{plan.display_name}</h3>
                      <p className="text-xs text-gray-500 font-mono mt-0.5">{plan.name}</p>
                    </div>
                    <div className="flex gap-1">
                      <button onClick={() => openEditModal(plan)} className="p-1.5 text-gray-400 hover:text-blue-600 rounded"><Pencil size={16} /></button>
                      <button onClick={() => handleDelete(plan.id)} className="p-1.5 text-gray-400 hover:text-red-600 rounded"><Trash2 size={16} /></button>
                    </div>
                  </div>
                  
                  <div className="mb-3 text-lg font-extrabold text-gray-900">
                    ${plan.price_monthly} <span className="text-xs font-normal text-gray-500">/mo</span>
                  </div>

                  <div className="space-y-2 mt-4">
                    <div className="flex items-center space-x-2">
                      {plan.can_incident_report ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-gray-300" />}
                      <span className={`text-xs ${plan.can_incident_report ? 'text-gray-700 font-medium' : 'text-gray-400'}`}>Incident Reports</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      {plan.can_search_warrant ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-gray-300" />}
                      <span className={`text-xs ${plan.can_search_warrant ? 'text-gray-700 font-medium' : 'text-gray-400'}`}>Search Warrants</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      {plan.can_arrest_warrant ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-gray-300" />}
                      <span className={`text-xs ${plan.can_arrest_warrant ? 'text-gray-700 font-medium' : 'text-gray-400'}`}>Arrest Warrants</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Check size={14} className="text-emerald-500" />
                      <span className="text-xs text-gray-700 font-medium">{formatLimit(plan.document_limit)} Incident Reports/mo</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Check size={14} className="text-emerald-500" />
                      <span className="text-xs text-gray-700 font-medium">{formatLimit(plan.warrant_document_limit)} Warrants/mo</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Subscription Accounts Log */}
        <div className="xl:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-white">
            <h2 className="text-lg font-bold text-gray-900">Subscription Accounts</h2>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-white">
                <tr>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Account</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Plan</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {usersLoading && users.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-10 text-center">
                      <Loader2 className="animate-spin text-gray-400 mx-auto" size={24} />
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-10 text-center text-gray-500">
                      No subscription accounts found.
                    </td>
                  </tr>
                ) : (
                  users.map((user) => {
                    const planName = user.subscription?.plan || user.plan || 'free';
                    const planDisplay = user.subscription?.plan_display || (plans.find(p => p.name === planName)?.display_name) || planName;
                    const amount = getPlanPrice(planName);
                    
                    return (
                      <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-semibold text-gray-900">{user.full_name || `${user.first_name} ${user.last_name}`}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <select
                            value={planName}
                            onChange={(e) => handleChangeUserPlan(user.id, e.target.value)}
                            disabled={updatingUserId === user.id}
                            className="bg-white border border-gray-200 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-sans"
                          >
                            {plans.map(p => (
                              <option key={p.id} value={p.name}>{p.display_name}</option>
                            ))}
                            {plans.length === 0 && (
                              <option value="free">Free</option>
                            )}
                          </select>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{amount}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-md ${
                            user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {user.is_active ? 'Active' : 'Suspended'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {!usersLoading && (userPage > 1 || hasMoreUsers) && (
            <div className="p-4 border-t border-gray-200 flex justify-between items-center bg-gray-50/30">
              <button 
                disabled={userPage === 1}
                onClick={() => setUserPage(p => p - 1)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600 font-medium">Page {userPage}</span>
              <button 
                disabled={!hasMoreUsers}
                onClick={() => setUserPage(p => p + 1)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Plan Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-6 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900">{editingPlan ? 'Edit Plan' : 'Create New Plan'}</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                <X size={24} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}
              
              <form id="plan-form" onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Internal Name *</label>
                    <input type="text" name="name" value={formData.name} onChange={handleInputChange} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. free, pro_monthly" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Display Name *</label>
                    <input type="text" name="display_name" value={formData.display_name} onChange={handleInputChange} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. Detective Plan" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                    <input type="text" name="description" value={formData.description} onChange={handleInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Short description for the pricing page" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Monthly Price ($) *</label>
                    <input type="number" step="0.01" name="price_monthly" value={formData.price_monthly} onChange={handleInputChange} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Incident Report Limit / Month</label>
                    <input type="number" name="document_limit" value={formData.document_limit} onChange={handleInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Leave blank for unlimited" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Warrant Limit / Month</label>
                    <input type="number" name="warrant_document_limit" value={formData.warrant_document_limit} onChange={handleInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Leave blank for unlimited" />
                  </div>
                </div>

                <div className="pt-6 border-t border-gray-100">
                  <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Module Access Rules</h3>
                  <div className="space-y-3">
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" name="can_incident_report" checked={formData.can_incident_report} onChange={handleInputChange} className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                      <span className="text-gray-700 font-medium">Incident Reports</span>
                    </label>
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" name="can_search_warrant" checked={formData.can_search_warrant} onChange={handleInputChange} className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                      <span className="text-gray-700 font-medium">Search Warrants</span>
                    </label>
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" name="can_arrest_warrant" checked={formData.can_arrest_warrant} onChange={handleInputChange} className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                      <span className="text-gray-700 font-medium">Arrest Warrants</span>
                    </label>
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" name="can_save_history" checked={formData.can_save_history} onChange={handleInputChange} className="form-checkbox h-5 w-5 text-purple-600 rounded border-gray-300 focus:ring-purple-500" />
                      <span className="text-gray-700 font-medium">Save Document History</span>
                    </label>
                  </div>
                </div>
                
                <div className="pt-6 border-t border-gray-100">
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input type="checkbox" name="is_active" checked={formData.is_active} onChange={handleInputChange} className="form-checkbox h-5 w-5 text-emerald-500 rounded border-gray-300 focus:ring-emerald-500" />
                    <span className="text-gray-900 font-bold">Plan is Active (Visible to public)</span>
                  </label>
                </div>
              </form>
            </div>
            
            <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
              <button type="button" onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button type="submit" form="plan-form" disabled={saving} className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center disabled:opacity-70 disabled:cursor-not-allowed">
                {saving && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
                {editingPlan ? 'Save Changes' : 'Create Plan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Billing;
