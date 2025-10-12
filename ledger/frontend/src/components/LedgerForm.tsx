import React, { useState } from 'react';
import type { LedgerEntry } from './LedgerList';

interface Props {
  onAdd: (entry: Omit<LedgerEntry, 'id'>) => void;
}

const initialForm = { account: '', amount: 0, description: '', date: '' };

const LedgerForm: React.FC<Props> = ({ onAdd }) => {
  const [form, setForm] = useState(initialForm);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.account || !form.date) return;
    onAdd({ ...form, amount: Number(form.amount) });
    setForm(initialForm);
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
      <input name="date" type="date" value={form.date} onChange={handleChange} required />
      <input name="account" placeholder="Account" value={form.account} onChange={handleChange} required />
      <input name="amount" type="number" placeholder="Amount" value={form.amount} onChange={handleChange} required />
      <input name="description" placeholder="Description" value={form.description} onChange={handleChange} />
      <button type="submit">Add Entry</button>
    </form>
  );
};

export default LedgerForm;
