import { Navigate, Outlet } from "react-router-dom";
import { isTenantHost } from "@/api/client";
import { useAuth } from "./AuthProvider";

export function RequireAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-400">Loading…</div>
    );
  }
  if (!user) {
    // On the apex host there's no school to sign into — show the marketing home.
    return <Navigate to={isTenantHost() ? "/login" : "/welcome"} replace />;
  }
  return <Outlet />;
}
