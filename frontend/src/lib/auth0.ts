/**
 * Auth0 SSO config (optional). Activates only when all three VITE_AUTH0_* vars
 * are set — otherwise the app runs with password login only.
 */
export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN ?? "",
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID ?? "",
  audience: import.meta.env.VITE_AUTH0_AUDIENCE ?? "",
};

export function auth0Enabled(): boolean {
  return Boolean(auth0Config.domain && auth0Config.clientId && auth0Config.audience);
}

export const AUTH0_REDIRECT_PATH = "/auth/callback";
