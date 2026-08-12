import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, RefreshCw, Download, AlertTriangle, Loader2, Database, Sparkles, Clock, CheckCircle, Cpu, FileCheck, ShieldAlert, ShieldCheck, PenLine, Gavel } from 'lucide-react';
import { getDocument, regenerateDocument, exportDocument, supervisorReview, prosecutorReview, signDocument } from '../../api/documents';
import { useAuth } from '../../contexts/AuthContext';
import AIGenerationLoader from '../../components/AIGenerationLoader';

// exportDocument uses responseType: 'blob' so on error axios still hands back
// a Blob (not parsed JSON) in err.response.data — it must be read as text first.
const parseBlobError = async (err) => {
  const data = err?.response?.data;
  if (!(data instanceof Blob)) return err?.response?.data?.error;
  try {
    const text = await data.text();
    return JSON.parse(text)?.error;
  } catch {
    return undefined;
  }
};

const renderFormData = (data, level = 0) => {
  if (data === null || data === undefined || data === '') return <span className="text-slate-400 italic">Not provided</span>;
  if (typeof data !== 'object') return <span className="text-slate-700 font-medium break-words leading-relaxed">{String(data)}</span>;
  
  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-slate-400 italic">Empty list</span>;
    return (
      <div className="flex flex-col gap-3 mt-2">
        {data.map((item, i) => (
          <div key={i} className="bg-slate-50/50 border border-slate-100 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow duration-200">
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
            <div key={key} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-0.5">
              <div className="bg-gradient-to-r from-slate-50 to-white px-5 py-3 border-b border-slate-100 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500"></div>
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                  {formatKey}
                </span>
              </div>
              <div className="p-5 text-sm text-slate-700 bg-white">
                {renderFormData(value, level + 1)}
              </div>
            </div>
          );
        }
        
        return (
          <div key={key} className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-6 border-b border-slate-50 last:border-0 pb-3 last:pb-0">
            <span className="capitalize text-slate-500 font-semibold text-sm sm:w-1/3 shrink-0 pt-0.5 flex items-center gap-1.5">
              <div className="w-1 h-1 rounded-full bg-slate-300"></div>
              {formatKey}
            </span>
            <div className="text-sm text-slate-800 flex-1 bg-slate-50/30 p-2 rounded-md border border-slate-100/50">
              {renderFormData(value, level + 1)}
            </div>
          </div>
        )
      })}
    </div>
  );
};

