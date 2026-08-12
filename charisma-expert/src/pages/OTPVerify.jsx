import { useState, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { X, Loader2, RotateCcw } from 'lucide-react'
import * as authApi from '../api/auth'

const OTP_LENGTH = 6

export default function OTPVerify() {
  const navigate = useNavigate()
  const location = useLocation()
  const { fromSignUp, fromForgotPassword, email, newPassword } = location.state || {}

  const [otp, setOtp] = useState(Array(OTP_LENGTH).fill(''))
  const inputs = useRef([])
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState('')
  const [resendMsg, setResendMsg] = useState('')

  const handleChange = (index, value) => {
    if (!/^\d?$/.test(value)) return
    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)
    if (error) setError('')
    if (value && index < OTP_LENGTH - 1) {
      inputs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH)
    const newOtp = Array(OTP_LENGTH).fill('')
    pasted.split('').forEach((d, i) => { newOtp[i] = d })
    setOtp(newOtp)
    inputs.current[Math.min(pasted.length, OTP_LENGTH - 1)]?.focus()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const code = otp.join('')
    if (code.length < OTP_LENGTH) {
      setError(`Please enter all ${OTP_LENGTH} digits.`)
      return
    }
    setLoading(true)
    setError('')
    try {
      if (fromSignUp) {
        // Email verification after registration
        await authApi.verifyEmail({ email, code })
        navigate('/login', { state: { verified: true } })
      } else if (fromForgotPassword) {
        // Password-reset confirmation — also needs new_password
        await authApi.confirmPasswordReset({ email, code, new_password: newPassword })
        navigate('/login', { state: { passwordReset: true } })
      } else {
        navigate('/login')
      }
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.detail ||
        err?.response?.data?.error?.detail ||
        'Invalid or expired code. Please try again.'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (!email) return
    setResending(true)
    setResendMsg('')
    setError('')
    try {
      if (fromSignUp) {
        await authApi.resendVerification({ email })
      } else {
        await authApi.requestPasswordReset({ email })
      }
      setResendMsg('A new code has been sent to your email.')
    } catch {
      setResendMsg('Could not resend. Please wait a moment and try again.')
    } finally {
      setResending(false)
    }
  }

  const flowLabel = fromSignUp ? 'verification code' : 'reset code'

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-md p-10 relative">
        {/* Close */}
        <button
          onClick={() => navigate(fromSignUp ? '/signup' : '/forgot-password')}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 transition-colors"
          aria-label="Close"
          id="otp-close-btn"
        >
          <X size={22} />
        </button>

        <h1 className="text-3xl font-bold text-center text-blue-600 mb-2">Check Your Email</h1>
        <p className="text-center text-gray-700 font-medium mb-2 leading-relaxed">
          We sent a {flowLabel} to{' '}
          <span className="font-bold text-gray-900">{email || 'your email'}</span>
        </p>
        <p className="text-center text-gray-500 text-sm mb-8">
          Enter the {OTP_LENGTH}-digit code from the email. It expires in 10 minutes.
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm text-center">
            {error}
          </div>
        )}
        {resendMsg && (
          <div className="mb-5 px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-xl text-sm text-center">
            {resendMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* OTP Boxes */}
          <div className="flex justify-center gap-2" onPaste={handlePaste}>
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputs.current[index] = el)}
                id={`otp-input-${index}`}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                className="otp-input"
                aria-label={`OTP digit ${index + 1}`}
                disabled={loading}
              />
            ))}
          </div>

          <button
            id="otp-verify-btn"
            type="submit"
            disabled={loading}
            className="btn-blue-gradient w-full py-4 text-base flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'Verifying…' : 'Verify'}
          </button>
        </form>

        {/* Resend */}
        <div className="mt-6 text-center">
          <button
            onClick={handleResend}
            disabled={resending || loading}
            className="text-blue-600 text-sm font-medium hover:underline flex items-center gap-1.5 mx-auto disabled:opacity-50"
          >
            <RotateCcw size={14} className={resending ? 'animate-spin' : ''} />
            {resending ? 'Sending…' : "Didn't receive a code? Resend"}
          </button>
        </div>
      </div>
    </div>
  )
}
