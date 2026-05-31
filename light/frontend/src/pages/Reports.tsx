import { useEffect, useState } from 'react';
import { reportsAPI, salesUserAPI } from '../api';
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

type CashierClosureDetail = {
  sales_user_id: number;
  sales_user_name: string;
  start_date: string;
  end_date: string;
  total_sales: number;
  transaction_count: number;
  by_payment_method: { [key: string]: number };
  reconciliation_status: 'reconciled' | 'variance' | 'unreconciled';
  expected_amount: number;
  actual_amount: number;
  variance: number;
};

type CashierClosureSummaryReport = {
  report_date: string;
  period_start: string;
  period_end: string;
  closures: CashierClosureDetail[];
  total_closures: number;
  total_revenue: number;
  total_transactions: number;
  total_variance: number;
  reconciliation_status: 'all_reconciled' | 'partial_variance' | 'unreconciled';
};

type SalesUser = {
  id: number;
  name: string;
};

const REPORT_GROUPS: ReportGroup[] = [
  {
    title: 'reports_section_core_financial_title',
    subtitle: 'reports_section_core_financial_subtitle',
    icon: '📘',
    reports: [
      {
        key: 'balance_sheet',
        name: 'reports_item_balance_sheet_name',
        description: 'reports_item_balance_sheet_desc',
        status: 'ready',
      },
      {
        key: 'income_statement',
        name: 'reports_item_income_statement_name',
        description: 'reports_item_income_statement_desc',
        status: 'coming_soon',
      },
      {
        key: 'cash_flow_statement',
        name: 'reports_item_cash_flow_statement_name',
        description: 'reports_item_cash_flow_statement_desc',
        status: 'coming_soon',
      },
    ],
  },
  {
    title: 'reports_section_audit_title',
    subtitle: 'reports_section_audit_subtitle',
    icon: '🧾',
    reports: [
      {
        key: 'trial_balance',
        name: 'reports_item_trial_balance_name',
        description: 'reports_item_trial_balance_desc',
        status: 'coming_soon',
      },
      {
        key: 'cashier_closure_summary',
        name: 'reports_item_cashier_closure_summary_name',
        description: 'reports_item_cashier_closure_summary_desc',
        status: 'ready',
      },
      {
        key: 'cashier_closure_daily',
        name: 'reports_item_cashier_closure_daily_name',
        description: 'reports_item_cashier_closure_daily_desc',
        status: 'ready',
      },
    ],
  },
  {
    title: 'reports_section_tax_title',
    subtitle: 'reports_section_tax_subtitle',
    icon: '💼',
    reports: [
      {
        key: 'tax_summary',
        name: 'reports_item_tax_summary_name',
        description: 'reports_item_tax_summary_desc',
        status: 'coming_soon',
      },
      {
        key: 'accounts_receivable',
        name: 'reports_item_accounts_receivable_name',
        description: 'reports_item_accounts_receivable_desc',
        status: 'coming_soon',
      },
      {
        key: 'accounts_payable',
        name: 'reports_item_accounts_payable_name',
        description: 'reports_item_accounts_payable_desc',
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
  const [cashierClosureReport, setCashierClosureReport] = useState<CashierClosureSummaryReport | null>(null);
  const [salesUsers, setSalesUsers] = useState<SalesUser[]>([]);
  const [closureFilterDate, setClosureFilterDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [closureFilterSalesUserId, setClosureFilterSalesUserId] = useState<string>('');
  const { i18n, t } = useTranslation();
  console.log("Current detected language:", i18n.language);

  useEffect(() => {
    loadReports();
  }, [dateRange]);

  useEffect(() => {
    loadSalesUsers();
  }, []);

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

  const loadSalesUsers = async () => {
    try {
      const response = await salesUserAPI.getAll({ active_only: true });
      setSalesUsers(response.data || []);
    } catch (err) {
      console.error('Failed to load sales users for report filters:', err);
      setSalesUsers([]);
    }
  };

  const openCashierClosureDailyReport = async () => {
    try {
      setReportActionLoading(true);
      setReportActionError('');
      setActiveReportKey('cashier_closure_daily');

      const dayStart = new Date(`${closureFilterDate}T00:00:00`);
      const dayEnd = new Date(`${closureFilterDate}T23:59:59.999`);

      const response = await reportsAPI.getCashierClosureSummaryReport({
        start_date: dayStart.toISOString(),
        end_date: dayEnd.toISOString(),
        sales_user_id: closureFilterSalesUserId ? Number(closureFilterSalesUserId) : undefined,
      });

      setCashierClosureReport(response.data);
    } catch (err: any) {
      setCashierClosureReport(null);
      setReportActionError(err.response?.data?.detail || t('report_cashier_closure_daily_load_failed'));
    } finally {
      setReportActionLoading(false);
    }
  };

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

    if (report.key === 'cashier_closure_summary') {
      try {
        setReportActionLoading(true);
        const days = parseInt(dateRange);
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        
        const response = await reportsAPI.getCashierClosureSummaryReport({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
        });
        setCashierClosureReport(response.data);
      } catch (err: any) {
        setCashierClosureReport(null);
        setReportActionError(err.response?.data?.detail || 'Failed to load cashier closure report');
      } finally {
        setReportActionLoading(false);
      }
      return;
    }

    if (report.key === 'cashier_closure_daily') {
      await openCashierClosureDailyReport();
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
          <p className="mt-4 text-lg text-gray-600">{t('reports_loading')}</p>
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
              <p className="font-semibold">{t('reports_error_title')}</p>
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
        <h1>{t('reports_page_title')}</h1>
        <p>{t('reports_page_subtitle')}</p>
      </div>

      <div className="mb-6" style={{ marginTop: 12 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ minWidth: 220 }}>
            <label style={{ display: 'block', marginBottom: 6 }}>{t('reports_date_range')}</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="7">{t('reports_date_range_7days')}</option>
              <option value="30">{t('reports_date_range_30days')}</option>
              <option value="90">{t('reports_date_range_90days')}</option>
              <option value="365">{t('reports_date_range_1year')}</option>
            </select>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>{t('reports_stat_total_sales')}</h3>
          <div className="value">${salesReport?.total_sales.toFixed(2)}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{salesReport?.total_transactions} {t('reports_stat_transactions')}</p>
        </div>

        <div className="stat-card">
          <h3>{t('reports_stat_current_balance')}</h3>
          <div className="value">${ledgerReport?.current_balance.toFixed(2)}</div>
          <p style={{ color: '#27ae60', marginTop: 10 }}>{t('reports_stat_income')} ${ledgerReport?.total_income.toFixed(2)}</p>
        </div>

        <div className="stat-card">
          <h3>{t('reports_stat_inventory_value')}</h3>
          <div className="value">${inventoryReport?.total_value.toFixed(2)}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{inventoryReport?.total_items} {t('reports_stat_items')}</p>
        </div>

        <div className="stat-card">
          <h3>{t('reports_stat_low_stock')}</h3>
          <div className="value" style={{ color: inventoryReport?.low_stock_items > 0 ? '#e74c3c' : '#27ae60' }}>{inventoryReport?.low_stock_items}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{t('reports_stat_out_of_stock')} {inventoryReport?.out_of_stock_items}</p>
        </div>

        <div className="stat-card">
          <h3>{t('reports_stat_net_profit')}</h3>
          <div className="value" style={{ color: (ledgerReport?.total_income - ledgerReport?.total_expenses) >= 0 ? '#1abc9c' : '#e74c3c' }}>${((ledgerReport?.total_income || 0) - (ledgerReport?.total_expenses || 0)).toFixed(2)}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{t('reports_stat_income_expenses')}</p>
        </div>

        <div className="stat-card">
          <h3>{t('reports_stat_total_transactions')}</h3>
          <div className="value">{ledgerReport?.transaction_count}</div>
          <p style={{ color: '#7f8c8d', marginTop: 10 }}>{t('reports_stat_all_ledgers')}</p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 10 }}>
        <h3>{t('reports_catalog_title')}</h3>
        <p style={{ color: '#7f8c8d', marginTop: 0, marginBottom: 16 }}>
          {t('reports_catalog_subtitle')}
        </p>

        <div className="reports-groups-grid">
          {REPORT_GROUPS.map((group) => (
            <section className="report-group-card" key={group.title}>
              <div className="report-group-header">
                <div>
                  <h4>
                    <span style={{ marginRight: 8 }}>{group.icon}</span>
                    {t(group.title)}
                  </h4>
                  <p>{t(group.subtitle)}</p>
                </div>
              </div>

              <div className="report-items-list">
                {group.reports.map((report) => (
                  <article className="report-item" key={report.key}>
                    <div>
                      <div className="report-item-title-row">
                        <h5>{t(report.name)}</h5>
                        <span className={`report-status-pill report-status-${report.status}`}>
                          {report.status === 'ready' ? t('reports_item_status_available') : t('reports_item_status_coming_soon')}
                        </span>
                      </div>
                      <p>{t(report.description)}</p>
                    </div>
                    <button
                      type="button"
                      className="button button-primary"
                      onClick={() => handleOpenReport(report)}
                      disabled={report.status !== 'ready'}
                      style={{ opacity: report.status === 'ready' ? 1 : 0.55 }}
                    >
                      {report.status === 'ready' ? t('reports_button_open') : t('reports_button_planned')}
                    </button>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>

      {(reportActionLoading || reportActionError || balanceSheetReport || cashierClosureReport) && (
        <div className="card" style={{ marginTop: 18 }}>
          <h3>{t('reports_viewer_title')}</h3>

          {activeReportKey === 'cashier_closure_daily' && (
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14, alignItems: 'end' }}>
              <div style={{ minWidth: 180 }}>
                <label style={{ display: 'block', marginBottom: 6 }}>{t('report_cashier_closure_filter_day')}</label>
                <input
                  type="date"
                  value={closureFilterDate}
                  onChange={(e) => setClosureFilterDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div style={{ minWidth: 220 }}>
                <label style={{ display: 'block', marginBottom: 6 }}>{t('report_cashier_closure_filter_cashier')}</label>
                <select
                  value={closureFilterSalesUserId}
                  onChange={(e) => setClosureFilterSalesUserId(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">{t('report_cashier_closure_filter_all_cashiers')}</option>
                  {salesUsers.map((user) => (
                    <option key={user.id} value={user.id}>{user.name}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                className="button button-primary"
                onClick={openCashierClosureDailyReport}
                disabled={reportActionLoading}
                style={{ height: 40 }}
              >
                {t('report_cashier_closure_filter_run')}
              </button>
            </div>
          )}

          {reportActionLoading && <p className="report-viewer-note">{t('reports_viewer_loading')}</p>}
          {!reportActionLoading && reportActionError && (
            <p className="report-viewer-error">{reportActionError}</p>
          )}

          {!reportActionLoading && !reportActionError && activeReportKey === 'balance_sheet' && balanceSheetReport && (
            <div className="balance-sheet-wrap">
              <div className="balance-sheet-meta">
                <strong>{t('reports_balance_sheet_as_of')}</strong> {new Date(balanceSheetReport.as_of_date).toLocaleString()}
              </div>

              <div className="balance-sheet-grid">
                <section>
                  <h4>{t('reports_balance_sheet_assets')}</h4>
                  <table className="table">
                    <tbody>
                      {balanceSheetReport.assets.map((line) => (
                        <tr key={`asset-${line.name}`}>
                          <td>{line.name}</td>
                          <td>{formatCurrency(line.amount)}</td>
                        </tr>
                      ))}
                      <tr>
                        <td><strong>{t('reports_balance_sheet_total_assets')}</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_assets)}</strong></td>
                      </tr>
                    </tbody>
                  </table>
                </section>

                <section>
                  <h4>{t('reports_balance_sheet_liabilities')}</h4>
                  <table className="table">
                    <tbody>
                      {balanceSheetReport.liabilities.map((line) => (
                        <tr key={`liability-${line.name}`}>
                          <td>{line.name}</td>
                          <td>{formatCurrency(line.amount)}</td>
                        </tr>
                      ))}
                      <tr>
                        <td><strong>{t('reports_balance_sheet_total_liabilities')}</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_liabilities)}</strong></td>
                      </tr>
                    </tbody>
                  </table>

                  <h4 style={{ marginTop: 14 }}>{t('reports_balance_sheet_equity')}</h4>
                  <table className="table">
                    <tbody>
                      {balanceSheetReport.equity.map((line) => (
                        <tr key={`equity-${line.name}`}>
                          <td>{line.name}</td>
                          <td>{formatCurrency(line.amount)}</td>
                        </tr>
                      ))}
                      <tr>
                        <td><strong>{t('reports_balance_sheet_total_equity')}</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_equity)}</strong></td>
                      </tr>
                      <tr>
                        <td><strong>{t('reports_balance_sheet_total_liab_equity')}</strong></td>
                        <td><strong>{formatCurrency(balanceSheetReport.total_liabilities + balanceSheetReport.total_equity)}</strong></td>
                      </tr>
                    </tbody>
                  </table>
                </section>
              </div>

              <p className={`balance-sheet-status ${balanceSheetReport.is_balanced ? 'ok' : 'warn'}`}>
                {balanceSheetReport.is_balanced
                  ? t('reports_balance_sheet_balanced')
                  : t('reports_balance_sheet_not_balanced')}
              </p>
            </div>
          )}

          {!reportActionLoading && !reportActionError && (activeReportKey === 'cashier_closure_summary' || activeReportKey === 'cashier_closure_daily') && cashierClosureReport && (
            <div className="cashier-closure-wrap">
              <div className="cashier-closure-meta">
                <strong>{t('report_cashier_closure_report_date')}:</strong> {new Date(cashierClosureReport.report_date).toLocaleString()} | 
                <strong style={{ marginLeft: 16 }}>{t('report_cashier_closure_period')}:</strong> {new Date(cashierClosureReport.period_start).toLocaleDateString()} to {new Date(cashierClosureReport.period_end).toLocaleDateString()}
              </div>

              <div className="cashier-closure-summary" style={{ marginBottom: 20, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
                <h4 style={{ marginTop: 0 }}>{t('report_cashier_closure_summary')}</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                  <div>
                    <strong>{t('report_cashier_closure_total_closures')}:</strong>
                    <div style={{ fontSize: '1.5em', color: '#2c3e50', marginTop: 4 }}>{cashierClosureReport.total_closures}</div>
                  </div>
                  <div>
                    <strong>{t('report_cashier_closure_total_revenue')}:</strong>
                    <div style={{ fontSize: '1.5em', color: '#27ae60', marginTop: 4 }}>{formatCurrency(cashierClosureReport.total_revenue)}</div>
                  </div>
                  <div>
                    <strong>{t('report_cashier_closure_total_transactions')}:</strong>
                    <div style={{ fontSize: '1.5em', color: '#2c3e50', marginTop: 4 }}>{cashierClosureReport.total_transactions}</div>
                  </div>
                  <div>
                    <strong>{t('report_cashier_closure_total_variance')}:</strong>
                    <div style={{ fontSize: '1.5em', color: cashierClosureReport.total_variance > 0 ? '#e74c3c' : '#27ae60', marginTop: 4 }}>{formatCurrency(cashierClosureReport.total_variance)}</div>
                  </div>
                </div>
              </div>

              <div className="cashier-closure-status" style={{ marginBottom: 20 }}>
                <p className={`report-status-label`}>
                  <strong>{t('report_cashier_closure_reconciliation_status')}:</strong> <span style={{
                    padding: '4px 8px',
                    borderRadius: 4,
                    backgroundColor: cashierClosureReport.reconciliation_status === 'all_reconciled' ? '#d4edda' : 
                                     cashierClosureReport.reconciliation_status === 'partial_variance' ? '#fff3cd' : '#f8d7da',
                    color: cashierClosureReport.reconciliation_status === 'all_reconciled' ? '#155724' : 
                           cashierClosureReport.reconciliation_status === 'partial_variance' ? '#856404' : '#721c24'
                  }}>
                    {cashierClosureReport.reconciliation_status === 'all_reconciled' ? t('report_cashier_closure_all_reconciled') : 
                     cashierClosureReport.reconciliation_status === 'partial_variance' ? t('report_cashier_closure_partial_variance') : 
                     t('report_cashier_closure_unreconciled')}
                  </span>
                </p>
              </div>

              <h4>{t('report_cashier_closure_closures')}</h4>
              <div style={{ overflowX: 'auto' }}>
                <table className="table" style={{ width: '100%' }}>
                  <thead>
                    <tr>
                      <th>{t('report_cashier_closure_cashier_name')}</th>
                      <th>{t('report_cashier_closure_col_period')}</th>
                      <th>{t('report_cashier_closure_col_transactions')}</th>
                      <th>{t('report_cashier_closure_col_total_sales')}</th>
                      <th>{t('report_cashier_closure_col_expected')}</th>
                      <th>{t('report_cashier_closure_col_actual')}</th>
                      <th>{t('report_cashier_closure_col_variance')}</th>
                      <th>{t('report_cashier_closure_col_status')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cashierClosureReport.closures.map((closure) => (
                      <tr key={closure.sales_user_id}>
                        <td><strong>{closure.sales_user_name}</strong></td>
                        <td>{new Date(closure.start_date).toLocaleDateString()} - {new Date(closure.end_date).toLocaleDateString()}</td>
                        <td>{closure.transaction_count}</td>
                        <td>{formatCurrency(closure.total_sales)}</td>
                        <td>{formatCurrency(closure.expected_amount)}</td>
                        <td>{formatCurrency(closure.actual_amount)}</td>
                        <td style={{ color: closure.variance > 0 ? '#e74c3c' : '#27ae60' }}>{formatCurrency(closure.variance)}</td>
                        <td>
                          <span style={{
                            padding: '2px 6px',
                            borderRadius: 3,
                            fontSize: '0.85em',
                            backgroundColor: closure.reconciliation_status === 'reconciled' ? '#d4edda' : 
                                           closure.reconciliation_status === 'variance' ? '#fff3cd' : '#f8d7da',
                            color: closure.reconciliation_status === 'reconciled' ? '#155724' : 
                                 closure.reconciliation_status === 'variance' ? '#856404' : '#721c24'
                          }}>
                            {closure.reconciliation_status === 'reconciled' ? t('report_cashier_closure_reconciled') : 
                             closure.reconciliation_status === 'variance' ? t('report_cashier_closure_variance') : 
                             t('report_cashier_closure_unreconciled')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: 16 }}>
                <h4>{t('report_cashier_closure_payment_breakdown')}</h4>
                {cashierClosureReport.closures.map((closure) => (
                  closure.by_payment_method && Object.keys(closure.by_payment_method).length > 0 && (
                    <div key={`breakdown-${closure.sales_user_id}`} style={{ marginBottom: 12, padding: 10, backgroundColor: '#fafafa', borderRadius: 4 }}>
                      <strong>{closure.sales_user_name}</strong>
                      <div style={{ marginTop: 6, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10 }}>
                        {Object.entries(closure.by_payment_method).map(([method, amount]) => (
                          <div key={`${closure.sales_user_id}-${method}`}>
                            <div style={{ fontSize: '0.9em', color: '#7f8c8d' }}>{method}</div>
                            <div style={{ fontSize: '1.1em', fontWeight: 'bold', color: '#2c3e50' }}>{formatCurrency(amount as number)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ marginTop: 18 }}>
        <h3>{t('reports_quick_stats')}</h3>
        <table className="table">
          <tbody>
            <tr>
              <td><strong>{t('reports_quick_stats_avg_transaction')}</strong></td>
              <td>${salesReport?.average_transaction.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>{t('reports_quick_stats_tax_collected')}</strong></td>
              <td>${salesReport?.total_tax.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>{t('reports_quick_stats_discounts')}</strong></td>
              <td>${salesReport?.total_discount.toFixed(2)}</td>
            </tr>
            <tr>
              <td><strong>{t('reports_quick_stats_expenses')}</strong></td>
              <td>${ledgerReport?.total_expenses.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Reports;
