import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export default function Login() {
  const { login, token } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  useEffect(() => {
    if (token) {
      navigate('/dashboard', { replace: true });
    }
  }, [token, navigate]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setInfo('');
    try {
      setInfo('');
      await login(username, code);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed.');
    }
  };

  return (
    <section className="page">
      <h1>Sign In</h1>
      <p>Enter your email and Google Authenticator code.</p>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            type="text"
            placeholder="Enter your email..."
            required
          />
        </label>
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
        <p className="muted">All users must use Google Authenticator.</p>
        <div className="form-actions">
          <button type="submit">Login</button>
        </div>
      </form>
      {error && <p className="error">{error}</p>}
      {info && <p className="success">{info}</p>}
    </section>
  );
}
