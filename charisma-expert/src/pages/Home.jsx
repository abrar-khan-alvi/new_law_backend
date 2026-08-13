import { Link } from 'react-router-dom'
import { Shield, Lock, Server, Zap, CheckCircle, FileText, Search, BookOpen } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const modules = [
  {
    icon: <FileText size={28} className="text-blue-600" />,
    iconBg: 'bg-blue-50',
    title: 'Incident Report Drafts',
    description:
      'Enter structured incident facts and generate a clear, chronological narrative for officer review and revision.',
  },
  {
    icon: <Search size={28} className="text-yellow-500" />,
    iconBg: 'bg-yellow-50',
    title: 'Search Warrant Applications',
    description:
      'Organize probable-cause facts, places, property, and requested authority in an agency-configured draft for review.',
  },
  {
    icon: <BookOpen size={28} className="text-teal-500" />,
    iconBg: 'bg-teal-50',
    title: 'Arrest Warrant Applications',
    description:
      'Structure offense, subject, evidence, and probable-cause information supplied by the officer into a reviewable application draft.',
  },
]

const whyPoints = [
  {
    icon: <Lock size={20} className="text-blue-600" />,
    title: 'Controlled Access',
    desc: 'Role-based permissions restrict document access to owners, authorized reviewers, and administrators.',
  },
  {
    icon: <Server size={20} className="text-blue-600" />,
    title: 'Auditable Workflows',
    desc: 'Generation, access, export, and administrative actions are recorded for operational accountability.',
  },
  {
    icon: <Zap size={20} className="text-blue-600" />,
    title: 'Operational Efficiency',
    desc: 'Structured intake and reusable agency configuration reduce repetitive drafting work.',
  },
  {
    icon: <CheckCircle size={20} className="text-blue-600" />,
    title: 'Human Review by Design',
    desc: 'Generated content remains a draft under officer, supervisor, prosecutor, and judicial review as applicable.',
  },
]

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero — full viewport height minus navbar (h-16 = 64px) */}
      <section className="relative flex items-center overflow-hidden bg-gray-900" style={{ minHeight: 'calc(100vh - 64px)' }}>
        <img
          src="/assets/home.png"
          alt="Police officer using the KLYVOREK platform"
          className="absolute inset-0 w-full h-full object-cover object-top opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-gray-900/85 via-gray-900/50 to-transparent" />
        <div className="relative z-10 w-full px-6 lg:px-10 xl:px-16 py-24">
          <div className="max-w-2xl xl:max-w-3xl">
            {/* Badge */}
            <span className="inline-flex items-center gap-2 bg-yellow-400/20 border border-yellow-400/40 text-yellow-300 text-sm font-semibold px-4 py-2 rounded-full mb-8">
              <Shield size={14} />
              Officer-Controlled AI Assistance
            </span>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-white leading-tight mb-8 tracking-tight">
              Turn Officer-Provided Facts<br />Into Clear, Structured<br />Reports
            </h1>
            <p className="text-gray-300 text-lg sm:text-xl lg:text-2xl leading-relaxed mb-10 max-w-2xl">
              Create incident reports and structured warrant application drafts using your agency information and the facts you provide. Every document remains under authorized human review.
            </p>


            <div className="flex flex-wrap gap-3">
              <Link
                to="/signup"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-7 py-3 rounded-lg transition-colors"
              >
                Create My First Report Free
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Core Modules */}
      <section className="py-20 bg-white">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          <div className="text-center mb-12">
            <p className="section-tag text-blue-600 mb-2">Drafting Workflows</p>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">From Structured Facts to Reviewable Draft</h2>
            <p className="text-gray-500 max-w-xl mx-auto">
              KLYVOREK organizes officer-provided information while keeping accuracy, legal sufficiency, approval, and submission under human control.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {modules.map(({ icon, iconBg, title, description }) => (
              <div key={title} className="card">
                <div className={`${iconBg} w-12 h-12 rounded-xl flex items-center justify-center mb-4`}>
                  {icon}
                </div>
                <h3 className="font-bold text-gray-900 mb-2 text-lg">{title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Specialized AI Matters */}
      <section className="py-20 bg-gray-50">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                AI Assistance Without Surrendering{' '}
                <span className="text-blue-600">Professional Judgment</span>
              </h2>
              <p className="text-gray-500 mb-8 leading-relaxed">
                KLYVOREK combines structured intake, configurable agency information, review workflows, and audit logging. Generated content is a draft and must be checked by authorized personnel before use.
              </p>
              <ul className="space-y-5">
                {whyPoints.map(({ icon, title, desc }) => (
                  <li key={title} className="flex items-start gap-4">
                    <span className="mt-0.5 shrink-0">{icon}</span>
                    <div>
                      <p className="font-semibold text-gray-900">{title}</p>
                      <p className="text-sm text-gray-500 mt-0.5">{desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl overflow-hidden shadow-xl">
              <img
                src="/assets/why_specialized_aI_matters.png"
                alt="Police officer reviewing a KLYVOREK document draft"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="bg-slate-50 py-20 px-6" aria-labelledby="demo-heading">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-10">
            <p className="text-blue-700 font-semibold uppercase tracking-wider text-sm">Fictional product demo</p>
            <h2 id="demo-heading" className="text-3xl sm:text-4xl font-bold text-slate-900 mt-2">See structured facts become a review-ready draft</h2>
            <p className="text-slate-600 mt-4">This example uses invented names and events. KLYVOREK does not independently verify facts or replace agency review.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-4">Officer-entered facts</h3>
              <dl className="space-y-3 text-sm"><div><dt className="font-semibold">Event</dt><dd className="text-slate-600">Fictional vehicle break-in reported at 08:15.</dd></div><div><dt className="font-semibold">Location</dt><dd className="text-slate-600">100 Example Street, Sample City.</dd></div><div><dt className="font-semibold">Officer action</dt><dd className="text-slate-600">Photographed damage and collected a witness statement.</dd></div></dl>
            </div>
            <div className="bg-slate-900 text-slate-100 rounded-2xl p-7 shadow-xl">
              <div className="flex justify-between gap-3 mb-4"><h3 className="font-bold">Generated incident narrative</h3><span className="text-xs bg-amber-300 text-amber-950 px-2 py-1 rounded">DRAFT — REVIEW REQUIRED</span></div>
              <p className="text-sm leading-7 text-slate-300">At approximately 0815 hours, I responded to 100 Example Street regarding a reported vehicle break-in. I documented the reported damage, photographed the vehicle, and obtained a statement from the witness.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section
        className="relative overflow-hidden"
        style={{ backgroundColor: '#1a3880', minHeight: '450px' }}
      >
        <div className="flex flex-col lg:flex-row items-center relative min-h-[450px]">
          {/* Left Content */}
          <div className="w-full lg:w-1/2 px-6 lg:px-10 xl:px-16 pt-16 pb-8 lg:py-16 relative z-10">
            <div className="max-w-2xl">
              <h2 className="text-3xl sm:text-4xl font-bold text-white leading-tight mb-4">
                Create your first incident report draft free.
              </h2>
              <p className="text-blue-200 text-base sm:text-lg mb-8">
                No payment card required. Review every draft before operational or legal use.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/signup"
                  className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 sm:px-8 py-3 rounded-lg transition-colors"
                >
                  Create Free Report
                </Link>
                <Link
                  to="/pricing"
                  className="border border-white/40 text-white font-semibold px-6 sm:px-8 py-3 rounded-lg hover:bg-white/10 transition-colors"
                >
                  View Plans
                </Link>
              </div>
            </div>
          </div>

          {/* Right: Aesthetic Mockup */}
          <div className="w-full lg:w-1/2 flex justify-center lg:absolute lg:right-0 lg:top-1/2 lg:-translate-y-1/2 pointer-events-none pb-12 lg:pb-0 z-0">
            <div className="w-full px-6 lg:px-0 flex justify-center lg:block" style={{ maxWidth: '850px' }}>
              <img
                src="/assets/blue_bg_dashboard_mockup_1781562999749.png"
                alt="KLYVOREK platform dashboard on laptop and mobile"
                className="w-full h-auto object-contain transform lg:translate-x-12"
              />
            </div>
          </div>
        </div>
      </section>


      <Footer />
    </div>
  )
}
