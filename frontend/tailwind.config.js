/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        obsidian: {
          950: '#07090E',
          900: '#0D1117',
          850: '#131923',
          800: '#1A2230',
          700: '#263145',
        },
      },
    },
  },
  plugins: [],
};
