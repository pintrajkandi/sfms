import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "@/api/auth";
import { ApiError } from "@/api/client";
import { useAuth } from "./AuthProvider";

export function ImpersonateScreen() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ticket = params.get("ticket");
    if (!ticket) {
      setError("Missing impersonation ticket.");
      return;
    }
    let active = true;
    (async () => {
      try {
        await authApi.csrf();
        const user = await authApi.impersonate(ticket);
        if (!active) return;
        setUser(user);
        navigate("/", { replace: true });
      } catch (e) {
        if (!active) return;
        setError(e instanceof ApiError ? e.detail : "Impersonation failed.");
      }
    })();
    return () => {
      active = false;
    };
  }, [params, navigate, setUser]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-100 bg-white p-8 text-center shadow-sm">
        {error ? (
          <>
            <p className="text-lg font-semibold text-rose-600">Couldn't start support session</p>
            <p className="mt-2 text-sm text-slate-500">{error}</p>
          </>
        ) : (
          <>
            <p className="text-lg font-semibold text-slate-800">Starting support session…</p>
            <p className="mt-2 text-sm text-slate-500">Signing you in as the school admin.</p>
          </>
        )}
      </div>
    </div>
  );
}
