import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ChevronLeft, Loader2, Calendar, User } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { getPost } from '../api/blog'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const resolveUrl = (url) => url?.startsWith('/') ? `${BASE_URL}${url}` : url
const categoryLabel = (category) => String(category || 'general').replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase())

const ArticleMedia = ({ media }) => {
  if (media.media_type === 'image') {
    return <figure className="my-12"><img src={resolveUrl(media.url)} alt={media.alt_text || media.caption || ''} loading="lazy" className="w-full rounded-2xl shadow-sm border border-gray-100" />{media.caption && <figcaption className="mt-3 text-center text-sm text-gray-500">{media.caption}</figcaption>}</figure>
  }
  if (media.media_type === 'video') {
    return <figure className="my-12"><video src={resolveUrl(media.url)} controls preload="metadata" className="w-full aspect-video rounded-2xl shadow-sm bg-black" />{media.caption && <figcaption className="mt-3 text-center text-sm text-gray-500">{media.caption}</figcaption>}</figure>
  }
  if (media.media_type === 'video_url' && media.embed_html) {
    return <figure className="my-12"><div className="blog-video-embed aspect-video overflow-hidden rounded-2xl shadow-sm bg-black" dangerouslySetInnerHTML={{ __html: media.embed_html }} />{media.caption && <figcaption className="mt-3 text-center text-sm text-gray-500">{media.caption}</figcaption>}</figure>
  }
  return null
}

export default function BlogPost() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    getPost(slug).then(({ data }) => setPost(data)).catch(() => setError(true)).finally(() => setLoading(false))
  }, [slug])

  if (loading) return <div className="min-h-screen flex flex-col bg-gray-50"><Navbar /><div className="flex-1 flex items-center justify-center"><Loader2 className="animate-spin text-blue-600 w-10 h-10" /></div><Footer /></div>
  if (error || !post) return <div className="min-h-screen flex flex-col bg-gray-50"><Navbar /><div className="flex-1 flex flex-col items-center justify-center px-6 text-center"><h2 className="text-2xl font-bold text-gray-900 mb-2">Article Not Found</h2><p className="text-gray-500 mb-6">The article does not exist or has been removed.</p><Link to="/blog" className="text-blue-600 hover:underline">← Back to Blog</Link></div><Footer /></div>

  const articleMedia = (post.media || []).filter(media => media.caption !== 'Cover Image')
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <main className="flex-1 pt-20 pb-20">
        <article className="max-w-3xl mx-auto px-6">
          <Link to="/blog" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 mb-8"><ChevronLeft size={16} className="mr-1" />Back to articles</Link>
          <div className="mb-4"><span className="text-sm font-semibold text-blue-600 uppercase tracking-wider">{categoryLabel(post.category)}</span></div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-950 mb-6 leading-tight">{post.title}</h1>
          {post.excerpt && <p className="text-xl leading-8 text-gray-600 mb-7">{post.excerpt}</p>}
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-10 pb-8 border-b border-gray-100">
            <div className="flex items-center gap-2"><User size={16} /><span className="font-medium text-gray-700">{post.author_name || 'Klyvorek Editorial Team'}</span></div>
            <div className="flex items-center gap-2"><Calendar size={16} /><span>{new Date(post.published_at || post.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span></div>
          </div>
          {post.cover_image_url && <figure className="mb-12 rounded-2xl overflow-hidden shadow-sm border border-gray-100"><img src={resolveUrl(post.cover_image_url)} alt={post.title} className="w-full max-h-[520px] object-cover" /></figure>}
          <div className="blog-rich-content" dangerouslySetInnerHTML={{ __html: post.content_html || '' }} />
          {articleMedia.map(media => <ArticleMedia key={media.id} media={media} />)}
          {post.tags?.length > 0 && <div className="flex flex-wrap gap-2 mt-14 pt-8 border-t border-gray-100">{post.tags.map(tag => <span key={tag.slug} className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full text-xs font-semibold">{tag.name}</span>)}</div>}
        </article>
      </main>
      <Footer />
    </div>
  )
}
