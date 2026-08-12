import { useState, useEffect } from 'react';
import { Building2, MapPin, Plus, Pencil, Trash2, Loader2, X, Image as ImageIcon } from 'lucide-react';
import {
  listAgencies, createAgency, updateAgency, deleteAgency, uploadAgencySeal,
  listJurisdictionProfiles, createJurisdictionProfile, updateJurisdictionProfile, deleteJurisdictionProfile,
} from '../../api/agency';

const JURISDICTION_TYPES = [
  { value: 'federal', label: 'Federal' },
  { value: 'state', label: 'State' },
  { value: 'municipal', label: 'Municipal/County' },
];

const initialAgencyForm = {
  name: '',
  jurisdiction_type: 'state',
  jurisdiction_profile: '',
  state: '',
  county: '',
  city: '',
  court_name: '',
  judicial_district: '',
  division: '',
  court_caption: '',
  judge_title: '',
  prosecuting_authority: '',
  case_number_format: '',
  ori: '',
  default_legal_citations: '',
  requires_supervisor_review: false,
  requires_prosecutor_review: false,
};

const initialProfileForm = {
  name: '',
  jurisdiction_type: 'state',
  state: '',
  county: '',
  default_legal_citations: '',
};

export default function AgencyManagement() {
  const [tab, setTab] = useState('agencies');

  // Agencies
  const [agencies, setAgencies] = useState([]);
  const [agenciesLoading, setAgenciesLoading] = useState(true);
  const [agencyPage, setAgencyPage] = useState(1);
  const [hasMoreAgencies, setHasMoreAgencies] = useState(false);
  const [isAgencyModalOpen, setIsAgencyModalOpen] = useState(false);
  const [editingAgency, setEditingAgency] = useState(null);
  const [agencyForm, setAgencyForm] = useState(initialAgencyForm);
  const [agencySaving, setAgencySaving] = useState(false);
  const [agencyError, setAgencyError] = useState('');
  const [sealFile, setSealFile] = useState(null);
  const [sealUploading, setSealUploading] = useState(false);

  // Jurisdiction profiles
  const [profiles, setProfiles] = useState([]);
  const [profilesLoading, setProfilesLoading] = useState(true);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [profileForm, setProfileForm] = useState(initialProfileForm);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState('');

  const fetchAgencies = (page) => {
    setAgenciesLoading(true);
    listAgencies({ page })
      .then(({ data }) => {
        setAgencies(data.results || data);
        setHasMoreAgencies(!!data.next);
      })
      .catch((err) => console.error('Failed to fetch agencies', err))
      .finally(() => setAgenciesLoading(false));
  };

  const fetchProfiles = () => {
    setProfilesLoading(true);
    listJurisdictionProfiles()
      .then(({ data }) => setProfiles(data))
      .catch((err) => console.error('Failed to fetch jurisdiction profiles', err))
      .finally(() => setProfilesLoading(false));
  };

  useEffect(() => { fetchProfiles(); }, []);
  useEffect(() => { fetchAgencies(agencyPage); }, [agencyPage]);

  // ── Agencies ────────────────────────────────────────────────────────────

  const openCreateAgency = () => {
    setEditingAgency(null);
    setAgencyForm(initialAgencyForm);
    setSealFile(null);
    setAgencyError('');
    setIsAgencyModalOpen(true);
  };

  const openEditAgency = (agency) => {
    setEditingAgency(agency);
    setAgencyForm({
      name: agency.name || '',
      jurisdiction_type: agency.jurisdiction_type || 'state',
      jurisdiction_profile: agency.jurisdiction_profile ?? '',
      state: agency.state || '',
      county: agency.county || '',
      city: agency.city || '',
      court_name: agency.court_name || '',
      judicial_district: agency.judicial_district || '',
      division: agency.division || '',
      court_caption: agency.court_caption || '',
      judge_title: agency.judge_title || '',
      prosecuting_authority: agency.prosecuting_authority || '',
      case_number_format: agency.case_number_format || '',
      ori: agency.ori || '',
      default_legal_citations: agency.default_legal_citations || '',
      requires_supervisor_review: agency.requires_supervisor_review ?? false,
      requires_prosecutor_review: agency.requires_prosecutor_review ?? false,
    });
    setSealFile(null);
    setAgencyError('');
    setIsAgencyModalOpen(true);
  };

  const handleAgencyInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setAgencyForm({ ...agencyForm, [name]: type === 'checkbox' ? checked : value });
  };

  const handleDeleteAgency = async (pk) => {
    if (!window.confirm('Are you sure you want to delete this agency?')) return;
    try {
      await deleteAgency(pk);
      fetchAgencies(agencyPage);
    } catch (err) {
      alert(err?.response?.data?.error?.detail || 'Failed to delete agency. It might have officers assigned.');
    }
  };

  const handleAgencySubmit = async (e) => {
    e.preventDefault();
    setAgencySaving(true);
    setAgencyError('');
    try {
      const payload = {
        ...agencyForm,
        jurisdiction_profile: agencyForm.jurisdiction_profile === '' ? null : Number(agencyForm.jurisdiction_profile),
      };
      let agency;
      if (editingAgency) {
        ({ data: agency } = await updateAgency(editingAgency.id, payload));
      } else {
        ({ data: agency } = await createAgency(payload));
      }
      if (sealFile) {
        setSealUploading(true);
        const formData = new FormData();
        formData.append('seal', sealFile);
        await uploadAgencySeal(agency.id, formData);
        setSealUploading(false);
      }
      setIsAgencyModalOpen(false);
      fetchAgencies(agencyPage);
    } catch (err) {
      if (err?.response?.data && typeof err.response.data === 'object' && !err.response.data.error) {
        setAgencyError(Object.entries(err.response.data).map(([k, v]) => `${k}: ${v}`).join(', '));
      } else {
        setAgencyError(err?.response?.data?.error?.detail || 'Failed to save agency.');
      }
    } finally {
      setAgencySaving(false);
      setSealUploading(false);
    }
  };

  // ── Jurisdiction Profiles ───────────────────────────────────────────────

  const openCreateProfile = () => {
    setEditingProfile(null);
    setProfileForm(initialProfileForm);
    setProfileError('');
    setIsProfileModalOpen(true);
  };

  const openEditProfile = (profile) => {
    setEditingProfile(profile);
    setProfileForm({
      name: profile.name || '',
      jurisdiction_type: profile.jurisdiction_type || 'state',
      state: profile.state || '',
      county: profile.county || '',
      default_legal_citations: profile.default_legal_citations || '',
    });
    setProfileError('');
    setIsProfileModalOpen(true);
  };

  const handleProfileInputChange = (e) => {
    const { name, value } = e.target;
    setProfileForm({ ...profileForm, [name]: value });
  };

  const handleDeleteProfile = async (pk) => {
    if (!window.confirm('Are you sure you want to delete this jurisdiction profile?')) return;
    try {
      await deleteJurisdictionProfile(pk);
      fetchProfiles();
    } catch (err) {
      alert(err?.response?.data?.error?.detail || 'Failed to delete profile. It might have agencies attached.');
    }
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileError('');
    try {
      if (editingProfile) {
        await updateJurisdictionProfile(editingProfile.id, profileForm);
      } else {
        await createJurisdictionProfile(profileForm);
      }
      setIsProfileModalOpen(false);
      fetchProfiles();
    } catch (err) {
      if (err?.response?.data && typeof err.response.data === 'object' && !err.response.data.error) {
        setProfileError(Object.entries(err.response.data).map(([k, v]) => `${k}: ${v}`).join(', '));
      } else {
        setProfileError(err?.response?.data?.error?.detail || 'Failed to save jurisdiction profile.');
      }
    } finally {
      setProfileSaving(false);
    }
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Agencies & Jurisdictions</h1>
          <p className="text-gray-500 mt-1">Court captions, citations, and review rules printed onto warrants — shared across every officer at an agency.</p>
        </div>
      </div>

      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setTab('agencies')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${tab === 'agencies' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          Agencies
        </button>
        <button
          onClick={() => setTab('profiles')}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${tab === 'profiles' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          Jurisdiction Profiles
        </button>
      </div>

      {tab === 'agencies' ? (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Building2 size={18} className="text-blue-600" /> Agencies
            </h2>
            <button onClick={openCreateAgency} className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors">
              <Plus size={16} /> New Agency
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50/80">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Agency</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Jurisdiction</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ORI</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Review Rules</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {agenciesLoading && agencies.length === 0 ? (
                  <tr><td colSpan="5" className="py-10 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" size={24} /></td></tr>
                ) : agencies.length === 0 ? (
                  <tr><td colSpan="5" className="py-10 text-center text-gray-500">No agencies found. Create one.</td></tr>
                ) : (
                  agencies.map((agency) => (
                    <tr key={agency.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          {agency.seal_image_url ? (
                            <img src={agency.seal_image_url} alt="" className="w-9 h-9 rounded-full object-cover border border-gray-200" />
                          ) : (
                            <div className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
                              <ImageIcon size={16} />
                            </div>
                          )}
                          <div>
                            <div className="font-semibold text-gray-900">{agency.name}</div>
                            <div className="text-xs text-gray-500">{[agency.city, agency.state].filter(Boolean).join(', ') || 'N/A'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 capitalize">{agency.jurisdiction_type}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-1"><MapPin size={11} /> {agency.jurisdiction_profile_name || 'No shared profile'}</div>
                      </td>
                      <td className="px-6 py-4 text-sm font-mono text-gray-700">{agency.ori || 'N/A'}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col gap-1 text-xs">
                          <span className={agency.requires_supervisor_review ? 'text-emerald-600 font-medium' : 'text-gray-400'}>
                            Optional supervisor review {agency.requires_supervisor_review ? 'enabled' : 'disabled'}
                          </span>
                          <span className={agency.requires_prosecutor_review ? 'text-emerald-600 font-medium' : 'text-gray-400'}>
                            Optional prosecutor review {agency.requires_prosecutor_review ? 'enabled' : 'disabled'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-3">
                          <button onClick={() => openEditAgency(agency)} className="text-gray-400 hover:text-blue-600"><Pencil size={16} /></button>
                          <button onClick={() => handleDeleteAgency(agency.id)} className="text-gray-400 hover:text-red-600"><Trash2 size={16} /></button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {!agenciesLoading && (agencyPage > 1 || hasMoreAgencies) && (
            <div className="p-4 border-t border-gray-100 flex justify-between items-center bg-gray-50/30">
              <button disabled={agencyPage === 1} onClick={() => setAgencyPage(p => p - 1)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">Previous</button>
              <span className="text-sm text-gray-600 font-medium">Page {agencyPage}</span>
              <button disabled={!hasMoreAgencies} onClick={() => setAgencyPage(p => p + 1)} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">Next</button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <MapPin size={18} className="text-blue-600" /> Jurisdiction Profiles
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">Shared state/federal defaults agencies can inherit from. Add a new state by creating one of these.</p>
            </div>
            <button onClick={openCreateProfile} className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors">
              <Plus size={16} /> New Profile
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50/80">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">State / County</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {profilesLoading && profiles.length === 0 ? (
                  <tr><td colSpan="4" className="py-10 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" size={24} /></td></tr>
                ) : profiles.length === 0 ? (
                  <tr><td colSpan="4" className="py-10 text-center text-gray-500">No jurisdiction profiles found. Create one.</td></tr>
                ) : (
                  profiles.map((profile) => (
                    <tr key={profile.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4 font-semibold text-gray-900">{profile.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-700 capitalize">{profile.jurisdiction_type}</td>
                      <td className="px-6 py-4 text-sm text-gray-700">{[profile.county, profile.state].filter(Boolean).join(', ') || 'N/A'}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-3">
                          <button onClick={() => openEditProfile(profile)} className="text-gray-400 hover:text-blue-600"><Pencil size={16} /></button>
                          <button onClick={() => handleDeleteProfile(profile.id)} className="text-gray-400 hover:text-red-600"><Trash2 size={16} /></button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Agency Modal */}
      {isAgencyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-6 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900">{editingAgency ? 'Edit Agency' : 'New Agency'}</h2>
              <button onClick={() => setIsAgencyModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors"><X size={24} /></button>
            </div>

            <div className="p-6 overflow-y-auto">
              {agencyError && <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{agencyError}</div>}

              <form id="agency-form" onSubmit={handleAgencySubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Agency Name *</label>
                    <input type="text" name="name" value={agencyForm.name} onChange={handleAgencyInputChange} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. Smyrna Police Department" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Jurisdiction Type</label>
                    <select name="jurisdiction_type" value={agencyForm.jurisdiction_type} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      {JURISDICTION_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Shared Jurisdiction Profile</label>
                    <select name="jurisdiction_profile" value={agencyForm.jurisdiction_profile} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      <option value="">None — use this agency's own citations only</option>
                      {profiles.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">State</label>
                    <input type="text" name="state" value={agencyForm.state} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">County</label>
                    <input type="text" name="county" value={agencyForm.county} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">City</label>
                    <input type="text" name="city" value={agencyForm.city} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">ORI Number</label>
                    <input type="text" name="ori" value={agencyForm.ori} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono" />
                  </div>
                </div>

                <div className="pt-6 border-t border-gray-100">
                  <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Court &amp; Filing Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Court Name</label>
                      <input type="text" name="court_name" value={agencyForm.court_name} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Judicial District</label>
                      <input type="text" name="judicial_district" value={agencyForm.judicial_district} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Division</label>
                      <input type="text" name="division" value={agencyForm.division} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Court Caption</label>
                      <input type="text" name="court_caption" value={agencyForm.court_caption} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. IN THE SUPERIOR COURT OF ..." />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Judge Title</label>
                      <input type="text" name="judge_title" value={agencyForm.judge_title} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. Magistrate Judge" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Prosecuting Authority</label>
                      <input type="text" name="prosecuting_authority" value={agencyForm.prosecuting_authority} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Case Number Format</label>
                      <input type="text" name="case_number_format" value={agencyForm.case_number_format} onChange={handleAgencyInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. {year}-CR-{seq:05d}" />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Default Legal Citations</label>
                      <textarea name="default_legal_citations" value={agencyForm.default_legal_citations} onChange={handleAgencyInputChange} rows={3} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Overrides the jurisdiction profile's citations for this agency, if set." />
                    </div>
                  </div>
                </div>

                <div className="pt-6 border-t border-gray-100">
                  <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Review Workflow</h3>
                  <div className="space-y-3">
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" name="requires_supervisor_review" checked={agencyForm.requires_supervisor_review} onChange={handleAgencyInputChange} className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                      <span className="text-gray-700 font-medium">Enable optional supervisor review tracking</span>
                    </label>
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input type="checkbox" name="requires_prosecutor_review" checked={agencyForm.requires_prosecutor_review} onChange={handleAgencyInputChange} className="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                      <span className="text-gray-700 font-medium">Enable optional prosecutor review tracking</span>
                    </label>
                  </div>
                </div>

                <div className="pt-6 border-t border-gray-100">
                  <h3 className="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Agency Seal</h3>
                  <div className="flex items-center gap-4">
                    {editingAgency?.seal_image_url && (
                      <img src={editingAgency.seal_image_url} alt="" className="w-14 h-14 rounded-full object-cover border border-gray-200" />
                    )}
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setSealFile(e.target.files?.[0] || null)}
                      className="text-sm text-gray-600"
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Uploaded when you save this form. Rendered on exported PDFs/DOCX for this agency.</p>
                </div>
              </form>
            </div>

            <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
              <button type="button" onClick={() => setIsAgencyModalOpen(false)} className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
              <button type="submit" form="agency-form" disabled={agencySaving} className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center disabled:opacity-70 disabled:cursor-not-allowed">
                {agencySaving && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
                {sealUploading ? 'Uploading seal...' : editingAgency ? 'Save Changes' : 'Create Agency'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Jurisdiction Profile Modal */}
      {isProfileModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-6 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900">{editingProfile ? 'Edit Jurisdiction Profile' : 'New Jurisdiction Profile'}</h2>
              <button onClick={() => setIsProfileModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors"><X size={24} /></button>
            </div>

            <div className="p-6 overflow-y-auto">
              {profileError && <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{profileError}</div>}

              <form id="profile-form" onSubmit={handleProfileSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Name *</label>
                  <input type="text" name="name" value={profileForm.name} onChange={handleProfileInputChange} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder='e.g. "Georgia — State"' />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Jurisdiction Type</label>
                  <select name="jurisdiction_type" value={profileForm.jurisdiction_type} onChange={handleProfileInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    {JURISDICTION_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">State</label>
                    <input type="text" name="state" value={profileForm.state} onChange={handleProfileInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">County</label>
                    <input type="text" name="county" value={profileForm.county} onChange={handleProfileInputChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Default Legal Citations</label>
                  <textarea name="default_legal_citations" value={profileForm.default_legal_citations} onChange={handleProfileInputChange} rows={4} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Statutes/citations agencies in this jurisdiction inherit by default." />
                </div>
              </form>
            </div>

            <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
              <button type="button" onClick={() => setIsProfileModalOpen(false)} className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
              <button type="submit" form="profile-form" disabled={profileSaving} className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors flex items-center disabled:opacity-70 disabled:cursor-not-allowed">
                {profileSaving && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
                {editingProfile ? 'Save Changes' : 'Create Profile'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
