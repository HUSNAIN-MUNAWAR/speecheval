import type { Config } from "tailwindcss";
const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: { xl: "0.875rem", "2xl": "1rem" },
      colors: {
        canvas: "hsl(var(--canvas))",
        surface: "hsl(var(--surface))",
        panel: "hsl(var(--panel))",
        line: "hsl(var(--line))",
        ink: "hsl(var(--ink))",
        muted: "hsl(var(--muted))",
        accent: "hsl(var(--accent))",
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        danger: "hsl(var(--danger))",
      },
      boxShadow: { panel: "0 18px 48px rgba(0,0,0,.20)" },
    },
  },
  plugins: [],
};
export default config;
