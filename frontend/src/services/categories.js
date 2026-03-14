import api from './api.js';

export async function listCategories(params) {
  const { data } = await api.get('/expense-categories', { params });
  return data;
}
