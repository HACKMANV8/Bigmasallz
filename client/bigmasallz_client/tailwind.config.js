/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      screens: {
        '3xl': '1800px',
        '4xl': '2200px',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
      height: {
        '112': '28rem',
        '128': '32rem',
      },
      animation: {
        'drift-slow': 'drift 8s ease-in-out infinite',
        'drift-fast': 'drift 4s ease-in-out infinite',
      },
      keyframes: {
        drift: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(-10px) rotate(2deg)' },
        },
      },
      backgroundImage: {
        'grid-white': "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32' fill='none' stroke='white'%3e%3cpath d='m0 .5h31.5v31'/%3e%3c/svg%3e\")",
      },
    },
  },
  plugins: [],
}