import React, { createContext, useContext, useState, useEffect } from 'react';
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

  // Check for existing token on app start
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');
    
    console.log('Checking auth state:', { savedToken, savedUser });
    
    if (savedToken && savedUser && savedUser !== 'undefined') {
      try {
        const userObj = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(userObj);
      } catch (error) {
        console.error('Error parsing saved user:', error);
        // Clear invalid data
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }
    setIsLoading(false);
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