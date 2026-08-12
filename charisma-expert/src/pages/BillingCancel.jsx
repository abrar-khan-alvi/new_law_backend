import { Link } from 'react-router-dom'
import { XCircle } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'

export default function BillingCancel() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="max-w-md w-full text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <XCircle className="text-gray-400" size={36} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Checkout cancelled</h1>
          <p className="text-gray-500 mb-8">
            No changes were made to your subscription. You can try again whenever you're ready.
          </p>
          <Link
            to="/pricing"
            className="inline-block bg-navy-800 text-white font-semibold px-6 py-3 rounded-xl hover:bg-navy-700 transition-colors"
          >
            Back to Pricing
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  )
}
