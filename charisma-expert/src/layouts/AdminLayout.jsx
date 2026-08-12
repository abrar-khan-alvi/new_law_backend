import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  Users,
  CreditCard,
  Database,
  FileText,
  FileCheck,
  Activity,
  Settings,
  Building2,
  ShieldCheck,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import logoImg from '../assets/logo.png';

const AdminLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { adminLogout } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    adminLogout();
    navigate('/admin/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
    { name: 'Officers', path: '/admin/users', icon: Users },
    { name: 'Administrators', path: '/admin/admins', icon: ShieldCheck },
    { name: 'Documents', path: '/admin/documents', icon: FileCheck },
    { name: 'Subscriptions & Billing', path: '/admin/billing', icon: CreditCard },
    { name: 'Agencies & Jurisdictions', path: '/admin/agencies', icon: Building2 },
    { name: 'AI Datasets & Training', path: '/admin/datasets', icon: Database },
    { name: 'Content (CMS)', path: '/admin/content', icon: FileText },
    { name: 'Activity Monitor', path: '/admin/activity', icon: Activity },
    { name: 'Settings', path: '/admin/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-slate-900">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`w-64 bg-[#111827] text-slate-300 flex flex-col flex-shrink-0 fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {/* Logo area */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div className="flex items-center">
            <img src={logoImg} alt="KLYVOREK logo" className="h-10 w-10 rounded-full object-cover mr-3" />
            <div>
              <h1 className="text-white font-bold text-lg leading-tight tracking-[0.08em]">KLYVOREK</h1>
              <div className="flex items-center text-blue-500 text-xs mt-0.5">
                <svg className="w-3 h-3 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                Admin
              </div>
            </div>
          </div>
          <button className="lg:hidden text-gray-400 hover:text-white" onClick={() => setIsSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              // Check if it's the exact match for /admin to avoid highlighting it for all /admin/* routes
              const isActive = item.path === '/admin' 
                ? location.pathname === '/admin' 
                : location.pathname.startsWith(item.path);

              return (
                <li key={item.name}>
                  <NavLink
                    to={item.path}
                    className={`flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
                    {item.name}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Profile & Logout */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center mb-4 px-2">
            <img 
              src="https://i.pravatar.cc/150?img=11" 
              alt="System Admin" 
              className="w-10 h-10 rounded-full mr-3 border border-gray-700"
            />
            <div>
              <div className="text-sm font-medium text-white">System Admin</div>
              <div className="text-xs text-gray-400">Owner</div>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center px-3 py-2 w-full text-sm font-medium text-gray-400 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 flex items-center justify-between lg:justify-end px-4 lg:px-8 flex-shrink-0 bg-white border-b border-gray-100">
          <div className="flex items-center lg:hidden">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 -ml-2 mr-2 text-gray-600 hover:text-gray-900 rounded-md"
            >
              <Menu size={24} />
            </button>
            <span className="font-bold text-gray-900 text-lg sm:hidden">Admin</span>
          </div>

          <div className="flex items-center px-3 py-1.5 bg-gray-50 rounded-full text-sm font-medium text-gray-600 border border-gray-200 shadow-sm">
            <div className="w-2 h-2 mr-2 bg-emerald-500 rounded-full"></div>
            System Operational
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-8 pt-2">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
