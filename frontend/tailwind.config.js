/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#141816",
        cream: { 50: "#FBF8F2", 100: "#F3EEE4", 200: "#E6DCCB" },
        pine: { 950: "#071610", 900: "#0C2E24", 800: "#12392C", 700: "#1A5240", 600: "#226B52" },
        lime: "#D6F25C",
        mango: "#E39B2B",
        cocoa: "#6B3A28",
        berry: "#9E3B3A",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
      },
      boxShadow: {
        card: "0 20px 50px -30px rgba(12, 46, 36, 0.45)",
      },
    },
  },
  plugins: [],
};
