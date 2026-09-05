/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        notion: {
          bg: '#fbfbfa',
          paper: '#f7f6f3',
          card: '#ffffff',
          text: '#191919',
          secondary: '#787774',
          muted: '#9b9a97',
          border: '#e9e9e8',
          borderSubtle: '#f1f1ef',
          blue: '#0075de',
          blueHover: '#005bb5',
          blueLight: '#eef5fd',
          red: '#eb5757',
          green: '#0f7b6c',
          amber: '#d9730d',
          amberLight: '#fdf5e8',
        }
      },
      boxShadow: {
        'notion-card': '0 1px 3px rgba(15, 15, 15, 0.05), 0 0 0 1px rgba(15, 15, 15, 0.08)',
        'notion-float': '0 4px 14px rgba(15, 15, 15, 0.08), 0 0 0 1px rgba(15, 15, 15, 0.08)',
      }
    },
  },
  plugins: [],
}
