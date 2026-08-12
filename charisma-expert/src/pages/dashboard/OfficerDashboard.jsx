import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { listDocuments } from '../../api/documents';
import { getSubscriptionStatus } from '../../api/subscriptions';
import { 
  ShieldAlert, 
  FileSearch, 
  UserPlus, 
  Lock, 
  FileText, 
  ArrowRight,
  User,
  ShieldCheck,
  Clock,
  Loader2
} from 'lucide-react';

const DOC_TYPE_LABELS = {
  incident_report: 'Incident Report',
  search_warrant: 'Search Warrant',
  arrest_warrant: 'Arrest Warrant',
};

export default function OfficerDashboard() {
  const { user } = useAuth();

  const [recentDocs, setRecentDocs] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [docsLoading, setDocsLoading] = useState(true);
  const [subLoading, setSubLoading] = useState(true);

  useEffect(() => {
    // Fetch recent documents (first 3)
    listDocuments({ page: 1 })
      .then(({ data }) => {
        const results = data.results || data;
        setRecentDocs(results.slice(0, 3));
      })
      .catch(() => {})
      .finally(() => setDocsLoading(false));

    // Fetch subscription status
    getSubscriptionStatus()
      .then(({ data }) => setSubscription(data))
      .catch(() => {})
      .finally(() => setSubLoading(false));
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Saved</span>;
      case 'failed':
        return <span className="px-3 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">Failed</span>;
      default:
        return <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">{status}</span>;
    }
  };

  // Subscription info
  const planName = subscription?.plan?.display_name || user?.subscription?.plan_display || 'Free';
  const docsUsed = subscription?.documents_generated_this_month ?? user?.subscription?.documents_generated_this_month ?? 0;
  // document_limit is a nullable field where null means "unlimited" (see
  // subscriptions/models.py) — must not fall through `??` to a default when
  // it's genuinely null, only when there's no plan data at all yet.
  const docsLimit = subscription?.plan
    ? subscription.plan.document_limit
    : (user?.subscription?.document_limit ?? 3);
  const usagePct = docsLimit > 0 ? Math.min((docsUsed / docsLimit) * 100, 100) : 0;

  // Search + arrest warrants draw from ONE combined quota bucket (see
  // Plan.warrant_document_limit / Subscription.warrants_generated_this_month)
  // — search_warrants_generated_this_month / arrest_warrants_generated_this_month
  // are display-only breakdowns of that same combined count, never a separate limit.
  const warrantsLimit = subscription?.plan
    ? subscription.plan.warrant_document_limit
    : (user?.subscription?.warrant_document_limit ?? null);
  const searchWarrantsUsed = subscription?.search_warrants_generated_this_month ?? 0;
  const arrestWarrantsUsed = subscription?.arrest_warrants_generated_this_month ?? 0;
  const warrantsUsed = subscription?.warrants_generated_this_month ?? (searchWarrantsUsed + arrestWarrantsUsed);
  const warrantsUsagePct = warrantsLimit > 0 ? Math.min((warrantsUsed / warrantsLimit) * 100, 100) : 0;

  // Plan capabilities (for module gating)
  const planObj = subscription?.plan || user?.subscription || {};
  const canSearchWarrant = true; // Unconditionally true for testing UI
  const canArrestWarrant = true; // Unconditionally true for testing UI

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome Banner */}
      <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2 font-serif">
            Welcome, {user?.full_name || user?.first_name || 'Officer'}
          </h1>
          <p className="text-gray-500 text-lg">Select a module below to begin drafting secure documentation.</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-100 min-w-[300px]">
          {subLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="animate-spin text-gray-400" size={20} />
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm text-gray-500 font-medium">
                  Current Plan: <span className="text-gray-900 font-bold">{planName}</span>
                </span>
              </div>
              <div className="flex justify-between items-center text-xs text-gray-500 mb-2 font-medium">
                <span>
                  {docsLimit == null ? `${docsUsed} Incident Reports (Unlimited)` : `${docsUsed}/${docsLimit} Incident Reports`}
                  {' · '}
                  {`${searchWarrantsUsed} Search Warrants`}
                  {' · '}
                  {`${arrestWarrantsUsed} Arrest Warrants`}
                  {warrantsLimit == null ? ' (Unlimited combined)' : ` (${warrantsUsed}/${warrantsLimit} combined)`}
                  {' — This Month'}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.max(usagePct, warrantsUsagePct)}%` }}
                ></div>
              </div>
            </>
          )}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6 font-serif">Document Generation Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Module 1 — Incident Reports (always available) */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-200">
              <ShieldAlert className="text-white" size={28} />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3 font-serif">AI Incident Reports</h3>
            <p className="text-gray-500 text-sm mb-8 leading-relaxed">
              Generate comprehensive, structured incident narratives from raw field notes and facts.
            </p>
            <Link to="/dashboard/create/incident-report" className="text-blue-600 font-semibold text-sm flex items-center hover:text-blue-700">
              Launch Module <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>

          {/* Module 2 — Search Warrants */}
          {canSearchWarrant ? (
            <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
              <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-200">
                <FileSearch className="text-white" size={28} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3 font-serif">AI Search Warrants</h3>
              <p className="text-gray-500 text-sm mb-8 leading-relaxed">
                Structure a search warrant application draft for authorized legal and supervisory review.
              </p>
              <Link to="/dashboard/create/search-warrant" className="text-blue-600 font-semibold text-sm flex items-center hover:text-blue-700">
                Launch Module <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm relative opacity-70">
              <div className="absolute top-6 right-6 text-gray-400"><Lock size={20} /></div>
              <div className="w-14 h-14 bg-gray-100 border-2 border-gray-200 rounded-2xl flex items-center justify-center mb-6">
                <FileSearch className="text-gray-400" size={28} />
              </div>
              <h3 className="text-xl font-bold text-gray-400 mb-3 font-serif">AI Search Warrants</h3>
              <p className="text-gray-400 text-sm mb-8 leading-relaxed">
                Structure an arrest warrant application draft for authorized legal and supervisory review.
              </p>
              <Link to="/pricing" className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
                Upgrade to Access
              </Link>
            </div>
          )}

          {/* Module 3 — Arrest Warrants */}
          {canArrestWarrant ? (
            <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
              <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-200">
                <UserPlus className="text-white" size={28} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3 font-serif">AI Arrest Warrants</h3>
              <p className="text-gray-500 text-sm mb-8 leading-relaxed">
                Create detailed arrest warrant applications based on suspect and case entity data.
              </p>
              <Link to="/dashboard/create/arrest-warrant" className="text-blue-600 font-semibold text-sm flex items-center hover:text-blue-700">
                Launch Module <ArrowRight size={16} className="ml-1 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-sm relative opacity-70">
              <div className="absolute top-6 right-6 text-gray-400"><Lock size={20} /></div>
              <div className="w-14 h-14 bg-gray-100 border-2 border-gray-200 rounded-2xl flex items-center justify-center mb-6">
                <UserPlus className="text-gray-400" size={28} />
              </div>
              <h3 className="text-xl font-bold text-gray-400 mb-3 font-serif">AI Arrest Warrants</h3>
              <p className="text-gray-400 text-sm mb-8 leading-relaxed">
                Create detailed arrest warrant applications based on suspect and case entity data.
              </p>
              <Link to="/pricing" className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
                Upgrade to Access
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Documents */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 rounded-lg">
                <Clock className="text-gray-500" size={20} />
              </div>
              <h2 className="text-xl font-bold text-gray-900 font-serif">Recent Documents</h2>
            </div>
            <Link to="/dashboard/history" className="text-sm font-medium text-gray-500 hover:text-gray-900">
              View All
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {docsLoading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="animate-spin text-gray-400" size={24} />
              </div>
            ) : recentDocs.length === 0 ? (
              <div className="text-center py-10 text-gray-400 text-sm">No documents yet. Generate your first one above!</div>
            ) : (
              recentDocs.map((doc) => (
                <Link key={doc.id} to={`/dashboard/document/${doc.id}`} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="mt-1 text-gray-400">
                      <FileText size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-1">
                        {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type} — {doc.case_number}
                      </h4>
                      <div className="text-xs text-gray-500 flex items-center gap-2">
                        <span>{doc.case_number}</span>
                        <span>•</span>
                        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div>{getStatusBadge(doc.status)}</div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Quick Actions</h2>
          </div>
          <div className="p-6 space-y-4">
            <Link to="/dashboard/profile" className="flex items-start gap-4 p-4 border border-gray-100 rounded-xl hover:border-gray-300 transition-colors group">
              <div className="p-3 bg-gray-50 rounded-lg group-hover:bg-white transition-colors">
                <User className="text-gray-600" size={20} />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-1">Update Profile</h4>
                <p className="text-xs text-gray-500">Manage credentials & security</p>
              </div>
            </Link>
            
            <Link to="/pricing" className="flex items-start gap-4 p-4 border border-gray-100 rounded-xl hover:border-gray-300 transition-colors group">
              <div className="p-3 bg-orange-50 rounded-lg group-hover:bg-white transition-colors">
                <ShieldCheck className="text-orange-600" size={20} />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-1">Manage Subscription</h4>
                <p className="text-xs text-gray-500">View billing & upgrade</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
