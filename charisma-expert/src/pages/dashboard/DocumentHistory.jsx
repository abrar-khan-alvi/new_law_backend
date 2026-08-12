import { useEffect, useState, useCallback, useRef } from 'react';
import { FileText, ChevronRight, Loader2, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { listDocuments } from '../../api/documents';

const DOC_TYPE_LABELS = {
  incident_report: 'Incident Report',
  search_warrant: 'Search Warrant',
  arrest_warrant: 'Arrest Warrant',
};

export default function DocumentHistory() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [docType, setDocType] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  // Debounce search query
  const searchTimeout = useRef(null);

  const fetchDocs = useCallback(async (p, q, type) => {
    setLoading(true);
    try {
      const params = { page: p };
      if (q) params.q = q;
      if (type) params.doc_type = type;

      const { data } = await listDocuments(params);
      
      const results = data.results || data;
      setDocuments(results);
      setHasMore(!!data.next);
    } catch (err) {
      console.error('Error fetching documents', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs(page, query, docType);
  }, [fetchDocs, page, docType]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchDocs(1, val, docType);
    }, 500);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded-full">Saved</span>;
      case 'failed':
        return <span className="px-3 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-full">Failed</span>;
      default:
        return <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-bold rounded-full">{status}</span>;
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 font-serif">Document History</h1>
        <p className="text-gray-500 mt-1 text-lg">View, search, and manage your previously generated documentation.</p>
      </div>

      {/* Main Card */}
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        {/* Toolbar */}
        <div className="p-6 border-b border-gray-100 flex flex-col md:flex-row gap-4 items-center justify-between bg-gray-50/30">
          <div className="relative w-full md:max-w-md">
             <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
             </div>
             <input 
               type="text" 
               placeholder="Search by case number or title..." 
               value={query}
               onChange={handleSearchChange}
               className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
             />
          </div>
          <div className="relative w-full md:w-auto">
            <select 
              value={docType}
              onChange={(e) => { setDocType(e.target.value); setPage(1); }}
              className="w-full md:w-48 px-4 py-2.5 bg-gray-100 border border-transparent rounded-lg text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-gray-200 font-medium cursor-pointer"
            >
              <option value="">All Types</option>
              <option value="incident_report">Incident Report</option>
              <option value="search_warrant">Search Warrant</option>
              <option value="arrest_warrant">Arrest Warrant</option>
            </select>
            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
              <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[800px]">
            {/* Table Head */}
            <div className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-gray-100 text-sm font-semibold text-gray-500 bg-gray-50/50">
              <div className="col-span-4">Document</div>
              <div className="col-span-3">Case Identifier</div>
              <div className="col-span-2">Generation Date</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-1 flex justify-end text-gray-900 font-bold">Open</div>
            </div>

            {/* Table Body */}
            {loading && documents.length === 0 ? (
              <div className="py-12 flex justify-center">
                 <Loader2 className="animate-spin text-gray-400" size={32} />
              </div>
            ) : documents.length === 0 ? (
              <div className="py-12 text-center text-gray-500">
                No documents found.
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {documents.map((doc) => {
                  const d = new Date(doc.created_at);
                  return (
                    <Link key={doc.id} to={`/dashboard/document/${doc.id}`} className="grid grid-cols-12 gap-4 px-6 py-5 items-center hover:bg-gray-50 transition-colors group cursor-pointer">
                      <div className="col-span-4 flex items-start gap-4">
                        <div className="mt-1 text-gray-400 shrink-0">
                          <FileText size={22} strokeWidth={1.5} />
                        </div>
                        <div>
                          <h4 className="text-[15px] font-semibold text-gray-900 mb-0.5 group-hover:text-blue-600 transition-colors truncate pr-4">
                            {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type}
                          </h4>
                          <div className="text-[13px] text-gray-500">{doc.model_used || 'AI Generated'}</div>
                        </div>
                      </div>
                      <div className="col-span-3 text-[14px] text-gray-700 font-medium truncate">
                        {doc.case_number || 'N/A'}
                      </div>
                      <div className="col-span-2">
                        <div className="text-[14px] text-gray-900">{d.toLocaleDateString()}</div>
                        <div className="text-[13px] text-gray-500">{d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                      </div>
                      <div className="col-span-2">
                        {getStatusBadge(doc.status)}
                      </div>
                      <div className="col-span-1 flex justify-end text-gray-400 group-hover:text-blue-600 transition-colors">
                        <ChevronRight size={20} />
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
            
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
      </div>
    </div>
  );
}
