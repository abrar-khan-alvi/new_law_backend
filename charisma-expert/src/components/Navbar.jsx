import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import logoImg from '../assets/logo.png';

const navLinks = [
  { label: 'Home', to: '/' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'Blog', to: '/blog' },

  { label: 'About', to: '/about' },
  { label: 'FAQ', to: '/faq' },
  { label: 'Contact', to: '/contact' },
  { label: 'Privacy', to: '/privacy-policy' },
  { label: 'Terms', to: '/terms-of-service' },
]

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { pathname } = useLocation();
  const { user } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-40">
      {/* Full-width bar — logo left, nav truly centered, auth right */}
      <div className="w-full px-6 lg:px-10 xl:px-16">
        <div className="relative flex items-center h-16">

          {/* Logo — pinned to the left */}
          <Link to="/" className="flex items-center gap-2 shrink-0 z-10">
            <img
              src={logoImg}
              alt="KLYVOREK logo"
              className="h-10 w-10 rounded-full object-cover shrink-0"
            />
            <div className="leading-tight hidden sm:block whitespace-nowrap">
              <p className="text-base font-extrabold tracking-[0.16em] text-navy-800">KLYVOREK</p>
              <p className="text-[10px] uppercase tracking-[0.12em] text-gray-500">AI-assisted documentation</p>
            </div>
          </Link>

          {/* Nav links — absolutely centered in the full bar */}
          <nav className="hidden md:flex items-center gap-3 lg:gap-5 absolute left-1/2 -translate-x-1/2">
            {navLinks.map(({ label, to }) => (
              <Link
                key={to}
                to={to}
                className={
                  pathname === to
                    ? 'nav-link-active'
                    : 'nav-link'
                }
              >
                {label}
              </Link>
            ))}
          </nav>

          {/* Auth buttons — pinned to the right */}
          <div className="flex items-center gap-3 ml-auto z-10">
            {user ? (
              <Link
                to="/dashboard"
                className="bg-navy-800 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-navy-700 transition-colors flex items-center gap-2"
              >
                {/* <LayoutDashboard size={16} /> */}
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="hidden sm:flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-navy-800 transition-colors"
                >
                  <Shield size={15} strokeWidth={1.5} />
                  Officer Login
                </Link>
                <Link
                  to="/signup"
                  className="bg-navy-800 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-navy-700 transition-colors"
                >
                  Create Free Report
                </Link>
              </>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden flex items-center justify-center p-2 -mr-2 text-gray-600 hover:text-navy-800 transition-colors"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 absolute top-full left-0 w-full shadow-lg z-50">
          <div className="px-6 py-4 flex flex-col gap-4">
            {navLinks.map(({ label, to }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setIsMobileMenuOpen(false)}
                className={
                  pathname === to
                    ? 'text-navy-800 font-bold text-lg'
                    : 'text-gray-600 hover:text-navy-800 font-medium text-lg'
                }
              >
                {label}
              </Link>
            ))}

            {/* Show Officer Login here on very small screens where it's hidden in the top bar */}
            {!user && (
              <>
                <hr className="border-gray-100 my-1" />
                <Link
                  to="/login"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="sm:hidden flex items-center gap-2 text-gray-700 hover:text-navy-800 font-medium text-lg"
                >
                  <Shield size={18} strokeWidth={1.5} />
                  Officer Login
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
