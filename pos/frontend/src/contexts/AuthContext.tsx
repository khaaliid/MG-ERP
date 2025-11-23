/**
 * Authentication Context for POS System
 * Manages user authentication state and JWT tokens
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { enhancedApiService, LoginRequest, User } from '../services/enhancedApiService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = async () => {
    try {
      setIsLoading(true);
      
      // Check if we have a token
      if (!enhancedApiService.isAuthenticated()) {
        setUser(null);
        return;
      }

      // Try to get user from localStorage first (faster)
      const storedUser = enhancedApiService.getCurrentUserFromStorage();
      if (storedUser) {
        setUser(storedUser);
      }

      // Verify token is still valid by fetching current user
      const currentUser = await enhancedApiService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
        // Update localStorage with fresh user data
        localStorage.setItem('pos_current_user', JSON.stringify(currentUser));
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true);
      console.log('AuthContext: Starting login process...');
      const loginResponse = await enhancedApiService.login(credentials);
      console.log('AuthContext: Login response received:', loginResponse);
      setUser(loginResponse.user);
      console.log('AuthContext: User set successfully:', loginResponse.user);
    } catch (error) {
      console.error('AuthContext: Login failed:', error);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    enhancedApiService.logout();
    setUser(null);
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user && enhancedApiService.isAuthenticated(),
    isLoading,
    login,
    logout,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;