/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#ffffff',
          soft: '#f6f5f4',
        },
        surface: {
          DEFAULT: '#ffffff',
          subtle: '#f9f9f8',
          hover: '#f1f0ee',
          active: '#e9e8e6',
        },
        hairline: '#e6e6e6',
        ink: {
          DEFAULT: '#000000',
          secondary: '#31302e',
          muted: '#615d59',
          faint: '#a39e98',
        },
        primary: {
          DEFAULT: '#0075de',
          active: '#005bab',
          subtle: '#eef6fe',
        },
        secondary: '#213183',
        sticker: {
          sky: '#62aef0',
          purple: '#d6b6f6',
          'purple-deep': '#391c57',
          pink: '#ff64c8',
          orange: '#dd5b00',
          'orange-deep': '#793400',
          teal: '#2a9d99',
          green: '#1aae39',
          brown: '#523410',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        xs: '4px',
        sm: '5px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        full: '9999px',
      },
      boxShadow: {
        'notion-soft': '0 0.175px 1.041px rgba(0,0,0,0.01), 0 0.8px 2.925px rgba(0,0,0,0.02), 0 2.025px 7.847px rgba(0,0,0,0.027), 0 4px 18px rgba(0,0,0,0.04)',
        'notion-elevated': '0 4px 12px rgba(0,0,0,0.03), 0 23px 52px rgba(0,0,0,0.05)',
      },
      letterSpacing: {
        'display-1': '-2.125px',
        'display-2': '-1.875px',
        'heading-1': '-1px',
        'heading-2': '-0.625px',
        'heading-3': '-0.25px',
        'title': '-0.125px',
        'eyebrow': '0.125px',
      }
    },
  },
  plugins: [],
}
