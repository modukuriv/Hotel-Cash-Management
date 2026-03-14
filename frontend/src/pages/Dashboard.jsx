import { useEffect, useMemo, useState } from 'react';

import { listTenants } from '../services/tenants.js';
import { getWeeklyDashboard } from '../services/reports.js';

const CATEGORY_COLUMNS = [
  { key: 'Hotel Misc', label: 'Hotel Misc.' },
  { key: 'CC Payments', label: 'CC Payments' },
  { key: 'Review Reward', label: 'Review Reward' },
  { key: 'Commissions', label: 'Commissions' },
  { key: 'Employee Payroll - Cash', label: 'Emp. Payroll - Cash' },
];

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

export default function Dashboard() {
  const [tenants, setTenants] = useState([]);
  const [filters, setFilters] = useState({ tenant_id: '', start: '', end: '' });
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTenants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!filters.tenant_id) return;
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.tenant_id]);

  const maxBalance = useMemo(() => {
    const max = rows.reduce(
      (acc, row) => Math.max(acc, Math.abs(row.balance_deposited || 0)),
      0
    );
    return max || 1;
  }, [rows]);

  const loadTenants = async () => {
    try {
      const data = await listTenants();
      setTenants(data);
      if (!filters.tenant_id && data.length > 0) {
        setFilters((prev) => ({ ...prev, tenant_id: data[0].id }));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load properties.');
    }
  };

  const loadDashboard = async () => {
    if (!filters.tenant_id) return;
    setLoading(true);
    setError('');
    try {
      const data = await getWeeklyDashboard({
        tenant_id: filters.tenant_id,
        start: filters.start || undefined,
        end: filters.end || undefined,
      });
      setRows(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    loadDashboard();
  };

  const getCategoryTotal = (row, key) => {
    if (!row?.category_totals) return 0;
    if (key === 'Commissions' && row.category_totals.Comissions) {
      return row.category_totals.Comissions;
    }
    return row.category_totals[key] || 0;
  };

  return (
    <section className="page">
      <h1>Dashboard</h1>
      <p>Weekly cash, expense categories, and bank deposit overview.</p>

      <div className="card">
        <h2>Filters</h2>
        <form className="form form-grid" onSubmit={handleSubmit}>
          <label>
            Property
            <select name="tenant_id" value={filters.tenant_id} onChange={handleChange} required>
              <option value="">Select a property</option>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.hotel_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Start Date
            <input name="start" type="date" value={filters.start} onChange={handleChange} />
          </label>
          <label>
            End Date
            <input name="end" type="date" value={filters.end} onChange={handleChange} />
          </label>
          <div className="span-2 form-actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Loading...' : 'Apply'}
            </button>
          </div>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h2>Cash in Hand / Expenses / Bank Deposit</h2>
        {rows.length === 0 && !loading && <p>No data for this period.</p>}
        {rows.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Cash Adjust</th>
                  <th>Cash From Safe</th>
                  {CATEGORY_COLUMNS.map((col) => (
                    <th key={col.key}>{col.label}</th>
                  ))}
                  <th>Total Expenses</th>
                  <th>Paid to Boss</th>
                  <th>Balance Deposited</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.weekly_cash_id}>
                    <td>{dateFormatter.format(new Date(row.week_start_date))}</td>
                    <td>{currencyFormatter.format(row.cash_adjust_amount || 0)}</td>
                    <td>{currencyFormatter.format(row.cash_from_safe || 0)}</td>
                    {CATEGORY_COLUMNS.map((col) => (
                      <td key={col.key}>
                        {currencyFormatter.format(getCategoryTotal(row, col.key))}
                      </td>
                    ))}
                    <td>{currencyFormatter.format(row.total_expenses || 0)}</td>
                    <td>{currencyFormatter.format(row.paid_to_boss || 0)}</td>
                    <td>
                      <div className="balance-cell">
                        <span
                          className={
                            row.balance_deposited < 0 ? 'balance-negative' : 'balance-positive'
                          }
                        >
                          {currencyFormatter.format(row.balance_deposited || 0)}
                        </span>
                        <div className="balance-bar">
                          <div
                            className={`balance-bar-fill ${
                              row.balance_deposited < 0 ? 'negative' : 'positive'
                            }`}
                            style={{
                              width: `${Math.min(
                                100,
                                (Math.abs(row.balance_deposited || 0) / maxBalance) * 100
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
