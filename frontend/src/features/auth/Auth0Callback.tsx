import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { auth0Config } from "@/lib/auth0";
import { log } from "@/lib/logger";
import { AuthLayout } from "./AuthLayout";
import { useAuth } from "./AuthProvider";

/** Handles the Auth0 redirect, then exchanges the token for a tenant session. */
export function Auth0Callback() {
  const { isLoading, isAuthenticated, getAccessTokenSilently, error } = useAuth0();
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [message, setMessage] = useState("Completing sign-in…");
  const exchanged = useRef(false);

  useEffect(() => {
    if (isLoading || exchanged.current) return;
    if (error) {
      setMessage("Sign-in was cancelled or failed.");
      setTimeout(() => navigate("/login"), 1500);
      return;
    }
    if (!isAuthenticated) return;

    exchanged.current = true;
    (async () => {
      try {
        const token = await getAccessTokenSilently({
          authorizationParams: { audience: auth0Config.audience },
        });
        await authApi.csrf();
        const user = await authApi.auth0Login(token);
        setUser(user);
        log.info("auth0 signed in", { entity: user.id, action: "auth0_login" });
        navigate("/");
      } catch {
        setMessage("Your SSO identity has no staff account at this school.");
        setTimeout(() => navigate("/login"), 2200);
      }
    })();
  }, [isLoading, isAuthenticated, error, getAccessTokenSilently, navigate, setUser]);

  return (
    <AuthLayout>
      <h1 className="text-2xl font-bold text-slate-900">Signing you in</h1>
      <p className="mt-2 text-slate-500">{message}</p>
    </AuthLayout>
  );
}
