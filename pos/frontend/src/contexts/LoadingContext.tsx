/**
 * Loading Context for POS System
 * Manages global loading states for all backend operations
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface LoadingContextType {
  isLoading: boolean;
  loadingMessage: string;
  setLoading: (isLoading: boolean, message?: string) => void;
  showLoading: (message?: string) => void;
  hideLoading: () => void;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export const useLoading = () => {
  const context = useContext(LoadingContext);
  if (context === undefined) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
};

interface LoadingProviderProps {
  children: ReactNode;
}

export const LoadingProvider: React.FC<LoadingProviderProps> = ({ children }) => {
  const [isLoading, setIsLoadingState] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  const setLoading = (loading: boolean, message: string = '') => {
    setIsLoadingState(loading);
    setLoadingMessage(message);
  };

  const showLoading = (message: string = 'Loading...') => {
    setIsLoadingState(true);
    setLoadingMessage(message);
  };

  const hideLoading = () => {
    setIsLoadingState(false);
    setLoadingMessage('');
  };

  return (
    <LoadingContext.Provider value={{
      isLoading,
      loadingMessage,
      setLoading,
      showLoading,
      hideLoading
    }}>
      {children}
    </LoadingContext.Provider>
  );
};