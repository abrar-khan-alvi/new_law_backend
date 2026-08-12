import { Link } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

export default function BillingSuccess() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-md w-full text-center">
          <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="text-emerald-500" size={36} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Subscription confirmed</h1>
          <p className="text-gray-500 mb-8">
            Your plan is active. It may take a few seconds for the change to reflect on your account.
          </p>
          <Link
            to="/dashboard"
            className="inline-block bg-navy-800 text-white font-semibold px-6 py-3 rounded-xl hover:bg-navy-700 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  )
}
