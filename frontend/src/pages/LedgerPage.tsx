import React, { useState } from 'react';
import LedgerList from '../components/LedgerList';
import type { LedgerEntry } from '../components/LedgerList';
import LedgerForm from '../components/LedgerForm';

const initialEntries: LedgerEntry[] = [
  { id: 1, account: 'Cash', amount: 1000, description: 'Initial deposit', date: '2025-09-17' },
];

const LedgerPage: React.FC = () => {
  const [entries, setEntries] = useState<LedgerEntry[]>(initialEntries);

  const handleAdd = (entry: Omit<LedgerEntry, 'id'>) => {
    setEntries([
      ...entries,
      { ...entry, id: entries.length ? entries[entries.length - 1].id + 1 : 1 },
    ]);
  };

  return (
    <div style={{ maxWidth: 600, margin: '40px auto' }}>
      <h2>Ledger</h2>
      <LedgerForm onAdd={handleAdd} />
      <LedgerList entries={entries} />
    </div>
  );
};

export default LedgerPage;
