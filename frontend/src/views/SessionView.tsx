import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useSession, useSubmitSessionMetrics } from "../hooks/useSession";

export function SessionView() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { session, error } = useSession(sessionId);
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
