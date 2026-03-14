import api from './api.js';

export async function listWeeks(params) {
  const { data } = await api.get('/weeks', { params });
  return data;
}

export async function createWeek(payload) {
  const { data } = await api.post('/weeks', payload);
  return data;
}

export async function updateWeek(id, payload) {
  const { data } = await api.put(`/weeks/${id}`, payload);
  return data;
}
