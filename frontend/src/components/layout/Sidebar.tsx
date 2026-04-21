import { Link, useLocation } from 'react-router-dom';
import { Button } from '../ui/button';
import {
  Home,
  CheckSquare,
  User,
  BookOpen,
  Map,
  HelpCircle,
  Lightbulb,
} from 'lucide-react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Home },
  { path: '/assessment', label: 'Assessment', icon: CheckSquare },
  { path: '/profile', label: 'Profile', icon: User },
  { path: '/skill/select', label: 'Skills', icon: BookOpen },
  { path: '/roadmap', label: 'Roadmap', icon: Map },
  { path: '/resources', label: 'Resources', icon: Lightbulb },
  { path: '/doubt', label: 'Help', icon: HelpCircle },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <nav className="w-64 border-r border-border bg-card p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-primary">SkillOS</h1>
      </div>

      <div className="space-y-2">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path || location.pathname.startsWith(path);
          return (
            <Link key={path} to={path}>
              <Button
                variant={isActive ? 'default' : 'ghost'}
                className="w-full justify-start"
              >
                <Icon className="mr-2 h-4 w-4" />
                {label}
              </Button>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
