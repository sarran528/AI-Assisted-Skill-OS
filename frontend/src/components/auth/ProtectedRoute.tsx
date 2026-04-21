import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../store/authStore";

export function ProtectedRoute() {
  const token = useAuth((state) => state.token);

  if (!token) {
    return <Navigate to="/login" />;
  }

  return <Outlet />;
}