export default function GeneratedDocument() {
  const { id } = useParams();
  const { user } = useAuth();
  const [doc, setDoc] = useState(null);
  const [editedText, setEditedText] = useState('');
  const [loading, setLoading] = useState(true);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingDocx, setExportingDocx] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState('');

  const [supervisorNotes, setSupervisorNotes] = useState('');
  const [submittingSupervisor, setSubmittingSupervisor] = useState(false);
  const [prosecutorName, setProsecutorName] = useState('');
  const [prosecutorNotes, setProsecutorNotes] = useState('');
  const [submittingProsecutor, setSubmittingProsecutor] = useState(false);
  const [signName, setSignName] = useState('');
  const [submittingSignature, setSubmittingSignature] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [reviewAcknowledged, setReviewAcknowledged] = useState(false);

  const fetchDoc = async ({ silent = false } = {}) => {
    try {
      const { data } = await getDocument(id);
      setDoc(data);
      setEditedText(data.ai_narrative || '');
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

  // Generation (and regeneration) runs on a Celery worker and can take
  // several minutes on CPU — poll for completion instead of showing a
  // stale/empty narrative forever.
  useEffect(() => {
    if (!doc || !['pending', 'generating'].includes(doc.status)) return;
    const interval = setInterval(() => fetchDoc({ silent: true }), 4000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.status, id]);

  const handleExport = async (format) => {
    if (format === 'pdf') setExportingPdf(true);
    else setExportingDocx(true);
    setError('');

    try {
      const response = await exportDocument(id, {
        format,
        edited_text: editedText !== doc.ai_narrative ? editedText : '',
        review_acknowledged: reviewAcknowledged,
      });

      // Trigger browser download of the binary blob
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${doc.case_number || 'document'}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const apiError = await parseBlobError(err);
      if (apiError?.code === 'incomplete_officer_profile') {
        setError(`${apiError.detail} You can update your profile on the Profile page.`);
      } else if (['missing_agency', 'agency_assignment_required'].includes(apiError?.code)) {
        setError(apiError.detail);
      } else if (err?.response?.status === 403) {
        setError(`Your subscription plan does not support ${format.toUpperCase()} export.`);
      } else if (err?.response?.status === 402) {
        setError(`You've reached your monthly limit for this document type.`);
      } else {
        setError(`Failed to export ${format.toUpperCase()}.`);
      }
    } finally {
      setExportingPdf(false);
      setExportingDocx(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    setError('');
    try {
      const { data } = await regenerateDocument(id);
      setDoc(data);
      setEditedText(data.ai_narrative || '');
    } catch (err) {
      if (err?.response?.status === 402) {
        setError("You've reached your monthly limit for this document type.");
      } else {
        setError('Failed to regenerate document.');
      }
    } finally {
      setRegenerating(false);
    }
  };

  const handleSupervisorReview = async (approved) => {
    setSubmittingSupervisor(true);
    setReviewError('');
    try {
      const { data } = await supervisorReview(id, { approved, notes: supervisorNotes });
      setDoc(data);
      setSupervisorNotes('');
    } catch (err) {
      setReviewError(err?.response?.data?.error?.detail || 'Failed to submit supervisor review.');
    } finally {
      setSubmittingSupervisor(false);
    }
  };

  const handleProsecutorReview = async (approved) => {
    if (!prosecutorName.trim()) {
      setReviewError("Enter the prosecutor's name before recording their decision.");
      return;
    }
    setSubmittingProsecutor(true);
    setReviewError('');
    try {
      const { data } = await prosecutorReview(id, {
        reviewer_name: prosecutorName,
        approved,
        notes: prosecutorNotes,
      });
      setDoc(data);
      setProsecutorNotes('');
    } catch (err) {
      setReviewError(err?.response?.data?.error?.detail || 'Failed to submit prosecutor review.');
    } finally {
      setSubmittingProsecutor(false);
    }
  };

  const handleSign = async () => {
    if (!signName.trim()) {
      setReviewError('Type your full legal name to sign.');
      return;
    }
    setSubmittingSignature(true);
    setReviewError('');
    try {
      const { data } = await signDocument(id, { full_name: signName, review_acknowledged: reviewAcknowledged });
      setDoc(data);
      setSignName('');
    } catch (err) {
      setReviewError(err?.response?.data?.error?.detail || 'Failed to sign document.');
    } finally {
      setSubmittingSignature(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-[600px]">
        <div className="relative">
          <div className="absolute inset-0 bg-indigo-500/20 blur-xl rounded-full"></div>
          <Loader2 className="w-16 h-16 text-indigo-600 animate-spin relative z-10" />
        </div>
        <p className="text-slate-500 font-medium mt-6 animate-pulse">Preparing your document...</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="bg-red-50/80 backdrop-blur p-8 rounded-2xl border border-red-200 text-red-700 flex items-center gap-4 shadow-sm">
          <AlertTriangle className="w-8 h-8 text-red-500 shrink-0" />
          <div>
            <h3 className="font-bold text-lg mb-1">Error Loading Document</h3>
            <p>{error || 'Document not found.'}</p>
          </div>
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
  const hasOptionalReviewStatus = reviewStatus && !['approved', 'not_required'].includes(reviewStatus);
  const isSigned = !!doc.signature_name;
  const canActAsSupervisor = user?.is_supervisor || user?.role === 'admin';
  const REVIEW_STATUS_LABELS = {
    pending_supervisor: 'Optional Supervisor Review Pending',
    pending_prosecutor: 'Optional Prosecutor Review Pending',
    approved: 'Optional Review Approved',
    rejected: 'Optional Review Not Approved',
    not_required: 'No External Approval Required',
  };
  const SOURCE_LABELS = { llm: 'AI Review', structural: 'Structural Check', system: 'System' };

  return (
    <div className="p-4 md:p-8 max-w-[95rem] mx-auto space-y-8 bg-slate-50/50 min-h-[calc(100vh-4rem)]">
      {/* Header Section */}
      <div className="bg-white rounded-3xl p-6 md:p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] border border-slate-200/60 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-full blur-3xl -z-10 opacity-70 translate-x-1/3 -translate-y-1/3"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-purple-50 to-pink-50 rounded-full blur-3xl -z-10 opacity-70 -translate-x-1/3 translate-y-1/3"></div>
        
        <div className="flex items-start gap-5 z-10">
          <div className="p-4 bg-gradient-to-br from-indigo-500 to-blue-600 text-white rounded-2xl shadow-lg shadow-indigo-200">
            <FileCheck size={32} strokeWidth={1.5} />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">Generated Document</h1>
              {isGenerating ? (
                <span className="px-3 py-1 bg-amber-50 text-amber-700 text-xs font-bold rounded-full flex items-center gap-1.5 border border-amber-200/60 shadow-sm">
                  <Loader2 size={14} className="animate-spin" /> Generating
                </span>
              ) : isFailed ? (
                <span className="px-3 py-1 bg-red-50 text-red-700 text-xs font-bold rounded-full flex items-center gap-1.5 border border-red-200/60 shadow-sm">
                  <AlertTriangle size={14} /> Failed
                </span>
              ) : (
                <span className="px-3 py-1 bg-green-50 text-green-700 text-xs font-bold rounded-full flex items-center gap-1.5 border border-green-200/60 shadow-sm">
                  <CheckCircle size={14} /> Ready
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500 mt-2 font-medium">
              <span className="capitalize flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-lg text-slate-700 border border-slate-200">
                <FileText size={16} />
                {doc.doc_type.replace('_', ' ')}
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-100">
                <Database size={16} />
                {doc.case_number || 'No Case #'}
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-100">
                <Clock size={16} />
                {new Date(doc.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex flex-wrap items-center gap-3 z-10">
          <label className="w-full flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-950">
            <input type="checkbox" checked={reviewAcknowledged} onChange={(e) => setReviewAcknowledged(e.target.checked)} className="mt-0.5" />
            <span>I reviewed the complete document, verified its facts and citations, and accept responsibility for its official use.</span>
          </label>
          <button
            onClick={handleRegenerate}
            disabled={regenerating || isGenerating}
            className="flex items-center px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 hover:border-indigo-300 hover:text-indigo-600 transition-all duration-200 shadow-sm hover:shadow disabled:opacity-50 group"
          >
            <RefreshCw size={18} className={`mr-2.5 text-slate-400 group-hover:text-indigo-500 ${regenerating ? 'animate-spin' : ''}`} />
            {isFailed ? 'Try Again' : 'Regenerate'}
          </button>
          <button
            onClick={() => handleExport('docx')}
            disabled={exportingDocx || isGenerating || isFailed || !reviewAcknowledged}
            className="flex items-center px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 hover:border-blue-300 hover:text-blue-600 transition-all duration-200 shadow-sm hover:shadow disabled:opacity-50 group"
          >
            {exportingDocx ? <Loader2 size={18} className="mr-2.5 animate-spin text-blue-500" /> : <Download size={18} className="mr-2.5 text-slate-400 group-hover:text-blue-500" />}
            DOCX
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exportingPdf || isGenerating || isFailed || !reviewAcknowledged}
            className="flex items-center px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 transition-all duration-200 shadow-md hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-70 disabled:transform-none"
          >
            {exportingPdf ? <Loader2 size={18} className="mr-2.5 animate-spin" /> : <Download size={18} className="mr-2.5" />}
            Export PDF
          </button>
        </div>
      </div>

      {hasOptionalReviewStatus && (
        <div className="bg-blue-50 text-blue-900 border border-blue-200 px-6 py-3 rounded-2xl text-sm font-semibold flex items-center gap-3 shadow-sm">
          <ShieldAlert size={18} className="shrink-0" />
          {REVIEW_STATUS_LABELS[reviewStatus] || reviewStatus}. This does not prevent officer verification, signing, or export.
        </div>
      )}

      {error && (
        <div className="bg-red-50/90 backdrop-blur border border-red-200 text-red-700 px-6 py-4 rounded-2xl text-sm font-medium flex items-center gap-3 shadow-sm">
          <AlertTriangle size={20} className="shrink-0" />
          {error}
        </div>
      )}

      {/* RAG Leak Warning */}
      {hasLeakFlags && (
        <div className="bg-amber-50/90 backdrop-blur border border-amber-200 rounded-2xl p-6 flex items-start gap-4 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-amber-400"></div>
          <div className="p-2.5 bg-amber-100 rounded-xl shrink-0">
            <AlertTriangle className="text-amber-600" size={24} />
          </div>
          <div>
            <h4 className="font-bold text-amber-900 text-lg mb-1.5">Potential Hallucination Detected</h4>
            <p className="text-amber-800 text-sm leading-relaxed max-w-4xl">
              The AI included proper nouns or specific details that were not found in your provided notes. 
              Please review the document carefully to ensure accuracy.
            </p>
            <ul className="mt-4 flex flex-wrap gap-2.5">
              {doc.leak_flags.map((flag, i) => (
                <li key={i} className="text-xs bg-amber-100 border border-amber-200 text-amber-800 px-3 py-1.5 rounded-lg font-mono font-bold flex items-center gap-1.5 shadow-sm">
                  <Sparkles size={14} className="text-amber-600" />
                  {flag.value}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Constitutional Quality Review */}
      {hasQualityFlags && (
        <div className="bg-slate-800 text-slate-100 rounded-2xl p-6 flex items-start gap-4 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-400"></div>
          <div className="p-2.5 bg-slate-700 rounded-xl shrink-0">
            <Gavel className="text-indigo-300" size={24} />
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-white text-lg mb-1.5">Constitutional Quality Review</h4>
            <p className="text-slate-300 text-sm leading-relaxed max-w-4xl mb-4">
              These flags are compliance checks, not hallucination warnings — resolve them before this document is relied upon.
            </p>
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

      {/* Review & Signature */}
      {reviewStatus && (
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <ShieldCheck size={20} className="text-indigo-500" /> Optional Oversight &amp; Officer Signature
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

          {reviewError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">{reviewError}</div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            {doc.supervisor_reviewed_by_email && (
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Supervisor Review</p>
                <p className="text-slate-900 font-medium">{doc.supervisor_reviewed_by_email}</p>
                {doc.supervisor_notes && <p className="text-slate-600 mt-1">{doc.supervisor_notes}</p>}
                <p className="text-xs text-slate-400 mt-1">{new Date(doc.supervisor_reviewed_at).toLocaleString()}</p>
              </div>
            )}
            {doc.prosecutor_reviewed_name && (
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Prosecutor Review</p>
                <p className="text-slate-900 font-medium">
                  {doc.prosecutor_reviewed_name} — {doc.prosecutor_approved ? 'Approved' : 'Rejected'}
                </p>
                {doc.prosecutor_notes && <p className="text-slate-600 mt-1">{doc.prosecutor_notes}</p>}
                <p className="text-xs text-slate-400 mt-1">{new Date(doc.prosecutor_reviewed_at).toLocaleString()}</p>
              </div>
            )}
            {isSigned && (
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
                <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">Signed</p>
                <p className="text-emerald-900 font-medium font-serif italic text-base">{doc.signature_name}</p>
                <p className="text-xs text-emerald-600 mt-1">{new Date(doc.signed_at).toLocaleString()}</p>
              </div>
            )}
          </div>

          {/* Supervisor action */}
          {canActAsSupervisor && reviewStatus === 'pending_supervisor' && (
            <div className="pt-4 border-t border-slate-100 space-y-3">
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

          {/* Prosecutor action (recorded on their behalf) */}
          {canActAsSupervisor && reviewStatus === 'pending_prosecutor' && (
            <div className="pt-4 border-t border-slate-100 space-y-3">
              <p className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                <Gavel size={16} className="text-slate-400" /> Record Prosecutor Decision
              </p>
              <input
                type="text"
                value={prosecutorName}
                onChange={(e) => setProsecutorName(e.target.value)}
                placeholder="Prosecutor's full name"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <textarea
                value={prosecutorNotes}
                onChange={(e) => setProsecutorNotes(e.target.value)}
                placeholder="Notes (optional)"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                rows={2}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => handleProsecutorReview(true)}
                  disabled={submittingProsecutor}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 disabled:opacity-60"
                >
                  Approved
                </button>
                <button
                  onClick={() => handleProsecutorReview(false)}
                  disabled={submittingProsecutor}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 disabled:opacity-60"
                >
                  Rejected
                </button>
              </div>
            </div>
          )}

          {/* Signature */}
          {!isSigned && (
            <div className="pt-4 border-t border-slate-100 space-y-3">
              <p className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                <PenLine size={16} className="text-slate-400" /> Sign This Document
              </p>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={signName}
                  onChange={(e) => setSignName(e.target.value)}
                  placeholder="Type your full legal name"
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm font-serif italic focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <button
                  onClick={handleSign}
                  disabled={submittingSignature || !reviewAcknowledged}
                  className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-60"
                >
                  {submittingSignature ? 'Signing...' : 'Sign'}
                </button>
              </div>
              <p className="text-xs text-slate-400">Your typed name, the current timestamp, and your IP address will be recorded as your signature.</p>
            </div>
          )}
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start pb-8">
        
        {/* Original Input Data */}
        <div className="lg:col-span-4 flex flex-col h-[calc(100vh-16rem)] min-h-[600px] sticky top-6">
          <div className="flex items-center gap-2.5 mb-5 px-2">
            <div className="p-2 bg-slate-200/70 rounded-xl text-slate-700 shadow-sm border border-slate-300/30">
              <Database size={18} />
            </div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">Original Input Data</h2>
          </div>
          
          <div className="bg-white/80 backdrop-blur border border-slate-200/60 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex-1 overflow-hidden flex flex-col relative transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
            <div className="absolute top-0 left-0 right-0 h-5 bg-gradient-to-b from-slate-50/80 to-transparent pointer-events-none z-10"></div>
            
            <div className="p-6 md:p-8 overflow-y-auto flex-1 custom-scrollbar">
              <div className="max-w-2xl mx-auto">
                {(() => {
                  let parsedData = doc.form_data;
                  if (typeof parsedData === 'string') {
                    try {
                      parsedData = JSON.parse(parsedData);
                    } catch (e) {
                      // Keep as string if parsing fails
                    }
                  }
                  return renderFormData(parsedData);
                })()}
              </div>
            </div>
            
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-white to-transparent pointer-events-none z-10"></div>
          </div>
        </div>

        {/* Workspace Editor */}
        <div className="lg:col-span-8 flex flex-col h-[calc(100vh-16rem)] min-h-[600px]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5 px-2">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-indigo-100 rounded-xl text-indigo-700 shadow-sm border border-indigo-200/50">
                <Sparkles size={18} />
              </div>
              <h2 className="text-xl font-bold text-slate-800 tracking-tight">Generated Narrative</h2>
            </div>
            
            <div className="flex items-center gap-4 bg-white px-4 py-2 rounded-xl border border-slate-200 shadow-sm text-xs font-semibold text-slate-600">
              <span className="flex items-center gap-1.5">
                <Cpu size={16} className="text-indigo-500" />
                {doc.model_used || 'Unknown Model'}
              </span>
              <div className="w-px h-5 bg-slate-200"></div>
              <span className="flex items-center gap-1.5">
                <Clock size={16} className="text-blue-500" />
                {(doc.generation_time_ms / 1000).toFixed(1)}s
              </span>
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden flex flex-col flex-1 relative group transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
            {/* Decorative top bar */}
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-blue-500 opacity-90"></div>
            
            {/* Editor Content */}
            <div className="flex-1 bg-white overflow-y-auto custom-scrollbar relative z-0 mt-1">
              {isGenerating ? (
                <AIGenerationLoader />
              ) : isFailed ? (
                <div className="h-full flex flex-col items-center justify-center gap-4 text-center px-8">
                  <AlertTriangle className="w-12 h-12 text-red-500" />
                  <div>
                    <p className="text-slate-700 font-semibold">Generation failed</p>
                    <p className="text-slate-500 text-sm mt-1 max-w-md">{doc.error_message || 'Something went wrong while generating this document.'}</p>
                  </div>
                </div>
              ) : (
                <textarea
                  className="w-full h-full p-8 md:p-12 bg-transparent text-slate-800 text-lg leading-[1.8] font-serif resize-none focus:outline-none placeholder-slate-300 transition-colors"
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  placeholder="The generated narrative will appear here..."
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Global styles for custom scrollbar */}
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #cbd5e1;
          border-radius: 20px;
          border: 2px solid white;
        }
        .custom-scrollbar:hover::-webkit-scrollbar-thumb {
          background-color: #94a3b8;
        }
      `}} />
    </div>
  );
}
