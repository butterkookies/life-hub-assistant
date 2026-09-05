/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Semantic theme tokens for Light & Dark mode
        surface: {
          bg: 'var(--color-bg)',
          card: 'var(--color-card)',
          elevated: 'var(--color-elevated)',
          secondary: 'var(--color-secondary)',
          border: 'var(--color-border)',
          borderSubtle: 'var(--color-border-subtle)',
        },
        content: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
        },
        brand: {
          blue: '#1a73e8',
          blueHover: '#1557b0',
          blueLight: '#e8f0fe',
          blueDark: '#174ea6',
          cyan: '#00d2ff',
          indigo: '#4f46e5',
        },
        // Legacy notion colors mapped for compatibility
        notion: {
          bg: 'var(--color-bg)',
          paper: 'var(--color-secondary)',
          card: 'var(--color-card)',
          text: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          border: 'var(--color-border)',
          borderSubtle: 'var(--color-border-subtle)',
          blue: '#1a73e8',
          blueHover: '#1557b0',
          blueLight: 'var(--color-blue-light)',
          red: '#eb5757',
          green: '#0f7b6c',
          amber: '#d9730d',
          amberLight: 'var(--color-amber-light)',
        }
      },
      boxShadow: {
        'notion-card': '0 1px 3px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(0, 0, 0, 0.06)',
        'notion-float': '0 8px 30px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.06)',
        'composer-light': '0 8px 32px rgba(26, 115, 232, 0.12), 0 2px 10px rgba(0, 0, 0, 0.06)',
        'composer-dark': '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)',
        'glow-blue': '0 0 35px rgba(26, 115, 232, 0.35)',
      },
      animation: {
        'gradient-flow': 'gradientFlow 12s ease infinite',
        'wobble-morph': 'wobbleMorph 6s ease-in-out infinite',
        'float-slow': 'floatSlow 4s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
      },
      keyframes: {
        gradientFlow: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        wobbleMorph: {
          '0%, 100%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%', transform: 'scale(1)' },
          '33%': { borderRadius: '40% 60% 70% 30% / 50% 60% 30% 60%', transform: 'scale(1.03) rotate(2deg)' },
          '66%': { borderRadius: '70% 30% 50% 50% / 30% 50% 60% 70%', transform: 'scale(0.97) rotate(-2deg)' },
        },
        floatSlow: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.08)' },
        },
      }
    },
  },
  plugins: [],
}
