import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/auth";
import { AssessmentView } from "./views/AssessmentView";
import { DashboardView } from "./views/DashboardView";
import { LoginView } from "./views/LoginView";
import { RegisterView } from "./views/RegisterView";
import { RoadmapView } from "./views/RoadmapView";
import { SessionView } from "./views/SessionView";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginView />} />
          <Route path="/register" element={<RegisterView />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardView />} />
            <Route path="/assessment" element={<AssessmentView />} />
            <Route path="/roadmap/:skillId" element={<RoadmapView />} />
            <Route path="/session/:sessionId" element={<SessionView />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}
