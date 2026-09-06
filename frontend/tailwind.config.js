/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0f1c2e",
        accent: "#0f6e56",
        paper: "#f3efe6",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["IBM Plex Sans", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
