import React from 'react';
import Layout from '../components/Layout';

const AgingReportPage: React.FC = () => {
  return (
    <Layout currentPage="reports" currentReport="aging">
      <div className="p-8">
        <div className="bg-white shadow-md rounded-lg p-8">
          <div className="text-center">
            <div className="text-6xl mb-6">📅</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Aging Report</h1>
            <p className="text-lg text-gray-600 mb-6">
              This report will show the aging of accounts receivable and payable
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-2xl mx-auto">
              <h3 className="text-lg font-medium text-blue-800 mb-3">Coming Soon</h3>
              <p className="text-blue-700 text-sm">
                The Aging Report will provide detailed analysis of:
              </p>
              <ul className="text-blue-700 text-sm mt-3 list-disc list-inside space-y-1">
                <li>Accounts Receivable aging (0-30, 31-60, 61-90, 90+ days)</li>
                <li>Accounts Payable aging buckets</li>
                <li>Customer payment history analysis</li>
                <li>Vendor payment due dates</li>
                <li>Cash flow projections based on aging</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AgingReportPage;