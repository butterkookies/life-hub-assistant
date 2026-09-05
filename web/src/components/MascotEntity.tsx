import React from 'react';

interface MascotEntityProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  state?: 'idle' | 'thinking' | 'listening';
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
    xl: 'w-20 h-20',
  }[size];

  const eyeScale = {
    sm: 0.75,
    md: 1,
    lg: 1.4,
    xl: 1.7,
  }[size];

  const isThinking = state === 'thinking';
  const isListening = state === 'listening';

  return (
    <div className={`relative inline-flex items-center justify-center select-none ${dimensions} ${className}`}>
      {/* Ambient Pulsing Glow behind Mascot */}
      <div
        className={`absolute inset-0 rounded-full blur-lg transition-opacity duration-700 ${
          isThinking
            ? 'bg-brand-blue/50 scale-125 animate-pulse'
            : isListening
            ? 'bg-brand-cyan/40 scale-110'
            : 'bg-brand-blue/30 group-hover:opacity-80'
        }`}
      />

      {/* Organic Morphing Wobbly Body */}
      <div
        className={`relative w-full h-full flex items-center justify-center transition-all duration-300 ${
          isThinking ? 'animate-bounce' : 'animate-float-slow'
        }`}
      >
        <div
          className={`w-full h-full animate-wobble-morph shadow-lg ${
            isThinking ? 'shadow-glow-blue duration-700' : ''
          }`}
          style={{
            background: 'linear-gradient(135deg, #00d2ff 0%, #1a73e8 50%, #4f46e5 100%)',
          }}
        >
          {/* Subtle inner light reflection */}
          <div
            className="absolute inset-1 rounded-full opacity-40 pointer-events-none"
            style={{
              background: 'radial-gradient(circle at 35% 25%, rgba(255,255,255,0.85) 0%, transparent 60%)',
            }}
          />
        </div>

        {/* Expressive Mascot Eyes */}
        <div
          className="absolute inset-0 flex items-center justify-center space-x-1.5 pointer-events-none"
          style={{ transform: `scale(${eyeScale}) translateY(${isThinking ? '-2px' : '0px'})` }}
        >
          {/* Left Eye */}
          <div className="relative w-2.5 h-3.5 bg-white rounded-full flex items-center justify-center shadow-sm">
            <div
              className={`w-1.5 h-2 bg-slate-900 rounded-full transition-transform duration-300 ${
                isThinking ? '-translate-y-0.5' : ''
              }`}
            >
              {/* Eye Glint */}
              <div className="w-0.5 h-0.5 bg-white rounded-full mt-0.5 ml-0.5" />
            </div>
          </div>

          {/* Right Eye */}
          <div className="relative w-2.5 h-3.5 bg-white rounded-full flex items-center justify-center shadow-sm">
            <div
              className={`w-1.5 h-2 bg-slate-900 rounded-full transition-transform duration-300 ${
                isThinking ? '-translate-y-0.5' : ''
              }`}
            >
              {/* Eye Glint */}
              <div className="w-0.5 h-0.5 bg-white rounded-full mt-0.5 ml-0.5" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
