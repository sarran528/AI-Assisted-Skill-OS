import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { Button } from '../ui/button';
import { LogOut } from 'lucide-react';

export function TopBar() {
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      window.location.href = '/login';
    }
  };

  return (
    <header className="border-b border-border bg-card px-8 py-4 flex items-center justify-between">
      <div>
        <h2 className="text-lg font-semibold">Welcome back, {user?.email}</h2>
      </div>

      <Button variant="ghost" onClick={handleLogout}>
        <LogOut className="mr-2 h-4 w-4" />
        Logout
      </Button>
    </header>
  );
}
