import { Fragment, useEffect, useMemo, useState } from 'react';
import { posAPI } from '../api';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../AuthContext';
import '../i18n';

interface TransactionItem {
  id: number;
  inventory_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

interface TransactionRecord {
  id: number;
  transaction_number: string;
  transaction_date: string;
  customer_name?: string | null;
  payment_method: string;
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  payment_received: number;
  change_returned: number;
  notes?: string | null;
  items: TransactionItem[];
}

interface TransactionsPageResponse {
  items: TransactionRecord[];
  total: number;
  skip: number;
  limit: number;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value || 0);
}

function toIsoDateStart(date: string): string | undefined {
  if (!date) {
    return undefined;
  }
  return new Date(`${date}T00:00:00`).toISOString();
}

function toIsoDateEnd(date: string): string | undefined {
  if (!date) {
    return undefined;
  }
  return new Date(`${date}T23:59:59`).toISOString();
}

function TransactionsHistory() {
  const { t } = useTranslation();
  const { hasRole } = useAuth();
  const canRefund = hasRole('manager', 'super_admin');
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchText, setSearchText] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [refundQtyByItem, setRefundQtyByItem] = useState<Record<number, string>>({});
  const [refundReasonByItem, setRefundReasonByItem] = useState<Record<number, string>>({});
  const [refundRestockByItem, setRefundRestockByItem] = useState<Record<number, boolean>>({});
  const [refundingItemId, setRefundingItemId] = useState<number | null>(null);

  const loadTransactions = async (
    nextPage: number = page,
    nextPageSize: number = pageSize,
    overrides?: {
      searchText?: string;
      startDate?: string;
      endDate?: string;
      paymentMethod?: string;
    }
  ) => {
    try {
      setLoading(true);
      const safePage = Math.max(1, nextPage);
      const safePageSize = Math.max(1, nextPageSize);
      const skip = (safePage - 1) * safePageSize;
      const effectiveSearchText = overrides?.searchText ?? searchText;
      const effectiveStartDate = overrides?.startDate ?? startDate;
      const effectiveEndDate = overrides?.endDate ?? endDate;
      const effectivePaymentMethod = overrides?.paymentMethod ?? paymentMethod;
      const response = await posAPI.getTransactions({
        search: effectiveSearchText.trim() || undefined,
        start_date: toIsoDateStart(effectiveStartDate),
        end_date: toIsoDateEnd(effectiveEndDate),
        payment_method: effectivePaymentMethod !== 'all' ? effectivePaymentMethod : undefined,
        skip,
        limit: safePageSize,
        paginated: true,
      });

      const data: TransactionsPageResponse = response.data;
      setTransactions(data?.items || []);
      setTotalCount(data?.total || 0);
      setPage(safePage);
      setPageSize(safePageSize);
      setExpandedIds(new Set());
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load transactions history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTransactions(1, pageSize);
  }, []);

  const totalPages = useMemo(() => {
    if (totalCount <= 0) {
      return 1;
    }
    return Math.ceil(totalCount / pageSize);
  }, [totalCount, pageSize]);

  const totalAmount = useMemo(
    () => transactions.reduce((sum, tx) => sum + (tx.total || 0), 0),
    [transactions]
  );

  const totalItemsSold = useMemo(
    () =>
      transactions.reduce(
        (sum, tx) => sum + tx.items.reduce((itemSum, item) => itemSum + (item.quantity || 0), 0),
        0
      ),
    [transactions]
  );

  const toggleTransactionDetails = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleItemRefund = async (tx: TransactionRecord, item: TransactionItem) => {
    const qtyValue = refundQtyByItem[item.id] || '';
    const refundQty = Number.parseInt(qtyValue, 10);

    if (!Number.isFinite(refundQty) || refundQty <= 0) {
      alert(t('transactions_history_enter_valid_refund_qty'));
      return;
    }

    if (refundQty > item.quantity) {
      alert(t('transactions_history_refund_qty_exceed', { quantity: item.quantity }));
      return;
    }

    const shouldProceed = confirm(
      t('transactions_history_refund_confirm', {
        qty: refundQty,
        product: item.product_name,
        transaction: tx.transaction_number,
      })
    );
    if (!shouldProceed) {
      return;
    }

    try {
      setRefundingItemId(item.id);
      await posAPI.refundTransactionItem(tx.id, {
        pos_item_id: item.id,
        quantity: refundQty,
        reason: (refundReasonByItem[item.id] || '').trim() || undefined,
        restock: refundRestockByItem[item.id] ?? true,
      });

      alert(t('transactions_history_refund_success'));
      setRefundQtyByItem((prev) => ({ ...prev, [item.id]: '' }));
      setRefundReasonByItem((prev) => ({ ...prev, [item.id]: '' }));
      setRefundRestockByItem((prev) => ({ ...prev, [item.id]: true }));
      await loadTransactions();
    } catch (err: any) {
      alert(err.response?.data?.detail || t('transactions_history_refund_failed'));
    } finally {
      setRefundingItemId(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>🧾 {t('transactions_history_title')}</h1>
        <p>{t('transactions_history_subtitle')}</p>
      </div>

      <div className="card">
        <h3>{t('transactions_history_filters')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>{t('transactions_history_search')}</label>
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder={t('transactions_history_search_placeholder')}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>{t('transactions_history_from')}</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>{t('transactions_history_to')}</label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>{t('transactions_history_payment_method')}</label>
            <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
              <option value="all">{t('transactions_history_all')}</option>
              <option value="cash">{t('transactions_history_payment_cash')}</option>
              <option value="card">{t('transactions_history_payment_card')}</option>
              <option value="bank_transfer">{t('transactions_history_payment_bank_transfer')}</option>
              <option value="mobile_payment">{t('transactions_history_payment_mobile_payment')}</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
          <button className="button button-primary" onClick={() => void loadTransactions(1, pageSize)}>
            {t('transactions_history_apply_filters')}
          </button>
          <button
            className="button"
            onClick={() => {
              setSearchText('');
              setStartDate('');
              setEndDate('');
              setPaymentMethod('all');
              setExpandedIds(new Set());
              setPage(1);
              void loadTransactions(1, pageSize, {
                searchText: '',
                startDate: '',
                endDate: '',
                paymentMethod: 'all',
              });
            }}
          >
            {t('transactions_history_reset')}
          </button>
        </div>
      </div>

      <div className="stats-grid" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <h3>{t('transactions_history_total_transactions')}</h3>
          <div className="value">{totalCount}</div>
        </div>
        <div className="stat-card">
          <h3>{t('transactions_history_total_sales_amount')}</h3>
          <div className="value" style={{ fontSize: 28 }}>{formatCurrency(totalAmount)}</div>
        </div>
        <div className="stat-card">
          <h3>{t('transactions_history_total_units_sold')}</h3>
          <div className="value">{totalItemsSold}</div>
        </div>
      </div>

      {loading && <div className="loading">{t('transactions_history_loading')}</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && (
        <div className="card">
          <h3>{t('transactions_history_transactions')}</h3>

          {transactions.length === 0 ? (
            <p style={{ color: '#7f8c8d' }}>{t('transactions_history_no_transactions')}</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>{t('transactions_history_col_transaction')}</th>
                  <th>{t('transactions_history_col_date')}</th>
                  <th>{t('transactions_history_col_customer')}</th>
                  <th>{t('transactions_history_col_payment')}</th>
                  <th>{t('transactions_history_col_total')}</th>
                  <th>{t('transactions_history_col_details')}</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => {
                  const isExpanded = expandedIds.has(tx.id);
                  return (
                    <Fragment key={tx.id}>
                      <tr>
                        <td>{tx.transaction_number}</td>
                        <td>{new Date(tx.transaction_date).toLocaleString()}</td>
                        <td>{tx.customer_name || t('transactions_history_walk_in')}</td>
                        <td style={{ textTransform: 'capitalize' }}>{(tx.payment_method || '').replace('_', ' ')}</td>
                        <td>{formatCurrency(tx.total)}</td>
                        <td>
                          <button className="button" onClick={() => toggleTransactionDetails(tx.id)}>
                            {isExpanded ? t('transactions_history_hide') : t('transactions_history_view')}
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr>
                          <td colSpan={6} style={{ background: '#f9fbff' }}>
                            <div style={{ padding: '8px 0' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 8, marginBottom: 10 }}>
                                <div><strong>{t('transactions_history_subtotal')}:</strong> {formatCurrency(tx.subtotal)}</div>
                                <div><strong>{t('transactions_history_tax')}:</strong> {formatCurrency(tx.tax)}</div>
                                <div><strong>{t('transactions_history_discount')}:</strong> {formatCurrency(tx.discount)}</div>
                                <div><strong>{t('transactions_history_paid')}:</strong> {formatCurrency(tx.payment_received)}</div>
                                <div><strong>{t('transactions_history_change')}:</strong> {formatCurrency(tx.change_returned)}</div>
                                <div><strong>{t('transactions_history_total')}:</strong> {formatCurrency(tx.total)}</div>
                              </div>

                              {tx.notes && (
                                <div style={{ marginBottom: 10 }}>
                                  <strong>{t('transactions_history_notes')}:</strong> {tx.notes}
                                </div>
                              )}

                              <table className="table" style={{ background: '#fff', borderRadius: 6, overflow: 'hidden' }}>
                                <thead>
                                  <tr>
                                    <th>{t('transactions_history_item')}</th>
                                    <th>{t('transactions_history_qty')}</th>
                                    <th>{t('transactions_history_unit_price')}</th>
                                    <th>{t('transactions_history_subtotal')}</th>
                                    {canRefund && <th>{t('transactions_history_refund_qty')}</th>}
                                    {canRefund && <th>{t('transactions_history_reason')}</th>}
                                    {canRefund && <th>{t('transactions_history_restock')}</th>}
                                    {canRefund && <th>{t('transactions_history_action')}</th>}
                                  </tr>
                                </thead>
                                <tbody>
                                  {tx.items.map((item) => (
                                    <tr key={item.id}>
                                      <td>{item.product_name}</td>
                                      <td>{item.quantity}</td>
                                      <td>{formatCurrency(item.unit_price)}</td>
                                      <td>{formatCurrency(item.subtotal)}</td>
                                      {canRefund && (
                                      <td style={{ minWidth: 110 }}>
                                        <input
                                          type="number"
                                          min="1"
                                          max={item.quantity}
                                          step="1"
                                          value={refundQtyByItem[item.id] ?? ''}
                                          onChange={(e) =>
                                            setRefundQtyByItem((prev) => ({ ...prev, [item.id]: e.target.value }))
                                          }
                                          placeholder={t('transactions_history_qty')}
                                          disabled={refundingItemId === item.id}
                                          style={{ width: '100%' }}
                                        />
                                      </td>
                                      )}
                                      {canRefund && (
                                      <td style={{ minWidth: 180 }}>
                                        <input
                                          type="text"
                                          value={refundReasonByItem[item.id] ?? ''}
                                          onChange={(e) =>
                                            setRefundReasonByItem((prev) => ({ ...prev, [item.id]: e.target.value }))
                                          }
                                          placeholder={t('transactions_history_optional')}
                                          disabled={refundingItemId === item.id}
                                          style={{ width: '100%' }}
                                        />
                                      </td>
                                      )}
                                      {canRefund && (
                                      <td>
                                        <input
                                          type="checkbox"
                                          checked={refundRestockByItem[item.id] ?? true}
                                          onChange={(e) =>
                                            setRefundRestockByItem((prev) => ({ ...prev, [item.id]: e.target.checked }))
                                          }
                                          disabled={refundingItemId === item.id}
                                        />
                                      </td>
                                      )}
                                      {canRefund && (
                                      <td>
                                        <button
                                          className="button button-danger"
                                          onClick={() => void handleItemRefund(tx, item)}
                                          disabled={refundingItemId === item.id}
                                        >
                                          {refundingItemId === item.id
                                            ? t('transactions_history_processing')
                                            : t('transactions_history_refund_item')}
                                        </button>
                                      </td>
                                      )}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          )}

          {!loading && !error && totalCount > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginTop: 14, flexWrap: 'wrap' }}>
              <div style={{ color: '#7f8c8d', fontSize: 14 }}>
                {t('transactions_history_page_summary', {
                  from: totalCount === 0 ? 0 : (page - 1) * pageSize + 1,
                  to: Math.min(page * pageSize, totalCount),
                  total: totalCount,
                })}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <label style={{ fontSize: 14 }}>{t('transactions_history_rows_per_page')}</label>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    const nextSize = Number.parseInt(e.target.value, 10) || 20;
                    void loadTransactions(1, nextSize);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>

                <button
                  className="button"
                  onClick={() => void loadTransactions(page - 1, pageSize)}
                  disabled={page <= 1 || loading}
                >
                  {t('transactions_history_previous')}
                </button>

                <span style={{ minWidth: 120, textAlign: 'center' }}>
                  {t('transactions_history_page_x_of_y', { page, totalPages })}
                </span>

                <button
                  className="button"
                  onClick={() => void loadTransactions(page + 1, pageSize)}
                  disabled={page >= totalPages || loading}
                >
                  {t('transactions_history_next')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TransactionsHistory;
