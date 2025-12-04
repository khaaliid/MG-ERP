import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import { authService, User } from '../services/apiService';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const expiryTimerRef = useRef<number | null>(null);

  const logout = () => {
    authService.logout();
    setUser(null);
    localStorage.removeItem('token');
    if (expiryTimerRef.current) {
      window.clearTimeout(expiryTimerRef.current);
      expiryTimerRef.current = null;
    }
  };

  const scheduleExpiryLogout = (jwt: string) => {
    try {
      const [, payload] = jwt.split('.');
      if (!payload) return;
      const decoded = JSON.parse(atob(payload));
      const expSec = decoded.exp;
      if (!expSec) return;
      const remainingMs = expSec * 1000 - Date.now();
      if (expiryTimerRef.current) {
        window.clearTimeout(expiryTimerRef.current);
      }
      if (remainingMs <= 0) {
        console.warn('Token already expired – logging out');
        logout();
        return;
      }
      expiryTimerRef.current = window.setTimeout(() => {
        console.warn('Token expiry reached – logging out');
        logout();
      }, remainingMs + 500);
    } catch (e) {
      console.warn('Failed to parse JWT for expiry', e);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const url = new URL(window.location.href);
      const ssoToken = url.searchParams.get('sso_token');
      if (ssoToken) {
        console.log('[SSO] Received sso_token from URL, storing token');
        localStorage.setItem('token', ssoToken);
        url.searchParams.delete('sso_token');
        window.history.replaceState({}, document.title, url.toString());
      }

      const token = localStorage.getItem('token');
      if (token) {
        try {
          const profile = await authService.getProfile();
          setUser(profile);
          scheduleExpiryLogout(token);
        } catch (error) {
          console.warn('Token validation failed; clearing stored token');
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password });
    localStorage.setItem('token', response.access_token);
    const profile = await authService.getProfile();
    setUser(profile);
  };

  

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
