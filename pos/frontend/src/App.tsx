import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import POSMain from './pages/POSMain';
import ProductManagement from './pages/ProductManagement';
import SalesHistory from './pages/SalesHistory';
import Header from './components/Header';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<POSMain />} />
            <Route path="/products" element={<ProductManagement />} />
            <Route path="/sales" element={<SalesHistory />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;