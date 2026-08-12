import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserPlus, ArrowRight, Loader2 } from 'lucide-react';
import { generateDocument } from '../../api/documents';

export default function CreateArrestWarrant() {
  const navigate = useNavigate();
  
  const [caseNumber, setCaseNumber] = useState('');
  const [courtDistrict, setCourtDistrict] = useState('');
  
  const [defendantName, setDefendantName] = useState('');
  
  const [chargingDocument, setChargingDocument] = useState('complaint');
  const [codeSection, setCodeSection] = useState('');
  const [briefDescription, setBriefDescription] = useState('');
  
  const [aliases, setAliases] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [sex, setSex] = useState('M');
  const [race, setRace] = useState('');
  const [residence, setResidence] = useState('');
  const [vehicle, setVehicle] = useState('');
  
  const [includeAffidavit, setIncludeAffidavit] = useState(true);
  const [affiantBackground, setAffiantBackground] = useState('');
  const [pcFacts, setPcFacts] = useState('');
  const [timeline, setTimeline] = useState('');
  
  const [narrativeStyle, setNarrativeStyle] = useState('third_person');

  const [loading, setLoading] = useState(false);
  const [factsAcknowledged, setFactsAcknowledged] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const payload = {
      doc_type: 'arrest_warrant',
      narrative_style: narrativeStyle,
      source_facts_acknowledged: factsAcknowledged,
      form_data: {
        case_number: caseNumber || null,
        court: {
          district: courtDistrict
        },
        defendant: {
          full_name: defendantName
        },
        charging_document: chargingDocument,
        offense: {
          code_section: codeSection,
          brief_description: briefDescription
        },
        identifiers: {
          aliases: aliases.split(',').map(a => a.trim()).filter(a => a),
          date_of_birth: dateOfBirth,
          height: height,
          weight: weight,
          sex: sex,
          race: race,
          last_known_residence: residence,
          vehicle_description: vehicle
        },
        probable_cause: includeAffidavit
          ? {
              include_affidavit: true,
              affiant_background: affiantBackground,
              facts: pcFacts,
              timeline: timeline.split('\n').map(i => i.trim()).filter(i => i)
            }
          : { include_affidavit: false }
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
           <UserPlus className="text-white" size={24} />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 font-serif">AI Arrest Warrant</h1>
          <p className="text-gray-500 mt-1">Create detailed arrest warrant applications.</p>
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
          <p className="text-gray-500">Structuring narrative and verifying elements...</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8 pb-20">
        
        {/* Case & Defendant Details */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Case & Defendant Details</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Case Number</label>
              <input type="text" value={caseNumber} onChange={(e) => setCaseNumber(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. 1:24-cr-001" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Court District *</label>
              <input type="text" value={courtDistrict} onChange={(e) => setCourtDistrict(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. Northern District of Georgia" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Defendant Full Name *</label>
              <input type="text" value={defendantName} onChange={(e) => setDefendantName(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. John A. Doe" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Charging Document</label>
              <select value={chargingDocument} onChange={(e) => setChargingDocument(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors">
                <option value="complaint">Complaint</option>
                <option value="indictment">Indictment</option>
                <option value="superseding_indictment">Superseding Indictment</option>
                <option value="information">Information</option>
                <option value="superseding_information">Superseding Information</option>
                <option value="probation_violation">Probation Violation</option>
                <option value="supervised_release_violation">Supervised Release Violation</option>
                <option value="violation_notice">Violation Notice</option>
                <option value="court_order">Court Order</option>
              </select>
            </div>
          </div>
        </div>

        {/* Offense */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Primary Offense</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Code Section *</label>
              <input type="text" value={codeSection} onChange={(e) => setCodeSection(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. 18 U.S.C. § 2113(a)" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Brief Description *</label>
              <input type="text" value={briefDescription} onChange={(e) => setBriefDescription(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors" placeholder="e.g. Bank robbery by force and violence" />
            </div>
          </div>
        </div>

        {/* Identifiers */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Defendant Identifiers</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Aliases (Comma separated)</label>
              <input type="text" value={aliases} onChange={(e) => setAliases(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="e.g. Johnny D, The Ghost" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Date of Birth</label>
              <input type="date" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Height</label>
              <input type="text" value={height} onChange={(e) => setHeight(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="e.g. 5'11&quot;" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Weight</label>
              <input type="text" value={weight} onChange={(e) => setWeight(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="e.g. 180 lbs" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Sex</label>
              <select value={sex} onChange={(e) => setSex(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg">
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Race</label>
              <input type="text" value={race} onChange={(e) => setRace(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="e.g. White, Black" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Last Known Residence</label>
              <input type="text" value={residence} onChange={(e) => setResidence(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="123 Peachtree St, Atlanta, GA" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Vehicle Description</label>
              <input type="text" value={vehicle} onChange={(e) => setVehicle(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg" placeholder="Black 2018 Honda Civic, GA tag ABC1234" />
            </div>
          </div>
        </div>

        {/* Probable Cause */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50/50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900 font-serif">Probable Cause Affidavit</h2>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <input type="checkbox" checked={includeAffidavit} onChange={(e) => setIncludeAffidavit(e.target.checked)} className="w-4 h-4 text-blue-600 rounded" />
              Include Affidavit
            </label>
          </div>
          {includeAffidavit && (
            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Affiant Background *</label>
                <textarea rows="2" value={affiantBackground} onChange={(e) => setAffiantBackground(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="e.g. Detective, Atlanta PD, 8 years..."></textarea>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Facts Establishing Probable Cause *</label>
                <textarea rows="4" value={pcFacts} onChange={(e) => setPcFacts(e.target.value)} required className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="Surveillance and eyewitness ID place the defendant at the scene..."></textarea>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Timeline of Events (One event per line)</label>
                <textarea rows="3" value={timeline} onChange={(e) => setTimeline(e.target.value)} className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg resize-none" placeholder="2026-05-01: Robbery occurred..."></textarea>
              </div>
            </div>
          )}
        </div>

        <label className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <input type="checkbox" checked={factsAcknowledged} onChange={(e) => setFactsAcknowledged(e.target.checked)} required className="mt-1" />
          <span>I confirm that the facts entered are accurate to the best of my knowledge, contain only information I am authorized to use, and will be reviewed before filing or official use.</span>
        </label>
        <div className="flex justify-end">
          <button type="submit" disabled={loading} className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors shadow-lg shadow-blue-500/30 disabled:opacity-70 disabled:cursor-not-allowed">
            Generate Arrest Warrant
            <ArrowRight className="ml-2" size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
