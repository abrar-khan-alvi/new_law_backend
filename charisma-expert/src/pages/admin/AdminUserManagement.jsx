import { useEffect, useState, useRef, useCallback } from 'react';
import { Search, Mail, Loader2, ShieldCheck, Plus, X } from 'lucide-react';
import { listAdminUsers, updateAdminUser, createAdminUser } from '../../api/adminPanel';

const parseFieldErrors = (err) => {
  const data = err?.response?.data;
  const errorDetail = data?.error?.detail || data?.error || data;
  if (typeof errorDetail === 'string') return { _global: errorDetail };
  if (errorDetail && typeof errorDetail === 'object') {
    const fieldErrors = {};
    Object.entries(errorDetail).forEach(([k, v]) => {
      let msg = Array.isArray(v) ? v[0] : v;
      if (typeof msg === 'object' && msg !== null) {
        msg = Array.isArray(Object.values(msg)[0]) ? Object.values(msg)[0][0] : Object.values(msg)[0];
      }
      fieldErrors[k] = String(msg);
    });
    return fieldErrors;
  }
  return { _global: 'Failed to create administrator.' };
};

function CreateAdminModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '' });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
    if (errors[name]) setErrors({ ...errors, [name]: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});
    try {
      const { data } = await createAdminUser(form);
      onCreated(data);
    } catch (err) {
      setErrors(parseFieldErrors(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-700" aria-label="Close">
          <X size={20} />
        </button>
        <h2 className="text-xl font-bold text-gray-900 mb-1">Create Administrator</h2>
        <p className="text-gray-500 text-sm mb-6">Grants full platform admin access immediately — no email verification step.</p>

        {errors._global && (
          <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{errors._global}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">First Name</label>
              <input
                type="text"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {errors.first_name && <p className="text-xs text-red-600 mt-1">{errors.first_name}</p>}
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Last Name</label>
              <input
                type="text"
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {errors.last_name && <p className="text-xs text-red-600 mt-1">{errors.last_name}</p>}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password}</p>}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {submitting && <Loader2 size={16} className="animate-spin" />}
            {submitting ? 'Creating...' : 'Create Administrator'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AdminUserManagement() {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const searchTimeout = useRef(null);

  const fetchAdmins = useCallback(async (p, q) => {
    setLoading(true);
    try {
      const params = { page: p, role: 'admin' };
      if (q) params.q = q;

      const { data } = await listAdminUsers(params);
      const results = data.results || data;
      setAdmins(results);
      setHasMore(!!data.next);
    } catch (err) {
      console.error('Failed to fetch admins', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAdmins(page, query);
  }, [fetchAdmins, page]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchAdmins(1, val);
    }, 500);
  };

  const handleToggleStatus = async (admin) => {
    setActionLoadingId(admin.id);
    try {
      const { data } = await updateAdminUser(admin.id, { is_active: !admin.is_active });
      setAdmins(admins.map((a) => (a.id === admin.id ? data : a)));
    } catch (err) {
      alert('Failed to update administrator status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Administrators</h1>
          <p className="text-gray-500 mt-1">Platform admin accounts, kept separate from officer users.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm"
        >
          <Plus size={18} /> Create Administrator
        </button>
      </div>

      {showCreateModal && (
        <CreateAdminModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            setPage(1);
            fetchAdmins(1, query);
          }}
        />
      )}

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        {/* Filters */}
        <div className="p-5 border-b border-gray-100 flex items-center gap-4 bg-gray-50/50">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search by email..."
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
                <th className="px-6 py-4">Administrator</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Joined</th>
                <th className="px-6 py-4">Last Active</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading && admins.length === 0 ? (
                <tr><td colSpan="5" className="py-10 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" size={24} /></td></tr>
              ) : admins.length === 0 ? (
                <tr><td colSpan="5" className="py-10 text-center text-gray-500">No administrators found.</td></tr>
              ) : (
                admins.map((admin) => (
                  <tr key={admin.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-sm">
                          <ShieldCheck size={18} />
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">{admin.full_name || admin.email}</div>
                          <div className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                            <Mail size={12} /> {admin.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {admin.is_active ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700">
                          <div className="w-1.5 h-1.5 rounded-full bg-red-500"></div> Suspended
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {admin.created_at ? new Date(admin.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {admin.last_active ? new Date(admin.last_active).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {actionLoadingId === admin.id ? (
                        <Loader2 className="animate-spin text-gray-400 inline-block" size={18} />
                      ) : (
                        <button
                          onClick={() => handleToggleStatus(admin)}
                          className={`text-sm font-medium ${admin.is_active ? 'text-red-600 hover:text-red-800' : 'text-emerald-600 hover:text-emerald-800'}`}
                        >
                          {admin.is_active ? 'Suspend' : 'Activate'}
                        </button>
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
              onClick={() => setPage((p) => p - 1)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 font-medium">Page {page}</span>
            <button
              disabled={!hasMore}
              onClick={() => setPage((p) => p + 1)}
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
