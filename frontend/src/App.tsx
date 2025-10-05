import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import Layout from './components/Layout';
import TransactionsPage from './pages/TransactionsPage';
import NewTransactionPage from './pages/NewTransactionPage';
import AccountsPage from './pages/AccountsPage';
import LedgerToday from './pages/LedgerToday';
import ReportsPage from './pages/ReportsPage';
import TrialBalancePage from './pages/TrialBalancePage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <TransactionsPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/transactions" 
            element={
              <ProtectedRoute>
                <TransactionsPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/transactions/new" 
            element={
              <ProtectedRoute>
                <NewTransactionPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/accounts" 
            element={
              <ProtectedRoute>
                <AccountsPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/ledger" 
            element={
              <ProtectedRoute>
                <LedgerToday />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports" 
            element={
              <ProtectedRoute>
                <ReportsPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/trial-balance" 
            element={
              <ProtectedRoute>
                <TrialBalancePage />
              </ProtectedRoute>
            } 
          />
          {/* Placeholder routes for other reports */}
          <Route 
            path="/reports/balance-sheet" 
            element={
              <ProtectedRoute>
                <Layout currentPage="reports" currentReport="balance-sheet">
                  <div className="p-8">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold text-gray-900 mb-4">📋 Balance Sheet</h2>
                      <p className="text-gray-600">Coming Soon - Balance Sheet Report</p>
                      <Link to="/reports" className="mt-4 inline-block text-blue-600 hover:text-blue-800">← Back to Reports</Link>
                    </div>
                  </div>
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/income-statement" 
            element={
              <ProtectedRoute>
                <Layout currentPage="reports" currentReport="income-statement">
                  <div className="p-8">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold text-gray-900 mb-4">💰 Income Statement</h2>
                      <p className="text-gray-600">Coming Soon - Income Statement Report</p>
                      <Link to="/reports" className="mt-4 inline-block text-blue-600 hover:text-blue-800">← Back to Reports</Link>
                    </div>
                  </div>
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/general-ledger" 
            element={
              <ProtectedRoute>
                <Layout currentPage="reports" currentReport="general-ledger">
                  <div className="p-8">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold text-gray-900 mb-4">📚 General Ledger</h2>
                      <p className="text-gray-600">Coming Soon - General Ledger Report</p>
                      <Link to="/reports" className="mt-4 inline-block text-blue-600 hover:text-blue-800">← Back to Reports</Link>
                    </div>
                  </div>
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/cash-flow" 
            element={
              <ProtectedRoute>
                <Layout currentPage="reports" currentReport="cash-flow">
                  <div className="p-8">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold text-gray-900 mb-4">💵 Cash Flow Statement</h2>
                      <p className="text-gray-600">Coming Soon - Cash Flow Report</p>
                      <Link to="/reports" className="mt-4 inline-block text-blue-600 hover:text-blue-800">← Back to Reports</Link>
                    </div>
                  </div>
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/aging" 
            element={
              <ProtectedRoute>
                <Layout currentPage="reports" currentReport="aging">
                  <div className="p-8">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold text-gray-900 mb-4">📅 Aging Report</h2>
                      <p className="text-gray-600">Coming Soon - Aging Report</p>
                      <Link to="/reports" className="mt-4 inline-block text-blue-600 hover:text-blue-800">← Back to Reports</Link>
                    </div>
                  </div>
                </Layout>
              </ProtectedRoute>
            } 
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
