import { useEffect, useState, useRef, useCallback } from 'react';
import { Search, Mail, Building, Loader2, Gavel } from 'lucide-react';
import { listAdminUsers, updateAdminUser, listAdminPlans } from '../../api/adminPanel';
import { listAgencies } from '../../api/agency';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const [plans, setPlans] = useState([]);
  const [agencies, setAgencies] = useState([]);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const searchTimeout = useRef(null);

  // Officers only — admin accounts are managed on their own separate page
  // (/admin/admins) since they don't carry agency/plan/supervisor concepts.
  const fetchUsers = useCallback(async (p, q) => {
    setLoading(true);
    try {
      const params = { page: p, exclude_role: 'admin' };
      if (q) params.q = q;

      const { data } = await listAdminUsers(params);
      const results = data.results || data;
      setUsers(results);
      setHasMore(!!data.next);
    } catch (err) {
      console.error('Failed to fetch users', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers(page, query);
  }, [fetchUsers, page]);

  useEffect(() => {
    listAdminPlans()
      .then(({ data }) => setPlans(data))
      .catch((err) => console.error('Failed to fetch plans', err));
  }, []);

  useEffect(() => {
    listAgencies({ page_size: 100 })
      .then(({ data }) => setAgencies(data.results || data))
      .catch((err) => console.error('Failed to fetch agencies', err));
  }, []);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchUsers(1, val);
    }, 500);
  };

  const handleToggleStatus = async (user) => {
    setActionLoadingId(user.id);
    try {
      const { data } = await updateAdminUser(user.id, { is_active: !user.is_active });
      setUsers(users.map(u => u.id === user.id ? data : u));
    } catch (err) {
      alert('Failed to update user status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleToggleSupervisor = async (user) => {
    setActionLoadingId(user.id);
    try {
      const { data } = await updateAdminUser(user.id, { is_supervisor: !user.is_supervisor });
      setUsers(users.map(u => u.id === user.id ? data : u));
    } catch (err) {
      alert('Failed to update supervisor status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleChangeAgency = async (userId, agencyId) => {
    setActionLoadingId(userId);
    try {
      const { data } = await updateAdminUser(userId, { agency: agencyId === '' ? null : Number(agencyId) });
      setUsers(users.map(u => u.id === userId ? data : u));
    } catch (err) {
      alert('Failed to update agency assignment.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleChangePlan = async (userId, planName) => {
    setActionLoadingId(userId);
    try {
      const { data } = await updateAdminUser(userId, { plan: planName });
      setUsers(users.map(u => u.id === userId ? data : u));
    } catch (err) {
      alert('Failed to update user subscription plan.');
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Officer Management</h1>
          <p className="text-gray-500 mt-1">Manage platform access and roles.</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        {/* Filters */}
        <div className="p-5 border-b border-gray-100 flex flex-col sm:flex-row items-center gap-4 bg-gray-50/50">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input 
              type="text" 
              placeholder="Search by name, email or badge..." 
              value={query}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                <th className="px-6 py-4">Officer Details</th>
                <th className="px-6 py-4">Department & Role</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Plan / Usage</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading && users.length === 0 ? (
                <tr><td colSpan="5" className="py-10 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" size={24} /></td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan="5" className="py-10 text-center text-gray-500">No users found.</td></tr>
              ) : (
                users.map(user => (
                  <tr key={user.id} className="hover:bg-gray-50/50 transition-colors">
                    {/* User Details */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                          {user.first_name?.[0]}{user.last_name?.[0]}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 flex items-center gap-1.5">
                            {user.first_name} {user.last_name}
                          </div>
                          <div className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                            <Mail size={12} /> {user.email}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Department / Agency */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <Building size={14} className="text-gray-400 shrink-0" />
                        <select
                          value={user.agency ?? ''}
                          onChange={(e) => handleChangeAgency(user.id, e.target.value)}
                          disabled={actionLoadingId === user.id}
                          title="Assign to an agency — drives court captions, review workflow, and legal templates on generated warrants"
                          className="bg-white border border-gray-200 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-sans"
                        >
                          <option value="">No Agency</option>
                          {agencies.map(a => (
                            <option key={a.id} value={a.id}>{a.name}</option>
                          ))}
                        </select>
                      </div>
                      {!user.agency && (
                        <div className="text-xs text-gray-400 pl-[20px]">{user.department_name || 'No department on file'}</div>
                      )}
                      <div className="text-xs text-gray-500 mt-1 pl-[20px]">Badge: {user.badge_number || 'N/A'}</div>
                    </td>

                    {/* Status */}
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1.5 items-start">
                        {user.is_active ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700">
                            <div className="w-1.5 h-1.5 rounded-full bg-red-500"></div> Suspended
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Usage */}
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-medium">
                        <select
                          value={user.subscription?.plan || user.plan || 'free'}
                          onChange={(e) => handleChangePlan(user.id, e.target.value)}
                          disabled={actionLoadingId === user.id}
                          className="bg-white border border-gray-200 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 font-sans"
                        >
                          {plans.map(p => (
                            <option key={p.id} value={p.name}>{p.display_name}</option>
                          ))}
                          {plans.length === 0 && (
                            <option value="free">Free</option>
                          )}
                        </select>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 text-right">
                      {actionLoadingId === user.id ? (
                        <Loader2 className="animate-spin text-gray-400 inline-block" size={18} />
                      ) : (
                        <div className="flex items-center justify-end gap-3">
                          <button
                            onClick={() => handleToggleSupervisor(user)}
                            className={`text-sm font-medium flex items-center gap-1 ${user.is_supervisor ? 'text-purple-600 hover:text-purple-800' : 'text-gray-500 hover:text-gray-700'}`}
                            title={user.is_supervisor ? 'Revoke supervisor review privileges' : 'Grant supervisor review privileges'}
                          >
                            <Gavel size={14} /> {user.is_supervisor ? 'Supervisor' : 'Make Supervisor'}
                          </button>
                          <button
                            onClick={() => handleToggleStatus(user)}
                            className={`text-sm font-medium ${user.is_active ? 'text-red-600 hover:text-red-800' : 'text-emerald-600 hover:text-emerald-800'}`}
                          >
                            {user.is_active ? 'Suspend' : 'Activate'}
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        {!loading && (page > 1 || hasMore) && (
          <div className="p-4 border-t border-gray-100 flex justify-between items-center bg-gray-50/30">
            <button 
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 font-medium">Page {page}</span>
            <button 
              disabled={!hasMore}
              onClick={() => setPage(p => p + 1)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
