import api from './api.js';

export async function createExpense(payload) {
  const { data } = await api.post('/expenses', payload);
  return data;
}

export async function listExpenses(params) {
  const { data } = await api.get('/expenses', { params });
  return data;
}

export async function updateExpense(id, payload) {
  const { data } = await api.put(`/expenses/${id}`, payload);
  return data;
}
