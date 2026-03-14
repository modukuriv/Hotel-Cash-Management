import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export default function Nav() {
  const { role, email, token, logout } = useAuth();
  const navigate = useNavigate();
  const normalizedRole = (role || localStorage.getItem('userRole') || '').toUpperCase();
  const links = token
    ? [
        { to: '/dashboard', label: 'Dashboard' },
        { to: '/weekly-cash', label: 'Weekly Cash' },
        { to: '/expenses', label: 'Expenses' },
        { to: '/reports', label: 'Reports' },
      ]
    : [];
  if (token && normalizedRole === 'GLOBAL_ADMIN') {
    links.push({ to: '/users', label: 'Users' });
  }

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };
  return (
    <header className="app-nav">
      <div className="nav-left">
        <div className="brand">Hotel Cash Management</div>
        <nav>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `nav-link${isActive ? ' nav-link-active' : ''}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
      {token ? (
        <div className="nav-right">
          <div className="user-chip">
            <div>{email || 'Signed in'}</div>
            {normalizedRole && <span className="user-role">{normalizedRole}</span>}
          </div>
          <NavLink className="nav-link" to="/profile">
            Profile
          </NavLink>
          <button type="button" className="nav-link" onClick={handleLogout}>
            Logout
          </button>
        </div>
      ) : null}
    </header>
  );
}
