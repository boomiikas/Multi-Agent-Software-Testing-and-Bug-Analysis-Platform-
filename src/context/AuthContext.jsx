import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { authApi } from '../services/api';
import { getStoredToken, storeToken, clearToken, setUnauthorizedHandler } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isRestoring, setIsRestoring] = useState(true);

  // Session persistence: on first load, if a token exists (localStorage
  // for "remember me", sessionStorage otherwise), validate it against the
  // API and restore the session instead of forcing a fresh login.
  useEffect(() => {
    let cancelled = false;
    async function restore() {
      const token = getStoredToken();
      if (!token) { setIsRestoring(false); return; }
      try {
        const { user } = await authApi.me();
        if (!cancelled) {
          setUser(user);
          setIsAuthenticated(true);
        }
      } catch {
        clearToken();
      } finally {
        if (!cancelled) setIsRestoring(false);
      }
    }
    restore();
    return () => { cancelled = true; };
  }, []);

  // If any API call comes back 401 (expired/invalid token), drop the
  // session everywhere in the app.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearToken();
      setUser(null);
      setIsAuthenticated(false);
    });
  }, []);

  const login = useCallback(async (email, password, rememberMe = false) => {
    setIsLoading(true);
    try {
      const { token, user } = await authApi.login(email, password, rememberMe);
      storeToken(token, rememberMe);
      setUser(user);
      setIsAuthenticated(true);
      return { success: true, user };
    } catch (err) {
      return { success: false, error: err.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (fullName, email, password) => {
    setIsLoading(true);
    try {
      const { token, user } = await authApi.register(fullName, email, password);
      storeToken(token, false);
      setUser(user);
      setIsAuthenticated(true);
      return { success: true, user };
    } catch (err) {
      return { success: false, error: err.message, errors: err.errors };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authApi.logout().catch(() => {}); // best-effort; token is discarded regardless
    clearToken();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const forgotPassword = useCallback(async (email) => {
    try {
      const res = await authApi.forgotPassword(email);
      return { success: true, ...res };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const resetPassword = useCallback(async (token, password) => {
    try {
      await authApi.resetPassword(token, password);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const changePassword = useCallback(async (currentPassword, password) => {
    try {
      await authApi.changePassword(currentPassword, password);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const isAdmin = user?.role === 'ADMIN';

  return (
    <AuthContext.Provider value={{
      user, isAuthenticated, isLoading, isRestoring, isAdmin,
      login, register, logout, forgotPassword, resetPassword, changePassword,
      setUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
