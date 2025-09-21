import React, { useEffect, useState } from 'react';

type LedgerEntry = {
  id?: number;
  datetime: string;
  description: string;
  amount: number;
  debit_account: string;
  credit_account: string;
};

const apiUrl = 'http://localhost:8000/transactions';

function getTodayISODate() {
  return new Date().toISOString().slice(0, 10);
}

const toNaiveISOString = (date: Date) => {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return (
    date.getFullYear() +
    '-' +
    pad(date.getMonth() + 1) +
    '-' +
    pad(date.getDate()) +
    'T' +
    pad(date.getHours()) +
    ':' +
    pad(date.getMinutes()) +
    ':' +
    pad(date.getSeconds())
  );
};

const PAGE_SIZE = 8;

// Add global styles for placeholder and body background
const globalStyle = `
  body {
    background: #f7f9fb !important;
    font-family: 'Inter', 'Roboto', Arial, sans-serif;
    margin: 0;
    padding: 0;
  }
  * {
    box-sizing: border-box;
  }
  input::placeholder {
    color: #b0b8c1 !important;
    opacity: 1;
  }
  table, th, td {
    color: #111 !important;
  }
  input, select, textarea {
    color: #111 !important;
  }
`;

type TransactionLine = {
  account: string;
  type: 'debit' | 'credit';
  amount: number | undefined;
};

type TransactionForm = {
  description: string;
  lines: TransactionLine[];
};

const initialForm: TransactionForm = {
  description: '',
  lines: [
    { account: '', type: 'debit', amount: undefined },
    { account: '', type: 'credit', amount: undefined },
  ],
};

