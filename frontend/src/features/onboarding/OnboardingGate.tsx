import { useQuery } from "@tanstack/react-query";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { settings } from "@/api/resources";

/**
 * Hard gate: until the school profile (settings) has a name, every route
 * redirects to /settings. Once saved, the rest of the app unlocks.
 */
export function OnboardingGate() {
  const loc = useLocation();
  const { data, isLoading } = useQuery({
    queryKey: ["onboarding"],
    queryFn: () => settings.get(),
  });

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-400">Loading…</div>
    );
  }

  const complete = Boolean(data?.results?.[0]?.name);
  if (!complete && loc.pathname !== "/settings") {
    return <Navigate to="/settings" replace />;
  }
  return <Outlet />;
}
