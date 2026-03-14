import api from './api.js';

export async function listAuditLogs(params) {
  const { data } = await api.get('/audit-logs', { params });
  return data;
}
