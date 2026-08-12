import { Play, Clock } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const videos = [
  {
    id: 1,
    category: 'Educational',
    categoryColor: 'text-yellow-500',
    duration: '04:15',
    title: 'Platform Overview: Secure AI for Law Enforcement',
    description:
      'A high-level overview of KLYVOREK, its document workflows, review controls, and core AI-assisted drafting features.',
    image: '/assets/secure_ai_platform_overview_1781562290869.png',
  },
  {
    id: 2,
    category: 'Instructional',
    categoryColor: 'text-yellow-500',
    duration: '06:30',
    title: 'Tutorial: Generating an Incident Report',
    description:
      'Step-by-step instructions on using the AI Incident Report module, from fact input to final PDF export.',
    image: '/assets/incident_report_tutorial_1781562302058.png',
  },
  {
    id: 3,
    category: 'Informational',
    categoryColor: 'text-yellow-500',
    duration: '08:45',
    title: 'Understanding Data Privacy and Security Controls',
    description:
      'An overview of access controls, audit logging, deployment responsibilities, and model-provider data considerations.',
    image: '/assets/data_privacy_cjis_1781562313066.png',
  },
]

export default function Videos() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Header */}
      <section className="pt-16 pb-8 bg-white text-center px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">Video Library</h1>
        <p className="text-gray-500 max-w-xl mx-auto">
          Educational and instructional content to help your department use KLYVOREK responsibly and effectively.
        </p>
      </section>

      {/* Videos Grid */}
      <section className="py-10 bg-white flex-1">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {videos.map((video) => (
              <div key={video.id} className="rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow group">
                {/* Thumbnail */}
                <div className="relative h-48 cursor-pointer overflow-hidden">
                  <img src={video.image} alt={video.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  <div className="absolute inset-0 bg-black/10 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                    <button className="w-14 h-14 rounded-full bg-white/20 border-2 border-white/50 flex items-center justify-center backdrop-blur-sm group-hover:bg-white/40 transition-colors shadow-lg">
                      <Play size={22} className="text-white fill-white ml-1" />
                    </button>
                  </div>
                  <div className="absolute bottom-3 right-3 flex items-center gap-1 text-white text-xs bg-black/50 px-2 py-1 rounded-md backdrop-blur-md shadow-sm">
                    <Clock size={11} />
                    {video.duration}
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  <p className={`text-xs font-semibold ${video.categoryColor} mb-2`}>{video.category}</p>
                  <h3 className="font-bold text-gray-900 text-lg mb-2 leading-snug">{video.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{video.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
