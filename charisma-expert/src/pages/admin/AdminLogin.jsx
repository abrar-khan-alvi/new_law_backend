import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, ShieldAlert, Loader2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import logoImg from '../../assets/logo.png';

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const { adminLogin } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(location.state?.error || '');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await adminLogin(form.email, form.password);
      navigate('/admin');
    } catch (err) {
      if (err?.message === 'Access denied: not an admin account.') {
        setError('Access denied: Regular accounts must use the Officer Login page.');
      } else {
        let msg = 'Authentication failed. Please check your credentials.'
        if (err?.response?.data) {
          const data = err.response.data
          if (typeof data === 'string') {
            msg = data
          } else if (typeof data === 'object') {
            const errorObj = data.error || data
            if (typeof errorObj === 'string') {
              msg = errorObj
            } else if (typeof errorObj === 'object' && errorObj !== null) {
              const nonField = errorObj.non_field_errors || errorObj.detail
              if (Array.isArray(nonField) && nonField.length > 0) {
                msg = nonField[0]
              } else if (typeof nonField === 'string') {
                msg = nonField
              } else {
                const firstKey = Object.keys(errorObj)[0]
                if (firstKey) {
                  const val = errorObj[firstKey]
                  if (Array.isArray(val) && val.length > 0) {
                    msg = val[0]
                  } else if (typeof val === 'string') {
                    msg = val
                  }
                }
              }
            }
          }
        } else if (err?.message) {
          msg = err.message
        }
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="min-h-screen bg-[#0f172a] flex items-center justify-center px-4 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/20 rounded-full blur-[120px]"></div>
      
      <div className="bg-[#1e293b] rounded-2xl shadow-2xl w-full max-w-md p-10 relative z-10 border border-slate-700/50">
        
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-lg">
            <img src={logoImg} alt="KLYVOREK logo" className="w-12 h-12 rounded-full object-cover" />
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 mb-2 text-slate-300">
           <ShieldAlert className="w-5 h-5 text-red-400" />
           <span className="text-sm font-semibold tracking-wider uppercase text-red-400">Admin Portal</span>
        </div>

        <h1 className="text-2xl font-bold text-center text-white mb-6">System Login</h1>

        {error && (
          <div className="mb-5 px-4 py-3 bg-red-900/40 border border-red-700 text-red-300 rounded-xl text-sm text-center">
            {error}
          </div>
        )}

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="admin-email" className="block text-sm font-medium text-slate-300 mb-2">
              Admin Email
            </label>
            <input
              id="admin-email"
              name="email"
              type="email"
              placeholder="admin@klyvorek.com"
              value={form.email}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-[#0f172a] border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="admin-password" className="block text-sm font-medium text-slate-300 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                id="admin-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                className="w-full pl-4 pr-12 py-3 bg-[#0f172a] border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                aria-label="Toggle password visibility"
              >
                {showPassword ? <Eye size={18} /> : <EyeOff size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 mt-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold shadow-lg shadow-blue-500/30 transition-all hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed disabled:translate-y-0"
          >
            {loading && <Loader2 size={18} className="animate-spin" />}
            {loading ? 'Authenticating…' : 'Authenticate'}
          </button>
        </form>
      </div>
    </div>
  );
}
