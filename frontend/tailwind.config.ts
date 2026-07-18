import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Fee Ledger blue (blue → indigo gradient brand).
        brand: {
          DEFAULT: "#2563EB", // blue-600
          dark: "#1D4ED8", // blue-700
          darker: "#1E3A8A", // blue-900
          light: "#EEF4FF", // very light blue tint
          ring: "#93C5FD", // blue-300
        },
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #2563EB 0%, #4F46E5 55%, #6366F1 100%)",
        "brand-gradient-soft": "linear-gradient(135deg, #EEF4FF 0%, #E0E7FF 100%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
