import { Auth0Provider } from "@auth0/auth0-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "./features/auth/AuthProvider";
import "./index.css";
import { AUTH0_REDIRECT_PATH, auth0Config, auth0Enabled } from "./lib/auth0";
import { router } from "./routes/router";

const queryClient = new QueryClient();

const tree = (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </QueryClientProvider>
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {auth0Enabled() ? (
      <Auth0Provider
        domain={auth0Config.domain}
        clientId={auth0Config.clientId}
        cacheLocation="localstorage"
        authorizationParams={{
          redirect_uri: `${window.location.origin}${AUTH0_REDIRECT_PATH}`,
          audience: auth0Config.audience,
        }}
      >
        {tree}
      </Auth0Provider>
    ) : (
      tree
    )}
  </React.StrictMode>,
);
