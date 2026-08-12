import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function AdminProtectedRoute({ children }) {
  const { adminUser } = useAuth();

  if (!adminUser) {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
}
