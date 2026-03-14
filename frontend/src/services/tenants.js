import api from './api.js';

export async function listTenants() {
  const { data } = await api.get('/tenants');
  return data;
}
