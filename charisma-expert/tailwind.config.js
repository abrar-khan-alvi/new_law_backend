/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        navy: {
          50: '#f0f4fb',
          100: '#d9e2f5',
          200: '#b3c5eb',
          300: '#7d9dd6',
          400: '#4d76be',
          500: '#2d57a8',
          600: '#1e3f8a',
          700: '#1a3470',
          800: '#1a2744',
          900: '#0f1a35',
        },
      },
    },
  },
  plugins: [],
}
