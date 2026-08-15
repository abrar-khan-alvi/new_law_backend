import { Shield, Target, BookOpen, Users } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const values = [
  {
    icon: <Shield size={28} strokeWidth={1.5} />,
    title: 'Access Controlled',
    desc: 'Role-based document and administrative permissions.',
  },
  {
    icon: <Target size={28} strokeWidth={1.5} />,
    title: 'Purpose Built',
    desc: 'Structured workflows for incident and warrant application drafts.',
  },
  {
    icon: <BookOpen size={28} strokeWidth={1.5} />,
    title: 'Review Centered',
    desc: 'Authorized people remain responsible for every document.',
  },
  {
    icon: <Users size={28} strokeWidth={1.5} />,
    title: 'Officer First',
    desc: 'Designed to reduce fatigue and burnout.',
  },
]

export default function About() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero */}
      <section className="relative py-24 bg-navy-800 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-navy-900/60 to-navy-800/80" />
        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-6 leading-tight">
            Advancing Law Enforcement Through Secure AI
          </h1>
          <p className="text-gray-300 max-w-2xl mx-auto text-lg leading-relaxed">
            KLYVOREK helps authorized law enforcement personnel turn structured, officer-provided facts into reviewable document drafts.
          </p>
        </div>
      </section>

      {/* Vision + Values */}
      <section className="py-20 bg-white">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
            {/* Vision text */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-5">Our Vision</h2>
              <p className="text-gray-600 mb-4 leading-relaxed">
                We believe that law enforcement officers should spend their time protecting communities, not battling administrative paperwork.
              </p>
              <p className="text-gray-600 leading-relaxed">
                By providing specialized, isolated AI models trained on legal and operational frameworks, we empower agencies to generate accurate, court-ready documentation in a fraction of the time it takes with traditional methods, without ever compromising data security.
              </p>
            </div>

            {/* Values grid */}
            <div className="grid grid-cols-2 gap-4">
              {values.map(({ icon, title, desc }) => (
                <div key={title} className="border border-gray-200 rounded-2xl p-5 text-center hover:shadow-md transition-shadow">
                  <div className="flex justify-center mb-3 text-navy-800">{icon}</div>
                  <h3 className="font-bold text-gray-900 text-sm mb-1">{title}</h3>
                  <p className="text-xs text-gray-500">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Founder story */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 lg:px-8">
          <p className="section-tag text-blue-600 mb-2">About KLYVOREK</p>
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Built From a Problem Seen in the Real World</h2>
          <div className="space-y-5 text-gray-600 leading-relaxed bg-white border border-gray-100 rounded-2xl p-8 shadow-sm">
            <p>KLYVOREK began with a simple observation. While serving as a police sergeant with a metro Atlanta (Georgia) law enforcement agency, Sergeant Edward Brown regularly reviewed reports written by officers and dispatchers. Important details were sometimes missing, grammar was inconsistent, and narratives did not always reflect the professionalism of the people doing the work.</p>
            <p>A police report is more than paperwork. It is a permanent legal document that may later be reviewed by prosecutors, attorneys, judges, juries, and the public. What is omitted or poorly explained can create unnecessary questions and potential liability.</p>
            <p>General-purpose AI tools, like ChatGPT, Google Gemini, and Claude, raised another concern: sensitive law enforcement information should not be entered into platforms that an agency has not approved for handling that information, nor are those platforms secure. Existing report-writing systems could also be complicated, expensive, or too broad for everyday law enforcement documentation.</p>
            <p>Brown partnered with an experienced AI and web-development team to create KLYVOREK around three principles: <strong>Secure by Design. Simple to Use. Affordable to Deploy.</strong></p>
            <p>KLYVOREK helps law enforcement personnel turn officer-provided facts into clear incident reports, organized investigative documentation, and structured drafts of arrest and search warrant applications, while keeping the officer in control.</p>
            <p className="font-semibold text-gray-900">KLYVOREK was created because law enforcement needed technology that better understood the documentation work they do.</p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
