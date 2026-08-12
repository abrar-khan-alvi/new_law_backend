import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Eye, EyeOff, X, Loader2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import GoogleSignInButton from '../components/GoogleSignInButton'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, logout } = useAuth()
  const [form, setForm] = useState({ email: '', password: '', remember: false })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(location.state?.error || '')

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
    if (error) setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await login(form.email, form.password)
      if (data?.user?.role === 'admin') {
        await logout()
        setError('Admin accounts must use the Admin Portal Login page.')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      let detail = 'Invalid credentials. Please try again.'
      if (err?.response?.data) {
        const data = err.response.data
        if (typeof data === 'string') {
          detail = data
        } else if (typeof data === 'object') {
          const errorObj = data.error || data
          if (typeof errorObj === 'string') {
            detail = errorObj
          } else if (typeof errorObj === 'object' && errorObj !== null) {
            const nonField = errorObj.non_field_errors || errorObj.detail
            if (Array.isArray(nonField) && nonField.length > 0) {
              detail = nonField[0]
            } else if (typeof nonField === 'string') {
              detail = nonField
            } else {
              const firstKey = Object.keys(errorObj)[0]
              if (firstKey) {
                const val = errorObj[firstKey]
                if (Array.isArray(val) && val.length > 0) {
                  detail = val[0]
                } else if (typeof val === 'string') {
                  detail = val
                }
              }
            }
          }
        }
      } else if (err?.message) {
        detail = err.message
      }
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleError = (err) => {
    setError(err?.response?.data?.error?.detail || 'Google sign-in failed. Please try again.')
  }



  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md p-10 relative">
        {/* Close */}
        <button
          onClick={() => navigate('/')}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 transition-colors"
          aria-label="Close"
          id="login-close-btn"
        >
          <X size={22} />
        </button>

        <h1 className="text-3xl font-bold text-center text-blue-600 mb-2">Login to Account</h1>
        <p className="text-center text-gray-700 font-medium mb-8">
          Please enter your email and password to continue
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
            {error}
          </div>
        )}

        <GoogleSignInButton onSuccess={() => navigate('/dashboard')} onError={handleGoogleError} />
        <div className="flex items-center gap-3 my-6"><span className="h-px flex-1 bg-gray-200" /><span className="text-xs uppercase text-gray-400">or use email</span><span className="h-px flex-1 bg-gray-200" /></div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="login-email" className="block text-sm font-semibold text-gray-800 mb-2">
              Email
            </label>
            <input
              id="login-email"
              name="email"
              type="email"
              placeholder="officer@dept.gov"
              value={form.email}
              onChange={handleChange}
              className="input-field"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="login-password" className="block text-sm font-semibold text-gray-800 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                id="login-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter Password"
                value={form.password}
                onChange={handleChange}
                className="input-field pr-12"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Toggle password visibility"
              >
                {showPassword ? <Eye size={18} /> : <EyeOff size={18} />}
              </button>
            </div>
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            disabled={loading}
            className="btn-blue-gradient w-full py-4 text-base rounded-xl font-semibold text-white shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed disabled:translate-y-0"
            style={{ background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)' }}
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'Signing in…' : 'Sign In'}
          </button>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                name="remember"
                checked={form.remember}
                onChange={handleChange}
                className="w-4 h-4 rounded accent-blue-600"
                id="remember-me"
              />
              <span className="text-blue-600 font-medium">Remember me ?</span>
            </label>
            <Link to="/forgot-password" className="text-blue-600 font-medium hover:underline">
              Forgot password?
            </Link>
          </div>
        </form>

        <p className="text-center text-gray-700 text-sm mt-7">
          don't have an account{' '}
          <Link to="/signup" className="font-bold text-gray-900 underline">
            Sign Up
          </Link>
        </p>
      </div>
    </div>
  )
}
