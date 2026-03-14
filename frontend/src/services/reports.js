import api from './api.js';

export async function exportExpensesCsv(params) {
  const response = await api.get('/reports/expenses-export', {
    params,
    responseType: 'blob',
  });
  return response.data;
}

export async function getWeeklyDashboard(params) {
  const { data } = await api.get('/reports/weekly-dashboard', { params });
  return data;
}
