import { Link, useLocation } from 'react-router-dom';
import { BrutalButton as Button } from '../brutal/BrutalButton';
import { useNavigationStore } from '../../store/navigationStore';
import { useAssessmentStore, GAME_IDS } from '../../stores/assessmentStore';
import {
  Home,
  CheckSquare,
  User,
  BookOpen,
  Map,
  HelpCircle,
  Lightbulb,
  Lock,
  Check,
  Clock,
  Play,
  AlertCircle,
} from 'lucide-react';

interface NavItem {
  id: string;
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  requiredState?: string;
  getState: () => 'locked' | 'incomplete' | 'active' | 'complete';
  getTooltip?: () => string;
  getProgress?: () => React.ReactNode;
}

export function StateAwareSidebar() {
  const location = useLocation();
  const { 
    systemState, 
    profileState, 
    currentSkill, 
    roadmapState, 
    sessionState 
  } = useNavigationStore();
  const { games } = useAssessmentStore();
  const completedCount = GAME_IDS.filter(id => games[id].completed).length;

  const navItems: NavItem[] = [
    {
      id: 'dashboard',
      path: '/dashboard',
      label: 'Dashboard',
      icon: Home,
      getState: () => location.pathname === '/dashboard' ? 'active' : 'incomplete',
    },
    {
      id: 'assessment',
      path: '/assessment',
      label: 'Assessment',
      icon: CheckSquare,
      getState: () => {
        if (location.pathname === '/assessment') return 'active';
        if (completedCount === 6) return 'complete';
        if (completedCount > 0) return 'incomplete';
        return 'incomplete';
      },
      getProgress: () => {
        return (
          <div className="flex items-center space-x-1">
            {GAME_IDS.map((id) => {
              const g = games[id];
              if (g.completed) {
                return <Check key={id} className="h-3 w-3 text-green-600" />;
              } else if (g.attempts > 0) {
                return <Play key={id} className="h-3 w-3 text-yellow-600" />;
              } else {
                return <Clock key={id} className="h-3 w-3 text-blue-600" />;
              }
            })}
            <span className="text-xs text-muted-foreground ml-2">
              {completedCount}/6 complete
            </span>
          </div>
        );
      },
    },
    {
      id: 'profile',
      path: '/profile',
      label: 'Profile',
      icon: User,
      getState: () => {
        if (location.pathname === '/profile') return 'active';
        if (completedCount < 6) return 'locked';
        if (profileState.isActive) return 'complete';
        return 'incomplete';
      },
      getTooltip: () => {
        if (completedCount < 6) {
          return `Complete all 6 assessment levels first (${completedCount}/6 done)`;
        }
        return profileState.isActive ? 'View your profile' : 'Profile building in progress';
      },
      getProgress: () => {
        if (!profileState.isActive) return null;
        
        return (
          <div className="text-xs text-muted-foreground">
            <div>Cognitive: {profileState.dimensions.cognitive_capacity.toFixed(2)}</div>
            <div>Attention: {profileState.dimensions.attention_stability.toFixed(2)}</div>
          </div>
        );
      },
    },
    {
      id: 'skills',
      path: '/skill/select',
      label: 'Skills',
      icon: BookOpen,
      getState: () => {
        if (location.pathname.startsWith('/skill')) return 'active';
        
        if (!profileState.isActive) return 'locked';
        if (currentSkill.skillId) return 'complete';
        return 'incomplete';
      },
      getTooltip: () => {
        if (!profileState.isActive) {
          return 'Complete assessment and build profile first';
        }
        return currentSkill.skillId ? 'Change selected skill' : 'Select a skill to learn';
      },
    },
    {
      id: 'roadmap',
      path: `/roadmap/${currentSkill.skillId || ''}`,
      label: 'Roadmap',
      icon: Map,
      getState: () => {
        if (location.pathname.startsWith('/roadmap')) return 'active';
        
        if (!currentSkill.skillId) return 'locked';
        if (roadmapState.isGenerated) return 'complete';
        return 'incomplete';
      },
      getTooltip: () => {
        if (!currentSkill.skillId) {
          return 'Select a skill first';
        }
        if (!roadmapState.isGenerated) {
          return 'Roadmap generation in progress';
        }
        return 'View your learning roadmap';
      },
      getProgress: () => {
        if (!roadmapState.isGenerated) return null;
        
        return (
          <div className="text-xs text-muted-foreground">
            <div>Current: {roadmapState.currentPhase || 'Not started'}</div>
            <div>Technique: {roadmapState.currentTechnique || 'None'}</div>
          </div>
        );
      },
    },
    {
      id: 'resources',
      path: '/resources',
      label: 'Resources',
      icon: Lightbulb,
      getState: () => {
        if (location.pathname === '/resources') return 'active';
        return 'incomplete'; // Always accessible
      },
      getTooltip: () => 'Resources and learning materials',
    },
    {
      id: 'help',
      path: '/help',
      label: 'Help',
      icon: HelpCircle,
      getState: () => {
        if (location.pathname === '/help') return 'active';
        return 'incomplete'; // Always accessible
      },
      getTooltip: () => 'Get help with current context',
    },
  ];

  const getStateStyles = (state: 'locked' | 'incomplete' | 'active' | 'complete') => {
    switch (state) {
      case 'locked':
        return 'opacity-50 cursor-not-allowed';
      case 'incomplete':
        return '';
      case 'active':
        return 'bg-primary text-primary-foreground';
      case 'complete':
        return 'text-green-600';
      default:
        return '';
    }
  };

  const getStateIcon = (state: 'locked' | 'incomplete' | 'active' | 'complete') => {
    switch (state) {
      case 'locked':
        return <Lock className="h-4 w-4" />;
      case 'complete':
        return <Check className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <nav className="w-64 border-r border-border bg-card p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-primary">SkillOS</h1>
        <div className="text-xs text-muted-foreground mt-1">
          State: {systemState.replace('_', ' ')}
        </div>
      </div>

      <div className="space-y-2">
        {navItems.map((item) => {
          const state = item.getState();
          const isLocked = state === 'locked';
          const Icon = item.icon;
          
          return (
            <div key={item.id} className="relative group">
              <Link to={isLocked ? '#' : item.path}>
                <Button
                  variant={state === 'active' ? 'primary' : 'secondary'}
                  className={`w-full justify-start ${getStateStyles(state)}`}
                  disabled={isLocked}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {item.label}
                  {getStateIcon(state)}
                </Button>
              </Link>
              
              {/* Progress indicator */}
              {item.getProgress && (
                <div className="ml-8 mt-1">
                  {item.getProgress()}
                </div>
              )}
              
              {/* Tooltip */}
              {item.getTooltip && isLocked && (
                <div className="absolute left-full ml-2 top-1/2 transform -translate-y-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                  {item.getTooltip()}
                  <div className="absolute right-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-r-gray-900"></div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </nav>
  );
}
