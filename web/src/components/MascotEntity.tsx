import React from 'react';

export type MascotState = 'idle' | 'thinking' | 'listening' | 'happy';

interface MascotEntityProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  state?: MascotState;
  className?: string;
}

export const MascotEntity: React.FC<MascotEntityProps> = ({
  size = 'md',
  state = 'idle',
  className = '',
}) => {
  const dimensions = {
    sm: 'w-7 h-7',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
  }[size];

  // Eye scaling and positioning based on size
  const eyeConfig = {
    sm: { width: 'w-1.5', height: 'h-3', spacing: 'space-x-1.5', glow: 'shadow-[0_0_4px_#ffffff]' },
    md: { width: 'w-2', height: 'h-4', spacing: 'space-x-2', glow: 'shadow-[0_0_6px_#ffffff]' },
    lg: { width: 'w-3', height: 'h-6', spacing: 'space-x-3', glow: 'shadow-[0_0_10px_#ffffff]' },
    xl: { width: 'w-4.5', height: 'h-9', spacing: 'space-x-4', glow: 'shadow-[0_0_14px_#ffffff]' },
  }[size];

  const isThinking = state === 'thinking';
  const isListening = state === 'listening';
  const isHappy = state === 'happy';

  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${dimensions} ${className}`}
      aria-label={`Life Hub Mascot (${state})`}
    >
      {/* 1. Concentric Soundwave Ripples (Pulsing Sonar Rings for Listening & Thinking) */}
      {(isListening || isThinking) && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none" aria-hidden="true">
          <span
            className="absolute rounded-full border border-brand-blue/35 dark:border-brand-cyan/40 animate-ping"
            style={{
              width: '180%',
              height: '180%',
              animationDuration: isListening ? '1.8s' : '2.4s',
            }}
          />
          <span
            className="absolute rounded-full border border-brand-cyan/20 animate-ping"
            style={{
              width: '240%',
              height: '240%',
              animationDuration: isListening ? '2.2s' : '3s',
              animationDelay: '0.4s',
            }}
          />
        </div>
      )}

      {/* 2. Ambient Aura Glow */}
      <div
        className={`absolute inset-0 rounded-full blur-xl transition-all duration-700 pointer-events-none ${
          isThinking
            ? 'bg-brand-indigo/60 scale-125 animate-pulse'
            : isListening
            ? 'bg-brand-cyan/50 scale-135'
            : 'bg-brand-blue/35 group-hover:scale-115'
        }`}
      />

      {/* 3. Luminous Spherical Orb (Gradient Circle from Reference Video) */}
      <div
        className={`relative w-full h-full rounded-full transition-transform duration-500 ease-out flex items-center justify-center ${
          isListening
            ? 'rotate-[7deg] scale-105'
            : isThinking
            ? 'scale-105'
            : 'animate-float-slow'
        }`}
        style={{
          background:
            'radial-gradient(circle at 35% 28%, #4f78fe 0%, #3054e8 32%, #1a32b8 68%, #0d195c 100%)',
          boxShadow:
            '0 0 20px rgba(26, 115, 232, 0.45), inset -4px -4px 10px rgba(0, 0, 0, 0.6), inset 3px 3px 8px rgba(255, 255, 255, 0.75)',
        }}
      >
        {/* Iridescent Rim Light Reflection (Top-Right / Edge Glint) */}
        <div
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            background:
              'radial-gradient(ellipse at 85% 25%, rgba(0, 210, 255, 0.65) 0%, transparent 45%), radial-gradient(ellipse at 15% 85%, rgba(139, 92, 246, 0.5) 0%, transparent 45%)',
          }}
        />

        {/* 4. Expressive Capsule Pill Eyes */}
        <div
          className={`relative z-10 flex items-center justify-center ${eyeConfig.spacing} pointer-events-none transition-all duration-300 ${
            isListening ? 'translate-x-0.5 -translate-y-0.5' : isThinking ? '-translate-y-1' : ''
          }`}
        >
          {isHappy ? (
            /* Happy / Smiling Curved Crescents */
            <>
              <div
                className={`${eyeConfig.width} h-2 rounded-t-full border-t-[2.5px] border-white ${eyeConfig.glow}`}
              />
              <div
                className={`${eyeConfig.width} h-2 rounded-t-full border-t-[2.5px] border-white ${eyeConfig.glow}`}
              />
            </>
          ) : (
            /* Vertical Glowing Pill Eyes (EVE / Cybernetic Companion) */
            <>
              {/* Left Eye */}
              <div
                className={`${eyeConfig.width} ${eyeConfig.height} rounded-full bg-white ${eyeConfig.glow} transition-all duration-200`}
                style={{
                  animation: isThinking ? 'pulse 1.4s ease-in-out infinite' : 'mascotBlink 4s ease-in-out infinite',
                  transformOrigin: 'center center',
                }}
              />

              {/* Right Eye */}
              <div
                className={`${eyeConfig.width} ${
                  isListening ? 'h-[90%]' : eyeConfig.height
                } rounded-full bg-white ${eyeConfig.glow} transition-all duration-200`}
                style={{
                  animation: isThinking ? 'pulse 1.4s ease-in-out infinite' : 'mascotBlink 4s ease-in-out infinite',
                  animationDelay: '0.05s',
                  transformOrigin: 'center center',
                }}
              />
            </>
          )}
        </div>
      </div>

      {/* Embedded Keyframes for Natural Blinking */}
      <style>{`
        @keyframes mascotBlink {
          0%, 92%, 100% {
            transform: scaleY(1);
          }
          95% {
            transform: scaleY(0.08);
          }
        }
      `}</style>
    </div>
  );
};
