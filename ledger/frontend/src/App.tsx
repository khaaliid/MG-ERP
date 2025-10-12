import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import TransactionsPage from './pages/TransactionsPage';
import NewTransactionPage from './pages/NewTransactionPage';
import AccountsPage from './pages/AccountsPage';
import LedgerToday from './pages/LedgerToday';
import ReportsPage from './pages/ReportsPage';
import TrialBalancePage from './pages/TrialBalancePage';
import BalanceSheetPage from './pages/BalanceSheetPage';
import IncomeStatementPage from './pages/IncomeStatementPage';
import GeneralLedgerPage from './pages/GeneralLedgerPage';
import CashFlowPage from './pages/CashFlowPage';
import DashboardPage from './pages/DashboardPage';
import AgingReportPage from './pages/AgingReportPage';

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
          {/* Report routes with actual implementations */}
          <Route 
            path="/reports/balance-sheet" 
            element={
              <ProtectedRoute>
                <BalanceSheetPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/income-statement" 
            element={
              <ProtectedRoute>
                <IncomeStatementPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/general-ledger" 
            element={
              <ProtectedRoute>
                <GeneralLedgerPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/cash-flow" 
            element={
              <ProtectedRoute>
                <CashFlowPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/reports/aging" 
            element={
              <ProtectedRoute>
                <AgingReportPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
