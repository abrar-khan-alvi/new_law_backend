import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

const faqs = [
  {
    id: 1,
    question: 'Is KLYVOREK CJIS compliant?',
    answer:
      "KLYVOREK includes role-based access, audit logging, secure authentication, and production HTTPS controls. Formal CJIS compliance is deployment- and agency-specific and should not be assumed without a completed assessment and documented controls.",
  },
  {
    id: 2,
    question: "Will our department's case data be used to train public AI models?",
    answer:
      "KLYVOREK does not intentionally use submitted case facts to train its application models. Data handling still depends on the configured inference and storage providers, so agency administrators should review those provider terms and retention controls.",
  },
  {
    id: 3,
    question: 'How accurate are the generated legal documents?',
    answer:
      "Generated content is a draft, not a legal determination. The responsible officer must verify every fact, citation, required element, and signature before operational or legal use. Supervisor or prosecutor review may be recorded as optional oversight but is not required by KLYVOREK for export.",
  },
  {
    id: 4,
    question: 'What happens if a user hits their monthly document save limit?',
    answer:
      "When a plan's generation limit is reached, new generations pause until the monthly reset or a plan upgrade. Existing documents remain available according to the user's plan and account status.",
  },
  {
    id: 5,
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
          Details on security, training data reliability, and subscription mechanics.
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
