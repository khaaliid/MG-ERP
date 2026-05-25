import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { expenseAPI } from '../api';
import '../i18n';

interface Expense {
  id: number;
  expense_date: string;
  category: string;
  description: string;
  amount: number;
  payment_method: string;
  vendor?: string;
  receipt_number?: string;
  notes?: string;
  recorded_by?: number;
  created_at: string;
}

const CATEGORIES = [
  { value: 'rent', label: 'Rent' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'salaries', label: 'Salaries' },
  { value: 'supplies', label: 'Supplies' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'transportation', label: 'Transportation' },
  { value: 'other', label: 'Other' },
];

const PAYMENT_METHODS = [
  { value: 'cash', label: 'Cash' },
  { value: 'card', label: 'Card' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'other', label: 'Other' },
];

function Expenses() {
  const { t } = useTranslation();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);

  const [formData, setFormData] = useState({
    expense_date: new Date().toISOString().split('T')[0],
    category: 'other',
    description: '',
    amount: '',
    payment_method: 'cash',
    vendor: '',
    receipt_number: '',
    notes: '',
  });

  useEffect(() => {
    void fetchPage(1, 20, { categoryFilter: '' });
  }, []);

  const fetchPage = async (
    nextPage: number,
    nextPageSize: number,
    overrides?: { categoryFilter?: string }
  ) => {
    setLoading(true);
    const filter = overrides?.categoryFilter !== undefined ? overrides.categoryFilter : categoryFilter;
    try {
      const response = await expenseAPI.getAll({
        category: filter || undefined,
        skip: (nextPage - 1) * nextPageSize,
        limit: nextPageSize,
        paginated: true,
      });
      const data = response.data;
      setExpenses(data.items);
      setTotalCount(data.total);
      setTotalAmount(data.total_amount);
      setPage(nextPage);
      setPageSize(nextPageSize);
    } catch (error) {
      console.error('Error fetching expenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const expenseData = {
        ...formData,
        amount: parseFloat(formData.amount),
        expense_date: new Date(formData.expense_date).toISOString(),
      };

      if (editingExpense) {
        await expenseAPI.update(editingExpense.id, expenseData);
      } else {
        await expenseAPI.create(expenseData);
      }

      resetForm();
      void fetchPage(page, pageSize);
    } catch (error: any) {
      console.error('Error saving expense:', error);
      alert(error.response?.data?.detail || 'Failed to save expense');
    }
  };

  const handleEdit = (expense: Expense) => {
    setEditingExpense(expense);
    setFormData({
      expense_date: expense.expense_date.split('T')[0],
      category: expense.category,
      description: expense.description,
      amount: expense.amount.toString(),
      payment_method: expense.payment_method,
      vendor: expense.vendor || '',
      receipt_number: expense.receipt_number || '',
      notes: expense.notes || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm(t('expenses_confirm_delete'))) return;

    try {
      await expenseAPI.delete(id);
      const newTotal = totalCount - 1;
      const maxPage = Math.ceil(newTotal / pageSize) || 1;
      void fetchPage(Math.min(page, maxPage), pageSize);
    } catch (error: any) {
      console.error('Error deleting expense:', error);
      alert(error.response?.data?.detail || 'Failed to delete expense');
    }
  };

  const resetForm = () => {
    setFormData({
      expense_date: new Date().toISOString().split('T')[0],
      category: 'other',
      description: '',
      amount: '',
      payment_method: 'cash',
      vendor: '',
      receipt_number: '',
      notes: '',
    });
    setEditingExpense(null);
    setShowForm(false);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>💰 {t('expenses_title')}</h1>
          <p>{t('expenses_subtitle')}</p>
        </div>
        <button
          className="button button-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? `✖ ${t('cancel')}` : `➕ ${t('expenses_add_button')}`}
        </button>
      </div>

      {/* Summary Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '20px', 
        marginBottom: '30px' 
      }}>
        <div className="card">
          <h3>{t('total_expenses')}</h3>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#e74c3c' }}>
            ${totalAmount.toFixed(2)}
          </div>
        </div>
        <div className="card">
          <h3>{t('expenses_total_records')}</h3>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#3498db' }}>
            {totalCount}
          </div>
        </div>
        <div className="card">
          <h3>{t('expenses_average_expense')}</h3>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#9b59b6' }}>
            ${totalCount ? (totalAmount / totalCount).toFixed(2) : '0.00'}
          </div>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="card" style={{ marginBottom: '30px' }}>
          <h2>{editingExpense ? t('expenses_edit_form_title') : t('expenses_add_form_title')}</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="form-group">
                <label>{t('ledger_col_date')} *</label>
                <input
                  type="date"
                  required
                  value={formData.expense_date}
                  onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>{t('category')} *</label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>{t(`expenses_cat_${cat.value}`)}</option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>{t('ledger_col_description')} *</label>
                <input
                  type="text"
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder={t('expenses_description_placeholder')}
                />
              </div>

              <div className="form-group">
                <label>{t('ledger_col_amount')} *</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label>{t('ledger_col_payment_method')} *</label>
                <select
                  required
                  value={formData.payment_method}
                  onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                >
                  {PAYMENT_METHODS.map(pm => (
                    <option key={pm.value} value={pm.value}>{t(`expenses_payment_${pm.value}`)}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>{t('expenses_vendor')}</label>
                <input
                  type="text"
                  value={formData.vendor}
                  onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                  placeholder={t('expenses_vendor_placeholder')}
                />
              </div>

              <div className="form-group">
                <label>{t('expenses_receipt_number')}</label>
                <input
                  type="text"
                  value={formData.receipt_number}
                  onChange={(e) => setFormData({ ...formData, receipt_number: e.target.value })}
                  placeholder={t('expenses_receipt_placeholder')}
                />
              </div>

              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>{t('transactions_history_notes')}</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder={t('expenses_notes_placeholder')}
                  rows={3}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button type="submit" className="button button-primary">
                {editingExpense ? `💾 ${t('expenses_update_button')}` : `➕ ${t('expenses_add_button')}`}
              </button>
              <button type="button" className="button button-secondary" onClick={resetForm}>
                {t('cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter */}
      <div className="card" style={{ marginBottom: '20px', padding: '15px' }}>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <label style={{ fontWeight: 'bold' }}>{t('expenses_filter_by_category')}:</label>
          <select
            value={categoryFilter}
            onChange={(e) => {
              const val = e.target.value;
              setCategoryFilter(val);
              void fetchPage(1, pageSize, { categoryFilter: val });
            }}
            style={{ maxWidth: '200px' }}
          >
            <option value="">{t('expenses_all_categories')}</option>
            {CATEGORIES.map(cat => (
              <option key={cat.value} value={cat.value}>{t(`expenses_cat_${cat.value}`)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Expenses Table */}
      <div className="card">
        <h2>{t('expenses_records_heading')}</h2>
        {loading ? (
          <p>{t('expenses_loading')}</p>
        ) : expenses.length === 0 ? (
          <p>{t('expenses_no_records')}</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('ledger_col_date')}</th>
                <th>{t('category')}</th>
                <th>{t('ledger_col_description')}</th>
                <th>{t('expenses_vendor')}</th>
                <th>{t('ledger_col_amount')}</th>
                <th>{t('ledger_col_payment_method')}</th>
                <th>{t('expenses_col_receipt')}</th>
                <th>{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((expense) => (
                <tr key={expense.id}>
                  <td>{new Date(expense.expense_date).toLocaleDateString()}</td>
                  <td>
                    <span className="badge" style={{ 
                      backgroundColor: getCategoryColor(expense.category),
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      {expense.category}
                    </span>
                  </td>
                  <td>{expense.description}</td>
                  <td>{expense.vendor || '-'}</td>
                  <td style={{ fontWeight: 'bold', color: '#e74c3c' }}>
                    ${expense.amount.toFixed(2)}
                  </td>
                  <td style={{ textTransform: 'capitalize' }}>
                    {expense.payment_method.replace('_', ' ')}
                  </td>
                  <td>{expense.receipt_number || '-'}</td>
                  <td>
                    <button
                      className="button button-sm button-secondary"
                      onClick={() => handleEdit(expense)}
                      style={{ marginRight: '5px' }}
                    >
                      ✏️ {t('edit')}
                    </button>
                    <button
                      className="button button-sm button-danger"
                      onClick={() => handleDelete(expense.id)}
                    >
                      🗑️ {t('expenses_delete_btn')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {/* Pagination */}
        {totalCount > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px' }}>{t('expenses_rows_per_page')}:</span>
              <select
                value={pageSize}
                onChange={(e) => void fetchPage(1, Number(e.target.value))}
                style={{ padding: '4px 8px' }}
              >
                {[10, 20, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px' }}>
              <span>
                {t('expenses_page_summary', {
                  from: (page - 1) * pageSize + 1,
                  to: Math.min(page * pageSize, totalCount),
                  total: totalCount,
                })}
              </span>
              <button
                className="button button-sm button-secondary"
                onClick={() => void fetchPage(page - 1, pageSize)}
                disabled={page <= 1}
              >
                {t('expenses_previous')}
              </button>
              <span>{t('expenses_page_x_of_y', { page, totalPages })}</span>
              <button
                className="button button-sm button-secondary"
                onClick={() => void fetchPage(page + 1, pageSize)}
                disabled={page >= totalPages}
              >
                {t('expenses_next')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    rent: '#e74c3c',
    utilities: '#3498db',
    salaries: '#2ecc71',
    supplies: '#f39c12',
    maintenance: '#9b59b6',
    marketing: '#1abc9c',
    transportation: '#34495e',
    other: '#95a5a6',
  };
  return colors[category] || '#95a5a6';
}

export default Expenses;
