import { useState, useEffect } from 'react';
import { FileText, Plus, Edit, Trash2, X, UploadCloud, Image as ImageIcon, Video, Eye, Link as LinkIcon, Loader2 } from 'lucide-react';
import { listPosts, createPost, updatePost, deletePost, getPost, addPostMedia, deletePostMedia } from '../../api/blog';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const resolveUrl = (url) => url?.startsWith('/') ? `${BASE_URL}${url}` : url;

export default function ContentManagement() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingPost, setEditingPost] = useState(null);
  const [formData, setFormData] = useState({ title: '', content: '', excerpt: '', category: 'general', tags: '', is_published: false, is_featured: false });
  const [editorMedia, setEditorMedia] = useState({ type: 'image', file: null, url: '', caption: '' });
  const [coverImage, setCoverImage] = useState(null);
  const [saving, setSaving] = useState(false);

  const [isMediaOpen, setIsMediaOpen] = useState(false);
  const [activeMediaPost, setActiveMediaPost] = useState(null);
  const [postMedia, setPostMedia] = useState([]);
  const [mediaLoading, setMediaLoading] = useState(false);
  
  const [mediaType, setMediaType] = useState('image'); // image, video, video_url
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaUrl, setMediaUrl] = useState('');
  const [mediaCaption, setMediaCaption] = useState('');
  const [uploadingMedia, setUploadingMedia] = useState(false);

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const { data } = await listPosts({ page: 1 });
      setPosts(data.results || data);
    } catch (err) {
      console.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  // --- Post Editor ---

  const openEditor = async (post = null) => {
    if (post) {
      setIsEditorOpen(true); // Open early to show loading state if needed, or wait
      try {
        const { data: fullPost } = await getPost(post.slug);
        setEditingPost(fullPost);
        setFormData({
          title: fullPost.title || '',
          content: fullPost.content || '',
          excerpt: fullPost.excerpt || '',
          category: fullPost.category || 'general',
          tags: fullPost.tags ? fullPost.tags.map(t => t.name).join(', ') : '',
          is_published: fullPost.is_published || false,
          is_featured: fullPost.is_featured || false,
        });
      } catch (err) {
        console.error("Failed to fetch full post", err);
        alert("Failed to load post details.");
        setIsEditorOpen(false);
      }
    } else {
      setEditingPost(null);
      setFormData({ title: '', content: '', excerpt: '', category: 'general', tags: '', is_published: false, is_featured: false });
      setIsEditorOpen(true);
    }
    setEditorMedia({ type: 'image', file: null, url: '', caption: '' });
    setCoverImage(null);
  };

  const handleSavePost = async () => {
    setSaving(true);
    try {
      const payload = {
        ...formData,
        publish: formData.is_published, // Map the state field to the API field
        tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
      };
      
      let postSlug;
      if (editingPost) {
        const { data } = await updatePost(editingPost.slug, payload);
        postSlug = data.slug || editingPost.slug;
      } else {
        const { data } = await createPost(payload);
        postSlug = data.slug;
      }

      // Handle Cover Image Upload
      if (coverImage) {
        try {
          const coverForm = new FormData();
          coverForm.append('media_type', 'image');
          coverForm.append('file', coverImage);
          coverForm.append('caption', 'Cover Image');
          
          // 1. Upload to the media gallery
          const coverRes = await addPostMedia(postSlug, coverForm);
          
          // 2. Patch the post to set this media's URL as the cover_image_url
          if (coverRes && coverRes.data && coverRes.data.url) {
            await updatePost(postSlug, { cover_image_url: coverRes.data.url });
          }
        } catch (coverErr) {
          console.error("Cover image upload failed", coverErr);
          alert('Article saved, but cover image upload failed. Details: ' + (coverErr.response?.data ? JSON.stringify(coverErr.response.data) : coverErr.message));
        }
      }

      // Handle initial media upload if provided
      if ((editorMedia.type === 'video_url' && editorMedia.url) || (editorMedia.type !== 'video_url' && editorMedia.file)) {
        try {
          if (editorMedia.type === 'video_url') {
            await addPostMedia(postSlug, {
              media_type: 'video_url',
              video_url: editorMedia.url,
              caption: editorMedia.caption
            });
          } else {
            const form = new FormData();
            form.append('media_type', editorMedia.type);
            form.append('file', editorMedia.file);
            form.append('caption', editorMedia.caption);
            await addPostMedia(postSlug, form);
          }
        } catch (mediaErr) {
          console.error("Media upload failed", mediaErr);
          alert('Article saved, but media upload failed. You can try uploading it again from the Manage Media option in the table.');
        }
      }

      setIsEditorOpen(false);
      fetchPosts();
    } catch (err) {
      alert('Failed to save post. ' + (err.response?.data?.detail || ''));
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePost = async (slug) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;
    try {
      await deletePost(slug);
      fetchPosts();
    } catch (err) {
      alert('Failed to delete post.');
    }
  };

  const togglePublish = async (post) => {
    try {
      await updatePost(post.slug, { is_published: !post.is_published });
      fetchPosts();
    } catch (err) {
      alert('Failed to toggle publish status.');
    }
  };

  // --- Media Manager ---

  const openMediaManager = async (post) => {
    setActiveMediaPost(post);
    setIsMediaOpen(true);
    setMediaLoading(true);
    setMediaType('image');
    setMediaFile(null);
    setMediaUrl('');
    setMediaCaption('');
    
    try {
      const { data } = await getPost(post.slug);
      setPostMedia(data.media || []);
      // Pre-fill content if we want to allow editing, but right now just media
    } catch (err) {
      console.error('Failed to load post details');
    } finally {
      setMediaLoading(false);
    }
  };

  const handleUploadMedia = async () => {
    if (!activeMediaPost) return;
    setUploadingMedia(true);
    
    try {
      if (mediaType === 'video_url') {
        if (!mediaUrl) throw new Error('URL required');
        await addPostMedia(activeMediaPost.slug, {
          media_type: 'video_url',
          video_url: mediaUrl,
          caption: mediaCaption
        });
      } else {
        if (!mediaFile) throw new Error('File required');
        const form = new FormData();
        form.append('media_type', mediaType);
        form.append('file', mediaFile);
        form.append('caption', mediaCaption);
        await addPostMedia(activeMediaPost.slug, form);
      }
      
      // Refresh media list
      const { data } = await getPost(activeMediaPost.slug);
      setPostMedia(data.media || []);
      setMediaFile(null);
      setMediaUrl('');
      setMediaCaption('');
    } catch (err) {
      alert(err.message || 'Failed to upload media.');
    } finally {
      setUploadingMedia(false);
    }
  };

  const handleDeleteMedia = async (mediaId) => {
    if (!window.confirm('Delete this media?')) return;
    try {
      await deletePostMedia(activeMediaPost.slug, mediaId);
      setPostMedia(postMedia.filter(m => m.id !== mediaId));
    } catch (err) {
      alert('Failed to delete media.');
    }
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Blog Manager</h1>
          <p className="text-gray-500 mt-1">Manage articles, images, and videos.</p>
        </div>
        <button 
          onClick={() => openEditor()}
          className="w-full sm:w-auto flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-full font-medium hover:bg-blue-700 shadow-sm transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          Create New Article
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden min-h-[400px]">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50/50">
              <tr>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Article</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Views</th>
                <th scope="col" className="px-6 py-4 text-right text-xs font-semibold text-gray-900 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan="5" className="px-6 py-8 text-center"><Loader2 className="animate-spin mx-auto text-gray-400" /></td></tr>
              ) : posts.length === 0 ? (
                <tr><td colSpan="5" className="px-6 py-8 text-center text-gray-500">No articles found.</td></tr>
              ) : (
                posts.map((post) => (
                  <tr key={post.slug} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-5 whitespace-nowrap">
                      <div className="text-sm font-semibold text-gray-900 max-w-xs truncate" title={post.title}>{post.title}</div>
                      <div className="text-xs text-gray-500 mt-0.5">By {post.author_name || 'Admin'}</div>
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-500">{post.category?.name || 'Uncategorized'}</td>
                    <td className="px-6 py-5 whitespace-nowrap">
                      <button 
                        onClick={() => togglePublish(post)}
                        className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-md transition-colors ${
                          post.is_published ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                        }`}
                        title="Click to toggle"
                      >
                        {post.is_published ? 'Published' : 'Draft'}
                      </button>
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-500 flex items-center gap-1">
                      <Eye size={14} className="text-gray-400" /> {post.view_count || 0}
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap text-sm font-medium text-right">
                      <div className="flex justify-end space-x-4">
                         <button onClick={() => openMediaManager(post)} className="text-blue-600 hover:text-blue-800 transition-colors" title="Manage Media">
                            <ImageIcon className="w-5 h-5" />
                         </button>
                         <button onClick={() => openEditor(post)} className="text-gray-500 hover:text-gray-800 transition-colors" title="Edit Article">
                            <Edit className="w-5 h-5" />
                         </button>
                         <button onClick={() => handleDeletePost(post.slug)} className="text-red-500 hover:text-red-700 transition-colors" title="Delete Article">
                            <Trash2 className="w-5 h-5" />
                         </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Editor Dialog */}
      {isEditorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 shrink-0">
              <h2 className="text-xl font-bold text-gray-900">{editingPost ? 'Edit Article' : 'Create New Article'}</h2>
              <button onClick={() => setIsEditorOpen(false)} className="text-gray-400 hover:text-gray-500 transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Article Title *</label>
                  <input type="text" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                    <option value="general">General</option>
                    <option value="law_enforcement">Law Enforcement</option>
                    <option value="technology">Technology</option>
                    <option value="ai">Artificial Intelligence</option>
                    <option value="legal_updates">Legal Updates</option>
                    <option value="training">Training & Education</option>
                    <option value="policy">Policy & Procedure</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma separated)</label>
                  <input type="text" value={formData.tags} onChange={e => setFormData({...formData, tags: e.target.value})} placeholder="news, update" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Excerpt / Summary</label>
                <textarea rows={2} value={formData.excerpt} onChange={e => setFormData({...formData, excerpt: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Article Content (Markdown supported) *</label>
                <textarea rows={10} value={formData.content} onChange={e => setFormData({...formData, content: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm" required />
              </div>

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={formData.is_published} onChange={e => setFormData({...formData, is_published: e.target.checked})} className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4" />
                  Publish immediately
                </label>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={formData.is_featured} onChange={e => setFormData({...formData, is_featured: e.target.checked})} className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4" />
                  Feature on homepage
                </label>
              </div>

              <div className="pt-4 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Cover Image</h3>
                <input type="file" accept="image/*" onChange={e => setCoverImage(e.target.files[0])} className="w-full text-sm py-1.5 px-2 border border-gray-300 rounded-lg file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-gray-100 file:text-gray-700" />
                <p className="text-xs text-gray-400 mt-1">This image will appear as the main preview card on the blog list.</p>
              </div>

              <div className="pt-4 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Attach Media (Optional)</h3>
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                  <div className="md:col-span-3">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
                    <select value={editorMedia.type} onChange={e => setEditorMedia({...editorMedia, type: e.target.value, file: null, url: ''})} className="w-full text-sm py-2 px-3 border border-gray-300 rounded-lg">
                      <option value="image">Image Upload</option>
                      <option value="video">Video Upload</option>
                      <option value="video_url">Video Embed URL</option>
                    </select>
                  </div>
                  
                  <div className="md:col-span-5">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Source</label>
                    {editorMedia.type === 'video_url' ? (
                      <input type="url" placeholder="https://youtube.com/..." value={editorMedia.url} onChange={e => setEditorMedia({...editorMedia, url: e.target.value})} className="w-full text-sm py-2 px-3 border border-gray-300 rounded-lg" />
                    ) : (
                      <input type="file" accept={editorMedia.type === 'image' ? 'image/*' : 'video/*'} onChange={e => setEditorMedia({...editorMedia, file: e.target.files[0]})} className="w-full text-sm py-1.5 px-2 border border-gray-300 rounded-lg file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-gray-100 file:text-gray-700" />
                    )}
                  </div>

                  <div className="md:col-span-4">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Caption</label>
                    <input type="text" placeholder="Caption..." value={editorMedia.caption} onChange={e => setEditorMedia({...editorMedia, caption: e.target.value})} className="w-full text-sm py-2 px-3 border border-gray-300 rounded-lg" />
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 shrink-0 flex justify-end gap-3 bg-gray-50/50 rounded-b-xl">
              <button onClick={() => setIsEditorOpen(false)} className="px-5 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-white transition-colors">Cancel</button>
              <button onClick={handleSavePost} disabled={saving || !formData.title || !formData.content} className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50">
                {saving ? 'Saving...' : 'Save Article'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Media Manager Dialog */}
      {isMediaOpen && activeMediaPost && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 shrink-0 bg-gray-50 rounded-t-xl">
              <div>
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2"><ImageIcon className="text-blue-600" /> Manage Media</h2>
                <p className="text-sm text-gray-500 mt-0.5 truncate max-w-md">{activeMediaPost.title}</p>
              </div>
              <button onClick={() => setIsMediaOpen(false)} className="text-gray-400 hover:text-gray-500 transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 bg-gray-50/30">
              {/* Upload Section */}
              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm mb-6">
                <h3 className="font-semibold text-gray-900 mb-4 text-sm uppercase tracking-wide">Add New Media</h3>
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                  <div className="md:col-span-3">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
                    <select value={mediaType} onChange={e => {setMediaType(e.target.value); setMediaFile(null); setMediaUrl('');}} className="w-full text-sm py-2 px-3 border border-gray-300 rounded-lg">
                      <option value="image">Image Upload</option>
                      <option value="video">Video Upload</option>
                      <option value="video_url">Video Embed URL</option>
                    </select>
                  </div>
                  
                  <div className="md:col-span-5">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Source</label>
                    {mediaType === 'video_url' ? (
                      <input type="url" placeholder="https://youtube.com/..." value={mediaUrl} onChange={e => setMediaUrl(e.target.value)} className="w-full text-sm py-2 px-3 border border-gray-300 rounded-lg" />
                    ) : (
                      <input type="file" accept={mediaType === 'image' ? 'image/*' : 'video/*'} onChange={e => setMediaFile(e.target.files[0])} className="w-full text-sm py-1.5 px-2 border border-gray-300 rounded-lg file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-gray-100 file:text-gray-700" />
                    )}
                  </div>

                  <div className="md:col-span-4">
                    <label className="block text-xs font-medium text-gray-500 mb-1">Caption (Optional)</label>
                    <div className="flex gap-2">
                      <input type="text" placeholder="Caption..." value={mediaCaption} onChange={e => setMediaCaption(e.target.value)} className="flex-1 text-sm py-2 px-3 border border-gray-300 rounded-lg" />
                      <button onClick={handleUploadMedia} disabled={uploadingMedia || (mediaType === 'video_url' ? !mediaUrl : !mediaFile)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 shrink-0">
                        {uploadingMedia ? <Loader2 size={16} className="animate-spin" /> : 'Add'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Gallery Section */}
              <h3 className="font-semibold text-gray-900 mb-4 text-sm uppercase tracking-wide">Attached Media</h3>
              {mediaLoading ? (
                <div className="py-10 text-center"><Loader2 className="animate-spin mx-auto text-blue-600" /></div>
              ) : postMedia.length === 0 ? (
                <div className="text-center py-10 bg-white border border-gray-200 border-dashed rounded-xl text-gray-500">No media attached to this post yet.</div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {postMedia.map(m => (
                    <div key={m.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden group relative">
                      <div className="aspect-video bg-gray-100 relative">
                        {m.media_type === 'image' && <img src={resolveUrl(m.url)} alt={m.caption} className="w-full h-full object-cover" />}
                        {m.media_type === 'video' && <div className="absolute inset-0 flex items-center justify-center"><Video className="text-gray-400 w-8 h-8" /></div>}
                        {m.media_type === 'video_url' && <div className="absolute inset-0 flex items-center justify-center"><LinkIcon className="text-gray-400 w-8 h-8" /></div>}
                        
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <button onClick={() => handleDeleteMedia(m.id)} className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600 shadow-lg">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      <div className="p-2 text-xs truncate text-gray-600" title={m.caption || m.media_type}>
                        {m.caption || m.media_type.toUpperCase()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
