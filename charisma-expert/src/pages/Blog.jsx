import { useState, useEffect } from 'react'
import { Search, ChevronRight, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { listPosts, listTags } from '../api/blog'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const resolveUrl = (url) => url?.startsWith('/') ? `${BASE_URL}${url}` : url;

export default function Blog() {
  const [posts, setPosts] = useState([])
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)

  const [activeTag, setActiveTag] = useState('')
  const [search, setSearch] = useState('')
  const [mediaMap, setMediaMap] = useState({})

  // Fetch initial data
  useEffect(() => {
    Promise.all([
      listPosts({ page: 1 }),
      listTags()
    ]).then(([postsRes, tagsRes]) => {
      setPosts(postsRes.data.results || postsRes.data)
      setTags(tagsRes.data)
    }).catch(err => {
      console.error('Failed to load blog data', err)
    }).finally(() => {
      setLoading(false)
    })
  }, [])

  // Handle filtering
  useEffect(() => {
    if (loading) return; // Don't trigger search on initial load
    const debounce = setTimeout(() => {
      setLoading(true)
      const params = { page: 1 }
      if (search) params.search = search
      if (activeTag) params.tag = activeTag
      
      listPosts(params)
        .then(({ data }) => setPosts(data.results || data))
        .catch(() => {})
        .finally(() => setLoading(false))
    }, 500)
    
    return () => clearTimeout(debounce)
  }, [search, activeTag]) // Removed 'loading' from dependencies so we don't loop

  // Fallback for posts without cover_image_url
  useEffect(() => {
    import('../api/blog').then(({ getPost }) => {
      posts.forEach(post => {
        if (!post.cover_image_url && mediaMap[post.slug] === undefined) {
          // Mark as fetching to avoid duplicate requests
          setMediaMap(prev => ({ ...prev, [post.slug]: null }));
          getPost(post.slug).then(res => {
            const fullPost = res.data;
            if (fullPost.media && fullPost.media.length > 0) {
              const coverMedia = fullPost.media.find(m => m.caption === 'Cover Image') || fullPost.media.find(m => m.media_type === 'image');
              if (coverMedia) {
                setMediaMap(prev => ({ ...prev, [post.slug]: coverMedia.url }));
              }
            }
          }).catch(() => {});
        }
      });
    });
  }, [posts, mediaMap]);

  const categoryColors = {
    'AI Technology Integrations': 'bg-gray-900 text-white',
    'Legal Updates & Policy': 'bg-gray-800 text-white',
    'Law Enforcement Operations': 'bg-gray-700 text-white',
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Header */}
      <section className="pt-16 pb-8 bg-white text-center px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">Resources & Insights</h1>
        <p className="text-gray-500 max-w-xl mx-auto">
          Expert perspectives on law enforcement operations, AI technology, and legal policy.
        </p>
      </section>

      {/* Filters */}
      <section className="bg-white pb-8">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            {/* Tag pills */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setActiveTag('')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  activeTag === ''
                    ? 'bg-gray-900 text-white'
                    : 'border border-gray-300 text-gray-700 hover:border-gray-500'
                }`}
              >
                All
              </button>
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => setActiveTag(tag.slug)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    activeTag === tag.slug
                      ? 'bg-gray-900 text-white'
                      : 'border border-gray-300 text-gray-700 hover:border-gray-500'
                  }`}
                >
                  {tag.name}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search articles..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-xl w-56 focus:outline-none focus:ring-2 focus:ring-navy-400"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Articles Grid */}
      <section className="py-8 bg-white flex-1">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="animate-spin text-blue-600" size={40} />
            </div>
          ) : posts.length === 0 ? (
             <div className="text-center text-gray-400 py-16">No articles found matching your criteria.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {posts.map((post) => (
                <Link to={`/blog/${post.slug}`} key={post.slug} className="rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow flex flex-col group block">
                  {/* Image */}
                  <div className="h-48 relative group-hover:opacity-90 transition-opacity overflow-hidden bg-gray-100">
                    {(post.cover_image_url || mediaMap[post.slug]) ? (
                       <img src={resolveUrl(post.cover_image_url || mediaMap[post.slug])} alt={post.title} className="w-full h-full object-cover" />
                    ) : (
                       <div className="w-full h-full flex items-center justify-center text-gray-400 font-medium bg-gray-100">No Image</div>
                    )}
                    {post.category && (
                      <span className={`absolute top-3 left-3 text-xs font-semibold px-2.5 py-1 rounded-full ${categoryColors[post.category?.name] || 'bg-gray-800 text-white'} shadow-md`}>
                        {post.category.name}
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-5 flex-1 flex flex-col">
                    <p className="text-xs text-gray-400 mb-2">
                      {new Date(post.published_at || post.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>
                    <h3 className="font-bold text-gray-900 text-lg mb-2 leading-snug group-hover:text-blue-600 transition-colors">{post.title}</h3>
                    <p className="text-sm text-gray-500 mb-4 leading-relaxed flex-1 line-clamp-3">
                      {post.excerpt || (post.content ? post.content.replace(/<[^>]+>/g, '').substring(0, 150) + '...' : '')}
                    </p>
                    <div className="flex items-center justify-between mt-auto">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-500">
                          {post.author_name ? post.author_name.charAt(0).toUpperCase() : 'A'}
                        </div>
                        <span className="text-sm text-gray-600">{post.author_name || 'Admin'}</span>
                      </div>
                      <span className="text-gray-400 group-hover:text-blue-600 transition-colors">
                        <ChevronRight size={18} />
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      <Footer />
    </div>
  )
}
