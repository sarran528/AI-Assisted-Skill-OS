import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { useSession, useSubmitSessionMetrics } from "../hooks/useSession";
import { useSessionStore } from "../store/sessionStore";

export function SessionView() {
  const [searchParams] = useSearchParams();
  const storedSession = useSessionStore((state) => state.session);
  const sessionId = useMemo(() => searchParams.get("sessionId") || storedSession?.session_id || "", [searchParams, storedSession]);
  const { session, error } = useSession(sessionId || undefined);
  const { mutate: submitMetrics } = useSubmitSessionMetrics();

  useEffect(() => {
    if (session && session.status === "active") {
      const interval = setInterval(() => {
        if (sessionId) {
          submitMetrics({ session_id: sessionId, metrics: {} });
        }
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [session, sessionId, submitMetrics]);

  if (error) {
    return <div>Error loading session</div>;
  }

  if (!session) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Session</h1>
      <p>ID: {session.id}</p>
      <p>Status: {session.status}</p>
    </div>
  );
}
