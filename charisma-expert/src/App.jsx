import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AdminProtectedRoute from './components/AdminProtectedRoute'
import OfficerLayout from './layouts/OfficerLayout'
import AdminLayout from './layouts/AdminLayout'

// Route-level code splitting: each page loads on demand instead of all being
// bundled into one ~690KB chunk up front — a visitor to the public site never
// needs the admin panel's code (or vice versa).
const Home = lazy(() => import('./pages/Home'))
const Pricing = lazy(() => import('./pages/Pricing'))
const Blog = lazy(() => import('./pages/Blog'))
const BlogPost = lazy(() => import('./pages/BlogPost'))
const BillingSuccess = lazy(() => import('./pages/BillingSuccess'))
const BillingCancel = lazy(() => import('./pages/BillingCancel'))

const About = lazy(() => import('./pages/About'))
const FAQ = lazy(() => import('./pages/FAQ'))
const Contact = lazy(() => import('./pages/Contact'))
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'))
const TermsOfService = lazy(() => import('./pages/TermsOfService'))
const Login = lazy(() => import('./pages/Login'))
const SignUp = lazy(() => import('./pages/SignUp'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const OTPVerify = lazy(() => import('./pages/OTPVerify'))
const SetNewPassword = lazy(() => import('./pages/SetNewPassword'))

const OfficerDashboard = lazy(() => import('./pages/dashboard/OfficerDashboard'))
const CreateIncidentReport = lazy(() => import('./pages/dashboard/CreateIncidentReport'))
const CreateSearchWarrant = lazy(() => import('./pages/dashboard/CreateSearchWarrant'))
const CreateArrestWarrant = lazy(() => import('./pages/dashboard/CreateArrestWarrant'))
const DocumentHistory = lazy(() => import('./pages/dashboard/DocumentHistory'))
const GeneratedDocument = lazy(() => import('./pages/dashboard/GeneratedDocument'))
const OfficerProfile = lazy(() => import('./pages/dashboard/OfficerProfile'))
const ManageBilling = lazy(() => import('./pages/dashboard/ManageBilling'))

const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))
const UserManagement = lazy(() => import('./pages/admin/UserManagement'))
const AdminUserManagement = lazy(() => import('./pages/admin/AdminUserManagement'))
const AdminLogin = lazy(() => import('./pages/admin/AdminLogin'))
const Billing = lazy(() => import('./pages/admin/Billing'))
const AgencyManagement = lazy(() => import('./pages/admin/AgencyManagement'))
const DocumentManagement = lazy(() => import('./pages/admin/DocumentManagement'))
const AdminDocumentPreview = lazy(() => import('./pages/admin/AdminDocumentPreview'))
const DatasetManagement = lazy(() => import('./pages/admin/DatasetManagement'))
const ActivityMonitor = lazy(() => import('./pages/admin/ActivityMonitor'))
const ContentManagement = lazy(() => import('./pages/admin/ContentManagement'))
const Settings = lazy(() => import('./pages/admin/Settings'))

const RouteFallback = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="w-8 h-8 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
  </div>
)

export default function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/blog/:slug" element={<BlogPost />} />
          <Route path="/billing/success" element={<BillingSuccess />} />
          <Route path="/billing/cancel" element={<BillingCancel />} />

          <Route path="/about" element={<About />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route path="/terms-of-service" element={<TermsOfService />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/verify-otp" element={<OTPVerify />} />
          <Route path="/reset-password" element={<SetNewPassword />} />

          {/* Protected Dashboard Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <OfficerLayout />
            </ProtectedRoute>
          }>
            <Route index element={<OfficerDashboard />} />
            <Route path="create/incident-report" element={<CreateIncidentReport />} />
            <Route path="create/search-warrant" element={<CreateSearchWarrant />} />
            <Route path="create/arrest-warrant" element={<CreateArrestWarrant />} />
            <Route path="history" element={<DocumentHistory />} />
            <Route path="document/:id" element={<GeneratedDocument />} />
            <Route path="profile" element={<OfficerProfile />} />
            <Route path="billing" element={<ManageBilling />} />
          </Route>

          {/* Admin Login */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* Protected Admin Routes */}
          <Route path="/admin" element={
            <AdminProtectedRoute>
              <AdminLayout />
            </AdminProtectedRoute>
          }>
            <Route index element={<AdminDashboard />} />
            <Route path="users" element={<UserManagement />} />
            <Route path="admins" element={<AdminUserManagement />} />
            <Route path="billing" element={<Billing />} />
            <Route path="agencies" element={<AgencyManagement />} />
            <Route path="documents" element={<DocumentManagement />} />
            <Route path="documents/:id" element={<AdminDocumentPreview />} />
            <Route path="datasets" element={<DatasetManagement />} />
            <Route path="content" element={<ContentManagement />} />
            <Route path="activity" element={<ActivityMonitor />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </Suspense>
    </AuthProvider>
  )
}
