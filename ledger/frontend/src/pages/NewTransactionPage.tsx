import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import TransactionForm from '../components/TransactionForm';

const NewTransactionPage: React.FC = () => {
  return (
    <Layout currentPage="transactions">
      <div className="p-8">
        <div className="flex items-center mb-6">
          <Link
            to="/transactions"
            className="text-blue-600 hover:text-blue-800 mr-4"
          >
            ← Back to Transactions
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Add New Transaction</h1>
        </div>

        <div className="bg-white shadow-md rounded-lg p-6">
          <TransactionForm />
        </div>
      </div>
    </Layout>
  );
};

export default NewTransactionPage;