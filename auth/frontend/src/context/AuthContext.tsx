import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import { authService, User } from '../services/apiService';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  applySsoToken: (token: string) => Promise<void>;
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
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const expiryTimerRef = useRef<number | null>(null);

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
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
      const savedToken = localStorage.getItem('auth_token');
      try {
        const toValidate = savedToken || token;
        if (toValidate) {
          const profile = await authService.getProfile();
          setToken(toValidate);
          setUser(profile);
          localStorage.setItem('auth_user', JSON.stringify(profile));
          scheduleExpiryLogout(toValidate);
        }
      } catch (e) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await authService.login({ email, password });
      localStorage.setItem('auth_token', response.access_token);
      const profile = await authService.getProfile();
      setToken(response.access_token);
      setUser(profile);
      localStorage.setItem('auth_user', JSON.stringify(profile));
      scheduleExpiryLogout(response.access_token);
      return true;
    } catch (e) {
      return false;
    }
  };

  const applySsoToken = async (incomingToken: string): Promise<void> => {
    try {
      localStorage.setItem('auth_token', incomingToken);
      setToken(incomingToken);
      const profile = await authService.getProfile();
      setUser(profile);
      localStorage.setItem('auth_user', JSON.stringify(profile));
      scheduleExpiryLogout(incomingToken);
    } catch (e) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      setToken(null);
      setUser(null);
      throw e;
    }
  };

  

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading,
    applySsoToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
