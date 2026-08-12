import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, FileText, Database, Clock, Loader2, AlertTriangle, Sparkles, Gavel, Mail, Building, ShieldCheck, CheckCircle, Cpu } from 'lucide-react';
import { getAdminDocument } from '../../api/adminPanel';
import { supervisorReview } from '../../api/documents';

const renderFormData = (data, level = 0) => {
  if (data === null || data === undefined || data === '') return <span className="text-slate-400 italic">Not provided</span>;
  if (typeof data !== 'object') return <span className="text-slate-700 font-medium break-words leading-relaxed">{String(data)}</span>;

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-slate-400 italic">Empty list</span>;
    return (
      <div className="flex flex-col gap-3 mt-2">
        {data.map((item, i) => (
          <div key={i} className="bg-slate-50/50 border border-slate-100 rounded-lg p-3">
            {renderFormData(item, level + 1)}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-4 ${level > 0 ? 'mt-2' : ''}`}>
      {Object.entries(data).map(([key, value]) => {
        if (key === 'attachments' && Array.isArray(value) && value.length === 0) return null;
        const formatKey = key.replace(/_/g, ' ');

        if (level === 0) {
          return (
            <div key={key} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-50 px-5 py-3 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">{formatKey}</span>
              </div>
              <div className="p-5 text-sm text-slate-700 bg-white">{renderFormData(value, level + 1)}</div>
            </div>
          );
        }

        return (
          <div key={key} className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-6 border-b border-slate-50 last:border-0 pb-3 last:pb-0">
            <span className="capitalize text-slate-500 font-semibold text-sm sm:w-1/3 shrink-0 pt-0.5">{formatKey}</span>
            <div className="text-sm text-slate-800 flex-1 bg-slate-50/30 p-2 rounded-md border border-slate-100/50">
              {renderFormData(value, level + 1)}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const REVIEW_STATUS_LABELS = {
  pending_supervisor: 'Optional Supervisor Review Pending',
  pending_prosecutor: 'Optional Prosecutor Review Pending',
  approved: 'Optional Review Approved',
  rejected: 'Optional Review Not Approved',
  not_required: 'No External Approval Required',
};

export default function AdminDocumentPreview() {
  const { id } = useParams();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [supervisorNotes, setSupervisorNotes] = useState('');
  const [submittingSupervisor, setSubmittingSupervisor] = useState(false);
  const [reviewError, setReviewError] = useState('');

  const fetchDoc = async ({ silent = false } = {}) => {
    try {
      const { data } = await getAdminDocument(id);
      setDoc(data);
    } catch (err) {
      if (!silent) setError('Could not load document.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoc();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!doc || !['pending', 'generating'].includes(doc.status)) return;
    const interval = setInterval(() => fetchDoc({ silent: true }), 4000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.status, id]);

  const handleSupervisorReview = async (approved) => {
    setSubmittingSupervisor(true);
    setReviewError('');
    try {
      const { data } = await supervisorReview(id, { approved, notes: supervisorNotes });
      // supervisorReview returns the officer-facing serializer, which omits
      // user_email/agency_name — merge rather than replace so the header
      // (which reads those fields) doesn't go blank after a decision.
      setDoc((prev) => ({ ...prev, ...data }));
      setSupervisorNotes('');
    } catch (err) {
      setReviewError(err?.response?.data?.error?.detail || 'Failed to submit supervisor review.');
    } finally {
      setSubmittingSupervisor(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
        <p className="text-slate-500 font-medium mt-6">Loading document...</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-8">
        <Link to="/admin/documents" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-4">
          <ArrowLeft size={16} /> Back to Documents
        </Link>
        <div className="bg-red-50 p-8 rounded-2xl border border-red-200 text-red-700 flex items-center gap-4">
          <AlertTriangle className="w-8 h-8 text-red-500 shrink-0" />
          <p>{error || 'Document not found.'}</p>
        </div>
      </div>
    );
  }

  const isGenerating = ['pending', 'generating'].includes(doc.status);
  const isFailed = doc.status === 'failed';
  const hasLeakFlags = doc.leak_flags && doc.leak_flags.length > 0;
  const qualityFlags = doc.quality_flags || [];
  const hasQualityFlags = qualityFlags.length > 0;
  const reviewStatus = doc.review_status;
  const SOURCE_LABELS = { llm: 'AI Review', structural: 'Structural Check', system: 'System' };

  let parsedData = doc.form_data;
  if (typeof parsedData === 'string') {
    try { parsedData = JSON.parse(parsedData); } catch (e) { /* keep as string */ }
  }

  return (
    <div className="pb-10 space-y-6">
      <Link to="/admin/documents" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft size={16} /> Back to Documents
      </Link>

      {/* Header */}
      <div className="bg-white rounded-3xl p-6 md:p-8 shadow-sm border border-slate-200/60">
        <div className="flex items-start gap-5">
          <div className="p-4 bg-gradient-to-br from-indigo-500 to-blue-600 text-white rounded-2xl shadow-lg shadow-indigo-200">
            <FileText size={32} strokeWidth={1.5} />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1 flex-wrap">
              <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight capitalize">{doc.doc_type.replace(/_/g, ' ')}</h1>
              {isGenerating ? (
                <span className="px-3 py-1 bg-amber-50 text-amber-700 text-xs font-bold rounded-full flex items-center gap-1.5 border border-amber-200/60">
                  <Loader2 size={14} className="animate-spin" /> Generating
                </span>
              ) : isFailed ? (
                <span className="px-3 py-1 bg-red-50 text-red-700 text-xs font-bold rounded-full flex items-center gap-1.5 border border-red-200/60">
                  <AlertTriangle size={14} /> Failed
                </span>
              ) : (
                <span className="px-3 py-1 bg-green-50 text-green-700 text-xs font-bold rounded-full flex items-center gap-1.5 border border-green-200/60">
                  <CheckCircle size={14} /> Ready
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500 mt-2 font-medium">
              <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-lg text-slate-700 border border-slate-200">
                <Mail size={16} /> {doc.user_email}
              </span>
              {doc.agency_name && (
                <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-100">
                  <Building size={16} /> {doc.agency_name}
                </span>
              )}
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-100">
                <Database size={16} /> {doc.case_number || 'No Case #'}
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-100">
                <Clock size={16} /> {new Date(doc.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {reviewStatus && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <ShieldCheck size={18} className="text-indigo-500" /> Optional Oversight Status
            </h3>
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
              reviewStatus === 'approved' ? 'bg-emerald-100 text-emerald-700'
                : reviewStatus === 'rejected' ? 'bg-red-100 text-red-700'
                : reviewStatus === 'not_required' ? 'bg-slate-100 text-slate-600'
                : 'bg-amber-100 text-amber-700'
            }`}>
              {REVIEW_STATUS_LABELS[reviewStatus] || reviewStatus}
            </span>
          </div>

          {doc.supervisor_reviewed_by_email && (
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 text-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Supervisor Review</p>
              <p className="text-slate-900 font-medium">{doc.supervisor_reviewed_by_email}</p>
              {doc.supervisor_notes && <p className="text-slate-600 mt-1">{doc.supervisor_notes}</p>}
              <p className="text-xs text-slate-400 mt-1">{new Date(doc.supervisor_reviewed_at).toLocaleString()}</p>
            </div>
          )}

          {reviewError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">{reviewError}</div>
          )}

          {reviewStatus === 'pending_supervisor' && (
            <div className="pt-2 border-t border-slate-100 space-y-3">
              <p className="text-sm font-semibold text-slate-700">Optional Supervisor Review</p>
              <textarea
                value={supervisorNotes}
                onChange={(e) => setSupervisorNotes(e.target.value)}
                placeholder="Notes (optional)"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                rows={2}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => handleSupervisorReview(true)}
                  disabled={submittingSupervisor}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 disabled:opacity-60"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleSupervisorReview(false)}
                  disabled={submittingSupervisor}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 disabled:opacity-60"
                >
                  Reject
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {hasLeakFlags && (
        <div className="bg-amber-50/90 border border-amber-200 rounded-2xl p-6 flex items-start gap-4">
          <AlertTriangle className="text-amber-600 shrink-0" size={24} />
          <div>
            <h4 className="font-bold text-amber-900 text-lg mb-1.5">Potential Hallucination Detected</h4>
            <ul className="mt-2 flex flex-wrap gap-2.5">
              {doc.leak_flags.map((flag, i) => (
                <li key={i} className="text-xs bg-amber-100 border border-amber-200 text-amber-800 px-3 py-1.5 rounded-lg font-mono font-bold flex items-center gap-1.5">
                  <Sparkles size={14} className="text-amber-600" /> {flag.value}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {hasQualityFlags && (
        <div className="bg-slate-800 text-slate-100 rounded-2xl p-6 flex items-start gap-4">
          <Gavel className="text-indigo-300 shrink-0" size={24} />
          <div className="flex-1">
            <h4 className="font-bold text-white text-lg mb-1.5">Constitutional Quality Review</h4>
            <ul className="space-y-2.5">
              {qualityFlags.map((flag, i) => (
                <li key={i} className="bg-slate-700/60 border border-slate-600 rounded-lg px-4 py-3 flex items-start gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shrink-0 mt-0.5">
                    {SOURCE_LABELS[flag.source] || flag.source || 'review'}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-white">{flag.issue}</p>
                    {flag.detail && <p className="text-xs text-slate-300 mt-0.5">{flag.detail}</p>}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-4">
          <h2 className="text-lg font-bold text-slate-800 mb-4 px-1">Original Input Data</h2>
          <div className="bg-white border border-slate-200/60 rounded-3xl shadow-sm p-6 max-h-[70vh] overflow-y-auto">
            {renderFormData(parsedData)}
          </div>
        </div>

        <div className="lg:col-span-8">
          <div className="flex items-center justify-between mb-4 px-1">
            <h2 className="text-lg font-bold text-slate-800">Generated Narrative</h2>
            {!isGenerating && !isFailed && (
              <div className="flex items-center gap-4 bg-white px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600">
                <span className="flex items-center gap-1.5"><Cpu size={16} className="text-indigo-500" /> {doc.model_used || 'Unknown Model'}</span>
                <div className="w-px h-5 bg-slate-200"></div>
                <span className="flex items-center gap-1.5"><Clock size={16} className="text-blue-500" /> {((doc.generation_time_ms || 0) / 1000).toFixed(1)}s</span>
              </div>
            )}
          </div>
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden min-h-[400px]">
            {isGenerating ? (
              <div className="h-full min-h-[400px] flex flex-col items-center justify-center gap-4 text-center px-8">
                <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
                <p className="text-slate-500 text-sm">Still generating — this page updates automatically.</p>
              </div>
            ) : isFailed ? (
              <div className="h-full min-h-[400px] flex flex-col items-center justify-center gap-4 text-center px-8">
                <AlertTriangle className="w-12 h-12 text-red-500" />
                <p className="text-slate-500 text-sm max-w-md">{doc.error_message || 'Something went wrong while generating this document.'}</p>
              </div>
            ) : (
              <div className="p-8 md:p-12 text-slate-800 text-lg leading-[1.8] font-serif whitespace-pre-wrap">
                {doc.ai_narrative || <span className="text-slate-300">No narrative content.</span>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
