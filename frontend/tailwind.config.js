/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          50: '#e6f7ff',
          500: '#0891b2',
          700: '#0e7490',
        }
      }
    },
  },
  plugins: [],
}