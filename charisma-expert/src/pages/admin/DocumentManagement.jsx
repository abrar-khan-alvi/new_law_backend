import { useEffect, useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search, Mail, Building, Loader2, AlertTriangle, Eye } from 'lucide-react';
import { listAdminDocuments } from '../../api/adminPanel';

const STATUS_STYLES = {
  pending: 'bg-slate-100 text-slate-600',
  generating: 'bg-amber-100 text-amber-700',
  completed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
};

const REVIEW_STATUS_LABELS = {
  pending_supervisor: 'Pending Supervisor',
  pending_prosecutor: 'Pending Prosecutor',
  approved: 'Approved',
  rejected: 'Rejected',
  not_required: 'No Review Required',
};

export default function DocumentManagement() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('');
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const searchTimeout = useRef(null);

  const fetchDocuments = useCallback(async (p, q, docType, status, reviewStatus, flagged) => {
    setLoading(true);
    try {
      const params = { page: p };
      if (q) params.q = q;
      if (docType) params.doc_type = docType;
      if (status) params.status = status;
      if (reviewStatus) params.review_status = reviewStatus;
      if (flagged) params.flagged = true;

      const { data } = await listAdminDocuments(params);
      const results = data.results || data;
      setDocuments(results);
      setHasMore(!!data.next);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments(page, query, docTypeFilter, statusFilter, reviewStatusFilter, flaggedOnly);
  }, [fetchDocuments, page, docTypeFilter, statusFilter, reviewStatusFilter, flaggedOnly]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchDocuments(1, val, docTypeFilter, statusFilter, reviewStatusFilter, flaggedOnly);
    }, 500);
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Documents</h1>
          <p className="text-gray-500 mt-1">Preview any officer's generated documents.</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        {/* Filters */}
        <div className="p-5 border-b border-gray-100 flex flex-col sm:flex-row items-center gap-4 bg-gray-50/50">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search by officer email..."
              value={query}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <select
            value={docTypeFilter}
            onChange={(e) => { setDocTypeFilter(e.target.value); setPage(1); }}
            className="w-full sm:w-48 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Document Types</option>
            <option value="incident_report">Incident Report</option>
            <option value="search_warrant">Search Warrant</option>
            <option value="arrest_warrant">Arrest Warrant</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="w-full sm:w-44 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="generating">Generating</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <select
            value={reviewStatusFilter}
            onChange={(e) => { setReviewStatusFilter(e.target.value); setPage(1); }}
            className="w-full sm:w-48 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Reviews</option>
            {Object.entries(REVIEW_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm text-gray-600 font-medium whitespace-nowrap">
            <input
              type="checkbox"
              checked={flaggedOnly}
              onChange={(e) => { setFlaggedOnly(e.target.checked); setPage(1); }}
              className="w-4 h-4 rounded accent-blue-600"
            />
            Flagged only
          </label>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                <th className="px-6 py-4">Officer</th>
                <th className="px-6 py-4">Document</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Review</th>
                <th className="px-6 py-4">Flags</th>
                <th className="px-6 py-4">Created</th>
                <th className="px-6 py-4 text-right">Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading && documents.length === 0 ? (
                <tr><td colSpan="7" className="py-10 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" size={24} /></td></tr>
              ) : documents.length === 0 ? (
                <tr><td colSpan="7" className="py-10 text-center text-gray-500">No documents found.</td></tr>
              ) : (
                documents.map((doc) => {
                  const flagCount = (doc.leak_flag_count || 0) + (doc.quality_flag_count || 0);
                  return (
                    <tr key={doc.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 font-medium flex items-center gap-1.5">
                          <Mail size={12} className="text-gray-400" /> {doc.user_email}
                        </div>
                        {doc.agency_name && (
                          <div className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                            <Building size={12} className="text-gray-400" /> {doc.agency_name}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 font-medium capitalize">{doc.doc_type.replace(/_/g, ' ')}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{doc.case_number || 'No case #'}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${STATUS_STYLES[doc.status] || 'bg-gray-100 text-gray-600'}`}>
                          {doc.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {REVIEW_STATUS_LABELS[doc.review_status] || doc.review_status || '—'}
                      </td>
                      <td className="px-6 py-4">
                        {flagCount > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700">
                            <AlertTriangle size={12} /> {flagCount}
                          </span>
                        ) : (
                          <span className="text-gray-300 text-sm">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/admin/documents/${doc.id}`}
                          className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          <Eye size={14} /> Preview
                        </Link>
                      </td>
                    </tr>
                  );
                })
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
