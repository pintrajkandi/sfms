import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["pwa-icon.svg", "apple-touch-icon.png"],
      devOptions: { enabled: true }, // let the app install/run standalone in dev too
      manifest: {
        name: "Fee Ledger — Smart School Finance",
        short_name: "Fee Ledger",
        description: "Manage school fees, invoices, payouts, expenses and more.",
        theme_color: "#2563EB",
        background_color: "#ffffff",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        scope: "/",
        icons: [
          { src: "/pwa-icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
          { src: "/pwa-icon.svg", sizes: "512x512", type: "image/svg+xml", purpose: "maskable" },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
        // Never cache API calls — always hit the tenant backend fresh.
        navigateFallbackDenylist: [/^\/api/],
      },
    }),
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: { port: 5173, host: true },
});
