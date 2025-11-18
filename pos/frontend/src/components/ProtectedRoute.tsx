/**
 * Protected Route Component
 * Handles route protection based on authentication and role requirements
 */

import React from 'react';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'cashier' | 'manager' | 'admin';
  fallback?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  fallback 
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show fallback if not authenticated
  if (!isAuthenticated || !user) {
    return fallback || <LoginPrompt />;
  }

  // Check role requirements
  if (requiredRole) {
    const hasRequiredRole = checkUserRole(user.role, requiredRole);
    if (!hasRequiredRole) {
      return <UnauthorizedAccess userRole={user.role} requiredRole={requiredRole} />;
    }
  }

  return <>{children}</>;
};

// Helper function to check if user role meets requirements
const checkUserRole = (userRole: string, requiredRole: string): boolean => {
  const roleHierarchy = {
    'admin': ['admin', 'manager', 'cashier'],
    'manager': ['manager', 'cashier'],
    'cashier': ['cashier']
  };

  return roleHierarchy[userRole as keyof typeof roleHierarchy]?.includes(requiredRole) || false;
};

// Login prompt component
const LoginPrompt: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full mx-4">
        <div className="text-center">
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please log in to access the POS system.</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Login
          </button>
        </div>
      </div>
    </div>
  );
};

// Unauthorized access component
interface UnauthorizedAccessProps {
  userRole: string;
  requiredRole: string;
}

const UnauthorizedAccess: React.FC<UnauthorizedAccessProps> = ({ userRole, requiredRole }) => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full mx-4">
        <div className="text-center">
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-2">
            You don't have permission to access this area.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Your role: <span className="font-medium">{userRole}</span><br />
            Required role: <span className="font-medium">{requiredRole}</span> or higher
          </p>
          <button
            onClick={() => window.history.back()}
            className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProtectedRoute;