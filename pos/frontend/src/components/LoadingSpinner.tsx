/**
 * Animated Loading Spinner Component
 * CSS-based transparent loading animation
 */

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  color = '#3B82F6',
  className = '' 
}) => {
  const sizeClasses = {
    small: 'w-8 h-8',
    medium: 'w-16 h-16',
    large: 'w-24 h-24'
  };

  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <div 
        className="w-full h-full border-4 border-gray-200 border-t-current rounded-full animate-spin"
        style={{ borderTopColor: color }}
      ></div>
    </div>
  );
};

export default LoadingSpinner;