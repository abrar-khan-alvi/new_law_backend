import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, Loader2 } from 'lucide-react'
import * as authApi from '../api/auth'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await authApi.requestPasswordReset({ email })
      // Pass email and context to OTP page for the reset-confirm call
      navigate('/verify-otp', { state: { fromForgotPassword: true, email } })
    } catch (err) {
      const msg =
        err?.response?.data?.error?.detail ||
        err?.response?.data?.detail ||
        'Something went wrong. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md p-10 relative">
        {/* Close */}
        <button
          onClick={() => navigate('/login')}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 transition-colors"
          aria-label="Close"
          id="forgot-close-btn"
        >
          <X size={22} />
        </button>

        <h1 className="text-3xl font-bold text-center text-blue-600 mb-2">Forgot Password</h1>
        <p className="text-center text-gray-700 font-medium mb-8">
          Enter your account email. We'll send you a 6-digit reset code.
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="forgot-email" className="block text-sm font-semibold text-gray-800 mb-2">
              Email Address
            </label>
            <input
              id="forgot-email"
              name="email"
              type="email"
              placeholder="officer@dept.gov"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError('') }}
              className="input-field"
              required
              disabled={loading}
            />
          </div>

          <button
            id="forgot-send-btn"
            type="submit"
            disabled={loading}
            className="btn-blue-gradient w-full py-4 text-base flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'Sending…' : 'Send Reset Code'}
          </button>
        </form>
      </div>
    </div>
  )
}
