import { useEffect, useState, useCallback } from 'react';
import { Info, AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import { listActivity } from '../../api/adminPanel';

const ACTION_LABELS = {
  'auth.login': 'Logged In',
  'auth.login_failed': 'Failed Login Attempt',
  'auth.logout': 'Logged Out',
  'document.generate': 'Generated Document',
  'document.export': 'Exported Document',
  'document.access': 'Viewed Document',
  'admin.user.update': 'Updated Officer Account',
  'admin.plan.create': 'Created Subscription Plan',
  'admin.plan.update': 'Updated Subscription Plan',
  'admin.plan.delete': 'Deleted Subscription Plan',
  'admin.agency.create': 'Created Agency',
  'admin.agency.update': 'Updated Agency',
  'admin.agency.delete': 'Deleted Agency',
  'admin.agency.seal_upload': 'Uploaded Agency Seal',
  'admin.jurisdiction_profile.create': 'Created Jurisdiction Profile',
  'admin.jurisdiction_profile.update': 'Updated Jurisdiction Profile',
  'admin.jurisdiction_profile.delete': 'Deleted Jurisdiction Profile',
};

const formatAction = (action) => ACTION_LABELS[action] || action;

const formatTimestamp = (iso) =>
  new Date(iso).toLocaleString(undefined, {
    month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  });

const ActivityMonitor = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severity, setSeverity] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState('');

  const fetchActivity = useCallback((p, sev) => {
    setLoading(true);
    setError('');
    const params = { page: p };
    if (sev) params.severity = sev;
    listActivity(params)
      .then(({ data }) => {
        setActivities(data.results || data);
        setHasMore(!!data.next);
      })
      .catch(() => setError('Failed to load activity feed.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchActivity(page, severity);
  }, [fetchActivity, page, severity]);

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-8">Activity Monitor</h1>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-wrap justify-between items-center gap-3">
          <h2 className="text-xl font-bold text-gray-900">Audit Trail</h2>
          <div className="flex items-center gap-3">
            <select
              value={severity}
              onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
              className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Severities</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
            </select>
            <button
              onClick={() => fetchActivity(page, severity)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50/50">
              <tr>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-48">Timestamp</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">Severity</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-48">Actor</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Action / Details</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {loading && activities.length === 0 ? (
                <tr><td colSpan="4" className="py-10 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" size={24} /></td></tr>
              ) : error ? (
                <tr><td colSpan="4" className="py-10 text-center text-red-600">{error}</td></tr>
              ) : activities.length === 0 ? (
                <tr><td colSpan="4" className="py-10 text-center text-gray-500">No activity recorded yet.</td></tr>
              ) : (
                activities.map((activity) => (
                  <tr key={activity.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {formatTimestamp(activity.created_at)}
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap">
                      {activity.severity === 'warning' ? (
                        <div className="flex items-center text-amber-500">
                          <AlertTriangle className="w-4 h-4 mr-1.5" />
                          <span className="text-sm font-medium">Warning</span>
                        </div>
                      ) : (
                        <div className="flex items-center text-blue-600">
                          <Info className="w-4 h-4 mr-1.5" />
                          <span className="text-sm font-medium">Info</span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-sm font-semibold text-gray-900">
                      {activity.actor_label}
                    </td>
                    <td className="px-6 py-5">
                      <div className="text-sm font-semibold text-gray-900 mb-0.5">{formatAction(activity.action)}</div>
                      {activity.detail && <div className="text-sm text-gray-500">{activity.detail}</div>}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

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
};

export default ActivityMonitor;
