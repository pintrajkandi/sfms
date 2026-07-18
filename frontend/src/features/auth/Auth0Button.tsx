import { useAuth0 } from "@auth0/auth0-react";
import { AUTH0_REDIRECT_PATH } from "@/lib/auth0";

/** "Sign in with SSO" — only rendered when Auth0 is configured. */
export function Auth0Button() {
  const { loginWithRedirect } = useAuth0();

  return (
    <button
      type="button"
      onClick={() =>
        loginWithRedirect({
          authorizationParams: {
            redirect_uri: `${window.location.origin}${AUTH0_REDIRECT_PATH}`,
          },
        })
      }
      className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
    >
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 2 4 5v6c0 5 3.5 8 8 11 4.5-3 8-6 8-11V5l-8-3Z" />
        <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Sign in with SSO
    </button>
  );
}
