import { useEffect, useMemo, useState } from 'react';
import { ledgerAPI } from '../api';

interface LedgerRecord {
  id: number;
  transaction_date: string;
  transaction_type: string;
  description: string;
  amount: number;
  balance: number;
  payment_method: string;
  notes?: string;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

function Ledger() {
  const [records, setRecords] = useState<LedgerRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterType, setFilterType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);

  const totalPages = useMemo(
    () => (totalCount > 0 ? Math.ceil(totalCount / pageSize) : 1),
    [totalCount, pageSize]
  );

  useEffect(() => {
    void fetchPage(1, 20, { filterType: '', startDate: '', endDate: '' });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchPage = async (
    nextPage: number,
    nextPageSize: number,
    overrides: { filterType: string; startDate: string; endDate: string }
  ) => {
    try {
      setLoading(true);
      const safePage = Math.max(1, nextPage);
      const safePageSize = Math.max(1, nextPageSize);
      const response = await ledgerAPI.getRecords({
        transaction_type: overrides.filterType || undefined,
        start_date: overrides.startDate ? new Date(`${overrides.startDate}T00:00:00`).toISOString() : undefined,
        end_date: overrides.endDate ? new Date(`${overrides.endDate}T23:59:59`).toISOString() : undefined,
        skip: (safePage - 1) * safePageSize,
        limit: safePageSize,
        paginated: true,
      });
      const data = response.data as { items: LedgerRecord[]; total: number };
      setRecords(data.items || []);
      setTotalCount(data.total || 0);
      setPage(safePage);
      setPageSize(safePageSize);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load ledger records');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = () => void fetchPage(1, pageSize, { filterType, startDate, endDate });

  const handleReset = () => {
    setFilterType('');
    setStartDate('');
    setEndDate('');
    void fetchPage(1, pageSize, { filterType: '', startDate: '', endDate: '' });
  };

  const formatDate = (dateString: string) => new Date(dateString).toLocaleString();

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'sale':
        return '#27ae60';
      case 'purchase':
        return '#e74c3c';
      case 'return':
        return '#f39c12';
      case 'adjustment':
        return '#3498db';
      default:
        return '#7f8c8d';
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Ledger Records</h1>
        <p>View all financial transactions</p>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 16, alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{ fontWeight: '500' }}>Filter by Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
            >
              <option value="">All Types</option>
              <option value="sale">Sales</option>
              <option value="purchase">Purchases</option>
              <option value="return">Returns</option>
              <option value="adjustment">Adjustments</option>
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{ fontWeight: '500' }}>From</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{ fontWeight: '500' }}>To</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
            />
          </div>

          <button className="button button-primary" onClick={handleApply}>Apply Filters</button>
          <button className="button" onClick={handleReset}>Reset</button>
        </div>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <>
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Balance</th>
                  <th>Payment Method</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{formatDate(record.transaction_date)}</td>
                    <td>
                      <span
                        style={{
                          padding: '5px 10px',
                          borderRadius: '5px',
                          backgroundColor: getTypeColor(record.transaction_type),
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          textTransform: 'uppercase',
                        }}
                      >
                        {record.transaction_type}
                      </span>
                    </td>
                    <td>{record.description}</td>
                    <td
                      style={{
                        color: record.transaction_type === 'sale' ? '#27ae60' : '#e74c3c',
                        fontWeight: 'bold',
                      }}
                    >
                      {record.transaction_type === 'sale' ? '+' : '-'}${record.amount.toFixed(2)}
                    </td>
                    <td style={{ fontWeight: 'bold' }}>${record.balance.toFixed(2)}</td>
                    <td style={{ textTransform: 'capitalize' }}>
                      {record.payment_method.replace('_', ' ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {records.length === 0 && (
              <p style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
                No ledger records found
              </p>
            )}

            {totalCount > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginTop: 14, flexWrap: 'wrap' }}>
                <div style={{ color: '#7f8c8d', fontSize: 14 }}>
                  Showing {totalCount === 0 ? 0 : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)} of {totalCount}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <label style={{ fontSize: 14 }}>Rows per page</label>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      const nextSize = Number.parseInt(e.target.value, 10) || 20;
                      void fetchPage(1, nextSize, { filterType, startDate, endDate });
                    }}
                  >
                    {PAGE_SIZE_OPTIONS.map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>

                  <button
                    className="button"
                    onClick={() => void fetchPage(page - 1, pageSize, { filterType, startDate, endDate })}
                    disabled={page <= 1}
                  >
                    Previous
                  </button>

                  <span style={{ minWidth: 120, textAlign: 'center' }}>
                    Page {page} of {totalPages}
                  </span>

                  <button
                    className="button"
                    onClick={() => void fetchPage(page + 1, pageSize, { filterType, startDate, endDate })}
                    disabled={page >= totalPages}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Ledger;
