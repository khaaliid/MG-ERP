import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  const hasSsoToken = location.search.includes('sso_token=');

  if (isLoading || hasSsoToken) {
    return <>{children}</>;
  }

  if (!user) {
    return <Navigate to={`/login${location.search}`} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
