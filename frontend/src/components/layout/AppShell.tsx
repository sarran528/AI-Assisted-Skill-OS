import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { Sidebar } from './Sidebar';

export function AppShell() {
  const token = useAuthStore((state) => state.token);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="page-grid">
      <Sidebar />
      <Outlet />
    </div>
  );
}
