import { useState } from 'react'
import { Mail, Phone, MapPin } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { sendContactMessage } from '../api/contact'

const contactInfo = [
  {
    icon: <Mail size={20} />,
    title: 'Email Us',
    lines: ['klyvorek@gmail.com'],
  },
  {
    icon: <Phone size={20} />,
    title: 'Call Us',
    lines: ['1-678-698-3386', 'Mon-Fri, 0800 - 1700 EST'],
  },
  {
    icon: <MapPin size={20} />,
    title: 'Headquarters',
    lines: ['Metro Atlanta, Georgia 30106'],
  },
]

export default function Contact() {
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    agency: '',
    email: '',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await sendContactMessage(form)
      setSubmitted(true)
    } catch (err) {
      setError(err.response?.data?.error?.detail || 'Unable to send your message right now. Please email klyvorek@gmail.com directly.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <section className="flex-1 py-16 bg-white">
        <div className="w-full px-6 lg:px-10 xl:px-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-14">
            {/* Left: Contact Info */}
            <div>
              <h1 className="text-4xl font-extrabold text-gray-900 mb-4">Get in Touch</h1>
              <p className="text-gray-500 mb-10 leading-relaxed">
                Interested in deploying KLYVOREK at your agency? Have questions about document workflows or security controls? Our team is ready to assist.
              </p>

              <div className="space-y-7">
                {contactInfo.map(({ icon, title, lines }) => (
                  <div key={title} className="flex items-start gap-4">
                    <div className="w-11 h-11 rounded-xl border border-gray-200 flex items-center justify-center text-gray-600 shrink-0">
                      {icon}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 mb-1">{title}</p>
                      {lines.map((line) => (
                        <p key={line} className="text-sm text-gray-500">{line}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Form */}
            <div className="border border-gray-200 rounded-2xl shadow-sm p-8">
              {submitted ? (
                <div className="text-center py-10">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Mail size={28} className="text-green-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Message Sent!</h3>
                  <p className="text-gray-500 text-sm">
                    Thank you for reaching out. Our team will contact you within 1–2 business days.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-5">
                  {error && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                      {error}
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1.5">
                        First Name
                      </label>
                      <input
                        id="firstName"
                        name="firstName"
                        type="text"
                        value={form.firstName}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-navy-400"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1.5">
                        Last Name
                      </label>
                      <input
                        id="lastName"
                        name="lastName"
                        type="text"
                        value={form.lastName}
                        onChange={handleChange}
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-navy-400"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="agency" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Agency / Department
                    </label>
                    <input
                      id="agency"
                      name="agency"
                      type="text"
                      value={form.agency}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-navy-400"
                    />
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Official Email Address
                    </label>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      value={form.email}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-navy-400"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Message
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows={5}
                      value={form.message}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-navy-400 resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    id="contact-submit-btn"
                    disabled={submitting}
                    className="w-full bg-navy-800 hover:bg-navy-700 text-white font-semibold py-3.5 rounded-xl transition-colors disabled:opacity-60"
                  >
                    {submitting ? 'Sending...' : 'Send Message'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
