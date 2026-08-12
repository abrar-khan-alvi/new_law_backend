import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Eye, EyeOff, X, Loader2 } from 'lucide-react'
import * as authApi from '../api/auth'

export default function SetNewPassword() {
  const navigate = useNavigate()
  const location = useLocation()
  // email and OTP code are forwarded through state from OTPVerify
  const { email, code } = location.state || {}

  const [form, setForm] = useState({ newPassword: '', confirmPassword: '' })
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    if (error) setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.newPassword !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await authApi.confirmPasswordReset({
        email,
        code,
        new_password: form.newPassword,
      })
      navigate('/login', { state: { passwordReset: true } })
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.detail ||
        err?.response?.data?.error?.detail ||
        'Failed to reset password. Please start over.'
      setError(typeof msg === 'string' ? msg : 'Failed to reset password. Please start over.')
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
          id="reset-close-btn"
        >
          <X size={22} />
        </button>

        <h1 className="text-3xl font-bold text-center text-blue-600 mb-2">Set a new password</h1>
        <p className="text-center text-gray-700 font-medium mb-8">
          Create a new password. Ensure it differs from previous ones for security.
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="new-password" className="block text-sm font-semibold text-gray-800 mb-2">
              New Password
            </label>
            <div className="relative">
              <input
                id="new-password"
                name="newPassword"
                type={showNew ? 'text' : 'password'}
                placeholder="Enter Password"
                value={form.newPassword}
                onChange={handleChange}
                className="input-field pr-12"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Toggle new password visibility"
              >
                {showNew ? <Eye size={18} /> : <EyeOff size={18} />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirm-password" className="block text-sm font-semibold text-gray-800 mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <input
                id="confirm-password"
                name="confirmPassword"
                type={showConfirm ? 'text' : 'password'}
                placeholder="Enter Password"
                value={form.confirmPassword}
                onChange={handleChange}
                className="input-field pr-12"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Toggle confirm password visibility"
              >
                {showConfirm ? <Eye size={18} /> : <EyeOff size={18} />}
              </button>
            </div>
          </div>

          <button
            id="reset-submit-btn"
            type="submit"
            disabled={loading}
            className="btn-blue-gradient w-full py-4 text-base flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'Updating…' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
