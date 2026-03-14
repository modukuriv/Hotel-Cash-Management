import { Fragment, useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { createExpense, listExpenses, updateExpense } from '../services/expenses.js';
import { listTenants } from '../services/tenants.js';
import { listWeeks } from '../services/weeks.js';
import { listCategories } from '../services/categories.js';
import { listAuditLogs } from '../services/auditLogs.js';

const initialForm = {
  tenant_id: '',
  weekly_cash_id: '',
  category_id: '',
  expense_date: '',
  item_name: '',
  vendor_name: '',
  amount: '',
  payment_type: 'CASH',
  notes: '',
};

export default function Expenses() {
  const { expenseId } = useParams();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [expenses, setExpenses] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [weeks, setWeeks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [historyOpenId, setHistoryOpenId] = useState(null);
  const [history, setHistory] = useState({});
  const [historyLoading, setHistoryLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [page, setPage] = useState(0);
  const [lastPageCount, setLastPageCount] = useState(0);
  const pageSize = 10;
  const role = (localStorage.getItem('userRole') || '').toUpperCase();
  const canEdit = role === 'ADMIN' || role === 'GLOBAL_ADMIN';

  const hasTenant = useMemo(() => form.tenant_id.trim().length > 0, [form.tenant_id]);
  const categoryMap = useMemo(() => {
    const map = new Map();
    categories.forEach((category) => {
      map.set(category.id, category.category_name);
    });
    return map;
  }, [categories]);

  useEffect(() => {
    loadTenants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!hasTenant) {
      setExpenses([]);
      setWeeks([]);
      setCategories([]);
      return;
    }
    setPage(0);
    loadWeeks();
    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.tenant_id]);

  useEffect(() => {
    if (!hasTenant) {
      return;
    }
    loadExpenses(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.tenant_id, page]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const loadTenants = async () => {
    setError('');
    try {
      const data = await listTenants();
      setTenants(data);
      if (!form.tenant_id && data.length > 0) {
        setForm((prev) => ({ ...prev, tenant_id: data[0].id }));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load tenants.');
    }
  };

  const loadWeeks = async () => {
    if (!form.tenant_id) return;
    try {
      const data = await listWeeks({ tenant_id: form.tenant_id });
      setWeeks(data);
      if (!form.weekly_cash_id && data.length > 0) {
        setForm((prev) => ({ ...prev, weekly_cash_id: data[0].id }));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load weeks.');
    }
  };

  const loadCategories = async () => {
    if (!form.tenant_id) return;
    try {
      const data = await listCategories({ tenant_id: form.tenant_id });
      setCategories(data);
      if (!form.category_id && data.length > 0) {
        setForm((prev) => ({ ...prev, category_id: data[0].id }));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load categories.');
    }
  };

  const loadExpenses = async (pageOverride) => {
    if (!form.tenant_id) {
      setError('Tenant ID is required to load expenses.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const currentPage = typeof pageOverride === 'number' ? pageOverride : page;
      const paged = await listExpenses({
        tenant_id: form.tenant_id,
        limit: pageSize,
        offset: currentPage * pageSize,
      });
      setLastPageCount(paged.length);
      setExpenses(paged);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load expenses.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canEdit) {
      setError('View-only access.');
      return;
    }
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      const payload = {
        ...form,
        amount: Number(form.amount),
      };
      if (editingId) {
        await updateExpense(editingId, payload);
        setSuccess('Expense updated.');
      } else {
        const created = await createExpense(payload);
        setSuccess(`Expense created: ${created.id}`);
      }
      setEditingId(null);
      setForm((prev) => ({ ...prev, item_name: '', vendor_name: '', amount: '', notes: '' }));
      setPage(0);
      await loadExpenses(0);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save expense.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setForm(initialForm);
    setPage(0);
    setExpenses([]);
    setWeeks([]);
    setCategories([]);
    setHistoryOpenId(null);
    setHistory({});
    setEditingId(null);
    setSuccess('');
    setError('');
    await loadTenants();
  };

  const startEdit = (expense) => {
    if (!canEdit) return;
    setEditingId(expense.id);
    setForm({
      tenant_id: expense.tenant_id,
      weekly_cash_id: expense.weekly_cash_id,
      category_id: expense.category_id,
      expense_date: expense.expense_date,
      item_name: expense.item_name,
      vendor_name: expense.vendor_name || '',
      amount: String(expense.amount ?? ''),
      payment_type: expense.payment_type || 'CASH',
      notes: expense.notes || '',
    });
    setSuccess('');
    setError('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm((prev) => ({
      ...prev,
      item_name: '',
      vendor_name: '',
      amount: '',
      notes: '',
      expense_date: '',
    }));
  };

  const toggleHistory = async (expenseId) => {
    if (historyOpenId === expenseId) {
      setHistoryOpenId(null);
      return;
    }
    setHistoryOpenId(expenseId);
    if (history[expenseId]) return;
    setHistoryLoading(true);
    try {
      const logs = await listAuditLogs({
        tenant_id: form.tenant_id,
        table_name: 'expenses',
        record_id: expenseId,
      });
      setHistory((prev) => ({ ...prev, [expenseId]: logs }));
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load history.');
    } finally {
      setHistoryLoading(false);
    }
  };

  const getLogValues = (log) => log?.old_values || {};

  const renderHistoryTable = (logs) => (
    <div className="history-panel">
      <table className="history-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>User</th>
            <th>Action</th>
            <th>Date</th>
            <th>Item</th>
            <th>Category</th>
            <th>Amount</th>
            <th>Payment</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => {
            const values = getLogValues(log);
            return (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.user_id || 'System'}</td>
                <td>{log.action_type}</td>
                <td>{values.expense_date || '-'}</td>
                <td>{values.item_name || '-'}</td>
                <td>{categoryMap.get(values.category_id) || values.category_id || '-'}</td>
                <td>{Number(values.amount || 0).toFixed(2)}</td>
                <td>{values.payment_type || '-'}</td>
                <td>{values.notes || '-'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

  return (
    <section className="page">
      <h1>Expenses</h1>
      {expenseId && <p>Viewing expense ID: {expenseId}</p>}
      <p>Track item-level expenses by category and payment type.</p>

      <div className="card">
        <h2>Add Expense</h2>
        {canEdit ? (
          <form className="form form-grid" onSubmit={handleSubmit}>
          <label>
            Tenant
            <select name="tenant_id" value={form.tenant_id} onChange={handleChange} required>
              <option value="">Select a tenant</option>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.hotel_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Week
            <select
              name="weekly_cash_id"
              value={form.weekly_cash_id}
              onChange={handleChange}
              required
            >
              <option value="">Select a week</option>
              {weeks.map((week) => (
                <option key={week.id} value={week.id}>
                  {week.week_start_date} → {week.week_end_date}
                </option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select name="category_id" value={form.category_id} onChange={handleChange} required>
              <option value="">Select a category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.category_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Expense Date
            <input name="expense_date" type="date" value={form.expense_date} onChange={handleChange} required />
          </label>
          <label>
            Item Name
            <input name="item_name" value={form.item_name} onChange={handleChange} required />
          </label>
          <label>
            Vendor
            <input name="vendor_name" value={form.vendor_name} onChange={handleChange} />
          </label>
          <label>
            Amount
            <input name="amount" type="number" step="0.01" value={form.amount} onChange={handleChange} required />
          </label>
          <label>
            Payment Type
            <select name="payment_type" value={form.payment_type} onChange={handleChange}>
              <option value="CASH">Cash</option>
              <option value="CARD">Card</option>
              <option value="BANK">Bank</option>
            </select>
          </label>
          <label className="span-2">
            Notes
            <textarea name="notes" value={form.notes} onChange={handleChange} rows={3} />
          </label>
          <div className="span-2 form-actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Saving...' : editingId ? 'Update Expense' : 'Save Expense'}
            </button>
            {editingId ? (
              <button type="button" onClick={cancelEdit} disabled={loading}>
                Cancel Edit
              </button>
            ) : (
              <button type="button" onClick={handleReset} disabled={loading}>
                Reset
              </button>
            )}
          </div>
          </form>
        ) : (
          <>
            <form className="form" onSubmit={(event) => event.preventDefault()}>
              <label>
                Tenant
                <select name="tenant_id" value={form.tenant_id} onChange={handleChange} required>
                  <option value="">Select a tenant</option>
                  {tenants.map((tenant) => (
                    <option key={tenant.id} value={tenant.id}>
                      {tenant.hotel_name}
                    </option>
                  ))}
                </select>
              </label>
            </form>
            <p className="muted">View-only access. Contact an admin to add or edit expenses.</p>
          </>
        )}
        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
      </div>

      <div className="card">
        <h2>Recent Expenses</h2>
        {!hasTenant && <p>Select a tenant to load expenses.</p>}
        {hasTenant && expenses.length === 0 && !loading && <p>No expenses yet.</p>}
        {expenses.length > 0 && (
          <div className="table-wrap">
            <div className="table-actions">
              <button
                type="button"
                onClick={() => setPage((prev) => Math.max(prev - 1, 0))}
                disabled={loading || page === 0}
              >
                Prev
              </button>
              <span>Page {page + 1}</span>
              <button
                type="button"
                onClick={() => setPage((prev) => prev + 1)}
                disabled={loading || lastPageCount < pageSize}
              >
                Next
              </button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Payment</th>
                  <th>History</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <Fragment key={expense.id}>
                    <tr key={expense.id}>
                      <td>{expense.expense_date}</td>
                      <td>{expense.item_name}</td>
                      <td>{categoryMap.get(expense.category_id) || expense.category_id}</td>
                      <td>{Number(expense.amount).toFixed(2)}</td>
                      <td>{expense.payment_type}</td>
                      <td>
                        <button
                          type="button"
                          className="link-button"
                          onClick={() => toggleHistory(expense.id)}
                        >
                          {historyOpenId === expense.id ? 'Hide' : 'View'}
                        </button>
                      </td>
                      <td>
                        {canEdit ? (
                          <button
                            type="button"
                            className="link-button"
                            onClick={() => startEdit(expense)}
                          >
                            Edit
                          </button>
                        ) : (
                          <span className="muted">View</span>
                        )}
                      </td>
                    </tr>
                    {historyOpenId === expense.id && (
                      <tr className="history-row">
                        <td colSpan={7}>
                          {historyLoading && <p>Loading history...</p>}
                          {!historyLoading && history[expense.id]?.length === 0 && (
                            <p>No history yet.</p>
                          )}
                          {!historyLoading && history[expense.id]?.length > 0 && (
                            renderHistoryTable(history[expense.id])
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
