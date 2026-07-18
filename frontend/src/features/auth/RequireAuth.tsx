import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export function RequireAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-400">Loading…</div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
