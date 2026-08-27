import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const faqs = [
  {
    id: 1,
    question: 'What is KLYVOREK?',
    answer:
      "KLYVOREK is AI-assisted documentation software built for law enforcement. It helps officers and investigators turn the facts they provide into clear, structured incident reports and drafts of search and arrest warrant applications. KLYVOREK assists with documentation; it does not replace the officer's judgment, investigation, or responsibility for the final document.",
  },
  {
    id: 2,
    question: 'How does KLYVOREK help law enforcement personnel?',
    answer:
      'KLYVOREK helps reduce the friction between doing police work and documenting it. Officers provide the facts and information from the incident or investigation, and KLYVOREK helps organize that information into a clearer, more professional draft for review.',
  },
  {
    id: 3,
    question: 'Can KLYVOREK invent or change facts in a report?',
    answer:
      'It should not, and officers should never assume that any AI-generated draft is automatically accurate. KLYVOREK is designed to work from information supplied by the user, not to create facts, evidence, observations, statements, charges, or probable cause. Because AI systems can produce errors, officers must carefully review every generated document against the original facts before using it.',
  },
  {
    id: 4,
    question: 'Does the officer remain responsible for the final report?',
    answer:
      "Yes. KLYVOREK produces a draft based on user-provided information. The officer or other authorized personnel must review the document, verify the facts, make necessary corrections, and determine whether the final document accurately reflects what occurred. KLYVOREK does not replace officer judgment, supervisory review, prosecutor review, judicial review, or agency policy.",
  },
  {
    id: 5,
    question: 'What training is required to use KLYVOREK?',
    answer:
      'KLYVOREK is designed to be straightforward and require minimal technical training. An officer does not need to understand prompt engineering or become an AI expert. Agencies should still provide appropriate training regarding their own policies, authorized use, information security, legal requirements, and review procedures.',
  },
  {
    id: 6,
    question: 'Is KLYVOREK CJIS compliant?',
    answer:
      "KLYVOREK includes role-based access, audit logging, secure authentication, and production HTTPS controls. Formal CJIS compliance is deployment- and agency-specific and should not be assumed without a completed assessment and documented controls.",
  },
  {
    id: 7,
    question: "Will our department's case data be used to train public AI models?",
    answer:
      "KLYVOREK does not intentionally use submitted case facts to train its application models. Data handling still depends on the configured inference and storage providers, so agency administrators should review those provider terms and retention controls.",
  },
  {
    id: 8,
    question: 'How accurate are the generated legal documents?',
    answer:
      "Generated content is a draft, not a legal determination. The responsible officer must verify every fact, citation, required element, and signature before operational or legal use. Supervisor or prosecutor review may be recorded as optional oversight but is not required by KLYVOREK for export.",
  },
  {
    id: 9,
    question: "Does KLYVOREK replace an officer's RMS or agency records system?",
    answer:
      "No. KLYVOREK is an AI-assisted documentation tool. It helps prepare and structure drafts for authorized review. The agency's approved records, case-management, warrant, and filing procedures remain controlling.",
  },
  {
    id: 10,
    question: 'What happens if a user hits their monthly document save limit?',
    answer:
      "When a plan's generation limit is reached, new generations pause until the monthly reset or a plan upgrade. Existing documents remain available according to the user's plan and account status.",
  },
  {
    id: 11,
    question: 'Can an agency cancel its subscription, and what happens to its data?',
    answer:
      'An agency should be able to cancel its KLYVOREK subscription according to the terms of its plan. After cancellation, account access ends according to the subscription terms. KLYVOREK handles retained or deleted account data according to its Privacy Policy and applicable data-retention requirements.',
  },
  {
    id: 12,
    question: 'Can we integrate this with our existing RMS (Records Management System)?',
    answer:
      "KLYVOREK does not currently provide direct RMS integration. Agencies interested in integration may contact us to discuss requirements and supported export formats.",
  },
]

function FAQItem({ faq }) {
  const [open, setOpen] = useState(faq.id === 1)

  return (
    <div className="border border-gray-200 rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-5 text-left bg-white hover:bg-gray-50 transition-colors"
        aria-expanded={open}
        id={`faq-btn-${faq.id}`}
      >
        <span className="font-semibold text-gray-900 pr-8">{faq.question}</span>
        {open ? (
          <ChevronUp size={18} className="text-gray-500 shrink-0" />
        ) : (
          <ChevronDown size={18} className="text-gray-500 shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-6 pb-5 bg-white">
          <p className="text-gray-600 text-sm leading-relaxed">{faq.answer}</p>
        </div>
      )}
    </div>
  )
}

export default function FAQ() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Header */}
      <section className="pt-16 pb-8 bg-white text-center px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-3">Frequently Asked Questions</h1>
        <p className="text-gray-500 max-w-lg mx-auto">
          Answers about KLYVOREK's role, officer responsibility, AI-assisted drafting, security, billing, and agency use.
        </p>
      </section>

      {/* FAQ Accordion */}
      <section className="py-10 bg-white flex-1">
        <div className="w-full max-w-2xl mx-auto px-6 lg:px-10 xl:px-16 space-y-4">
          {faqs.map((faq) => (
            <FAQItem key={faq.id} faq={faq} />
          ))}
        </div>
      </section>

      {/* CTA link to pricing */}
      <div className="text-center py-12 bg-white">
        <p className="text-gray-500 mb-2">Have more questions about billing or compliance?</p>
        <Link to="/pricing" className="font-semibold text-gray-900 hover:text-blue-600 transition-colors">
          View our Pricing Plans →
        </Link>
      </div>

      <Footer />
    </div>
  )
}
