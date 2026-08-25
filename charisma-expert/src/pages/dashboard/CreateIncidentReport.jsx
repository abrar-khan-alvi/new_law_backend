import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Shield, Clock, Trash2, ArrowRight, Loader2 } from 'lucide-react';
import { generateDocument } from '../../api/documents';

export default function CreateIncidentReport() {
  const navigate = useNavigate();
  const locationState = useLocation().state || {};
  const sourceDoc = locationState.sourceDoc;
  
  // Form State
  const [templateType, setTemplateType] = useState('campus');
  const [caseNumber, setCaseNumber] = useState('');
  const [incidentType, setIncidentType] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [timeFormat, setTimeFormat] = useState('standard');
  const [location, setLocation] = useState('');
  const [reportedDate, setReportedDate] = useState('');
  const [reportedTime, setReportedTime] = useState('');
  const [outsideAgency, setOutsideAgency] = useState('');
  const [additionalNotes, setAdditionalNotes] = useState('');
  
  // Facts
  const [factsWho, setFactsWho] = useState('');
  const [factsWhat, setFactsWhat] = useState('');
  const [factsWhen, setFactsWhen] = useState('');
  const [factsWhere, setFactsWhere] = useState('');
  const [factsWhenTouched, setFactsWhenTouched] = useState(false);
  const [factsWhereTouched, setFactsWhereTouched] = useState(false);
  const [factsHow, setFactsHow] = useState('');
  const [factsOfficerActions, setFactsOfficerActions] = useState('');
  
  const [narrativeStyle, setNarrativeStyle] = useState('third_person'); // match API enum
  
  // Involved Parties
  const [involvedParties, setInvolvedParties] = useState([
    { id: 1, role: 'complainant', full_name: '', alias: '', id_number: '', phone: '', relationship: '' }
  ]);

  // Property Items
  const [propertyItems, setPropertyItems] = useState([]);

  // Notifications
  const [notifications, setNotifications] = useState({
    weapon_involved: false,
    weapon_detail: '',
    alcohol_drugs: false,
    alcohol_drugs_detail: '',
    is_hazing: false,
    acts_of_terrorism: false,
    acts_of_terrorism_detail: '',
    death_involved: false,
    death_detail: ''
  });
  
  const [incidentUrgency, setIncidentUrgency] = useState('normal');

  const [loading, setLoading] = useState(false);
  const [factsAcknowledged, setFactsAcknowledged] = useState(false);
  const [error, setError] = useState('');

  const formatIncidentDateTime = (incidentDate, incidentTime) => {
    const pieces = [incidentDate, incidentTime].filter(Boolean);
    return pieces.length ? pieces.join(' ') : '';
  };

  const normalizeTime = (value) => {
    const raw = value.trim();
    if (!raw) return '';
    const compact = raw.replace(/[^\d]/g, '');
    if (compact.length === 3 || compact.length === 4) {
      const padded = compact.padStart(4, '0');
      const hours = Number(padded.slice(0, 2));
      const minutes = Number(padded.slice(2));
      if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
        return `${padded.slice(0, 2)}:${padded.slice(2)}`;
      }
    }
    return raw;
  };

  const hydrateFromFormData = (formData, style) => {
    if (!formData) return;
    const incident = formData.incident || {};
    const facts = formData.facts || {};
    const restoredParties = (formData.involved_parties || []).map((party, idx) => ({
      id: Date.now() + idx,
      role: party.role || 'other',
      full_name: party.full_name || '',
      alias: party.alias || '',
      id_number: party.id_number || '',
      phone: party.phone || '',
      relationship: party.relationship || ''
    }));
    const restoredItems = (formData.property_items || []).map((item, idx) => ({
      id: Date.now() + 1000 + idx,
      type: item.type || '',
      value: item.value ?? '',
      status: item.status || (formData.template_type === 'nibrs' ? 'stolen' : 'missing')
    }));

    setTemplateType(formData.template_type || 'campus');
    setCaseNumber(formData.case_number || '');
    setIncidentType((incident.categories || []).join(', '));
    setDate(incident.date || '');
    setTime(incident.time || '');
    setLocation(incident.location || '');
    setReportedDate(incident.reported_date || '');
    setReportedTime(incident.reported_time || '');
    setIncidentUrgency(incident.urgency || 'normal');
    setInvolvedParties(restoredParties.length ? restoredParties : []);
    setPropertyItems(restoredItems);
    setNotifications({
      weapon_involved: Boolean(formData.notifications?.weapon_involved),
      weapon_detail: formData.notifications?.weapon_detail || '',
      alcohol_drugs: Boolean(formData.notifications?.alcohol_drugs),
      alcohol_drugs_detail: formData.notifications?.alcohol_drugs_detail || '',
      is_hazing: Boolean(formData.notifications?.is_hazing),
      acts_of_terrorism: Boolean(formData.notifications?.acts_of_terrorism),
      acts_of_terrorism_detail: formData.notifications?.acts_of_terrorism_detail || '',
      death_involved: Boolean(formData.notifications?.death_involved),
      death_detail: formData.notifications?.death_detail || ''
    });
    setOutsideAgency(formData.notifications?.outside_agency || '');
    setFactsWho(facts.who || '');
    setFactsWhat(facts.what || '');
    setFactsWhen(facts.when || formatIncidentDateTime(incident.date, incident.time));
    setFactsWhere(facts.where || incident.location || '');
    setFactsHow(facts.how || '');
    setFactsOfficerActions(facts.officer_actions || '');
    setAdditionalNotes(facts.additional_notes || '');
    setNarrativeStyle(style || 'third_person');
    setFactsWhenTouched(Boolean(facts.when));
    setFactsWhereTouched(Boolean(facts.where));
  };

  useEffect(() => {
    if (sourceDoc?.form_data) {
      hydrateFromFormData(sourceDoc.form_data, sourceDoc.narrative_style);
      setFactsAcknowledged(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceDoc?.id]);

  useEffect(() => {
    if (!factsWhenTouched) setFactsWhen(formatIncidentDateTime(date, time));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date, time, factsWhenTouched]);

  useEffect(() => {
    if (!factsWhereTouched) setFactsWhere(location);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location, factsWhereTouched]);

  const addInvolvedParty = (role) => {
    setInvolvedParties([...involvedParties, { id: Date.now(), role, full_name: '', alias: '', id_number: '', phone: '', relationship: '' }]);
  };

  const removeInvolvedParty = (id) => {
    setInvolvedParties(involvedParties.filter(p => p.id !== id));
  };

  const updateInvolvedParty = (id, field, value) => {
    setInvolvedParties(involvedParties.map(p => p.id === id ? { ...p, [field]: value } : p));
  };

  const handleTemplateChange = (type) => {
    setTemplateType(type);
    if (type === 'nibrs') {
      setInvolvedParties(prev => prev.map(p => p.role === 'alleged' ? { ...p, role: 'suspect' } : p));
      setPropertyItems(prev => prev.map(item => item.status === 'missing' ? { ...item, status: 'stolen' } : item));
    } else {
      setPropertyItems(prev => prev.map(item => ['burned', 'counterfeited'].includes(item.status) ? { ...item, status: 'missing' } : item));
    }
  };

  const addPropertyItem = () => {
    const defaultStatus = templateType === 'nibrs' ? 'stolen' : 'missing';
    setPropertyItems([...propertyItems, { id: Date.now(), type: 'currency', value: '', status: defaultStatus }]);
  };

  const removePropertyItem = (id) => {
    setPropertyItems(propertyItems.filter(p => p.id !== id));
  };

  const updatePropertyItem = (id, field, value) => {
    setPropertyItems(propertyItems.map(p => p.id === id ? { ...p, [field]: value } : p));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Clean up empty involved parties
    const finalParties = involvedParties.filter(p => p.full_name.trim() !== '').map(p => {
      const party = {
        role: p.role,
        full_name: p.full_name,
        alias: p.alias || undefined,
        id_number: p.id_number || undefined,
        phone: p.phone || undefined
      };
      if (templateType === 'nibrs' && p.role === 'victim') {
        party.relationship = p.relationship || undefined;
      }
      return party;
    });

    // Clean up empty property items
    const finalItems = propertyItems.filter(p => p.value !== '' || p.type.trim() !== '').map(p => ({
      type: p.type,
      value: p.value ? Number(p.value) : 0,
      status: p.status
    }));

    const payload = {
      doc_type: 'incident_report',
      narrative_style: narrativeStyle,
      source_facts_acknowledged: factsAcknowledged,
      form_data: {
        template_type: templateType,
        case_number: caseNumber || null,
        incident: {
          categories: incidentType.split(',').map(c => c.trim()).filter(Boolean),
          urgency: incidentUrgency,
          date,
          time,
          location,
          reported_date: reportedDate || undefined,
          reported_time: reportedTime || undefined
        },
        involved_parties: finalParties,
        property_items: finalItems,
        notifications: {
          ...notifications,
          outside_agency: outsideAgency || null
        },
        facts: {
          who: factsWho,
          what: factsWhat || `Incident: ${incidentType}`,
          where: factsWhere || location,
          when: factsWhen || `${date} ${time}`,
          how: factsHow,
          officer_actions: factsOfficerActions,
          additional_notes: additionalNotes || null
        },
        attachments: []
      }
    };

    try {
      const { data } = await generateDocument(payload);
      // Navigate to the generated document view
      navigate(`/dashboard/document/${data.id}`);
    } catch (err) {
      const msg = err?.response?.data?.error?.detail || err?.response?.data?.detail || 'Failed to generate document. Please try again.';
      if (err?.response?.status === 403) {
         setError('Your subscription plan does not allow generating this document type, or you have exceeded your limit.');
      } else if (err?.response?.status === 503) {
         setError('AI Engine is currently unavailable or loading. Please wait a moment and try again.');
      } else {
         setError(msg);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setLoading(false);
    }
  };

  const getRoleStyles = (role) => {
    switch (role) {
      case 'alleged':
      case 'suspect':
      case 'offender':
        return 'bg-red-50 text-red-700';
      case 'victim': return 'bg-purple-50 text-purple-700';
      case 'witness': return 'bg-blue-50 text-blue-700';
      case 'complainant': return 'bg-green-50 text-green-700';
      default: return 'bg-gray-50 text-gray-700';
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="bg-[#111625] w-12 h-12 rounded-xl flex items-center justify-center shadow-md">
           <Shield className="text-white absolute" size={24} />
           <Clock className="text-[#111625] relative" size={12} fill="white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 font-serif">AI Incident Report Generator</h1>
          <p className="text-gray-500 mt-1">Enter the raw facts and field notes below. The AI will structure them into a professional incident narrative.</p>
        </div>
      </div>

      {sourceDoc && (
        <div className="p-4 bg-blue-50 border border-blue-200 text-blue-900 rounded-xl text-sm">
          Editing original facts from case {sourceDoc.case_number || sourceDoc.id}. Submitting this form creates a revised draft while preserving the prior generated document.
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-white/80 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
          <Loader2 className="w-16 h-16 text-blue-600 animate-spin mb-6" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Generating Document...</h2>
          <p className="text-gray-500">The AI is structuring your narrative and performing leak checks. This may take up to a minute.</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8 pb-20">
        {/* Template Selection Toggle */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Select Incident Report Template Form
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => handleTemplateChange('campus')}
              className={`px-4 py-4 rounded-xl border-2 text-left transition-all ${
                templateType === 'campus'
                  ? 'border-blue-600 bg-blue-50/35 text-blue-900 shadow-sm shadow-blue-50'
                  : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-gray-50/20'
              }`}
            >
              <div className="font-bold text-base">Official Incident Report Draft</div>
              <div className="text-xs text-gray-500 mt-1">General-purpose structure for agency incident reporting and review.</div>
            </button>

            <button
              type="button"
              onClick={() => handleTemplateChange('nibrs')}
              className={`px-4 py-4 rounded-xl border-2 text-left transition-all ${
                templateType === 'nibrs'
                  ? 'border-blue-600 bg-blue-50/35 text-blue-900 shadow-sm shadow-blue-50'
                  : 'border-gray-200 hover:border-gray-300 text-gray-600 bg-gray-50/20'
              }`}
            >
              <div className="font-bold text-base">NIBRS (FBI National Standard)</div>
              <div className="text-xs text-gray-500 mt-1">Structured standards for criminal offense statistics and federal submissions.</div>
            </button>
          </div>
        </div>

        {/* Core Case Details */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Core Case Details</h2>
          </div>
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Case / Incident Number</label>
                <input 
                  type="text" 
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" 
                  placeholder="e.g. 2023-0842 (Optional)" 
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Incident Type *</label>
                <input 
                  type="text" 
                  value={incidentType}
                  onChange={(e) => setIncidentType(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" 
                  placeholder="e.g. Burglary, Assault" 
                  required 
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Date *</label>
                <input 
                  type="date" 
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors text-gray-700" 
                  required 
                />
              </div>
              <div>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <label className="block text-sm font-semibold text-gray-700">Time *</label>
                  <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5 text-xs font-semibold">
                    <button
                      type="button"
                      onClick={() => setTimeFormat('standard')}
                      className={`px-2.5 py-1 rounded-md ${timeFormat === 'standard' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                    >
                      Standard
                    </button>
                    <button
                      type="button"
                      onClick={() => setTimeFormat('military')}
                      className={`px-2.5 py-1 rounded-md ${timeFormat === 'military' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                    >
                      Military
                    </button>
                  </div>
                </div>
                <input 
                  type={timeFormat === 'military' ? 'text' : 'time'}
                  inputMode={timeFormat === 'military' ? 'numeric' : undefined}
                  value={time}
                  onChange={(e) => setTime(timeFormat === 'military' ? e.target.value : normalizeTime(e.target.value))}
                  onBlur={(e) => setTime(normalizeTime(e.target.value))}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors text-gray-700" 
                  placeholder={timeFormat === 'military' ? 'e.g. 1930' : undefined}
                  required 
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Urgency</label>
                <select
                  value={incidentUrgency}
                  onChange={(e) => setIncidentUrgency(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors text-gray-700"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            {templateType === 'nibrs' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-100">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Reported Date</label>
                  <input 
                    type="date" 
                    value={reportedDate}
                    onChange={(e) => setReportedDate(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors text-gray-700" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Reported Time</label>
                  <input 
                    type="time" 
                    value={reportedTime}
                    onChange={(e) => setReportedTime(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors text-gray-700" 
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Location *</label>
              <input 
                type="text" 
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" 
                placeholder="123 Main St, City, State" 
                required 
              />
            </div>

            <div className="pt-4 border-t border-gray-100">
              <h3 className="text-lg font-bold text-gray-900 font-serif mb-4">Detailed Facts</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Who (Parties involved)</label>
                  <textarea 
                    rows="3" 
                    value={factsWho}
                    onChange={(e) => setFactsWho(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Complainant Justin Kim; alleged party Martrece Smith..."
                  ></textarea>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">What (Incident description)</label>
                  <textarea 
                    rows="3" 
                    value={factsWhat}
                    onChange={(e) => setFactsWhat(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Report of $400 in currency missing from a wallet..."
                  ></textarea>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">When (Timeframe details)</label>
                  <textarea 
                    rows="3" 
                    value={factsWhen}
                    onChange={(e) => {
                      setFactsWhenTouched(true);
                      setFactsWhen(e.target.value);
                    }}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Between 1930 on 01/04 and 1930 on 01/06..."
                  ></textarea>
                  <button
                    type="button"
                    onClick={() => {
                      setFactsWhenTouched(false);
                      setFactsWhen(formatIncidentDateTime(date, time));
                    }}
                    className="mt-2 text-xs font-semibold text-blue-700 hover:text-blue-800"
                  >
                    Use case date/time
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Where (Location details)</label>
                  <textarea 
                    rows="3" 
                    value={factsWhere}
                    onChange={(e) => {
                      setFactsWhereTouched(true);
                      setFactsWhere(e.target.value);
                    }}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Dorm room NC1 1240B..."
                  ></textarea>
                  <button
                    type="button"
                    onClick={() => {
                      setFactsWhereTouched(false);
                      setFactsWhere(location);
                    }}
                    className="mt-2 text-xs font-semibold text-blue-700 hover:text-blue-800"
                  >
                    Use incident location
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">How (Modus Operandi)</label>
                  <textarea 
                    rows="3" 
                    value={factsHow}
                    onChange={(e) => setFactsHow(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Wallet found under bed, cash missing..."
                  ></textarea>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Officer Actions *</label>
                  <textarea 
                    rows="3" 
                    value={factsOfficerActions}
                    onChange={(e) => setFactsOfficerActions(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Took report at 1945; called Smith..."
                    required
                  ></textarea>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Additional Notes (Optional)</label>
                  <textarea 
                    rows="3" 
                    value={additionalNotes}
                    onChange={(e) => setAdditionalNotes(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors resize-none" 
                    placeholder="e.g. Any other relevant observations or background information..."
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Involved Parties */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200 flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Involved Parties</h2>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => addInvolvedParty('complainant')} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">+ Complainant</button>
              <button type="button" onClick={() => addInvolvedParty('victim')} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">+ Victim</button>
              <button type="button" onClick={() => addInvolvedParty('suspect')} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">+ Suspect</button>
              {templateType === 'nibrs' && (
                <button type="button" onClick={() => addInvolvedParty('offender')} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">+ Offender</button>
              )}
              <button type="button" onClick={() => addInvolvedParty('witness')} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">+ Witness</button>
              <button type="button" onClick={() => addInvolvedParty('other')} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">+ Other</button>
            </div>
          </div>
          <div className="p-6 space-y-4">
            {involvedParties.map((party) => (
              <div key={party.id} className="p-4 bg-gray-50/50 border border-gray-100 rounded-xl space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                  <div className={`md:col-span-2 px-4 py-1.5 rounded-full text-xs font-bold text-center capitalize ${getRoleStyles(party.role)}`}>
                    {party.role}
                  </div>
                  <div className="md:col-span-3">
                    <input 
                      type="text" 
                      value={party.full_name}
                      onChange={(e) => updateInvolvedParty(party.id, 'full_name', e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                      placeholder="Full Name" 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <input
                      type="text"
                      value={party.alias || ''}
                      onChange={(e) => updateInvolvedParty(party.id, 'alias', e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm"
                      placeholder="Alias"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <input 
                      type="text" 
                      value={party.id_number}
                      onChange={(e) => updateInvolvedParty(party.id, 'id_number', e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                      placeholder="ID Number" 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <input 
                      type="text" 
                      value={party.phone}
                      onChange={(e) => updateInvolvedParty(party.id, 'phone', e.target.value)}
                      className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                      placeholder="Phone" 
                    />
                  </div>
                  <div className="md:col-span-1 flex justify-end">
                    <button type="button" onClick={() => removeInvolvedParty(party.id)} className="p-2 text-gray-400 hover:text-red-500 transition-colors">
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>

                {templateType === 'nibrs' && party.role === 'victim' && (
                  <div className="mt-3 border-t border-gray-100 pt-3">
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Relationship to Suspect/Offender *</label>
                    <select
                      value={party.relationship || ''}
                      onChange={(e) => updateInvolvedParty(party.id, 'relationship', e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                      required
                    >
                      <option value="">-- Select Relationship --</option>
                      <option value="spouse">Spouse</option>
                      <option value="family_member">Other Family Member</option>
                      <option value="acquaintance">Acquaintance</option>
                      <option value="neighbor">Neighbor</option>
                      <option value="stranger">Stranger</option>
                      <option value="other">Other/Unknown</option>
                    </select>
                  </div>
                )}
              </div>
            ))}
            {involvedParties.length === 0 && (
              <div className="text-center py-6 text-gray-400 text-sm">
                No parties added yet.
              </div>
            )}
          </div>
        </div>

        {/* Property Items */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Property Items</h2>
            <button type="button" onClick={addPropertyItem} className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
              + Add Property
            </button>
          </div>
          <div className="p-6 space-y-4">
            {propertyItems.map((item) => (
              <div key={item.id} className="grid grid-cols-1 md:grid-cols-12 gap-4 p-4 bg-gray-50/50 border border-gray-100 rounded-xl items-center">
                <div className="md:col-span-4">
                  <input 
                    type="text" 
                    value={item.type}
                    onChange={(e) => updatePropertyItem(item.id, 'type', e.target.value)}
                    className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                    placeholder="Type (e.g. currency, electronics)" 
                  />
                </div>
                <div className="md:col-span-3">
                  <input 
                    type="number" 
                    value={item.value}
                    onChange={(e) => updatePropertyItem(item.id, 'value', e.target.value)}
                    className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                    placeholder="Value ($)" 
                  />
                </div>
                <div className="md:col-span-4">
                  <select
                    value={item.status}
                    onChange={(e) => updatePropertyItem(item.id, 'status', e.target.value)}
                    className="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-gray-700"
                  >
                    {templateType === 'campus' ? (
                      <>
                        <option value="missing">Missing</option>
                        <option value="stolen">Stolen</option>
                        <option value="damaged">Damaged</option>
                        <option value="recovered">Recovered</option>
                        <option value="seized">Seized</option>
                      </>
                    ) : (
                      <>
                        <option value="stolen">Stolen</option>
                        <option value="recovered">Recovered</option>
                        <option value="damaged">Destroyed/Damaged/Vandalized</option>
                        <option value="seized">Seized/Impounded</option>
                        <option value="burned">Burned</option>
                        <option value="counterfeited">Counterfeited/Forged</option>
                      </>
                    )}
                  </select>
                </div>
                <div className="md:col-span-1 flex justify-end">
                  <button type="button" onClick={() => removePropertyItem(item.id)} className="p-2 text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 size={20} />
                  </button>
                </div>
              </div>
            ))}
            {propertyItems.length === 0 && (
              <div className="text-center py-6 text-gray-400 text-sm">
                No property items added.
              </div>
            )}
          </div>
        </div>

        {/* Notifications & Modifiers */}
        {templateType === 'campus' ? (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 font-serif">Critical Notifications</h2>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex flex-wrap gap-8">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={notifications.weapon_involved}
                    onChange={(e) => setNotifications({...notifications, weapon_involved: e.target.checked})}
                    className="form-checkbox h-5 w-5 text-red-600 rounded border-gray-300 focus:ring-red-500" 
                  />
                  <span className="text-gray-800 font-semibold text-sm">Weapon Involved</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={notifications.alcohol_drugs}
                    onChange={(e) => setNotifications({...notifications, alcohol_drugs: e.target.checked})}
                    className="form-checkbox h-5 w-5 text-purple-600 rounded border-gray-300 focus:ring-purple-500" 
                  />
                  <span className="text-gray-800 font-semibold text-sm">Alcohol/Drugs</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={notifications.is_hazing}
                    onChange={(e) => setNotifications({...notifications, is_hazing: e.target.checked})}
                    className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" 
                  />
                  <span className="text-gray-800 font-semibold text-sm">Hazing Related</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.acts_of_terrorism}
                    onChange={(e) => setNotifications({...notifications, acts_of_terrorism: e.target.checked})}
                    className="form-checkbox h-5 w-5 text-red-700 rounded border-gray-300 focus:ring-red-500"
                  />
                  <span className="text-gray-800 font-semibold text-sm">Acts of Terrorism</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.death_involved}
                    onChange={(e) => setNotifications({...notifications, death_involved: e.target.checked})}
                    className="form-checkbox h-5 w-5 text-gray-900 rounded border-gray-300 focus:ring-gray-700"
                  />
                  <span className="text-gray-800 font-semibold text-sm">Death Involved</span>
                </label>
              </div>

              {(notifications.acts_of_terrorism || notifications.death_involved) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {notifications.acts_of_terrorism && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Terrorism Notification Details</label>
                      <input
                        type="text"
                        value={notifications.acts_of_terrorism_detail || ''}
                        onChange={(e) => setNotifications({ ...notifications, acts_of_terrorism_detail: e.target.value })}
                        placeholder="Agency notified, threat detail, or related notes"
                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                      />
                    </div>
                  )}
                  {notifications.death_involved && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Death Notification Details</label>
                      <input
                        type="text"
                        value={notifications.death_detail || ''}
                        onChange={(e) => setNotifications({ ...notifications, death_detail: e.target.value })}
                        placeholder="Decedent, coroner/ME notification, or related notes"
                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                      />
                    </div>
                  )}
                </div>
              )}

              <div className="pt-4 border-t border-gray-100">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Outside Agency Notified</label>
                <input
                  type="text"
                  placeholder="e.g. State Police, Local PD (Optional)"
                  value={outsideAgency}
                  onChange={(e) => setOutsideAgency(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm p-6 space-y-6">
            <h3 className="text-lg font-bold text-gray-900 font-serif">NIBRS Modifiers</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Weapon Details */}
              <div className="p-4 border border-gray-100 rounded-xl bg-gray-50/20">
                <label className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.weapon_involved}
                    onChange={(e) => setNotifications({ ...notifications, weapon_involved: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-5 w-5"
                  />
                  Weapon Involved?
                </label>
                {notifications.weapon_involved && (
                  <select
                    value={notifications.weapon_detail || ''}
                    onChange={(e) => setNotifications({ ...notifications, weapon_detail: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm mt-2 text-gray-700"
                  >
                    <option value="">Select Weapon Type...</option>
                    <option value="handgun">Handgun / Firearm</option>
                    <option value="sharp_object">Knife / Cutting Instrument</option>
                    <option value="blunt_object">Blunt Object (Club, Pipe, etc.)</option>
                    <option value="personal_weapons">Personal Weapons (Fists, Teeth)</option>
                  </select>
                )}
              </div>

              {/* Drug/Alcohol Modifiers */}
              <div className="p-4 border border-gray-100 rounded-xl bg-gray-50/20">
                <label className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.alcohol_drugs}
                    onChange={(e) => setNotifications({ ...notifications, alcohol_drugs: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-5 w-5"
                  />
                  Suspected Alcohol/Drug Involvement?
                </label>
                {notifications.alcohol_drugs && (
                  <input
                    type="text"
                    placeholder="e.g. Suspected Marijuana, Alcohol consumption"
                    value={notifications.alcohol_drugs_detail || ''}
                    onChange={(e) => setNotifications({ ...notifications, alcohol_drugs_detail: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm mt-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                  />
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border border-gray-100 rounded-xl bg-gray-50/20">
                <label className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.acts_of_terrorism}
                    onChange={(e) => setNotifications({ ...notifications, acts_of_terrorism: e.target.checked })}
                    className="rounded border-gray-300 text-red-700 focus:ring-red-500 h-5 w-5"
                  />
                  Acts of Terrorism?
                </label>
                {notifications.acts_of_terrorism && (
                  <input
                    type="text"
                    placeholder="Agency notified, threat detail, or related notes"
                    value={notifications.acts_of_terrorism_detail || ''}
                    onChange={(e) => setNotifications({ ...notifications, acts_of_terrorism_detail: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm mt-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                  />
                )}
              </div>

              <div className="p-4 border border-gray-100 rounded-xl bg-gray-50/20">
                <label className="flex items-center gap-2 font-semibold text-sm text-gray-700 mb-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifications.death_involved}
                    onChange={(e) => setNotifications({ ...notifications, death_involved: e.target.checked })}
                    className="rounded border-gray-300 text-gray-900 focus:ring-gray-700 h-5 w-5"
                  />
                  Death Involved?
                </label>
                {notifications.death_involved && (
                  <input
                    type="text"
                    placeholder="Decedent, coroner/ME notification, or related notes"
                    value={notifications.death_detail || ''}
                    onChange={(e) => setNotifications({ ...notifications, death_detail: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm mt-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                  />
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-gray-100">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Outside Agency Notified</label>
              <input
                type="text"
                placeholder="e.g. State Police, Local PD (Optional)"
                value={outsideAgency}
                onChange={(e) => setOutsideAgency(e.target.value)}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
              />
            </div>
          </div>
        )}

        {/* Narrative Style */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Narrative Style</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <label className={`flex items-start p-4 border rounded-xl cursor-pointer transition-colors ${narrativeStyle === 'first_person' ? 'border-blue-500 bg-blue-50/30' : 'border-gray-200 hover:bg-gray-50'}`}>
              <input 
                type="radio" 
                name="narrativeStyle" 
                value="first_person" 
                checked={narrativeStyle === 'first_person'} 
                onChange={() => setNarrativeStyle('first_person')}
                className="mt-1 mr-4 w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500" 
              />
              <div>
                <div className="font-bold text-gray-900 mb-1">First-Person</div>
                <div className="text-sm text-gray-500">"I responded to the scene..."</div>
              </div>
            </label>

            <label className={`flex items-start p-4 border rounded-xl cursor-pointer transition-colors ${narrativeStyle === 'third_person' ? 'border-blue-500 bg-blue-50/30' : 'border-gray-200 hover:bg-gray-50'}`}>
              <input 
                type="radio" 
                name="narrativeStyle" 
                value="third_person" 
                checked={narrativeStyle === 'third_person'} 
                onChange={() => setNarrativeStyle('third_person')}
                className="mt-1 mr-4 w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500" 
              />
              <div>
                <div className="font-bold text-gray-900 mb-1">Third-Person</div>
                <div className="text-sm text-gray-500">"Officer Smith responded to..."</div>
              </div>
            </label>
          </div>
        </div>

        <label className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <input type="checkbox" checked={factsAcknowledged} onChange={(e) => setFactsAcknowledged(e.target.checked)} required className="mt-1" />
          <span>I confirm that the facts entered are accurate to the best of my knowledge, contain only information I am authorized to use, and will be reviewed before official use.</span>
        </label>
        <div className="flex justify-end">
          <button 
            type="submit" 
            disabled={loading}
            className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors shadow-lg shadow-blue-500/30 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {sourceDoc ? 'Generate Revised Draft' : 'One-Click AI Generation'}
            <ArrowRight className="ml-2" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
