import { Navigate, Route, Routes } from 'react-router-dom';

import Dashboard from './pages/Dashboard.jsx';
import WeeklyCash from './pages/WeeklyCash.jsx';
import Expenses from './pages/Expenses.jsx';
import Reports from './pages/Reports.jsx';
import Users from './pages/Users.jsx';
import Profile from './pages/Profile.jsx';
import Login from './pages/Login.jsx';
import NotFound from './pages/NotFound.jsx';
import Nav from './components/Nav.jsx';
import { useAuth } from './context/AuthContext.jsx';

function RequireAuth({ children }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <div className="app-shell">
      <Nav />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/weekly-cash"
            element={
              <RequireAuth>
                <WeeklyCash />
              </RequireAuth>
            }
          />
          <Route
            path="/expenses"
            element={
              <RequireAuth>
                <Expenses />
              </RequireAuth>
            }
          />
          <Route
            path="/expenses/:expenseId"
            element={
              <RequireAuth>
                <Expenses />
              </RequireAuth>
            }
          />
          <Route
            path="/reports"
            element={
              <RequireAuth>
                <Reports />
              </RequireAuth>
            }
          />
          <Route
            path="/profile"
            element={
              <RequireAuth>
                <Profile />
              </RequireAuth>
            }
          />
          <Route
            path="/users"
            element={
              <RequireAuth>
                <Users />
              </RequireAuth>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}
