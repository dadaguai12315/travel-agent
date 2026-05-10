/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        accent: '#111111',
        surface: '#f9fafb',
        'surface-hover': '#f3f4f6',
        border: '#e5e7eb',
      },
    },
  },
  plugins: [],
}
