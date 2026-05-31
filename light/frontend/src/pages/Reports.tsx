import { useEffect, useState } from 'react';
import { reportsAPI } from '../api';
import { useTranslation } from 'react-i18next';
import '../i18n';

type ReportItem = {
  key: string;
  name: string;
  description: string;
  status: 'ready' | 'coming_soon';
};

type ReportGroup = {
  title: string;
  subtitle: string;
  icon: string;
  reports: ReportItem[];
};

type BalanceSheetLineItem = {
  name: string;
  amount: number;
};

type BalanceSheetReport = {
  as_of_date: string;
  assets: BalanceSheetLineItem[];
  liabilities: BalanceSheetLineItem[];
  equity: BalanceSheetLineItem[];
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  is_balanced: boolean;
};

const REPORT_GROUPS: ReportGroup[] = [
  {
    title: 'Core Financial Statements (Legal Requirement)',
    subtitle: 'Essential statutory reports for compliance and formal financial review.',
    icon: '📘',
    reports: [
      {
        key: 'balance_sheet',
        name: 'Balance Sheet',
        description: 'Assets, liabilities, and equity snapshot for the selected period.',
        status: 'ready',
      },
      {
        key: 'income_statement',
        name: 'Income Statement',
        description: 'Revenue, expenses, and net income performance summary.',
        status: 'coming_soon',
      },
      {
        key: 'cash_flow_statement',
        name: 'Cash Flow Statement',
        description: 'Operating, investing, and financing cash movement analysis.',
        status: 'coming_soon',
      },
    ],
  },
  {
    title: 'Audit Reports',
    subtitle: 'Operational control and reconciliation reports for audit teams.',
    icon: '🧾',
    reports: [
      {
        key: 'trial_balance',
        name: 'Trial Balance',
        description: 'Consolidated debit and credit balances across ledger accounts.',
        status: 'coming_soon',
      },
      {
        key: 'cashier_closure_summary',
        name: 'Cashier Closure Summary',
        description: 'Cashier session closure totals, variances, and reconciliation status.',
        status: 'coming_soon',
      },
    ],
  },
  {
    title: 'Tax Summary',
    subtitle: 'Tax and settlement visibility for payable and receivable positions.',
    icon: '💼',
    reports: [
      {
        key: 'tax_summary',
        name: 'Tax Summary',
        description: 'Collected tax, payable tax, and net tax obligation overview.',
        status: 'coming_soon',
      },
      {
        key: 'accounts_receivable',
        name: 'Accounts Receivable',
        description: 'Outstanding customer balances and aging distribution.',
        status: 'coming_soon',
      },
      {
        key: 'accounts_payable',
        name: 'Accounts Payable',
        description: 'Outstanding supplier balances and due-date obligations.',
        status: 'coming_soon',
      },
    ],
  },
];

