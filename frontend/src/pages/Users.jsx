import { useEffect, useMemo, useState } from 'react';
import QRCode from 'qrcode';
import api from '../services/api.js';

const ROLE_OPTIONS = ['ADMIN', 'USER', 'GLOBAL_ADMIN'];

const emptyInvite = {
  email: '',
  role: 'USER',
  tenant_id: '',
  first_name: '',
  last_name: '',
};

export default function Users() {
  const [users, setUsers] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [invite, setInvite] = useState(emptyInvite);
  const [inviteMessage, setInviteMessage] = useState('');
  const [inviteSetup, setInviteSetup] = useState(null);
  const [inviteQr, setInviteQr] = useState('');
  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState({ role: 'USER', is_active: true });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const role = (localStorage.getItem('userRole') || '').toUpperCase();

  const tenantMap = useMemo(
    () => new Map(tenants.map((tenant) => [tenant.id, tenant.hotel_name])),
    [tenants]
  );

  const loadTenants = async () => {
    try {
      const { data } = await api.get('/tenants');
      setTenants(data);
      if (data.length && !invite.tenant_id) {
        setInvite((prev) => ({ ...prev, tenant_id: data[0].id }));
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load properties.');
    }
  };

  const loadUsers = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/users');
      setUsers(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTenants();
  }, []);

  useEffect(() => {
    if (role === 'GLOBAL_ADMIN') {
      loadUsers();
    }
  }, [role]);

  const handleInviteChange = (field) => (event) => {
    setInvite((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleInvite = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setInviteMessage('');
    setInviteSetup(null);
    setInviteQr('');
    try {
      const payload = {
        email: invite.email,
        role: invite.role,
        tenant_id: invite.tenant_id,
        first_name: invite.first_name || null,
        last_name: invite.last_name || null,
      };
      const { data } = await api.post('/users', payload);
      setInviteMessage(data.message || 'Invite sent.');
      setSuccess(`User invited: ${data.user.email}`);
      if (data.totp_setup) {
        setInviteSetup(data.totp_setup);
        const url = await QRCode.toDataURL(data.totp_setup.otpauth_uri);
        setInviteQr(url);
      }
      setInvite(emptyInvite);
      await loadUsers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to invite user.');
    }
  };

  const startEdit = (user) => {
    setEditing(user);
    setEditForm({
      role: user.role,
      is_active: user.is_active,
    });
    setSuccess('');
    setError('');
  };

  const cancelEdit = () => {
    setEditing(null);
    setEditForm({ role: 'USER', is_active: true });
  };

  const handleEditChange = (field) => (event) => {
    const isCheckbox = field === 'is_active';
    const value = isCheckbox ? event.target.checked : event.target.value;
    setEditForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleUpdate = async (event) => {
    event.preventDefault();
    if (!editing) return;
    setError('');
    setSuccess('');
    try {
      const payload = {
        role: editForm.role,
        is_active: editForm.is_active,
      };
      await api.put(`/users/${editing.id}`, payload);
      setSuccess('User updated.');
      setEditing(null);
      await loadUsers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to update user.');
    }
  };

  const handleResetTotp = async (user) => {
    setError('');
    setSuccess('');
    setInviteSetup(null);
    setInviteQr('');
    try {
      const { data } = await api.post(`/users/${user.id}/totp`);
      setInviteSetup(data);
      const url = await QRCode.toDataURL(data.otpauth_uri);
      setInviteQr(url);
      setSuccess(`Authenticator reset for ${user.email}`);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to reset authenticator.');
    }
  };
  const handleDelete = async (userId) => {
    if (!window.confirm('Delete this user?')) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`/users/${userId}`);
      setSuccess('User deleted.');
      await loadUsers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to delete user.');
    }
  };

  if (role !== 'GLOBAL_ADMIN') {
    return (
      <section className="page">
        <h1>User Management</h1>
        <p>Only global admins can manage users.</p>
      </section>
    );
  }

  return (
    <section className="page">
      <h1>User Management</h1>
      <p>Invite users, assign roles, and review login activity.</p>

      <div className="card">
        <h2>Invite User</h2>
        <form className="form form-grid" onSubmit={handleInvite}>
          <label>
            Email
            <input value={invite.email} onChange={handleInviteChange('email')} type="email" />
          </label>
          <label>
            Role
            <select value={invite.role} onChange={handleInviteChange('role')}>
              {ROLE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Property
            <select value={invite.tenant_id} onChange={handleInviteChange('tenant_id')}>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.hotel_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            First Name
            <input value={invite.first_name} onChange={handleInviteChange('first_name')} />
          </label>
          <label>
            Last Name
            <input value={invite.last_name} onChange={handleInviteChange('last_name')} />
          </label>
          <div className="form-actions span-2">
            <button type="submit">Send Invite</button>
          </div>
        </form>
        {inviteMessage && <p className="success">{inviteMessage}</p>}
        {inviteSetup && (
          <div className="card">
            <h3>Authenticator Setup</h3>
            <p>Scan this QR code in Google Authenticator for the invited user.</p>
            {inviteQr && <img src={inviteQr} alt="Authenticator QR" />}
            <p>
              Secret: <strong>{inviteSetup.secret}</strong>
            </p>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Users</h2>
        {loading ? <p>Loading users...</p> : null}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
                <th>Property</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Login Count</th>
                <th>Authenticator</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.email}</td>
                  <td>{user.role}</td>
                  <td>{tenantMap.get(user.tenant_id) || user.tenant_id}</td>
                  <td>{user.is_active ? 'Active' : 'Inactive'}</td>
                  <td>
                    {user.last_login_at
                      ? new Date(user.last_login_at).toLocaleString()
                      : '—'}
                  </td>
                  <td>{user.login_count ?? 0}</td>
                  <td>{user.totp_enabled ? 'Enabled' : 'Not Set'}</td>
                  <td>
                    <button className="link-button" type="button" onClick={() => startEdit(user)}>
                      Edit
                    </button>
                    <button
                      className="link-button"
                      type="button"
                      onClick={() => handleResetTotp(user)}
                    >
                      Reset Auth
                    </button>
                    <button
                      className="link-button danger"
                      type="button"
                      onClick={() => handleDelete(user.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {editing && (
          <div className="card">
            <h3>Edit User</h3>
            <form className="form" onSubmit={handleUpdate}>
              <label>
                Role
                <select value={editForm.role} onChange={handleEditChange('role')}>
                  {ROLE_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Active
                <input
                  type="checkbox"
                  checked={editForm.is_active}
                  onChange={handleEditChange('is_active')}
                />
              </label>
              <div className="form-actions">
                <button type="submit">Save</button>
                <button type="button" onClick={cancelEdit}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </section>
  );
}
