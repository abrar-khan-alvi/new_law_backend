import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, X, Loader2 } from 'lucide-react'
import * as authApi from '../api/auth'
import GoogleSignInButton from '../components/GoogleSignInButton'

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC',
]

const initialForm = {
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password2: '',
  badge_number: '',
  department_name: '',
  department_address: '',
  department_state: '',
  ori: '',
  phone_number: '',
  rank: '',
  division: '',
}

const Field = ({ id, name, label, type = 'text', placeholder, required = false, form, errors, handleChange, loading }) => (
  <div>
    <label htmlFor={id} className="block text-sm font-semibold text-gray-800 mb-2">
      {label}{required && ' *'}
    </label>
    <input
      id={id}
      name={name}
      type={type}
      placeholder={placeholder}
      value={form[name]}
      onChange={handleChange}
      className={`input-field ${errors[name] ? 'border-red-400 focus:border-red-500' : ''}`}
      required={required}
      disabled={loading}
    />
    {errors[name] && <p className="text-red-500 text-xs mt-1">{errors[name]}</p>}
  </div>
)

export default function SignUp() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [globalError, setGlobalError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm({ ...form, [name]: value })
    if (errors[name]) setErrors({ ...errors, [name]: '' })
    if (globalError) setGlobalError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setErrors({})
    setGlobalError('')
    try {
      await authApi.register(form)
      // Navigate to OTP page passing email so it can be used for verification
      navigate('/verify-otp', { state: { fromSignUp: true, email: form.email } })
    } catch (err) {
      const data = err?.response?.data
      if (data && typeof data === 'object') {
        const errorDetail = data.error?.detail || data.error || data;
        
        if (typeof errorDetail === 'string') {
          setGlobalError(errorDetail)
        } else if (typeof errorDetail === 'object') {
          const fieldErrors = {}
          Object.entries(errorDetail).forEach(([k, v]) => {
            let msg = Array.isArray(v) ? v[0] : v
            if (typeof msg === 'object' && msg !== null) {
              msg = Object.values(msg)[0]
              if (Array.isArray(msg)) msg = msg[0]
              if (typeof msg === 'object') msg = JSON.stringify(msg)
            }
            fieldErrors[k] = String(msg)
          })
          setErrors(fieldErrors)
        } else {
          setGlobalError('Registration failed. Please try again.')
        }
      } else {
        setGlobalError('Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleError = (err) => {
    setGlobalError(err?.response?.data?.error?.detail || 'Google sign-up failed. Please try again.')
  }



  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-2xl p-10 relative">
        {/* Close */}
        <button
          onClick={() => navigate('/')}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 transition-colors"
          aria-label="Close"
          id="signup-close-btn"
        >
          <X size={22} />
        </button>

        <h1 className="text-3xl font-bold text-center text-blue-600 mb-2">Create Officer Account</h1>
        <p className="text-center text-gray-700 font-medium mb-8">
          Enter your credentials to register. A 6-digit verification code will be emailed to you.
        </p>

        {globalError && (
          <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
            {globalError}
          </div>
        )}

        <GoogleSignInButton onSuccess={() => navigate('/dashboard')} onError={handleGoogleError} />
        <p className="text-center text-xs text-gray-500 mt-3">Start immediately. Complete your officer profile later; an administrator must assign your agency before export.</p>
        <div className="flex items-center gap-3 my-6"><span className="h-px flex-1 bg-gray-200" /><span className="text-xs uppercase text-gray-400">or register with email</span><span className="h-px flex-1 bg-gray-200" /></div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Personal Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-first-name" name="first_name" label="First Name" placeholder="Edward" required />
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-last-name" name="last_name" label="Last Name" placeholder="Brown" required />
          </div>

          <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-email" name="email" label="Email" type="email" placeholder="officer@dept.gov" required />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* Password */}
            <div>
              <label htmlFor="signup-password" className="block text-sm font-semibold text-gray-800 mb-2">Password *</label>
              <div className="relative">
                <input
                  id="signup-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="StrongPass123!"
                  value={form.password}
                  onChange={handleChange}
                  className={`input-field pr-12 ${errors.password ? 'border-red-400' : ''}`}
                  required
                  disabled={loading}
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" aria-label="Toggle password">
                  {showPassword ? <Eye size={18} /> : <EyeOff size={18} />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
            </div>
            {/* Confirm Password */}
            <div>
              <label htmlFor="signup-password2" className="block text-sm font-semibold text-gray-800 mb-2">Confirm Password *</label>
              <div className="relative">
                <input
                  id="signup-password2"
                  name="password2"
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="StrongPass123!"
                  value={form.password2}
                  onChange={handleChange}
                  className={`input-field pr-12 ${errors.password2 ? 'border-red-400' : ''}`}
                  required
                  disabled={loading}
                />
                <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600" aria-label="Toggle confirm password">
                  {showConfirm ? <Eye size={18} /> : <EyeOff size={18} />}
                </button>
              </div>
              {errors.password2 && <p className="text-red-500 text-xs mt-1">{errors.password2}</p>}
            </div>
          </div>

          {/* Officer Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-badge" name="badge_number" label="Badge Number" placeholder="2911" required />
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-phone" name="phone_number" label="Phone Number" type="tel" placeholder="770-426-2911" required />
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-rank" name="rank" label="Rank / Title" placeholder="Police Officer" required />
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-division" name="division" label="Division" placeholder="Patrol" />
          </div>

          {/* Department */}
          <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-dept-name" name="department_name" label="Department Name" placeholder="Life University Police Department" required />
          <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-dept-address" name="department_address" label="Department Address" placeholder="1269 Barclay Cir SE, Marietta, GA" required />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label htmlFor="signup-dept-state" className="block text-sm font-semibold text-gray-800 mb-2">State *</label>
              <select
                id="signup-dept-state"
                name="department_state"
                value={form.department_state}
                onChange={handleChange}
                className={`input-field ${errors.department_state ? 'border-red-400' : ''}`}
                required
                disabled={loading}
              >
                <option value="">Select state…</option>
                {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              {errors.department_state && <p className="text-red-500 text-xs mt-1">{errors.department_state}</p>}
            </div>
            <Field form={form} errors={errors} handleChange={handleChange} loading={loading} id="signup-ori" name="ori" label="ORI Number" placeholder="GA0331100" />
          </div>

          <button
            id="signup-submit-btn"
            type="submit"
            disabled={loading}
            className="btn-blue-gradient w-full py-4 text-base flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'Creating Account…' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-gray-700 text-sm mt-7">
          Already have an account{' '}
          <Link to="/login" className="font-bold text-gray-900 underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  )
}
