/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#142b45",
        muted: "#6d7f91",
        line: "#e5ebf1",
        canvas: "#f5f8fc",
        teal: "#168c88",
        blue: "#2768b2",
      },
      boxShadow: {
        panel: "0 12px 36px rgba(28, 54, 80, 0.06)",
      },
    },
  },
  plugins: [],
};
