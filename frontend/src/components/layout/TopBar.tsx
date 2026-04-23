import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/authApi';
import { BrutalButton as Button } from '../brutal/BrutalButton';
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
      {/* App Logo/Name */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-sm">S</span>
        </div>
        <h1 className="text-xl font-bold text-primary">SkillOS</h1>
      </div>

      {/* User Info and Logout */}
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-sm font-medium">{user?.email || 'User'}</p>
          <p className="text-xs text-muted-foreground">Active Session</p>
        </div>
        
        <div className="w-px h-8 bg-border"></div>
        
        <Button variant="mono" onClick={handleLogout}>
          <LogOut className="h-4 w-4" />
          <span className="ml-2 hidden sm:inline">Logout</span>
        </Button>
      </div>
    </header>
  );
}
