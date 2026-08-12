import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileSearch, Trash2, ArrowRight, Loader2, Plus } from 'lucide-react';
import { generateDocument } from '../../api/documents';

export default function CreateSearchWarrant() {
  const navigate = useNavigate();
  
  const [caseNumber, setCaseNumber] = useState('');
  const [courtDistrict, setCourtDistrict] = useState('');
  const [judgeName, setJudgeName] = useState('');
  
  const [offenses, setOffenses] = useState([{ id: 1, code_section: '', description: '' }]);
  
  const [placeType, setPlaceType] = useState('residence');
  const [placeDescription, setPlaceDescription] = useState('');
  const [placeAddress, setPlaceAddress] = useState('');
  
  const [itemsToSeize, setItemsToSeize] = useState('');
  
  const [executeByDate, setExecuteByDate] = useState('');
  const [timeWindow, setTimeWindow] = useState('anytime');
  
  const [affiantBackground, setAffiantBackground] = useState('');
  const [investigationSummary, setInvestigationSummary] = useState('');
  const [timeline, setTimeline] = useState('');
  const [nexusToPlace, setNexusToPlace] = useState('');
  
  const [narrativeStyle, setNarrativeStyle] = useState('first_person');

  const [loading, setLoading] = useState(false);
  const [factsAcknowledged, setFactsAcknowledged] = useState(false);
  const [error, setError] = useState('');

  const addOffense = () => {
    setOffenses([...offenses, { id: Date.now(), code_section: '', description: '' }]);
  };

  const removeOffense = (id) => {
    if (offenses.length > 1) {
      setOffenses(offenses.filter(o => o.id !== id));
    }
  };

  const updateOffense = (id, field, value) => {
    setOffenses(offenses.map(o => o.id === id ? { ...o, [field]: value } : o));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const payload = {
      doc_type: 'search_warrant',
      narrative_style: narrativeStyle,
      source_facts_acknowledged: factsAcknowledged,
      form_data: {
        case_number: caseNumber || null,
        court: {
          district: courtDistrict,
          judge_name: judgeName
        },
        offenses: offenses.filter(o => o.code_section || o.description).map(o => ({
          code_section: o.code_section,
          description: o.description
        })),
        place_to_search: {
          type: placeType,
          description: placeDescription,
          address: placeAddress
        },
        items_to_seize: itemsToSeize.split('\n').map(i => i.trim()).filter(i => i),
        execution: {
          execute_by_date: executeByDate,
          time_window: timeWindow
        },
        probable_cause: {
          affiant_background: affiantBackground,
          investigation_summary: investigationSummary,
          timeline: timeline.split('\n').map(i => i.trim()).filter(i => i),
          nexus_to_place: nexusToPlace
        }
      }
    };

    try {
      const { data } = await generateDocument(payload);
      navigate(`/dashboard/document/${data.id}`);
    } catch (err) {
      const msg = err?.response?.data?.error?.detail || err?.response?.data?.detail || 'Failed to generate document.';
      if (err?.response?.status === 403) {
         setError('Your subscription plan does not allow generating this document type, or you have exceeded your limit.');
      } else if (err?.response?.status === 503) {
         setError('AI Engine is currently unavailable. Please try again.');
      } else {
         setError(msg);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <div className="bg-[#111625] w-12 h-12 rounded-xl flex items-center justify-center shadow-md">
           <FileSearch className="text-white" size={24} />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 font-serif">AI Search Warrant</h1>
          <p className="text-gray-500 mt-1">Structure a search warrant application draft for authorized review.</p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="fixed inset-0 bg-white/80 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
          <Loader2 className="w-16 h-16 text-blue-600 animate-spin mb-6" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Generating Warrant...</h2>
          <p className="text-gray-500">Structuring your probable cause and checking guidelines...</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8 pb-20">
        
        {/* Core Case & Court Details */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Case & Court</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Case Number</label>
              <input type="text" value={caseNumber} onChange={(e) => setCaseNumber(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. 2:23-mj-281" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Court District *</label>
              <input type="text" value={courtDistrict} onChange={(e) => setCourtDistrict(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. Central District of California" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Judge Name</label>
              <input type="text" value={judgeName} onChange={(e) => setJudgeName(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. Patricia Donahue" />
            </div>
          </div>
        </div>

        {/* Offenses */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Offenses</h2>
            <button type="button" onClick={addOffense} className="text-sm font-medium text-blue-600 flex items-center gap-1 hover:text-blue-800"><Plus size={16} /> Add Offense</button>
          </div>
          <div className="p-6 space-y-4">
            {offenses.map((offense, index) => (
              <div key={offense.id} className="flex gap-4 items-start">
                <div className="flex-1">
                  <input type="text" value={offense.code_section} onChange={(e) => updateOffense(offense.id, 'code_section', e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="Code Section (e.g. 18 U.S.C. § 1030)" />
                </div>
                <div className="flex-[2]">
                  <input type="text" value={offense.description} onChange={(e) => updateOffense(offense.id, 'description', e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="Description (e.g. Computer fraud)" />
                </div>
                {offenses.length > 1 && (
                  <button type="button" onClick={() => removeOffense(offense.id)} className="p-3 text-gray-400 hover:text-red-500 mt-1"><Trash2 size={20} /></button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Place & Items */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 font-serif">Place to Search</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Type</label>
                <select value={placeType} onChange={(e) => setPlaceType(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <option value="residence">Residence</option><option value="vehicle">Vehicle</option><option value="business">Business</option><option value="digital">Digital Device or Account</option><option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Location or Property Description *</label>
                <textarea rows="2" value={placeDescription} onChange={(e) => setPlaceDescription(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="Servers at the data center..."></textarea>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Address *</label>
                <input type="text" value={placeAddress} onChange={(e) => setPlaceAddress(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="e.g. Los Angeles, CA" />
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm flex flex-col">
            <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 font-serif">Items to Seize & Execution</h2>
            </div>
            <div className="p-6 space-y-4 flex-1">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Items to Seize (One per line) *</label>
                <textarea rows="3" value={itemsToSeize} onChange={(e) => setItemsToSeize(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="All data and logs relating to the offense..."></textarea>
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Execute By Date</label>
                  <input type="date" value={executeByDate} onChange={(e) => setExecuteByDate(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" />
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Time Window</label>
                  <select value={timeWindow} onChange={(e) => setTimeWindow(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <option value="daytime">Daytime</option>
                    <option value="anytime">Anytime</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Probable Cause */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Probable Cause Affidavit</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Affiant Background *</label>
              <textarea rows="3" value={affiantBackground} onChange={(e) => setAffiantBackground(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="e.g. FBI Special Agent, cybercrime since 2018..."></textarea>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Connection Between Evidence and Location *</label>
              <textarea rows="3" value={nexusToPlace} onChange={(e) => setNexusToPlace(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="e.g. Evidence physically resides on these servers..."></textarea>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Investigation Summary *</label>
              <textarea rows="4" value={investigationSummary} onChange={(e) => setInvestigationSummary(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="Summary of the investigation leading to this warrant..."></textarea>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Timeline of Events (One event per line)</label>
              <textarea rows="4" value={timeline} onChange={(e) => setTimeline(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="2026-06-01: forensic images obtained&#10;2026-06-05: secondary analysis confirmed..."></textarea>
            </div>
          </div>
        </div>

        <label className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <input type="checkbox" checked={factsAcknowledged} onChange={(e) => setFactsAcknowledged(e.target.checked)} required className="mt-1" />
          <span>I confirm that the facts entered are accurate to the best of my knowledge, contain only information I am authorized to use, and will be reviewed before filing or official use.</span>
        </label>
        <div className="flex justify-end">
          <button type="submit" disabled={loading} className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors shadow-lg shadow-blue-500/30 disabled:opacity-70 disabled:cursor-not-allowed">
            Generate Search Warrant
            <ArrowRight className="ml-2" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
