import { Link } from 'react-router-dom'
import { Shield } from 'lucide-react'
import logoImg from '../assets/logo.png'

const footerLinks = {
  Platform: [
    { label: 'Pricing & Plans', to: '/pricing' },
    { label: 'Officer Dashboard', to: '/login' },
    { label: 'Admin Portal', to: '/login' },
  ],
  Resources: [
    { label: 'Blog & News', to: '/blog' },

    { label: 'FAQ', to: '/faq' },
  ],
  Company: [
    { label: 'About Us', to: '/about' },
    { label: 'Contact', to: '/contact' },
    { label: 'Privacy Policy', to: '/privacy-policy' },
    { label: 'Terms of Service', to: '/terms-of-service' },
  ],
}

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#111625] text-gray-300 font-sans pt-16 pb-8 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
          
          {/* Brand Info */}
          <div className="space-y-6">
            <Link to="/" className="flex items-center gap-3">
              <img src={logoImg} alt="KLYVOREK logo" className="h-12 w-12 rounded-full object-cover" />
              <span className="text-xl font-bold text-white tracking-[0.16em]">KLYVOREK</span>
            </Link>
            <p className="text-sm text-gray-300 leading-relaxed">
              AI-assisted incident reports and structured warrant application drafts, built around officer-provided facts and human review.
            </p>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-sm font-semibold text-white mb-4">{category}</h4>
              <ul className="space-y-2.5">
                {links.map(({ label, to }) => (
                  <li key={label}>
                    <Link
                      to={to}
                      className="text-sm text-gray-300 hover:text-white transition-colors"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-white/10 mt-12 pt-6 flex flex-col sm:flex-row justify-between items-center gap-3">
          <p className="text-xs text-gray-400">
            © {currentYear} KLYVOREK. All rights reserved.
          </p>
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <Shield size={13} strokeWidth={1.5} />
            Role-Based Access &amp; Audit Logging
          </div>
        </div>
      </div>
    </footer>
  )
}
