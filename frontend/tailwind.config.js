/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        display: ['"Sora"', '"Inter"', "ui-sans-serif", "sans-serif"],
      },
      colors: {
        night: "#050812",
        panel: "#0b1020",
        aqua: "#22d3ee",
        mint: "#34d399",
        iris: "#8b5cf6",
        rose2: "#f472b6",
      },
      boxShadow: {
        glow: "0 0 60px -12px rgba(34, 211, 238, 0.45)",
        card: "0 24px 60px -24px rgba(0, 0, 0, 0.7)",
      },
      keyframes: {
        drift: {
          "0%, 100%": { transform: "translate3d(0,0,0) scale(1)" },
          "33%": { transform: "translate3d(6%, -8%, 0) scale(1.12)" },
          "66%": { transform: "translate3d(-7%, 6%, 0) scale(0.94)" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        spinSlow: { to: { transform: "rotate(360deg)" } },
        bar: {
          "0%, 100%": { transform: "scaleY(0.3)" },
          "50%": { transform: "scaleY(1)" },
        },
        ring: {
          "0%": { transform: "scale(0.7)", opacity: "0.7" },
          "100%": { transform: "scale(1.9)", opacity: "0" },
        },
      },
      animation: {
        drift: "drift 22s ease-in-out infinite",
        "drift-slow": "drift 32s ease-in-out infinite reverse",
        shimmer: "shimmer 2.2s linear infinite",
        "spin-slow": "spinSlow 14s linear infinite",
        bar: "bar 1.1s ease-in-out infinite",
        ring: "ring 2.4s ease-out infinite",
      },
    },
  },
  plugins: [],
};
