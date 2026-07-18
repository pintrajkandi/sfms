import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "@/api/auth";
import { ApiError } from "@/api/client";
import { AuthLayout } from "./AuthLayout";

type State = "verifying" | "ok" | "error";

export function VerifyEmailScreen() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [state, setState] = useState<State>("verifying");
  const [message, setMessage] = useState("Verifying your email…");
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;
    if (!token) {
      setState("error");
      setMessage("This verification link is missing its token.");
      return;
    }
    authApi
      .verifyEmail(token)
      .then((r) => {
        setState("ok");
        setMessage(r.detail);
        setTimeout(() => navigate("/login"), 2000);
      })
      .catch((err) => {
        setState("error");
        setMessage(err instanceof ApiError ? err.detail : "Could not verify your email.");
      });
  }, [token, navigate]);

  return (
    <AuthLayout>
      <h1 className="text-3xl font-bold text-slate-900">
        {state === "ok" ? "Email verified ✅" : "Verify your email"}
      </h1>
      <p className="mt-3 text-slate-600">{message}</p>
      {state === "ok" && <p className="mt-2 text-sm text-slate-500">Redirecting you to sign in…</p>}
      {state === "error" && (
        <a
          href="/login"
          className="mt-8 block w-full rounded-xl bg-brand-gradient py-3.5 text-center text-base font-semibold text-white hover:opacity-95"
        >
          Back to sign in
        </a>
      )}
    </AuthLayout>
  );
}
