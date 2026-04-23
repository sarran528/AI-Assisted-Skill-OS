import { Link, useLocation } from 'react-router-dom';
import { BrutalButton as Button } from '../brutal/BrutalButton';
import { useAuthStore } from '../../store/authStore';
import { useNavigationStore } from '../../store/navigationStore';
import {
  Home,
  CheckSquare,
  User,
  BookOpen,
  Map,
  HelpCircle,
  Lightbulb,
  Lock,
  LogOut,
} from 'lucide-react';

interface NavItem {
  id: string;
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  getStateText: () => string;
  isLocked: () => boolean;
}

export function RevisedSidebar() {
  const location = useLocation();
  const { user, clearAuth } = useAuthStore();
  const { 
    assessmentProgress, 
    profileState, 
    currentSkill, 
    roadmapState 
  } = useNavigationStore();

  const handleLogout = async () => {
    try {
      clearAuth();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const navItems: NavItem[] = [
    {
      id: 'dashboard',
      path: '/dashboard',
      label: 'Dashboard',
      icon: Home,
      getStateText: () => '',
      isLocked: () => false,
    },
    {
      id: 'assessment',
      path: '/assessment',
      label: 'Assessment',
      icon: CheckSquare,
      getStateText: () => {
        const completedLevels = Object.values(assessmentProgress)
          .filter(level => level.status === 'complete').length;
        
        if (completedLevels === 6) return 'Complete';
        return `${completedLevels} / 6 complete`;
      },
      isLocked: () => false,
    },
    {
      id: 'profile',
      path: '/profile',
      label: 'Profile',
      icon: User,
      getStateText: () => {
        const completedLevels = Object.values(assessmentProgress)
          .filter(level => level.status === 'complete').length;
        
        if (completedLevels < 6) return 'Locked';
        if (profileState.isActive) return 'Active';
        return 'Inactive';
      },
      isLocked: () => {
        const completedLevels = Object.values(assessmentProgress)
          .filter(level => level.status === 'complete').length;
        return completedLevels < 6;
      },
    },
    {
      id: 'skills',
      path: '/skill/select',
      label: 'Skills',
      icon: BookOpen,
      getStateText: () => {
        if (!profileState.isActive) return 'Locked';
        if (currentSkill.skillName) return `${currentSkill.skillName} selected`;
        return 'No skill selected';
      },
      isLocked: () => !profileState.isActive,
    },
    {
      id: 'roadmap',
      path: `/roadmap/${currentSkill.skillId || ''}`,
      label: 'Roadmap',
      icon: Map,
      getStateText: () => {
        if (!currentSkill.skillId) return 'Locked';
        if (!roadmapState.isGenerated) return 'No roadmap';
        if (roadmapState.currentPhase) {
          const phases = ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'];
          const currentPhaseIndex = phases.findIndex(p => p === roadmapState.currentPhase);
          if (currentPhaseIndex >= 0) {
            return `${roadmapState.currentPhase} — active`;
          }
        }
        return 'Roadmap generated';
      },
      isLocked: () => !currentSkill.skillId || !roadmapState.isGenerated,
    },
    {
      id: 'resources',
      path: '/resources',
      label: 'Resources',
      icon: Lightbulb,
      getStateText: () => {
        if (roadmapState.currentPhase) {
          return `Showing ${roadmapState.currentPhase} content`;
        }
        return 'No active phase';
      },
      isLocked: () => false,
    },
    {
      id: 'help',
      path: '/doubt',
      label: 'Help',
      icon: HelpCircle,
      getStateText: () => '',
      isLocked: () => false,
    },
  ];

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    if (path === '/assessment') return location.pathname === '/assessment';
    if (path === '/profile') return location.pathname === '/profile';
    if (path === '/skill/select') return location.pathname.startsWith('/skill');
    if (path.startsWith('/roadmap')) return location.pathname.startsWith('/roadmap');
    if (path === '/resources') return location.pathname === '/resources';
    if (path === '/doubt') return location.pathname === '/doubt';
    return false;
  };

  const getLockTooltip = (item: NavItem) => {
    if (!item.isLocked()) return '';
    
    if (item.id === 'profile') {
      return 'Complete all 6 assessments to unlock';
    }
    if (item.id === 'skills') {
      return 'Complete assessment and build profile to unlock';
    }
    if (item.id === 'roadmap') {
      return 'Select a skill and generate roadmap to unlock';
    }
    
    return 'Prerequisites not met';
  };

  return (
    <div className="fixed left-0 top-0 h-screen w-[220px] bg-card border-r border-border flex flex-col">
      {/* App Name */}
      <div className="p-4 border-b border-border">
        <h1 className="text-xl font-bold text-primary">SkillOS</h1>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 overflow-hidden">
        <nav className="p-2">
          {navItems.map((item) => {
            const active = isActive(item.path);
            const locked = item.isLocked();
            const stateText = item.getStateText();
            const Icon = item.icon;
            
            return (
              <div key={item.id} className="relative group">
                <Link to={locked ? '#' : item.path}>
                  <div
                    className={`
                      flex items-center px-3 py-2 rounded-md mb-1 transition-colors
                      ${active 
                        ? 'bg-yellow-400 text-black font-medium' 
                        : locked 
                          ? 'text-muted-foreground cursor-not-allowed opacity-50'
                          : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                      }
                    `}
                  >
                    <Icon className="h-4 w-4 mr-3 flex-shrink-0" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                </Link>
                
                {/* State Indicator */}
                {stateText && (
                  <div className="ml-10 mb-1">
                    <span className={`text-xs ${
                      locked 
                        ? 'text-muted-foreground' 
                        : active 
                          ? 'text-black/70' 
                          : 'text-muted-foreground'
                    }`}>
                      {stateText}
                    </span>
                  </div>
                )}

                {/* Lock Tooltip */}
                {locked && (
                  <div className="absolute left-full ml-2 top-1/2 transform -translate-y-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                    {getLockTooltip(item)}
                    <div className="absolute right-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-r-gray-900"></div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section - User Info and Logout */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground mb-2">
          {user?.email || 'user@example.com'}
        </div>
        <Button
          variant="secondary"
          onClick={handleLogout}
          className="w-full"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>
    </div>
  );
}
