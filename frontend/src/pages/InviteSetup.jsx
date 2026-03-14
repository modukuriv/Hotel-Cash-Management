import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import QRCode from 'qrcode';
import api from '../services/api.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function InviteSetup() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { applySession } = useAuth();
  const [invite, setInvite] = useState(null);
  const [qr, setQr] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    let active = true;
    const loadInvite = async () => {
      try {
        setLoading(true);
        const { data } = await api.get(`/invites/${token}`);
        if (!active) return;
        setInvite(data);
        if (data?.otpauth_uri) {
          const url = await QRCode.toDataURL(data.otpauth_uri);
          if (active) setQr(url);
        }
      } catch (err) {
        if (active) {
          setError(err?.response?.data?.detail || 'Invite not found or expired.');
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    loadInvite();
    return () => {
      active = false;
    };
  }, [token]);

  const handleAccept = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    try {
      const { data } = await api.post(`/invites/${token}/accept`, { code });
      applySession(data);
      setSuccess('Invite accepted. Redirecting...');
      setTimeout(() => navigate('/dashboard', { replace: true }), 600);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to accept invite.');
    }
  };

  if (loading) {
    return (
      <section className="page">
        <h1>Invite Setup</h1>
        <p>Loading invite...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="page">
        <h1>Invite Setup</h1>
        <p className="error">{error}</p>
      </section>
    );
  }

  return (
    <section className="page">
      <h1>Welcome{invite?.property_name ? ` to ${invite.property_name}` : ''}</h1>
      <p>Set up Google Authenticator to access your account.</p>

      <div className="card">
        <h2>Account</h2>
        <p>
          <strong>Email:</strong> {invite?.email}
        </p>
        {invite?.role ? (
          <p>
            <strong>Role:</strong> {invite.role}
          </p>
        ) : null}
      </div>

      <div className="card">
        <h2>Authenticator Setup</h2>
        <p>Scan this QR code in Google Authenticator.</p>
        {qr && <img src={qr} alt="Authenticator QR" />}
        <p className="muted">Then enter the 6-digit code below to confirm.</p>
        <form className="form" onSubmit={handleAccept}>
          <label>
            Authenticator Code
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              inputMode="numeric"
              placeholder="123456"
              required
            />
          </label>
          <div className="form-actions">
            <button type="submit">Activate Account</button>
          </div>
        </form>
      </div>

      {success && <p className="success">{success}</p>}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
