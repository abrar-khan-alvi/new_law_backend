import { useEffect, useState } from 'react';
import { UploadCloud, FileText, Database, ChevronDown, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { listTrainingDocs, uploadTrainingDoc } from '../../api/aiEngine';

export default function DatasetManagement() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [uploading, setUploading] = useState(false);
  const [targetRepo, setTargetRepo] = useState('incident_report');
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');

  const fetchFiles = async () => {
    try {
      const { data } = await listTrainingDocs();
      setFiles(data.results || data);
    } catch (err) {
      console.error('Failed to load training documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError('');
    setUploadSuccess('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', targetRepo);
    formData.append('title', file.name);

    try {
      await uploadTrainingDoc(formData);
      setUploadSuccess(`Successfully uploaded ${file.name}`);
      fetchFiles(); // reload the list
    } catch (err) {
      const apiError = err?.response?.data?.error;
      const message = typeof apiError === 'string' ? apiError : apiError?.detail;
      setUploadError(message || 'Failed to upload document. Maximum 50MB PDF/TXT/DOCX supported.');
    } finally {
      setUploading(false);
      // Reset input
      e.target.value = null;
    }
  };

  const incidentReportsCount = files.filter(f => f.doc_type === 'incident_report').length;
  const searchWarrantsCount = files.filter(f => f.doc_type === 'search_warrant').length;
  const arrestWarrantsCount = files.filter(f => f.doc_type === 'arrest_warrant').length;
  const totalCount = files.length;

  const incidentPercentage = totalCount > 0 ? (incidentReportsCount / totalCount) * 100 : 0;
  const searchPercentage = totalCount > 0 ? (searchWarrantsCount / totalCount) * 100 : 0;
  const arrestPercentage = totalCount > 0 ? (arrestWarrantsCount / totalCount) * 100 : 0;

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-8">AI Dataset & Training Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Upload Training Data */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm relative">
            {uploading && (
              <div className="absolute inset-0 bg-white/80 z-10 flex flex-col items-center justify-center rounded-xl">
                <Loader2 className="w-10 h-10 text-blue-600 animate-spin mb-3" />
                <p className="font-medium text-gray-900">Uploading and indexing document...</p>
                <p className="text-sm text-gray-500">This may take a moment</p>
              </div>
            )}
            
            <h2 className="text-xl font-bold text-gray-900 mb-6">Upload Training Data</h2>
            
            {uploadError && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg text-sm flex items-start gap-2">
                <AlertCircle size={16} className="mt-0.5" /> {uploadError}
              </div>
            )}
            {uploadSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-sm flex items-start gap-2">
                <CheckCircle2 size={16} className="mt-0.5" /> {uploadSuccess}
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Target Engine Repository</label>
              <div className="relative">
                <select 
                  value={targetRepo}
                  onChange={(e) => setTargetRepo(e.target.value)}
                  className="appearance-none block w-full bg-gray-50 border border-gray-300 text-gray-900 py-3 px-4 pr-8 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="incident_report">Incident Report Engine</option>
                  <option value="search_warrant">Search Warrant Engine</option>
                  <option value="arrest_warrant">Arrest Warrant Engine</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
                  <ChevronDown className="h-5 w-5" />
                </div>
              </div>
            </div>

            <label className="mt-6 border-2 border-dashed border-gray-300 rounded-xl p-12 flex flex-col items-center justify-center hover:bg-gray-50 transition-colors cursor-pointer group">
              <UploadCloud className="h-12 w-12 text-gray-400 group-hover:text-blue-500 transition-colors" />
              <div className="mt-4 flex text-sm justify-center leading-6 text-gray-600">
                <span className="relative rounded-md bg-transparent font-semibold text-blue-600 hover:text-blue-500">
                  Click to upload or drag and drop
                </span>
              </div>
              <p className="text-xs leading-5 text-gray-500 mt-1">PDF, Word, or Text files (Max 50MB per file)</p>
              <input type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>

          {/* Recent Training Files */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Recent Training Files</h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50/50">
                  <tr>
                    <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">File</th>
                    <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Repository</th>
                    <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {loading && files.length === 0 ? (
                    <tr><td colSpan="3" className="px-6 py-8 text-center"><Loader2 className="animate-spin text-gray-400 mx-auto" /></td></tr>
                  ) : files.length === 0 ? (
                    <tr><td colSpan="3" className="px-6 py-8 text-center text-gray-500">No training documents uploaded yet.</td></tr>
                  ) : (
                    files.map((file) => (
                      <tr key={file.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-5 whitespace-nowrap">
                          <div className="flex items-center">
                            <FileText className="h-6 w-6 text-gray-400 mr-4 flex-shrink-0" />
                            <div>
                              <div className="text-sm font-semibold text-gray-900 truncate max-w-[200px]" title={file.title}>{file.title}</div>
                              <div className="text-xs text-gray-500 mt-0.5">{new Date(file.created_at).toLocaleString()}</div>
                              <div className="text-xs text-gray-400 mt-0.5">By: {file.uploaded_by_email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-600 capitalize">
                          {file.doc_type.replace('_', ' ')}
                        </td>
                        <td className="px-6 py-5 whitespace-nowrap">
                          {file.is_indexed ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                              <CheckCircle2 size={12} /> Indexed ({file.chunk_count} chunks)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                              <Loader2 size={12} className="animate-spin" /> Processing
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* Right Column: Data Volumetrics */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col items-center">
          <div className="w-full flex items-center mb-8 gap-3">
             <Database className="w-6 h-6 text-gray-700" />
             <h2 className="text-xl font-bold text-gray-900">Data Volumetrics</h2>
          </div>

          <div className="flex-1 flex flex-col justify-center items-center py-12 w-full">
            <div className="text-center mb-12">
              <div className="flex items-baseline justify-center">
                <span className="text-6xl font-bold text-gray-900 tracking-tight">{totalCount}</span>
              </div>
              <p className="text-sm text-gray-500 mt-2">Total Documents</p>
            </div>

            <div className="w-full space-y-6">
              <div>
                <div className="flex justify-between text-sm font-medium mb-2">
                  <span className="text-gray-700">Incident Reports</span>
                  <span className="text-gray-900 font-semibold">{incidentReportsCount}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-[#111827] h-2 rounded-full transition-all duration-500" style={{ width: `${incidentPercentage}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm font-medium mb-2">
                  <span className="text-gray-700">Search Warrants</span>
                  <span className="text-gray-900 font-semibold">{searchWarrantsCount}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full transition-all duration-500" style={{ width: `${searchPercentage}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm font-medium mb-2">
                  <span className="text-gray-700">Arrest Warrants</span>
                  <span className="text-gray-900 font-semibold">{arrestWarrantsCount}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-amber-500 h-2 rounded-full transition-all duration-500" style={{ width: `${arrestPercentage}%` }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
