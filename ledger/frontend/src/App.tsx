import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { I18nProvider, useI18n } from './i18n/I18nContext';
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

type RouteConfigItem = {
  path: string;
  element: React.ReactElement;
  labelKey: string;
};

const routeConfig: RouteConfigItem[] = [
  { path: '/', element: <TransactionsPage />, labelKey: 'nav_transactions' },
  { path: '/transactions', element: <TransactionsPage />, labelKey: 'nav_transactions' },
  { path: '/transactions/new', element: <NewTransactionPage />, labelKey: 'nav_new_transaction' },
  { path: '/accounts', element: <AccountsPage />, labelKey: 'nav_accounts' },
  { path: '/ledger', element: <LedgerToday />, labelKey: 'nav_ledger_today' },
  { path: '/reports', element: <ReportsPage />, labelKey: 'nav_reports' },
  { path: '/reports/trial-balance', element: <TrialBalancePage />, labelKey: 'nav_trial_balance' },
  { path: '/reports/balance-sheet', element: <BalanceSheetPage />, labelKey: 'nav_balance_sheet' },
  { path: '/reports/income-statement', element: <IncomeStatementPage />, labelKey: 'nav_income_statement' },
  { path: '/reports/general-ledger', element: <GeneralLedgerPage />, labelKey: 'nav_general_ledger' },
  { path: '/reports/cash-flow', element: <CashFlowPage />, labelKey: 'nav_cash_flow' },
  { path: '/reports/dashboard', element: <DashboardPage />, labelKey: 'nav_dashboard' },
  { path: '/reports/aging', element: <AgingReportPage />, labelKey: 'nav_aging_report' },
];

function AppShell() {
  const { dir } = useI18n();
  return (
    <div dir={dir} className="min-h-screen bg-gray-50">
      <BrowserRouter>
        <Routes>
          {routeConfig.map(({ path, element }) => (
            <Route
              key={path}
              path={path}
              element={<ProtectedRoute>{element}</ProtectedRoute>}
            />
          ))}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </I18nProvider>
  );
}

export default App;
