import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <header className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">MG-ERP POS</h1>
          <nav>
            <ul className="flex space-x-6">
              <li>
                <Link 
                  to="/" 
                  className="hover:text-blue-200 transition-colors"
                >
                  Sales
                </Link>
              </li>
              <li>
                <Link 
                  to="/products" 
                  className="hover:text-blue-200 transition-colors"
                >
                  Products
                </Link>
              </li>
              <li>
                <Link 
                  to="/sales" 
                  className="hover:text-blue-200 transition-colors"
                >
                  History
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;