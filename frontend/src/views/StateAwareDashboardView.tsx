import { useNavigate } from "react-router-dom";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";
import { useAuthStore } from "../store/authStore";
import { useAssessmentStore, GAME_IDS } from "../stores/assessmentStore";
import { SidebarLayout } from "../components/layout/SidebarLayout";
import {
  CheckSquare,
  User,
  BookOpen,
  Map,
  Play,
  Lock,
  Clock,
  Check,
  AlertCircle,
  Target,
  TrendingUp,
} from "lucide-react";

export function StateAwareDashboardView() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const {
    systemState,
    profileState,
    currentSkill,
    roadmapState,
    sessionState,
  } = useNavigationStore();
  const { games } = useAssessmentStore();

  // Calculate assessment completion
  const completedLevels = GAME_IDS.filter(id => games[id].completed).length;
  const inProgressLevels = GAME_IDS.filter(id => !games[id].completed && games[id].attempts > 0).length;

  // Render different dashboard states based on system state
  const renderDashboardContent = () => {
    switch (systemState) {
      case 'assessment_incomplete':
        return <AssessmentIncompleteDashboard />;
      case 'profile_inactive':
        return <ProfileInactiveDashboard />;
      case 'skill_selection':
        return <SkillSelectionDashboard />;
      case 'roadmap_generation':
        return <RoadmapGenerationDashboard />;
      case 'roadmap_active':
        return <RoadmapActiveDashboard />;
      case 'session_active':
        return <SessionActiveDashboard />;
      default:
        return <AssessmentIncompleteDashboard />;
    }
  };

  const AssessmentIncompleteDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Welcome to SkillOS</h1>
        <p className="text-lg text-muted-foreground mb-2">
          Let's build your personalized learning profile
        </p>
        <p className="text-sm text-muted-foreground">
          Complete the assessment to unlock your learning journey
        </p>
      </div>

      {/* Assessment Progress */}
      <BrutalCard className="max-w-2xl mx-auto">
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold mb-2">Assessment Progress</h2>
          <p className="text-muted-foreground">
            {completedLevels} of 6 levels completed
          </p>
        </div>

        {/* Level Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {GAME_IDS.map((levelNum) => {
            const progress = games[levelNum];
            const isComplete = progress.completed;
            const isInProgress = !isComplete && progress.attempts > 0;
            const isLocked = !isComplete && !isInProgress;

            return (
              <BrutalCard
                key={levelNum}
                className={`${isLocked ? 'opacity-50' : ''} ${
                  isInProgress ? 'border-yellow-500' : ''
                } ${isComplete ? 'border-green-500' : ''}`}
              >
                <div className="text-center">
                  <div className="mb-2">
                    {isLocked && <Lock className="h-8 w-8 text-gray-400 mx-auto" />}
                    {isInProgress && <Play className="h-8 w-8 text-yellow-500 mx-auto" />}
                    {isComplete && <Check className="h-8 w-8 text-green-500 mx-auto" />}
                  </div>
                  <h3 className="font-bold mb-1">Level {levelNum}</h3>
                  <p className="text-sm text-muted-foreground mb-2">
                    {isLocked && 'Locked'}
                    {isInProgress && 'In Progress'}
                    {isComplete && 'Complete'}
                  </p>
                  {isInProgress && (
                    <p className="text-xs text-muted-foreground">
                      {progress.lastLivesRemaining} lives remaining
                    </p>
                  )}
                </div>
              </BrutalCard>
            );
          })}
        </div>

        {/* Primary CTA */}
        <div className="text-center">
          <BrutalButton
            variant="primary"
            onClick={() => navigate('/assessment')}
            className="px-8 py-3"
          >
            <CheckSquare className="mr-2 h-5 w-5" />
            {inProgressLevels > 0 ? 'Continue Assessment' : 'Start Assessment'}
          </BrutalButton>
        </div>
      </BrutalCard>

      {/* Instructions */}
      <div className="text-center text-sm text-muted-foreground max-w-2xl mx-auto">
        <p>
          The assessment consists of 6 levels that measure different aspects of your learning profile.
          Complete all levels to unlock personalized skill recommendations and learning roadmaps.
        </p>
      </div>
    </div>
  );

  const ProfileInactiveDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Assessment Complete!</h1>
        <p className="text-lg text-muted-foreground mb-2">
          Your learning profile is being generated
        </p>
        <p className="text-sm text-muted-foreground">
          This usually takes a few moments...
        </p>
      </div>

      {/* Profile Generation Status */}
      <BrutalCard className="max-w-2xl mx-auto">
        <div className="text-center">
          <div className="animate-pulse mb-4">
            <div className="w-16 h-16 bg-yellow-200 rounded-full mx-auto flex items-center justify-center">
              <User className="h-8 w-8 text-yellow-600" />
            </div>
          </div>
          <h2 className="text-xl font-bold mb-2">Building Your Profile</h2>
          <p className="text-muted-foreground mb-4">
            Analyzing your assessment results to create your personalized learning profile
          </p>
          <div className="animate-pulse space-y-2">
            <div className="h-2 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-2 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-2 bg-gray-200 rounded w-2/3 mx-auto"></div>
          </div>
        </div>
      </BrutalCard>
    </div>
  );

  const SkillSelectionDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Your Learning Profile</h1>
        <p className="text-lg text-muted-foreground mb-2">
          Choose a skill to begin your learning journey
        </p>
      </div>

      {/* Profile Summary */}
      <BrutalCard className="max-w-4xl mx-auto">
        <h2 className="text-xl font-bold mb-4 text-center">Profile Dimensions</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(profileState.dimensions).map(([key, value]) => (
            <div key={key} className="text-center">
              <div className="text-2xl font-bold text-primary mb-1">
                {value.toFixed(2)}
              </div>
              <div className="text-xs text-muted-foreground">
                {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
            </div>
          ))}
        </div>
      </BrutalCard>

      {/* Skill Selection CTA */}
      <div className="text-center">
        <BrutalButton
          variant="primary"
          onClick={() => navigate('/skill/select')}
          className="px-8 py-3"
        >
          <BookOpen className="mr-2 h-5 w-5" />
          Select a Skill to Learn
        </BrutalButton>
      </div>
    </div>
  );

  const RoadmapGenerationDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Generating Your Roadmap</h1>
        <p className="text-lg text-muted-foreground mb-2">
          Creating a personalized learning path for {currentSkill.skillName}
        </p>
      </div>

      {/* Generation Status */}
      <BrutalCard className="max-w-2xl mx-auto">
        <div className="text-center">
          <div className="animate-pulse mb-4">
            <div className="w-16 h-16 bg-blue-200 rounded-full mx-auto flex items-center justify-center">
              <Map className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <h2 className="text-xl font-bold mb-2">Building Learning Roadmap</h2>
          <p className="text-muted-foreground mb-4">
            Creating phases, techniques, and checkpoints tailored to your profile
          </p>
          <div className="animate-pulse space-y-2">
            <div className="h-2 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-2 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-2 bg-gray-200 rounded w-2/3 mx-auto"></div>
          </div>
        </div>
      </BrutalCard>
    </div>
  );

  const RoadmapActiveDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Learning Roadmap Active</h1>
        <p className="text-lg text-muted-foreground mb-2">
          Current Phase: {roadmapState.currentPhase || 'Not Started'}
        </p>
        <p className="text-sm text-muted-foreground">
          Technique: {roadmapState.currentTechnique || 'None'}
        </p>
      </div>

      {/* Roadmap Progress */}
      <BrutalCard className="max-w-4xl mx-auto">
        <h2 className="text-xl font-bold mb-4">Roadmap Progress</h2>
        <div className="space-y-4">
          {/* Current Phase Info */}
          <div className="border-l-4 border-yellow-500 pl-4">
            <h3 className="font-bold text-lg">Current Focus</h3>
            <p className="text-muted-foreground">
              {roadmapState.currentPhase} - {roadmapState.currentTechnique}
            </p>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {roadmapState.phases.filter(p => p.status === 'complete').length}
              </div>
              <div className="text-sm text-muted-foreground">Phases Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {roadmapState.phases.reduce((acc, phase) => 
                  acc + phase.competencies.reduce((cAcc, comp) => 
                    cAcc + comp.techniques.reduce((tAcc, tech) => 
                      tAcc + tech.checkpoints.filter(cp => cp.status === 'passed').length
                    , 0)
                  , 0)
                , 0)}
              </div>
              <div className="text-sm text-muted-foreground">Checkpoints Passed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {sessionState.retryCount}/{sessionState.maxRetries}
              </div>
              <div className="text-sm text-muted-foreground">Retries Available</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4">
            <BrutalButton
              variant="primary"
              onClick={() => navigate(`/roadmap/${currentSkill.skillId}`)}
            >
              <Map className="mr-2 h-4 w-4" />
              View Full Roadmap
            </BrutalButton>
            <BrutalButton
              variant="secondary"
              onClick={() => navigate('/session')}
            >
              <Play className="mr-2 h-4 w-4" />
              Start Session
            </BrutalButton>
          </div>
        </div>
      </BrutalCard>
    </div>
  );

  const SessionActiveDashboard = () => (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Session in Progress</h1>
        <p className="text-lg text-muted-foreground mb-2">
          {roadmapState.currentTechnique}
        </p>
        <p className="text-sm text-muted-foreground">
          Step {sessionState.currentStep} of {sessionState.totalSteps}
        </p>
      </div>

      {/* Session Status */}
      <BrutalCard className="max-w-2xl mx-auto">
        <div className="text-center">
          <div className="mb-4">
            <Play className="h-16 w-16 text-green-500 mx-auto" />
          </div>
          <h2 className="text-xl font-bold mb-2">Active Session</h2>
          <p className="text-muted-foreground mb-4">
            You are currently in a learning session
          </p>
          <BrutalButton
            variant="primary"
            onClick={() => navigate('/session')}
          >
            Return to Session
          </BrutalButton>
        </div>
      </BrutalCard>
    </div>
  );

  return (
    <SidebarLayout>
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Dashboard Content */}
          {renderDashboardContent()}
        </div>
      </div>
    </SidebarLayout>
  );
}
