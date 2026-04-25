import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Sidebar } from './Sidebar';

export function AppShell() {
  const token = useAuthStore((state) => state.token);
  const location = useLocation();
  const hideSidebar = location.pathname.startsWith("/assessment/run") || location.pathname.startsWith("/session");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (hideSidebar) {
    return <Outlet />;
  }

  return (
    <div className="page-grid">
      <Sidebar />
      <Outlet />
    </div>
  );
}
