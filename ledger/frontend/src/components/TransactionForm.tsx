import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Types
interface Account {
  id: number;
  name: string;
  type: string;
  code: string;
  is_active: boolean;
}

interface TransactionLine {
  account_name: string;
  type: 'debit' | 'credit';
  amount: string;
}

interface TransactionFormData {
  description: string;
  reference: string;
  date: string;
  source: string;
  lines: TransactionLine[];
}

interface TransactionFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const TransactionForm: React.FC<TransactionFormProps> = ({ onSuccess, onCancel }) => {
  const { token } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState<TransactionFormData>({
    description: '',
    reference: '',
    date: new Date().toISOString().split('T')[0], // Today's date in YYYY-MM-DD format
    source: 'MANUAL',
    lines: [
      { account_name: '', type: 'debit', amount: '' },
      { account_name: '', type: 'credit', amount: '' }
    ]
  });

  // Fetch accounts for dropdown
  useEffect(() => {
    fetchAccounts();
  }, [token]);

  const fetchAccounts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/accounts', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAccounts(data.filter((account: Account) => account.is_active));
      }
    } catch (err) {
      console.error('Error fetching accounts:', err);
    }
  };

  const addLine = () => {
    setFormData(prev => ({
      ...prev,
      lines: [...prev.lines, { account_name: '', type: 'debit', amount: '' }]
    }));
  };

  const removeLine = (index: number) => {
    if (formData.lines.length > 2) {
      setFormData(prev => ({
        ...prev,
        lines: prev.lines.filter((_, i) => i !== index)
      }));
    }
  };

  const updateLine = (index: number, field: keyof TransactionLine, value: string) => {
    setFormData(prev => ({
      ...prev,
      lines: prev.lines.map((line, i) => 
        i === index ? { ...line, [field]: value } : line
      )
    }));
  };

  const calculateTotals = () => {
    const totals = formData.lines.reduce(
      (acc, line) => {
        const amount = parseFloat(line.amount) || 0;
        if (line.type === 'debit') {
          acc.totalDebit += amount;
        } else {
          acc.totalCredit += amount;
        }
        return acc;
      },
      { totalDebit: 0, totalCredit: 0 }
    );

    return {
      ...totals,
      isBalanced: Math.abs(totals.totalDebit - totals.totalCredit) < 0.01,
      difference: totals.totalDebit - totals.totalCredit
    };
  };

  const validateForm = () => {
    if (!formData.description.trim()) {
      return 'Description is required';
    }

    if (formData.lines.length < 2) {
      return 'At least 2 transaction lines are required';
    }

    for (const line of formData.lines) {
      if (!line.account_name) {
        return 'All lines must have an account selected';
      }
      if (!line.amount || parseFloat(line.amount) <= 0) {
        return 'All lines must have a positive amount';
      }
    }

    const totals = calculateTotals();
    if (!totals.isBalanced) {
      return `Transaction is not balanced. Difference: $${Math.abs(totals.difference).toFixed(2)}`;
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      // Create a clean transaction object with proper validation  
      const transactionData = {
        description: formData.description.trim(),
        reference: formData.reference.trim() || undefined, // Send undefined instead of empty string
        date: formData.date + 'T12:00:00', // Send as simple datetime string (noon to avoid timezone issues)
        source: formData.source,
        lines: formData.lines
          .filter(line => line.account_name && line.amount) // Filter out empty lines
          .map(line => ({
            account_name: line.account_name.trim(),
            type: line.type,
            amount: parseFloat(line.amount)
          }))
      };

      // Additional validation
      if (transactionData.lines.length < 2) {
        setError('At least 2 valid transaction lines are required');
        return;
      }

      console.log('📤 Sending transaction data:', JSON.stringify(transactionData, null, 2));

      const response = await fetch('http://localhost:8000/api/v1/transactions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactionData),
      });

      console.log('📬 Response status:', response.status, response.statusText);

      if (response.ok) {
        const newTransaction = await response.json();
        console.log('✅ Transaction created successfully:', newTransaction);
        
        if (onSuccess) {
          onSuccess();
        }
        
        // Reset form
        setFormData({
          description: '',
          reference: '',
          date: new Date().toISOString().split('T')[0],
          source: 'manual',
          lines: [
            { account_name: '', type: 'debit', amount: '' },
            { account_name: '', type: 'credit', amount: '' }
          ]
        });
      } else {
        const errorData = await response.json();
        console.error('❌ Backend validation error:', errorData);
        
        // Try to extract meaningful error message
        let errorMessage = 'Failed to create transaction';
        
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors
            const validationErrors = errorData.detail.map((err: any) => {
              const field = err.loc ? err.loc.join('.') : 'unknown field';
              return `${field}: ${err.msg}`;
            }).join('; ');
            errorMessage = `Validation errors: ${validationErrors}`;
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          }
        }
        
        setError(errorMessage);
      }
    } catch (err) {
      console.error('💥 Network/parsing error:', err);
      setError('Failed to create transaction. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">📝 New Transaction</h2>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Transaction Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📋 Description *
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
              placeholder="Enter transaction description..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📅 Date *
            </label>
            <input
              type="date"
              value={formData.date}
              onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🏷️ Reference
            </label>
            <input
              type="text"
              value={formData.reference}
              onChange={(e) => setFormData(prev => ({ ...prev, reference: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
              placeholder="Invoice #, Check #, etc."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📍 Source
            </label>
            <select
              value={formData.source}
              onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
            >
              <option value="manual">Manual Entry</option>
              <option value="import">Import</option>
              <option value="api">API</option>
              <option value="pos">Point of Sale</option>
              <option value="web">Web</option>
            </select>
          </div>
        </div>

        {/* Transaction Lines */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">💰 Journal Entries</h3>
            <button
              type="button"
              onClick={addLine}
              className="flex items-center space-x-2 px-3 py-1 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Add Line</span>
            </button>
          </div>

          <div className="space-y-2">
            {formData.lines.map((line, index) => (
              <div key={index} className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <select
                    value={line.account_name}
                    onChange={(e) => updateLine(index, 'account_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-600 focus:outline-none"
                    required
                  >
                    <option value="">Select Account...</option>
                    {accounts.map(account => (
                      <option key={account.id} value={account.name}>
                        {account.code} - {account.name} ({account.type})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="w-32">
                  <select
                    value={line.type}
                    onChange={(e) => updateLine(index, 'type', e.target.value as 'debit' | 'credit')}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-600 focus:outline-none"
                  >
                    <option value="debit">Debit</option>
                    <option value="credit">Credit</option>
                  </select>
                </div>

                <div className="w-32">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={line.amount}
                    onChange={(e) => updateLine(index, 'amount', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-600 focus:outline-none"
                    placeholder="0.00"
                    required
                  />
                </div>

                {formData.lines.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeLine(index)}
                    className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Balance Summary */}
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Total Debits:</span>
                <span className="ml-2 font-bold text-green-600">
                  ${totals.totalDebit.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Total Credits:</span>
                <span className="ml-2 font-bold text-blue-600">
                  ${totals.totalCredit.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Status:</span>
                <span className={`ml-2 font-bold ${totals.isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                  {totals.isBalanced ? '✅ Balanced' : `❌ Off by $${Math.abs(totals.difference).toFixed(2)}`}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Form Actions */}
        <div className="flex items-center justify-end space-x-4 pt-4 border-t">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isLoading || !totals.isBalanced}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isLoading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            <span>{isLoading ? 'Creating...' : '💾 Create Transaction'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default TransactionForm;