function Reports() {
  const [salesReport, setSalesReport] = useState<any>(null);
  const [inventoryReport, setInventoryReport] = useState<any>(null);
  const [ledgerReport, setLedgerReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState('30'); // days
  const [reportActionLoading, setReportActionLoading] = useState(false);
  const [reportActionError, setReportActionError] = useState('');
  const [activeReportKey, setActiveReportKey] = useState<string | null>(null);
  const [balanceSheetReport, setBalanceSheetReport] = useState<BalanceSheetReport | null>(null);
  const { i18n } = useTranslation();
  console.log("Current detected language:", i18n.language);

  useEffect(() => {
    loadReports();
  }, [dateRange]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const days = parseInt(dateRange);
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - days);

      const [salesRes, inventoryRes, ledgerRes] = await Promise.all([
        reportsAPI.getSalesReport({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
        }),
        reportsAPI.getInventoryReport(),
        reportsAPI.getLedgerReport({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
        }),
      ]);

      setSalesReport(salesRes.data);
      setInventoryReport(inventoryRes.data);
      setLedgerReport(ledgerRes.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => `$${(value || 0).toFixed(2)}`;

  const handleOpenReport = async (report: ReportItem) => {
    if (report.status !== 'ready') {
      return;
    }

    setActiveReportKey(report.key);
    setReportActionError('');

    if (report.key === 'balance_sheet') {
      try {
        setReportActionLoading(true);
        const response = await reportsAPI.getBalanceSheetReport({
          as_of_date: new Date().toISOString(),
        });
        setBalanceSheetReport(response.data);
      } catch (err: any) {
        setBalanceSheetReport(null);
        setReportActionError(err.response?.data?.detail || 'Failed to load balance sheet report');
      } finally {
        setReportActionLoading(false);
      }
      return;
    }

    setReportActionError('This report is marked available but is not fully wired yet.');
  };

  if (loading) {
    return (
      <div className="p-6 bg-gray-50 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 mx-auto text-blue-500" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="mt-4 text-lg text-gray-600">Loading reports...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-6 bg-gray-50 min-h-screen">
        <div className="bg-red-50 border-l-4 border-red-500 text-red-800 px-6 py-4 rounded-lg shadow-md">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-semibold">Error Loading Reports</p>
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="page-header">
        <h1>📊 Business Reports & Analytics</h1>
        <p>Comprehensive overview of sales, inventory, and financial performance</p>
      </div>

      <div className="mb-6" style={{ marginTop: 12 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ minWidth: 220 }}>
            <label style={{ display: 'block', marginBottom: 6 }}>📅 Report Period</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="7">Last 7 Days</option>
              <option value="30">Last 30 Days</option>
              <option value="90">Last 90 Days</option>
              <option value="365">Last Year</option>
            </select>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Sales</h3>
          <div className="value">${salesReport?.total_sales.toFixed(2)}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{salesReport?.total_transactions} transactions</p>
        </div>

        <div className="stat-card">
          <h3>Current Balance</h3>
          <div className="value">${ledgerReport?.current_balance.toFixed(2)}</div>
          <p style={{ color: '#27ae60', marginTop: 10 }}>Income: ${ledgerReport?.total_income.toFixed(2)}</p>
        </div>

        <div className="stat-card">
          <h3>Inventory Value</h3>
          <div className="value">${inventoryReport?.total_value.toFixed(2)}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{inventoryReport?.total_items} items</p>
        </div>

        <div className="stat-card">
          <h3>Low Stock Items</h3>
          <div className="value" style={{ color: inventoryReport?.low_stock_items > 0 ? '#e74c3c' : '#27ae60' }}>{inventoryReport?.low_stock_items}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>Out of stock: {inventoryReport?.out_of_stock_items}</p>
        </div>

        <div className="stat-card">
          <h3>Net Profit</h3>
          <div className="value" style={{ color: (ledgerReport?.total_income - ledgerReport?.total_expenses) >= 0 ? '#1abc9c' : '#e74c3c' }}>${((ledgerReport?.total_income || 0) - (ledgerReport?.total_expenses || 0)).toFixed(2)}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>Income − Expenses</p>
        </div>

        <div className="stat-card">
          <h3>Total Transactions</h3>
          <div className="value">{ledgerReport?.transaction_count}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>All ledgers</p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 10 }}>
        <h3>📚 Report Catalog</h3>
        <p style={{ color: '#7f8c8d', marginTop: 0, marginBottom: 16 }}>
          Access legal financial statements, audit reports, and tax summaries from one place.
        </p>

        <div className="reports-groups-grid">
          {REPORT_GROUPS.map((group) => (
            <section className="report-group-card" key={group.title}>
              <div className="report-group-header">
                <div>
                  <h4>
                    <span style={{ marginRight: 8 }}>{group.icon}</span>
                    {group.title}
                  </h4>
                  <p>{group.subtitle}</p>
                </div>
              </div>

              <div className="report-items-list">
                {group.reports.map((report) => (
                  <article className="report-item" key={report.key}>
                    <div>
                      <div className="report-item-title-row">
                        <h5>{report.name}</h5>
                        <span className={`report-status-pill report-status-${report.status}`}>
                          {report.status === 'ready' ? 'Available' : 'Coming Soon'}
                        </span>
                      </div>
                      <p>{report.description}</p>
                    </div>
                    <button
                      type="button"
                      className="button button-primary"
                      onClick={() => handleOpenReport(report)}
                      disabled={report.status !== 'ready'}
                      style={{ opacity: report.status === 'ready' ? 1 : 0.55 }}
                    >
                      {report.status === 'ready' ? 'Open Report' : 'Planned'}
                    </button>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>

      {(reportActionLoading || reportActionError || balanceSheetReport) && (
        <div className="card" style={{ marginTop: 18 }}>
          <h3>🧮 Report Viewer</h3>
          {reportActionLoading && <p className="report-viewer-note">Loading selected report...</p>}
          {!reportActionLoading && reportActionError && (
            <p className="report-viewer-error">{reportActionError}</p>
          )}

          {!reportActionLoading && !reportActionError && activeReportKey === 'balance_sheet' && balanceSheetReport && (
            <div className="balance-sheet-wrap">
              <div className="balance-sheet-meta">
                <strong>As Of:</strong> {new Date(balanceSheetReport.as_of_date).toLocaleString()}
              </div>

              <div className="balance-sheet-grid">
                <section>
                  <h4>Assets</h4>
                  <table className="table">
                    <tbody>
                      {balanceSheetReport.assets.map((line) => (
                        <tr key={`asset-${line.name}`}>
                          <td>{line.name}</td>
                          <td>{formatCurrency(line.amount)}</td>
                        </tr>
                      ))}
                      <tr>
                        <td><strong>Total Assets</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_assets)}</strong></td>
                      </tr>
                    </tbody>
                  </table>
                </section>

                <section>
                  <h4>Liabilities</h4>
                  <table className="table">
                    <tbody>
                      {balanceSheetReport.liabilities.map((line) => (
                        <tr key={`liability-${line.name}`}>
                          <td>{line.name}</td>
                          <td>{formatCurrency(line.amount)}</td>
                        </tr>
                      ))}
                      <tr>
                        <td><strong>Total Liabilities</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_liabilities)}</strong></td>
                      </tr>
                    </tbody>
                  </table>

                  <h4 style={{ marginTop: 14 }}>Equity</h4>
                  <table className="table">
                    <tbody>
                      {balanceSheetReport.equity.map((line) => (
                        <tr key={`equity-${line.name}`}>
                          <td>{line.name}</td>
                          <td>{formatCurrency(line.amount)}</td>
                        </tr>
                      ))}
                      <tr>
                        <td><strong>Total Equity</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_equity)}</strong></td>
                      </tr>
                      <tr>
                        <td><strong>Total Liabilities + Equity</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_liabilities + balanceSheetReport.total_equity)}</strong></td>
                      </tr>
                    </tbody>
                  </table>
                </section>
              </div>

              <p className={`balance-sheet-status ${balanceSheetReport.is_balanced ? 'ok' : 'warn'}`}>
                {balanceSheetReport.is_balanced
                  ? 'Balance sheet is balanced.'
                  : 'Balance sheet is not balanced. Review source transactions and mappings.'}
              </p>
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ marginTop: 18 }}>
        <h3>Quick Stats</h3>
        <table className="table">
          <tbody>
            <tr>
              <td><strong>Average Transaction</strong></td>
              <td>${salesReport?.average_transaction.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>Total Tax Collected</strong></td>
              <td>${salesReport?.total_tax.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>Total Discounts</strong></td>
              <td>${salesReport?.total_discount.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>Total Expenses</strong></td>
              <td>${ledgerReport?.total_expenses.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Reports;
