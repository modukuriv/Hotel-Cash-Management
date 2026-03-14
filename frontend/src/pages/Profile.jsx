import { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import api from '../services/api.js';

export default function Profile() {
  const [user, setUser] = useState(null);
  const [profileForm, setProfileForm] = useState({ first_name: '', last_name: '' });
  const [totpSetup, setTotpSetup] = useState(null);
  const [totpQr, setTotpQr] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadProfile = async () => {
    try {
      const { data } = await api.get('/users/me');
      setUser(data);
      setProfileForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
      });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load profile.');
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleProfileChange = (field) => (event) => {
    setProfileForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const saveProfile = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    try {
      const payload = {
        first_name: profileForm.first_name || null,
        last_name: profileForm.last_name || null,
      };
      const { data } = await api.put('/users/me', payload);
      setUser(data);
      setSuccess('Profile updated.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to update profile.');
    }
  };

  const handleTotpSetup = async () => {
    setError('');
    setSuccess('');
    setTotpSetup(null);
    setTotpQr('');
    try {
      const { data } = await api.post('/users/me/totp');
      setTotpSetup(data);
      const url = await QRCode.toDataURL(data.otpauth_uri);
      setTotpQr(url);
      setSuccess('Authenticator setup generated.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate authenticator setup.');
    }
  };

  return (
    <section className="page">
      <h1>Profile</h1>
      <p>Manage your account details.</p>

      <div className="card">
        <h2>Account Info</h2>
        {user ? (
          <div className="profile-grid">
            <div>
              <strong>Email</strong>
              <div>{user.email}</div>
            </div>
            <div>
              <strong>Role</strong>
              <div>{user.role}</div>
            </div>
            <div>
              <strong>Property</strong>
              <div>{user.tenant_id}</div>
            </div>
            <div>
              <strong>Last Login</strong>
              <div>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '—'}</div>
            </div>
            <div>
              <strong>Authenticator</strong>
              <div>{user.totp_enabled ? 'Enabled' : 'Not Set'}</div>
            </div>
          </div>
        ) : (
          <p>Loading profile...</p>
        )}
      </div>

      <div className="card">
        <h2>Update Profile</h2>
        <form className="form" onSubmit={saveProfile}>
          <label>
            First Name
            <input value={profileForm.first_name} onChange={handleProfileChange('first_name')} />
          </label>
          <label>
            Last Name
            <input value={profileForm.last_name} onChange={handleProfileChange('last_name')} />
          </label>
          <div className="form-actions">
            <button type="submit">Save Profile</button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Authenticator Setup</h2>
        <p>Use Google Authenticator to scan your QR code.</p>
        <div className="form-actions">
          <button type="button" onClick={handleTotpSetup}>
            Generate Authenticator QR
          </button>
        </div>
        {totpSetup && (
          <div className="card">
            {totpQr && <img src={totpQr} alt="Authenticator QR" />}
            <p>
              Secret: <strong>{totpSetup.secret}</strong>
            </p>
          </div>
        )}
      </div>

      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </section>
  );
}
