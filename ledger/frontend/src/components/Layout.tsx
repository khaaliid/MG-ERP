import React from 'react';
import Header from './Header';

interface LayoutProps {
  children: React.ReactNode;
  currentPage?: string;
  currentReport?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, currentPage, currentReport }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Navigation */}
      <Header currentPage={currentPage} currentReport={currentReport} />
      
      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};

export default Layout;