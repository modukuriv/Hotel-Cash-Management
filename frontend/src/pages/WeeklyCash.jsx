import { Fragment, useEffect, useMemo, useState } from 'react';

import { listTenants } from '../services/tenants.js';
import { createWeek, listWeeks, updateWeek } from '../services/weeks.js';
import { listAuditLogs } from '../services/auditLogs.js';

const initialForm = {
  tenant_id: '',
  frequency: 'WEEKLY',
  week_start_date: '',
  week_end_date: '',
  cash_adjust_amount: '',
  cash_from_safe: '',
  notes: '',
};

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  weekday: 'long',
  month: 'long',
  day: '2-digit',
  year: 'numeric',
});

export default function WeeklyCash() {
  const [form, setForm] = useState(initialForm);
  const [tenants, setTenants] = useState([]);
  const [weeks, setWeeks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(0);
  const [lastPageCount, setLastPageCount] = useState(0);
  const [historyOpenId, setHistoryOpenId] = useState(null);
  const [history, setHistory] = useState({});
  const [historyLoading, setHistoryLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const pageSize = 10;
  const role = (localStorage.getItem('userRole') || '').toUpperCase();
  const canEdit = role === 'ADMIN' || role === 'GLOBAL_ADMIN';

  const hasTenant = useMemo(() => form.tenant_id.trim().length > 0, [form.tenant_id]);

  useEffect(() => {
    loadTenants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!form.week_start_date) {
      setForm((prev) => ({ ...prev, week_end_date: '' }));
      return;
    }
    const start = new Date(`${form.week_start_date}T00:00:00`);
    const daysToAdd = form.frequency === 'BIWEEKLY' ? 13 : 6;
    const end = new Date(start);
    end.setDate(start.getDate() + daysToAdd);
    const endValue = end.toISOString().split('T')[0];
    setForm((prev) => ({ ...prev, week_end_date: endValue }));
  }, [form.week_start_date, form.frequency]);

  useEffect(() => {
    if (!hasTenant) {
      setWeeks([]);
      return;
    }
    setPage(0);
    loadWeeks(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.tenant_id]);

  useEffect(() => {
    if (!hasTenant) return;
    loadWeeks(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const loadTenants = async () => {
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

  const loadWeeks = async (pageOverride = 0) => {
    if (!form.tenant_id) return;
    setLoading(true);
    setError('');
    try {
      const data = await listWeeks({
        tenant_id: form.tenant_id,
        limit: pageSize,
        offset: pageOverride * pageSize,
      });
      setWeeks(data);
      setLastPageCount(data.length);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load weekly cash records.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canEdit) {
      setError('View-only access.');
      return;
    }
    setError('');
    setSuccess('');
    if (!form.week_start_date || !form.week_end_date) {
      setError('Start and end dates are required.');
      return;
    }
    setLoading(true);
    try {
      const payload = {
        tenant_id: form.tenant_id,
        week_start_date: form.week_start_date,
        week_end_date: form.week_end_date,
        cash_adjust_amount: Number(form.cash_adjust_amount || 0),
        cash_from_safe: Number(form.cash_from_safe || 0),
        notes: form.notes || null,
      };
      if (editingId) {
        await updateWeek(editingId, payload);
        setSuccess('Week updated successfully.');
      } else {
        await createWeek(payload);
        setSuccess('Week created successfully.');
      }
      setEditingId(null);
      setForm((prev) => ({
        ...prev,
        week_start_date: '',
        week_end_date: '',
        cash_adjust_amount: '',
        cash_from_safe: '',
        notes: '',
      }));
      setPage(0);
      await loadWeeks(0);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save week.');
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (week) => {
    if (!canEdit) return;
    const start = new Date(`${week.week_start_date}T00:00:00`);
    const end = new Date(`${week.week_end_date}T00:00:00`);
    const diffDays = Math.round((end - start) / (1000 * 60 * 60 * 24));
    const frequency = diffDays >= 13 ? 'BIWEEKLY' : 'WEEKLY';
    setEditingId(week.id);
    setForm({
      tenant_id: week.tenant_id,
      frequency,
      week_start_date: week.week_start_date,
      week_end_date: week.week_end_date,
      cash_adjust_amount: String(week.cash_adjust_amount ?? ''),
      cash_from_safe: String(week.cash_from_safe ?? ''),
      notes: week.notes || '',
    });
    setError('');
    setSuccess('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm((prev) => ({
      ...prev,
      week_start_date: '',
      week_end_date: '',
      cash_adjust_amount: '',
      cash_from_safe: '',
      notes: '',
      frequency: 'WEEKLY',
    }));
  };

  const toggleHistory = async (weekId) => {
    if (historyOpenId === weekId) {
      setHistoryOpenId(null);
      return;
    }
    setHistoryOpenId(weekId);
    if (history[weekId]) return;
    setHistoryLoading(true);
    try {
      const logs = await listAuditLogs({
        tenant_id: form.tenant_id,
        table_name: 'weekly_cash_records',
        record_id: weekId,
      });
      setHistory((prev) => ({ ...prev, [weekId]: logs }));
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
            <th>Start</th>
            <th>End</th>
            <th>Cash Adjust</th>
            <th>Cash From Safe</th>
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
                <td>{values.week_start_date || '-'}</td>
                <td>{values.week_end_date || '-'}</td>
                <td>{currencyFormatter.format(Number(values.cash_adjust_amount || 0))}</td>
                <td>{currencyFormatter.format(Number(values.cash_from_safe || 0))}</td>
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
      <h1>Weekly Cash</h1>
      <p>Track weekly/bi-weekly cash adjustments and safe withdrawals.</p>

      <div className="card">
        <h2>Create Week Record</h2>
        {canEdit ? (
          <form className="form form-grid" onSubmit={handleSubmit}>
          <label>
            Property
            <select name="tenant_id" value={form.tenant_id} onChange={handleChange} required>
              <option value="">Select a property</option>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.hotel_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Frequency
            <select name="frequency" value={form.frequency} onChange={handleChange}>
              <option value="WEEKLY">Weekly</option>
              <option value="BIWEEKLY">Bi-Weekly</option>
            </select>
          </label>
          <label>
            Week Start Date
            <input
              name="week_start_date"
              type="date"
              value={form.week_start_date}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Week End Date
            <input name="week_end_date" type="date" value={form.week_end_date} readOnly />
          </label>
          <label>
            Cash Adjust Amount
            <input
              name="cash_adjust_amount"
              type="number"
              step="0.01"
              value={form.cash_adjust_amount}
              onChange={handleChange}
            />
          </label>
          <label>
            Cash From Safe
            <input
              name="cash_from_safe"
              type="number"
              step="0.01"
              value={form.cash_from_safe}
              onChange={handleChange}
            />
          </label>
          <label className="span-2">
            Notes
            <textarea name="notes" value={form.notes} onChange={handleChange} rows={3} />
          </label>
          <div className="span-2 form-actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Saving...' : editingId ? 'Update Week' : 'Save Week'}
            </button>
            {editingId && (
              <button type="button" onClick={cancelEdit} disabled={loading}>
                Cancel Edit
              </button>
            )}
          </div>
          </form>
        ) : (
          <>
            <form className="form" onSubmit={(event) => event.preventDefault()}>
              <label>
                Property
                <select name="tenant_id" value={form.tenant_id} onChange={handleChange} required>
                  <option value="">Select a property</option>
                  {tenants.map((tenant) => (
                    <option key={tenant.id} value={tenant.id}>
                      {tenant.hotel_name}
                    </option>
                  ))}
                </select>
              </label>
            </form>
            <p className="muted">View-only access. Contact an admin to add or edit weeks.</p>
          </>
        )}
        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
      </div>

      <div className="card">
        <h2>Weekly / Bi-Weekly Cash Report</h2>
        {!hasTenant && <p>Select a property to view the report.</p>}
        {hasTenant && weeks.length === 0 && !loading && <p>No week records yet.</p>}
        {weeks.length > 0 && (
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
                  <th>Week Range</th>
                  <th>Cash Adjust</th>
                  <th>Cash From Safe</th>
                  <th>History</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {weeks.map((week) => (
                  <Fragment key={week.id}>
                    <tr>
                      <td>{dateFormatter.format(new Date(week.week_start_date))}</td>
                      <td>
                        {week.week_start_date} → {week.week_end_date}
                      </td>
                      <td>{currencyFormatter.format(Number(week.cash_adjust_amount || 0))}</td>
                      <td>{currencyFormatter.format(Number(week.cash_from_safe || 0))}</td>
                      <td>
                        <button
                          type="button"
                          className="link-button"
                          onClick={() => toggleHistory(week.id)}
                        >
                          {historyOpenId === week.id ? 'Hide' : 'View'}
                        </button>
                      </td>
                      <td>
                        {canEdit ? (
                          <button type="button" className="link-button" onClick={() => startEdit(week)}>
                            Edit
                          </button>
                        ) : (
                          <span className="muted">View</span>
                        )}
                      </td>
                    </tr>
                    {historyOpenId === week.id && (
                      <tr className="history-row">
                        <td colSpan={6}>
                          {historyLoading && <p>Loading history...</p>}
                          {!historyLoading && history[week.id]?.length === 0 && <p>No history yet.</p>}
                          {!historyLoading && history[week.id]?.length > 0 && (
                            renderHistoryTable(history[week.id])
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
