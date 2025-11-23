/**
 * Loading Screen Component
 * Displays a loading overlay with spinner or custom GIF
 */

import React from 'react';
import { useLoading } from '../contexts/LoadingContext';

interface LoadingScreenProps {
  gifUrl?: string; // Optional transparent GIF URL
  className?: string;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  gifUrl, 
  className = '' 
}) => {
  const { isLoading, loadingMessage } = useLoading();

  if (!isLoading) return null;

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center ${className}`}>
      <div className="bg-white rounded-lg p-8 shadow-2xl flex flex-col items-center max-w-sm mx-4">
        {/* Loading Animation */}
        <div className="mb-4">
          {gifUrl ? (
            <img 
              src={gifUrl} 
              alt="Loading..." 
              className="w-16 h-16 object-contain"
            />
          ) : (
            <img 
              src="/loading.svg" 
              alt="Loading..." 
              className="w-16 h-16 object-contain"
            />
          )}
        </div>
        
        {/* Loading Message */}
        <div className="text-center">
          <p className="text-gray-800 font-medium mb-2">
            {loadingMessage || 'Processing...'}
          </p>
          <p className="text-gray-600 text-sm">
            Please wait while we complete your request
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;