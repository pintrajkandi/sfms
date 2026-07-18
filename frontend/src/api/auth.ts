import { api } from "./client";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
}

export interface SchoolRef {
  school_name: string;
  school_code: string;
  slug: string;
  domain: string;
  login_url: string;
}

export interface TenantInfo {
  name: string | null;
  code: string | null;
  slug: string | null;
}

export interface SignupPayload {
  school_name: string;
  slug: string;
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  agree_terms: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
  school_code?: string;
  keep_signed_in?: boolean;
}

export const authApi = {
  // Public onboarding (apex host).
  signup: (payload: SignupPayload) => api.post<SchoolRef>("/onboarding/signup/", payload),
  resolveSchool: (school_code: string) =>
    api.post<SchoolRef>("/onboarding/resolve/", { school_code }),
  slugAvailable: (slug: string) =>
    api.get<{ slug: string; available: boolean }>(
      `/onboarding/slug-available/?slug=${encodeURIComponent(slug)}`,
    ),

  // Tenant auth (school subdomain).
  csrf: () => api.get<{ detail: string }>("/auth/csrf/"),
  tenant: () => api.get<TenantInfo>("/auth/tenant/"),
  login: (payload: LoginPayload) => api.post<User>("/auth/login/", payload),
  logout: () => api.post<void>("/auth/logout/", {}),
  me: () => api.get<User>("/auth/me/"),

  // Exchange an Auth0 access token for a tenant session.
  auth0Login: (accessToken: string) =>
    api.post<User>("/auth/auth0/", { access_token: accessToken }),

  verifyEmail: (token: string) =>
    api.post<{ detail: string }>("/auth/verify-email/", { token }),
  resendVerification: (email: string) =>
    api.post<{ detail: string }>("/auth/resend-verification/", { email }),

  requestPasswordReset: (email: string) =>
    api.post<{ detail: string }>("/auth/password-reset/", { email }),
  confirmPasswordReset: (uid: string, token: string, new_password: string) =>
    api.post<{ detail: string }>("/auth/password-reset/confirm/", {
      uid,
      token,
      new_password,
    }),
};
