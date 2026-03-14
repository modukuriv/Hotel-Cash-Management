import { createContext, useContext, useMemo, useState } from 'react';
import api from '../services/api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('accessToken'));
  const [role, setRole] = useState(() => localStorage.getItem('userRole') || '');
  const [email, setEmail] = useState(() => localStorage.getItem('userEmail') || '');
  const [refreshToken, setRefreshToken] = useState(
    () => localStorage.getItem('refreshToken') || ''
  );
  const [mustReset, setMustReset] = useState(
    () => localStorage.getItem('mustResetPassword') === 'true'
  );

  const applySession = (data) => {
    if (!data?.access_token) return;
    localStorage.setItem('accessToken', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refreshToken', data.refresh_token);
      setRefreshToken(data.refresh_token);
    }
    localStorage.setItem('userRole', data.user.role);
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('tenantId', data.user.tenant_id || '');
    localStorage.setItem('userEmail', data.user.email);
    localStorage.setItem('mustResetPassword', String(data.user.must_reset_password));
    setToken(data.access_token);
    setRole(data.user.role);
    setEmail(data.user.email);
    setMustReset(Boolean(data.user.must_reset_password));
  };

  const login = async (email, code) => {
    const { data } = await api.post('/auth/login', { email, code });
    applySession(data);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userId');
    localStorage.removeItem('tenantId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('mustResetPassword');
    setToken(null);
    setRole('');
    setEmail('');
    setMustReset(false);
    setRefreshToken('');
  };

  const value = useMemo(
    () => ({ token, role, email, refreshToken, mustReset, login, logout, applySession }),
    [token, role, email, refreshToken, mustReset]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
