import React from 'react';

export interface LedgerEntry {
  id: number;
  account: string;
  amount: number;
  description: string;
  date: string;
}

interface Props {
  entries: LedgerEntry[];
}

const LedgerList: React.FC<Props> = ({ entries }) => {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          <th>Date</th>
          <th>Account</th>
          <th>Amount</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(entry => (
          <tr key={entry.id}>
            <td>{entry.date}</td>
            <td>{entry.account}</td>
            <td>{entry.amount}</td>
            <td>{entry.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default LedgerList;
