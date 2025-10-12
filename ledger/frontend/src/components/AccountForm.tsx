import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Types
interface AccountFormData {
  name: string;
  code: string;
  type: string;
  description: string;
  is_active: boolean;
}

interface AccountFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const AccountForm: React.FC<AccountFormProps> = ({ onSuccess, onCancel }) => {
  const { token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState<AccountFormData>({
    name: '',
    code: '',
    type: 'asset',
    description: '',
    is_active: true
  });

  const accountTypes = [
    { value: 'asset', label: '🏦 Asset', description: 'Resources owned by the business' },
    { value: 'liability', label: '📋 Liability', description: 'Debts owed by the business' },
    { value: 'equity', label: '💰 Equity', description: 'Owner\'s stake in the business' },
    { value: 'income', label: '📈 Income', description: 'Revenue and earnings' },
    { value: 'expense', label: '📉 Expense', description: 'Costs and expenditures' }
  ];

  const validateForm = () => {
    if (!formData.name.trim()) {
      return 'Account name is required';
    }
    if (!formData.code.trim()) {
      return 'Account code is required';
    }
    if (formData.code.length > 20) {
      return 'Account code must be 20 characters or less';
    }
    if (formData.name.length > 100) {
      return 'Account name must be 100 characters or less';
    }
    if (!formData.type) {
      return 'Account type is required';
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
      console.log('🏦 Creating account:', formData);

      const response = await fetch('http://localhost:8000/api/v1/accounts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const newAccount = await response.json();
        console.log('✅ Account created successfully:', newAccount);
        
        if (onSuccess) {
          onSuccess();
        }
        
        // Reset form
        setFormData({
          name: '',
          code: '',
          type: 'asset',
          description: '',
          is_active: true
        });
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create account');
      }
    } catch (err) {
      console.error('❌ Error creating account:', err);
      setError('Failed to create account. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof AccountFormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const generateSuggestedCode = () => {
    if (!formData.name || !formData.type) return;

    const typePrefix = {
      asset: '1',
      liability: '2',
      equity: '3',
      income: '4',
      expense: '5'
    }[formData.type] || '1';

    // Generate a simple code based on name
    const nameCode = formData.name
      .replace(/[^a-zA-Z0-9]/g, '')
      .substring(0, 3)
      .toUpperCase();
    
    const suggestedCode = `${typePrefix}${nameCode}${Math.floor(Math.random() * 100).toString().padStart(2, '0')}`;
    
    setFormData(prev => ({
      ...prev,
      code: suggestedCode
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">🏦 New Account</h2>
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
        {/* Account Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📝 Account Name *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
            placeholder="Enter account name (e.g., Cash in Bank, Accounts Receivable)"
            maxLength={100}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Maximum 100 characters. Be descriptive and clear.
          </p>
        </div>

        {/* Account Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🏷️ Account Type *
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {accountTypes.map(type => (
              <div
                key={type.value}
                className={`relative border rounded-lg p-3 cursor-pointer transition-all ${
                  formData.type === type.value
                    ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onClick={() => handleInputChange('type', type.value)}
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    name="type"
                    value={type.value}
                    checked={formData.type === type.value}
                    onChange={() => handleInputChange('type', type.value)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div className="ml-3">
                    <label className="text-sm font-medium text-gray-900 cursor-pointer">
                      {type.label}
                    </label>
                    <p className="text-xs text-gray-500">{type.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Account Code */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🔢 Account Code *
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={formData.code}
              onChange={(e) => handleInputChange('code', e.target.value.toUpperCase())}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
              placeholder="Enter unique code (e.g., 1001, CASH01)"
              maxLength={20}
              required
            />
            <button
              type="button"
              onClick={generateSuggestedCode}
              disabled={!formData.name || !formData.type}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              ✨ Suggest
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Maximum 20 characters. Must be unique across all accounts.
          </p>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📄 Description (Optional)
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:outline-none"
            placeholder="Add a detailed description of this account's purpose..."
          />
          <p className="text-xs text-gray-500 mt-1">
            Optional but recommended for clarity and audit purposes.
          </p>
        </div>

        {/* Active Status */}
        <div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => handleInputChange('is_active', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
              ✅ Account is active and available for transactions
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Inactive accounts won't appear in transaction forms but remain in the system.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            ❌ {error}
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
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isLoading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            <span>{isLoading ? 'Creating...' : '💾 Create Account'}</span>
          </button>
        </div>
      </form>

      {/* Account Type Guide */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">📚 Account Type Guide</h3>
        <div className="text-xs text-blue-800 space-y-1">
          <p><strong>Assets:</strong> Cash, Bank accounts, Inventory, Equipment, Accounts Receivable</p>
          <p><strong>Liabilities:</strong> Accounts Payable, Loans, Credit cards, Taxes owed</p>
          <p><strong>Equity:</strong> Owner's capital, Retained earnings, Paid-in capital</p>
          <p><strong>Income:</strong> Sales revenue, Service income, Interest income</p>
          <p><strong>Expenses:</strong> Rent, Utilities, Salaries, Office supplies, Marketing</p>
        </div>
      </div>
    </div>
  );
};

export default AccountForm;