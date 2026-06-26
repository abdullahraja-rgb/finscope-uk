import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18212f",
        paper: "#f7f4ee",
        panel: "#ffffff",
        teal: "#0f766e",
        cobalt: "#2558a5",
        amber: "#b7791f",
        rose: "#be123c"
      },
      boxShadow: {
        soft: "0 12px 30px rgba(24, 33, 47, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
