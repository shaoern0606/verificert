import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13211e",
        trust: "#13795b",
        warning: "#b7791f",
        danger: "#b42318",
        panel: "#f7f8f6",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(19,33,30,0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
