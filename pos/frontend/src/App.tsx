import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './components/Login';
import Header from './components/Header';
import POS from './pages/POS';
import SalesHistory from './pages/SalesHistory';
import Reports from './pages/Reports';
import './App.css';

// Loading component
const LoadingScreen: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
  </div>
);

// Main app layout with header and navigation
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-gray-50">
    <Header />
    {children}
  </div>
);

// Main app component with authentication
const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      {/* Login Route */}
      <Route 
        path="/login" 
        element={
          isAuthenticated ? <Navigate to="/" replace /> : <Login />
        } 
      />
      
      {/* Protected Routes */}
      <Route 
        path="/" 
        element={
          isAuthenticated ? (
            <MainLayout>
              <ProtectedRoute>
                <POS />
              </ProtectedRoute>
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
      <Route 
        path="/history" 
        element={
          isAuthenticated ? (
            <MainLayout>
              <ProtectedRoute>
                <SalesHistory />
              </ProtectedRoute>
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
      <Route 
        path="/reports" 
        element={
          isAuthenticated ? (
            <MainLayout>
              <ProtectedRoute requiredRole="manager">
                <Reports />
              </ProtectedRoute>
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
      
      {/* Catch-all redirect */}
      <Route 
        path="*" 
        element={
          <Navigate to={isAuthenticated ? "/" : "/login"} replace />
        } 
      />
    </Routes>
  );
};

// Root app component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;