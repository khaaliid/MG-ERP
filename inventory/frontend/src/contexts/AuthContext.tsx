import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';

// Types
interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  role: string;
  permissions: string[];
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const expiryTimerRef = useRef<number | null>(null);

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
      }, remainingMs + 500); // small buffer
    } catch (e) {
      console.warn('Failed to parse JWT for expiry', e);
    }
  };

  // Check for existing token on app start
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');
    
    console.log('Checking auth state:', { savedToken, savedUser });
    
    const validate = async () => {
      if (savedToken) {
        try {
          const resp = await fetch('http://localhost:8004/api/v1/auth/profile', {
            headers: { 'Authorization': `Bearer ${savedToken}` }
          });
          if (resp.ok) {
            const userObj = await resp.json();
            setToken(savedToken);
            setUser(userObj);
            localStorage.setItem('auth_user', JSON.stringify(userObj));
            scheduleExpiryLogout(savedToken);
          } else {
            console.warn('Token invalid; clearing stored auth');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            setToken(null);
            setUser(null);
          }
        } catch (e) {
          console.error('Failed to validate token', e);
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    validate();
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      console.log('🔐 Starting login process for:', username);
      setIsLoading(true);
      
      // Convert username to email if needed (for compatibility)
      const email = username.includes('@') ? username : `${username}@mg-erp.com`;
      
      const loginData = {
        email: email,
        password: password
      };

      console.log('📡 Sending login request to auth service...');
      const response = await fetch('http://localhost:8004/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      });

      console.log('📬 Response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Login failed with response:', errorText);
        throw new Error('Login failed');
      }

      const tokenData: { access_token: string; refresh_token: string; token_type: string } = await response.json();
      console.log('✅ Login response received:', {
        hasToken: !!tokenData.access_token,
      });
      
      // Get user profile with the token
      console.log('👤 Fetching user profile...');
      const profileResponse = await fetch('http://localhost:8004/api/v1/auth/profile', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokenData.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!profileResponse.ok) {
        console.error('❌ Failed to fetch user profile');
        throw new Error('Failed to fetch user profile');
      }

      const userData: User = await profileResponse.json();
      console.log('✅ User profile received:', userData);
      
      // Store auth data
      console.log('💾 Setting user state and localStorage...');
      setToken(tokenData.access_token);
      setUser(userData);
      localStorage.setItem('auth_token', tokenData.access_token);
      localStorage.setItem('auth_user', JSON.stringify(userData));
      scheduleExpiryLogout(tokenData.access_token);
      
      console.log('🎉 Login successful! User state updated.');
      return true;
    } catch (error) {
      console.error('❌ Login error:', error);
      return false;
    } finally {
      console.log('🔄 Setting loading to false');
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    if (expiryTimerRef.current) {
      window.clearTimeout(expiryTimerRef.current);
      expiryTimerRef.current = null;
    }
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};