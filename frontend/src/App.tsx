import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/auth";
import { AppShell } from "./components/layout/AppShell";
import { AssessmentView } from "./views/AssessmentView";
import { AssessmentRunView } from "./views/AssessmentRunView";
import { AuthView } from "./views/AuthView";
import { CheckpointView } from "./views/CheckpointView";
import { DashboardView } from "./views/DashboardView";
import { DoubtView } from "./views/DoubtView";
import { GroundingView } from "./views/GroundingView";
import { ProfileView } from "./views/ProfileView";
import { ResourcesView } from "./views/ResourcesView";
import { RoadmapView } from "./views/RoadmapView";
import { SessionView } from "./views/SessionView";
import { SkillSelectView } from "./views/SkillSelectView";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/profile" replace />} />
          <Route path="/login" element={<AuthView defaultMode="login" />} />
          <Route path="/register" element={<AuthView defaultMode="register" />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/profile" element={<DashboardView />} />
              <Route path="/assessment" element={<AssessmentView />} />
              <Route path="/assessment/run/:level" element={<AssessmentRunView />} />
              <Route path="/skill/select" element={<SkillSelectView />} />
              <Route path="/skill/grounding" element={<GroundingView />} />
              <Route path="/roadmap" element={<RoadmapView />} />
              <Route path="/session" element={<SessionView />} />
              <Route path="/checkpoint/:roadmapId" element={<CheckpointView />} />
              <Route path="/resources" element={<ResourcesView />} />
              <Route path="/help" element={<DoubtView />} />
              <Route path="/doubt" element={<Navigate to="/help" replace />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/profile" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}
