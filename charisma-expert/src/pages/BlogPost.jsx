import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ChevronLeft, Loader2, Calendar, User } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { getPost } from '../api/blog'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const resolveUrl = (url) => url?.startsWith('/') ? `${BASE_URL}${url}` : url;

export default function BlogPost() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    getPost(slug)
      .then(({ data }) => setPost(data))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="animate-spin text-blue-600 w-10 h-10" />
        </div>
        <Footer />
      </div>
    )
  }

  if (error || !post) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Article Not Found</h2>
          <p className="text-gray-500 mb-6">The article you are looking for does not exist or has been removed.</p>
          <Link to="/blog" className="text-blue-600 hover:underline">← Back to Blog</Link>
        </div>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />

      <main className="flex-1 pt-20 pb-16">
        <article className="max-w-3xl mx-auto px-6">
          <Link to="/blog" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 mb-8 transition-colors">
            <ChevronLeft size={16} className="mr-1" />
            Back to articles
          </Link>

          {post.category && (
            <div className="mb-4">
              <span className="text-sm font-semibold text-blue-600 uppercase tracking-wider">
                {post.category.name}
              </span>
            </div>
          )}

          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-6 leading-tight">
            {post.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-10 pb-8 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <User size={16} />
              <span className="font-medium text-gray-700">{post.author_name || 'Admin'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar size={16} />
              <span>{new Date(post.published_at || post.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
            </div>
            {post.tags && post.tags.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap ml-auto">
                {post.tags.map(t => (
                  <span key={t.slug} className="px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
                    {t.name}
                  </span>
                ))}
              </div>
            )}
          </div>

          {post.cover_image_url && (
            <figure className="mb-10 rounded-2xl overflow-hidden shadow-sm border border-gray-100">
              <img src={resolveUrl(post.cover_image_url)} alt={post.title} className="w-full h-auto object-cover max-h-[500px]" />
            </figure>
          )}

          {/* Render Markdown/HTML content with interspersed media */}
          <div 
            className="prose prose-lg prose-blue max-w-none text-gray-800 prose-headings:text-gray-900 prose-a:text-blue-600 prose-p:leading-relaxed"
            dangerouslySetInnerHTML={{ __html: (() => {
              let finalHtml = post.content_html || post.content || '';
              
              // Filter out the cover image from being interspersed in the content
              const inlineMedia = post.media ? post.media.filter(m => m.caption !== 'Cover Image') : [];
              
              if (inlineMedia.length === 0) return finalHtml;

              const renderMediaHtml = (m) => {
                const mediaUrl = resolveUrl(m.url);
                if (m.media_type === 'image') {
                  return `<figure class="my-12 mx-auto"><img src="${mediaUrl}" alt="${m.caption || ''}" class="w-full h-auto rounded-2xl shadow-md object-cover m-0" />${m.caption ? `<figcaption class="text-center text-sm text-gray-500 mt-3 font-medium">${m.caption}</figcaption>` : ''}</figure>`;
                } else if (m.media_type === 'video') {
                  return `<figure class="my-12 mx-auto"><video src="${mediaUrl}" controls class="w-full h-auto rounded-2xl shadow-md bg-black m-0"></video>${m.caption ? `<figcaption class="text-center text-sm text-gray-500 mt-3 font-medium">${m.caption}</figcaption>` : ''}</figure>`;
                } else if (m.media_type === 'video_url') {
                  if (m.embed_html) {
                     return `<div class="my-12 mx-auto aspect-video rounded-2xl overflow-hidden shadow-md">${m.embed_html}</div>`;
                  } else {
                     return `<div class="my-12 mx-auto aspect-video bg-gray-50 border border-gray-100 rounded-2xl flex items-center justify-center shadow-sm"><a href="${m.video_url}" target="_blank" class="text-blue-600 font-medium hover:underline">View Video ↗</a></div>`;
                  }
                }
                return '';
              };

              const parts = finalHtml.split('</p>');
              if (parts.length > 1) {
                const paragraphCount = parts.length - 1;
                const mediaCount = inlineMedia.length;
                const interval = Math.max(1, Math.floor(paragraphCount / (mediaCount + 1)));
                
                let mediaIndex = 0;
                for (let i = 0; i < paragraphCount; i++) {
                  parts[i] = parts[i] + '</p>';
                  if (mediaIndex < mediaCount && (i + 1) % interval === 0) {
                    parts[i] += renderMediaHtml(inlineMedia[mediaIndex]);
                    mediaIndex++;
                  }
                }
                
                // Append any remaining media to the very end
                let leftover = '';
                while (mediaIndex < mediaCount) {
                  leftover += renderMediaHtml(inlineMedia[mediaIndex]);
                  mediaIndex++;
                }
                parts[parts.length - 1] = leftover + parts[parts.length - 1];
                
                return parts.join('');
              } else {
                // If there are no <p> tags, just append all media to the bottom
                return finalHtml + inlineMedia.map(renderMediaHtml).join('');
              }
            })() }}
          />

        </article>
      </main>

      <Footer />
    </div>
  )
}
