import { useEffect, useMemo, useState } from 'react';

import { listTenants } from '../services/tenants.js';
import { listCategories } from '../services/categories.js';
import { listExpenses } from '../services/expenses.js';
import { exportExpensesCsv } from '../services/reports.js';

const initialFilters = {
  tenant_id: '',
  category_id: '',
  payment_type: '',
  start: '',
  end: '',
};

export default function Reports() {
  const [filters, setFilters] = useState(initialFilters);
  const [tenants, setTenants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [lastPageCount, setLastPageCount] = useState(0);
  const pageSize = 10;

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
    if (!filters.tenant_id) {
      setCategories([]);
      setExpenses([]);
      return;
    }
    setPage(0);
    loadCategories(filters.tenant_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.tenant_id]);

  useEffect(() => {
    if (!filters.tenant_id) return;
    runReport(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const loadTenants = async () => {
    try {
      const data = await listTenants();
      setTenants(data);
      if (!filters.tenant_id && data.length > 0) {
        setFilters((prev) => ({ ...prev, tenant_id: data[0].id }));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load tenants.');
    }
  };

  const loadCategories = async (tenantId) => {
    try {
      const data = await listCategories({ tenant_id: tenantId });
      setCategories(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load categories.');
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const runReport = async (pageOverride = 0) => {
    if (!filters.tenant_id) {
      setError('Select a property to run the report.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const params = {
        tenant_id: filters.tenant_id,
        start: filters.start || undefined,
        end: filters.end || undefined,
        category_id: filters.category_id || undefined,
        payment_type: filters.payment_type || undefined,
        limit: pageSize,
        offset: pageOverride * pageSize,
      };
      const data = await listExpenses(params);
      setExpenses(data);
      setLastPageCount(data.length);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load report data.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setPage(0);
    runReport(0);
  };

  const handleExport = async () => {
    if (!filters.tenant_id) {
      setError('Select a property to export.');
      return;
    }
    setError('');
    try {
      const blob = await exportExpensesCsv({
        tenant_id: filters.tenant_id,
        start: filters.start || undefined,
        end: filters.end || undefined,
        category_id: filters.category_id || undefined,
        payment_type: filters.payment_type || undefined,
      });
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'expenses_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to export report.');
    }
  };

  return (
    <section className="page">
      <h1>Expense Reports</h1>
      <p>Filter by property, category, and date range. Export to CSV.</p>

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
            Category
            <select name="category_id" value={filters.category_id} onChange={handleChange}>
              <option value="">All categories</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.category_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Payment Type
            <select name="payment_type" value={filters.payment_type} onChange={handleChange}>
              <option value="">All</option>
              <option value="CASH">Cash</option>
              <option value="CARD">Card</option>
              <option value="BANK">Bank</option>
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
              {loading ? 'Running...' : 'Run Report'}
            </button>
            <button type="button" onClick={handleExport} disabled={loading || !filters.tenant_id}>
              Download CSV
            </button>
          </div>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h2>Expense History</h2>
        {expenses.length === 0 && !loading && <p>No expenses found for this filter.</p>}
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
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr key={expense.id}>
                    <td>{expense.expense_date}</td>
                    <td>{expense.item_name}</td>
                    <td>{categoryMap.get(expense.category_id) || expense.category_id}</td>
                    <td>{Number(expense.amount).toFixed(2)}</td>
                    <td>{expense.payment_type}</td>
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
