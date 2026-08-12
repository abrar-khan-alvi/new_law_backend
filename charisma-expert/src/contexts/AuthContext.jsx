import { createContext, useContext, useState, useCallback } from 'react';
import * as authApi from '../api/auth';

const AuthContext = createContext(null);

// ── Keys used in localStorage ─────────────────────────────────────────────────
const KEYS = {
  user: 'auth_user',
  access: 'access_token',
  refresh: 'refresh_token',
  adminUser: 'admin_user',
  adminAccess: 'admin_access_token',
  adminRefresh: 'admin_refresh_token',
};

const loadJson = (key) => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  // ── Officer auth ─────────────────────────────────────────────────────────────
  const [user, setUser] = useState(() => loadJson(KEYS.user));

  const login = useCallback(async (email, password) => {
    const { data } = await authApi.login({ email, password });
    localStorage.setItem(KEYS.access, data.access);
    localStorage.setItem(KEYS.refresh, data.refresh);
    localStorage.setItem(KEYS.user, JSON.stringify(data.user));
    setUser(data.user);
    return data;
  }, []);

  const googleLogin = useCallback(async (credential) => {
    const { data } = await authApi.googleLogin(credential);
    localStorage.setItem(KEYS.access, data.access);
    localStorage.setItem(KEYS.refresh, data.refresh);
    localStorage.setItem(KEYS.user, JSON.stringify(data.user));
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem(KEYS.refresh);
    if (refresh) {
      try {
        await authApi.logout({ refresh });
      } catch (_) {
        // ignore — still clear local storage
      }
    }
    [KEYS.user, KEYS.access, KEYS.refresh].forEach((k) =>
      localStorage.removeItem(k)
    );
    setUser(null);
  }, []);

  /** Update in-memory user after profile edits */
  const updateUser = useCallback((updatedUser) => {
    localStorage.setItem(KEYS.user, JSON.stringify(updatedUser));
    setUser(updatedUser);
  }, []);

  // ── Admin auth ───────────────────────────────────────────────────────────────
  const [adminUser, setAdminUser] = useState(() => loadJson(KEYS.adminUser));

  const adminLogin = useCallback(async (email, password) => {
    const { data } = await authApi.login({ email, password });
    if (data.user?.role !== 'admin') {
      throw new Error('Access denied: not an admin account.');
    }
    localStorage.setItem(KEYS.adminAccess, data.access);
    localStorage.setItem(KEYS.adminRefresh, data.refresh);
    localStorage.setItem(KEYS.adminUser, JSON.stringify(data.user));
    // Also set the primary access token so axiosInstance uses it for admin requests
    localStorage.setItem(KEYS.access, data.access);
    localStorage.setItem(KEYS.refresh, data.refresh);
    setAdminUser(data.user);
    return data;
  }, []);

  const adminLogout = useCallback(async () => {
    const refresh = localStorage.getItem(KEYS.adminRefresh);
    if (refresh) {
      try {
        await authApi.logout({ refresh });
      } catch (_) {
        // ignore
      }
    }
    [KEYS.adminUser, KEYS.adminAccess, KEYS.adminRefresh, KEYS.access, KEYS.refresh].forEach(
      (k) => localStorage.removeItem(k)
    );
    setAdminUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, login, googleLogin, logout, updateUser, adminUser, adminLogin, adminLogout }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