const LedgerToday: React.FC = () => {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [form, setForm] = useState<TransactionForm>(initialForm);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [formTouched, setFormTouched] = useState(false);

  const fetchEntries = async () => {
    setLoading(true);
    const res = await fetch(apiUrl);
    const data: any[] = await res.json();
    const today = getTodayISODate();

    // Adapt to new transaction/lines structure
    // Flatten each transaction into multiple LedgerEntry-like rows for display
    const ledgerRows: LedgerEntry[] = [];
    data.forEach(tx => {
      if (Array.isArray(tx.lines)) {
        tx.lines.forEach((line: any) => {
          ledgerRows.push({
            id: tx.id,
            datetime: tx.date,
            description: tx.description,
            amount: line.amount,
            debit_account: line.type === 'debit' ? line.account : '',
            credit_account: line.type === 'credit' ? line.account : '',
          });
        });
      }
    });
    setEntries(ledgerRows.filter(e => e.datetime && e.datetime.slice(0, 10) === today));
    setLoading(false);
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  // Filtering and pagination
  const filtered = entries.filter(
    e =>
      e.description.toLowerCase().includes(search.toLowerCase()) ||
      e.debit_account.toLowerCase().includes(search.toLowerCase()) ||
      e.credit_account.toLowerCase().includes(search.toLowerCase())
  );
  const pageCount = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleLineChange = (idx: number, field: keyof TransactionLine, value: string | number) => {
    setForm(f => {
      const lines = [...f.lines];
      if (field === 'amount') {
        lines[idx][field] = value === '' ? undefined : Number(value);
      } else if (field === 'type') {
        lines[idx][field] = value as 'debit' | 'credit';
      } else {
        lines[idx][field] = value as string;
      }
      return { ...f, lines };
    });
    setFormTouched(true);
  };

  const handleDescriptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, description: e.target.value });
    setFormTouched(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const transaction = {
      description: form.description,
      date: toNaiveISOString(new Date()),
      lines: form.lines.map(line => ({
        ...line,
        amount: line.amount ?? 0,
      })),
    };
    await fetch('http://localhost:8000/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(transaction),
    });
    setForm(initialForm);
    setFormTouched(false);
    fetchEntries();
  };

  const handleCancel = () => {
    setForm(initialForm);
    setFormTouched(false);
  };

  // Table row hover and button styles
  const tableRowStyle: React.CSSProperties = {
    transition: 'background 0.2s',
    cursor: 'pointer',
  };

  // Responsive layout
  return (
    <>
      <style>{globalStyle}</style>
      <div
        style={{
          width: '100vw',
          minHeight: '100vh',
          background: '#f7f9fb',
          fontFamily: 'Inter, Roboto, Arial, sans-serif',
          padding: 0,
          margin: 0,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            flex: 1,
            maxWidth: 1200,
            minHeight: '100vh',
            margin: '0 auto',
            padding: '2rem 1rem',
            display: 'flex',
            gap: 32,
            alignItems: 'flex-start',
            flexWrap: 'wrap',
          }}
        >
          {/* Entries List Section */}
          <section
            style={{
              flex: 2,
              minWidth: 350,
              background: '#fff',
              borderRadius: 16,
              boxShadow: '0 2px 16px 0 #e6ecf5',
              padding: '2rem 1.5rem',
              marginBottom: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontWeight: 700, fontSize: 22, margin: 0, color: '#1a2a3a' }}>Today's Entries</h2>
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={e => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                style={{
                  border: '1px solid #e0e6ed',
                  borderRadius: 8,
                  padding: '6px 12px',
                  fontSize: 15,
                  background: '#f7f9fb',
                  outline: 'none',
                  transition: 'border 0.2s',
                }}
              />
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
                <thead>
                  <tr style={{ background: '#f0f4fa' }}>
                    <th style={{ padding: '10px 8px', fontWeight: 600, color: '#3a4a5a', fontSize: 15, borderTopLeftRadius: 8 }}>Date/Time</th>
                    <th style={{ padding: '10px 8px', fontWeight: 600, color: '#3a4a5a', fontSize: 15 }}>Description</th>
                    <th style={{ padding: '10px 8px', fontWeight: 600, color: '#3a4a5a', fontSize: 15 }}>Amount</th>
                    <th style={{ padding: '10px 8px', fontWeight: 600, color: '#3a4a5a', fontSize: 15 }}>Debit</th>
                    <th style={{ padding: '10px 8px', fontWeight: 600, color: '#3a4a5a', fontSize: 15 }}>Credit</th>
                    <th style={{ padding: '10px 8px', fontWeight: 600, color: '#3a4a5a', fontSize: 15, borderTopRightRadius: 8 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: 24 }}>Loading...</td>
                    </tr>
                  ) : paged.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: '#b0b8c1' }}>No entries for today.</td>
                    </tr>
                  ) : (
                    paged.map((e, idx) => (
                      <tr
                        key={e.id}
                        style={{
                          ...tableRowStyle,
                          background: idx % 2 === 0 ? '#f7fbf7ff' : '#fff',
                          borderRadius: 8,
                        }}
                        onMouseOver={ev => (ev.currentTarget.style.background = '#eaf3fb')}
                        onMouseOut={ev => (ev.currentTarget.style.background = idx % 2 === 0 ? '#f7f9fb' : '#fff')}
                      >
                        <td style={{ padding: '10px 8px', borderRadius: 0 }}>{new Date(e.datetime).toLocaleString()}</td>
                        <td style={{ padding: '10px 8px' }}>{e.description}</td>
                        <td style={{ padding: '10px 8px', color: '#0a7cff', fontWeight: 600 }}>{e.amount}</td>
                        <td style={{ padding: '10px 8px' }}>{e.debit_account}</td>
                        <td style={{ padding: '10px 8px' }}>{e.credit_account}</td>
                        <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                          {/* Replace with icons as needed */}
                          <span title="View" style={{ cursor: 'pointer', marginRight: 8, color: '#0a7cff', fontSize: 18 }}>👁️</span>
                          <span title="Edit" style={{ cursor: 'pointer', marginRight: 8, color: '#1bc5b4', fontSize: 18 }}>✏️</span>
                          <span title="Delete" style={{ cursor: 'pointer', color: '#ff5a5f', fontSize: 18 }}>🗑️</span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            {/* Pagination */}
            {pageCount > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 18, gap: 8 }}>
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  style={{
                    background: '#e0e6ed',
                    border: 'none',
                    borderRadius: 6,
                    padding: '6px 14px',
                    cursor: page === 1 ? 'not-allowed' : 'pointer',
                    color: '#3a4a5a',
                    fontWeight: 500,
                    transition: 'background 0.2s',
                  }}
                >
                  Prev
                </button>
                <span style={{ alignSelf: 'center', color: '#3a4a5a', fontWeight: 500 }}>
                  Page {page} of {pageCount}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(pageCount, p + 1))}
                  disabled={page === pageCount}
                  style={{
                    background: '#e0e6ed',
                    border: 'none',
                    borderRadius: 6,
                    padding: '6px 14px',
                    cursor: page === pageCount ? 'not-allowed' : 'pointer',
                    color: '#3a4a5a',
                    fontWeight: 500,
                    transition: 'background 0.2s',
                  }}
                >
                  Next
                </button>
              </div>
            )}
          </section>

          {/* Add Transaction Form Section */}
          <section
            style={{
              flex: 1,
              minWidth: 320,
              background: '#fff', // light background
              borderRadius: 16,
              boxShadow: '0 2px 16px 0 #e6ecf5',
              padding: '2rem 1.5rem',
              marginBottom: 24,
              maxWidth: 420,
            }}
          >
            <h3 style={{ fontWeight: 700, fontSize: 20, marginBottom: 18, color: '#1a2a3a' }}>Add New Transaction</h3>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', marginBottom: 4, color: '#3a4a5a', fontWeight: 500 }}>Description</label>
                <input
                  name="description"
                  placeholder="Description"
                  value={form.description}
                  onChange={handleDescriptionChange}
                  required
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 8,
                    border: '1px solid #e0e6ed',
                    fontSize: 15,
                    background: '#f7f9fb',
                    color: '#111',
                    outline: 'none',
                    transition: 'border 0.2s',
                  }}
                />
              </div>
              {form.lines.map((line, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#f7f9fb',
                    borderRadius: 8,
                    padding: 0,
                    marginBottom: 4,
                    border: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                  }}
                >
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <select
                      value={line.type}
                      onChange={e => handleLineChange(idx, 'type', e.target.value)}
                      style={{
                        border: '1px solid #e0e6ed',
                        borderRadius: 6,
                        padding: '6px 8px',
                        background: '#fff',
                        color: '#111',
                        fontWeight: 500,
                        fontSize: 15,
                        marginRight: 8,
                      }}
                    >
                      <option value="debit">Debit</option>
                      <option value="credit">Credit</option>
                    </select>
                    <input
                      placeholder="Account"
                      value={line.account}
                      onChange={e => handleLineChange(idx, 'account', e.target.value)}
                      required
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        borderRadius: 8,
                        border: '1px solid #e0e6ed',
                        fontSize: 15,
                        background: '#fff',
                        color: '#111',
                        outline: 'none',
                        transition: 'border 0.2s',
                      }}
                    />
                  </div>
                  <input
                    type="number"
                    placeholder="Amount"
                    value={line.amount === undefined ? '' : line.amount}
                    onChange={e => handleLineChange(idx, 'amount', e.target.value)}
                    required
                    min={0}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 8,
                      border: '1px solid #e0e6ed',
                      fontSize: 15,
                      background: '#fff',
                      color: '#111',
                      outline: 'none',
                      transition: 'border 0.2s',
                    }}
                  />
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  onClick={() =>
                    setForm(f => ({
                      ...f,
                      lines: [...f.lines, { account: '', type: 'debit', amount: undefined }],
                    }))
                  }
                  style={{
                    flex: 1,
                    background: '#e0e6ed',
                    color: '#111',
                    border: 'none',
                    borderRadius: 8,
                    padding: '8px 0',
                    fontWeight: 500,
                    fontSize: 15,
                    cursor: 'pointer',
                  }}
                >
                  + Add Line
                </button>
                {form.lines.length > 2 && (
                  <button
                    type="button"
                    onClick={() =>
                      setForm(f => ({
                        ...f,
                        lines: f.lines.slice(0, -1),
                      }))
                    }
                    style={{
                      flex: 1,
                      background: '#e0e6ed',
                      color: '#111',
                      border: 'none',
                      borderRadius: 8,
                      padding: '8px 0',
                      fontWeight: 500,
                      fontSize: 15,
                      cursor: 'pointer',
                    }}
                  >
                    - Remove Line
                  </button>
                )}
              </div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                <button
                  type="submit"
                  disabled={
                    !formTouched ||
                    !form.description ||
                    form.lines.some(
                      l => !l.account || l.amount === undefined || l.amount === null || isNaN(Number(l.amount))
                    )
                  }
                  style={{
                    flex: 1,
                    background: '#0a7cff',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    padding: '10px 0',
                    fontWeight: 600,
                    fontSize: 16,
                    cursor: formTouched ? 'pointer' : 'not-allowed',
                    boxShadow: '0 2px 8px 0 #e6ecf5',
                    transition: 'background 0.2s, box-shadow 0.2s',
                  }}
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  style={{
                    flex: 1,
                    background: '#e0e6ed',
                    color: '#0a7cff',
                    border: 'none',
                    borderRadius: 8,
                    padding: '10px 0',
                    fontWeight: 600,
                    fontSize: 16,
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px 0 #e6ecf5',
                    transition: 'background 0.2s, box-shadow 0.2s',
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </>
  );
};

export default LedgerToday;
