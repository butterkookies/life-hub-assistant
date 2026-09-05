import React, { useState, useMemo, useRef } from 'react';
import {
  ArrowLeft,
  Sun,
  Moon,
  RotateCcw,
  Sliders,
  MessageSquare,
  Copy,
  Check,
  Send,
  Sparkles,
  Database,
  Bell,
  Camera,
  Image as ImageIcon,
  FileText,
  ChevronDown,
  Menu,
  SquarePen,
  ArrowUp,
  Plus,
  X,
  Layers,
  Type,
  Eye,
  Trash2,
  Palette,
  Pipette,
} from 'lucide-react';
import { MascotEntity, MascotState } from './MascotEntity';

interface DesignKitViewProps {
  onBackToChat: () => void;
  onSendFeedbackToChat: (feedbackText: string) => void;
  activeAppTheme: 'light' | 'dark';
  userPhoto?: string | null;
  onUpdatePhoto?: (photo: string | null) => void;
}

interface ComponentComment {
  id: string;
  componentId: string;
  componentName: string;
  text: string;
  timestamp: string;
}

export const DesignKitView: React.FC<DesignKitViewProps> = ({
  onBackToChat,
  onSendFeedbackToChat,
  activeAppTheme,
  userPhoto,
  onUpdatePhoto,
}) => {
  // --- 1. Isolated Sandbox State (does not mutate main app) ---
  const [sbTheme, setSbTheme] = useState<'light' | 'dark'>(activeAppTheme);
  const [sbRadius, setSbRadius] = useState<number>(18);
  const [sbBlur, setSbBlur] = useState<number>(16);
  const [sbPadding, setSbPadding] = useState<number>(16);
  const [sbFontScale, setSbFontScale] = useState<number>(100);
  const [sbAccent, setSbAccent] = useState<string>('#1a73e8');

  // Gradient Studio State (interactive moving ambient canvas)
  const [gradColor1, setGradColor1] = useState<string>('#1a73e8');
  const [gradColor2, setGradColor2] = useState<string>('#4f46e5');
  const [gradColor3, setGradColor3] = useState<string>('#00d2ff');
  const [gradSpeed, setGradSpeed] = useState<number>(14);
  const [gradBlur, setGradBlur] = useState<number>(45);
  const [gradientSynced, setGradientSynced] = useState<boolean>(false);

  // Hidden photo input ref for settings preview
  const photoInputRef = useRef<HTMLInputElement | null>(null);

  // Mascot Studio interactive controls
  const [mascotSize, setMascotSize] = useState<'sm' | 'md' | 'lg' | 'xl'>('lg');
  const [mascotState, setMascotState] = useState<MascotState>('idle');

  // Composer state preview
  const [composerMode, setComposerMode] = useState<'normal' | 'recording' | 'attachment'>('normal');

  // Navigation pill dropdown preview
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // --- 2. Tap-to-Comment Annotation System ---
  const [comments, setComments] = useState<ComponentComment[]>([]);
  const [activeCommentTarget, setActiveCommentTarget] = useState<{ id: string; name: string } | null>(null);
  const [commentInput, setCommentInput] = useState('');
  const [showExportModal, setShowExportModal] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  const GRADIENT_PRESETS = [
    { name: 'Cosmic Orbit (Default)', c1: '#1a73e8', c2: '#4f46e5', c3: '#00d2ff' },
    { name: 'Sunset Radiance', c1: '#f43f5e', c2: '#8b5cf6', c3: '#f59e0b' },
    { name: 'Aurora Borealis', c1: '#10b981', c2: '#14b8a6', c3: '#6366f1' },
    { name: 'Cyber Neon', c1: '#ec4899', c2: '#8b5cf6', c3: '#06b6d4' },
    { name: 'Monochrome Silver', c1: '#475569', c2: '#64748b', c3: '#94a3b8' },
  ];

  const handleResetTweaks = () => {
    setSbRadius(18);
    setSbBlur(16);
    setSbPadding(16);
    setSbFontScale(100);
    setSbAccent('#1a73e8');
    setGradColor1('#1a73e8');
    setGradColor2('#4f46e5');
    setGradColor3('#00d2ff');
    setGradSpeed(14);
    setGradBlur(45);
  };

  const handleSyncGradientToApp = () => {
    const isDark = sbTheme === 'dark';
    document.documentElement.style.setProperty('--gradient-glow-1', isDark ? `${gradColor1}40` : `${gradColor1}18`);
    document.documentElement.style.setProperty('--gradient-glow-2', isDark ? `${gradColor2}38` : `${gradColor2}14`);
    document.documentElement.style.setProperty('--gradient-glow-3', isDark ? `${gradColor3}30` : `${gradColor3}16`);
    document.documentElement.style.setProperty('--gradient-speed', `${gradSpeed}s`);
    document.documentElement.style.setProperty('--gradient-blur', `${gradBlur}px`);
    localStorage.setItem(
      'life_hub_custom_gradient',
      JSON.stringify({
        gradColor1,
        gradColor2,
        gradColor3,
        gradSpeed,
        gradBlur,
      })
    );
    setGradientSynced(true);
    setTimeout(() => setGradientSynced(false), 2200);
  };

  const handleAddComment = () => {
    if (!commentInput.trim() || !activeCommentTarget) return;
    const newComment: ComponentComment = {
      id: Math.random().toString(36).substring(2, 9),
      componentId: activeCommentTarget.id,
      componentName: activeCommentTarget.name,
      text: commentInput.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setComments((prev) => [...prev, newComment]);
    setCommentInput('');
    setActiveCommentTarget(null);
  };

  const handleDeleteComment = (id: string) => {
    setComments((prev) => prev.filter((c) => c.id !== id));
  };

  const getCommentsFor = (componentId: string) => {
    return comments.filter((c) => c.componentId === componentId);
  };

  // Generate Markdown report from comments and tweaks
  const generatedReport = useMemo(() => {
    const lines: string[] = [
      '# 🎨 Life Hub UI Design System Feedback & Review Report',
      '',
      '### ⚙️ Sandbox Tweaks Tested:',
      `- **Target Theme Tested**: ${sbTheme.toUpperCase()}`,
      `- **Corner Radius**: ${sbRadius}px (Baseline: 18px)`,
      `- **Backdrop Blur**: ${sbBlur}px (Baseline: 16px)`,
      `- **Container Padding**: ${sbPadding}px (Baseline: 16px)`,
      `- **Typography Scale**: ${sbFontScale}%`,
      `- **Accent Hue**: \`${sbAccent}\``,
      `- **Ambient Gradient Stops**: Stop 1: \`${gradColor1}\`, Stop 2: \`${gradColor2}\`, Stop 3: \`${gradColor3}\``,
      `- **Ambient Gradient Speed & Blur**: ${gradSpeed}s, ${gradBlur}px blur`,
      '',
      '### 💬 Annotated Component Comments & Change Requests:',
    ];

    if (comments.length === 0) {
      lines.push('*No specific component comments recorded yet.*');
    } else {
      const grouped: Record<string, ComponentComment[]> = {};
      comments.forEach((c) => {
        if (!grouped[c.componentName]) grouped[c.componentName] = [];
        grouped[c.componentName].push(c);
      });

      Object.entries(grouped).forEach(([name, list]) => {
        lines.push(`#### 📌 ${name}`);
        list.forEach((item) => {
          lines.push(`- ${item.text} _(${item.timestamp})_`);
        });
        lines.push('');
      });
    }

    lines.push('', '---', '> Please implement these design refinements to the Life Hub Assistant UI.');
    return lines.join('\n');
  }, [
    sbTheme,
    sbRadius,
    sbBlur,
    sbPadding,
    sbFontScale,
    sbAccent,
    gradColor1,
    gradColor2,
    gradColor3,
    gradSpeed,
    gradBlur,
    comments,
  ]);

  const handleCopyReport = () => {
    navigator.clipboard.writeText(generatedReport);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2000);
  };

  const handleSendReport = () => {
    onSendFeedbackToChat(generatedReport);
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col h-full w-full overflow-y-auto overflow-x-hidden transition-colors duration-200 ${
        sbTheme === 'dark' ? 'dark bg-[#090a0f] text-[#f3f4f6]' : 'bg-[#f8f9fb] text-[#111827]'
      }`}
      style={
        {
          '--sb-radius': `${sbRadius}px`,
          '--sb-blur': `${sbBlur}px`,
          '--sb-padding': `${sbPadding}px`,
          '--sb-accent': sbAccent,
          '--gradient-glow-1': sbTheme === 'dark' ? `${gradColor1}40` : `${gradColor1}18`,
          '--gradient-glow-2': sbTheme === 'dark' ? `${gradColor2}38` : `${gradColor2}14`,
          '--gradient-glow-3': sbTheme === 'dark' ? `${gradColor3}30` : `${gradColor3}16`,
          '--gradient-speed': `${gradSpeed}s`,
          '--gradient-blur': `${gradBlur}px`,
          fontSize: `${sbFontScale}%`,
          WebkitOverflowScrolling: 'touch',
        } as React.CSSProperties
      }
    >
      {/* Background ambient moving gradient canvas */}
      <div className="moving-gradient-canvas opacity-70" aria-hidden="true" />

      {/* Top Navigation Bar of Design Kit (Spacious, uncompressed, icon-only back button) */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))] pb-3 bg-surface-bg/85 backdrop-blur-xl border-b border-surface-borderSubtle shrink-0">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBackToChat}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-card border border-surface-border text-content-primary shadow-xs hover:bg-surface-secondary active:scale-95 transition-all"
            title="Back to Chat"
            aria-label="Back to Chat"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-base font-bold tracking-tight text-content-primary">
            Design Kit
          </h1>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 max-w-5xl w-full mx-auto px-4 py-6 pb-36 space-y-8 flex-1">
        {/* SECTION 0: LIVE PROPERTY TWEAKER TOOLBAR */}
        <section className="rounded-3xl border border-surface-border bg-surface-card/90 p-4 sm:p-6 shadow-sm backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between border-b border-surface-borderSubtle pb-3">
            <div className="flex items-center space-x-2">
              <Sliders className="h-4 w-4 text-brand-blue" />
              <h2 className="text-sm font-bold text-content-primary">Isolated Sandbox Tweakers</h2>
              <span className="text-[11px] text-content-muted">(Affects preview only)</span>
            </div>
            <div className="flex items-center space-x-3">
              {/* Sandbox Theme Toggle */}
              <button
                onClick={() => setSbTheme(sbTheme === 'light' ? 'dark' : 'light')}
                className="flex items-center space-x-1.5 rounded-xl border border-surface-border bg-surface-card px-2.5 py-1 text-xs font-semibold text-content-primary shadow-xs hover:bg-surface-secondary active:scale-95 transition-all"
                title={`Switch preview to ${sbTheme === 'light' ? 'Dark' : 'Light'} mode`}
              >
                {sbTheme === 'light' ? (
                  <>
                    <Moon className="h-3.5 w-3.5 text-indigo-500" />
                    <span>Dark Mode</span>
                  </>
                ) : (
                  <>
                    <Sun className="h-3.5 w-3.5 text-amber-400" />
                    <span>Light Mode</span>
                  </>
                )}
              </button>
              <button
                onClick={handleResetTweaks}
                className="flex items-center space-x-1 text-xs font-semibold text-content-muted hover:text-brand-blue transition-colors"
                title="Reset sliders to defaults"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Corner Radius Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium text-content-secondary">
                <span>Corner Radius</span>
                <span className="font-mono text-content-primary">{sbRadius}px</span>
              </div>
              <input
                type="range"
                min="4"
                max="32"
                value={sbRadius}
                onChange={(e) => setSbRadius(Number(e.target.value))}
                className="w-full accent-brand-blue cursor-pointer"
              />
            </div>

            {/* Backdrop Blur Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium text-content-secondary">
                <span>Glassmorphism Blur</span>
                <span className="font-mono text-content-primary">{sbBlur}px</span>
              </div>
              <input
                type="range"
                min="0"
                max="32"
                value={sbBlur}
                onChange={(e) => setSbBlur(Number(e.target.value))}
                className="w-full accent-brand-blue cursor-pointer"
              />
            </div>

            {/* Container Padding Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium text-content-secondary">
                <span>Element Padding</span>
                <span className="font-mono text-content-primary">{sbPadding}px</span>
              </div>
              <input
                type="range"
                min="8"
                max="28"
                value={sbPadding}
                onChange={(e) => setSbPadding(Number(e.target.value))}
                className="w-full accent-brand-blue cursor-pointer"
              />
            </div>

            {/* Font Scale Multiplier */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium text-content-secondary">
                <span>Typography Scale</span>
                <span className="font-mono text-content-primary">{sbFontScale}%</span>
              </div>
              <input
                type="range"
                min="85"
                max="120"
                value={sbFontScale}
                onChange={(e) => setSbFontScale(Number(e.target.value))}
                className="w-full accent-brand-blue cursor-pointer"
              />
            </div>
          </div>

          {/* Accent Color Palettes & Custom Hex Picker */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <span className="text-xs font-medium text-content-secondary">Accent Hue:</span>
            <div className="flex items-center space-x-2">
              {[
                { hex: '#1a73e8', name: 'Google Blue' },
                { hex: '#007aff', name: 'Apple Blue' },
                { hex: '#6366f1', name: 'Indigo' },
                { hex: '#8b5cf6', name: 'Purple' },
                { hex: '#00d2ff', name: 'Cyan' },
                { hex: '#10b981', name: 'Emerald' },
                { hex: '#ec4899', name: 'Rose Pink' },
                { hex: '#f59e0b', name: 'Amber' },
              ].map((c) => (
                <button
                  key={c.hex}
                  onClick={() => setSbAccent(c.hex)}
                  className={`h-6 w-6 rounded-full border-2 transition-transform ${
                    sbAccent.toLowerCase() === c.hex.toLowerCase()
                      ? 'scale-110 border-content-primary ring-2 ring-brand-blue/30'
                      : 'border-transparent hover:scale-105'
                  }`}
                  style={{ backgroundColor: c.hex }}
                  title={c.name}
                />
              ))}
            </div>

            {/* Custom Color Eyedropper & Hex Input */}
            <div className="flex items-center space-x-2 pl-2 border-l border-surface-borderSubtle">
              <label className="relative flex items-center justify-center cursor-pointer" title="Pick custom color">
                <input
                  type="color"
                  value={sbAccent.startsWith('#') && sbAccent.length === 7 ? sbAccent : '#1a73e8'}
                  onChange={(e) => setSbAccent(e.target.value)}
                  className="sr-only"
                />
                <div
                  className="h-6 w-6 rounded-full border border-surface-border shadow-2xs flex items-center justify-center overflow-hidden hover:scale-105 transition-transform"
                  style={{ backgroundColor: sbAccent }}
                >
                  <Pipette className="h-3 w-3 text-white drop-shadow" />
                </div>
              </label>
              <input
                type="text"
                value={sbAccent}
                onChange={(e) => setSbAccent(e.target.value)}
                className="w-20 px-2 py-0.5 text-xs font-mono rounded-lg border border-surface-border bg-surface-card text-content-primary focus:outline-none focus:ring-1 focus:ring-brand-blue uppercase"
                placeholder="#1A73E8"
                maxLength={7}
              />
            </div>
          </div>
        </section>

        {/* SECTION 1: DESIGN FOUNDATIONS (Colors, Blur, Typography) */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-content-primary flex items-center space-x-2">
                <Layers className="h-4 w-4 text-brand-blue" />
                <span>1. Design Foundations & Material Tokens</span>
              </h2>
              <p className="text-xs text-content-secondary">Apple Human Interface tokens & translucent surfaces</p>
            </div>
            <CommentTriggerButton
              targetId="foundation_tokens"
              targetName="Design Foundations & Material Tokens"
              count={getCommentsFor('foundation_tokens').length}
              onClick={() =>
                setActiveCommentTarget({
                  id: 'foundation_tokens',
                  name: 'Design Foundations & Material Tokens',
                })
              }
            />
          </div>

          {/* Colors Palette Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-2xl border border-surface-border bg-surface-bg p-3 shadow-2xs">
              <div className="h-8 rounded-xl bg-surface-bg border border-surface-border mb-2" />
              <div className="text-xs font-semibold text-content-primary">Surface Background</div>
              <div className="text-[10px] text-content-muted font-mono">{sbTheme === 'dark' ? '#090a0f' : '#f8f9fb'}</div>
            </div>
            <div className="rounded-2xl border border-surface-border bg-surface-card p-3 shadow-2xs">
              <div className="h-8 rounded-xl bg-surface-card border border-surface-border mb-2" />
              <div className="text-xs font-semibold text-content-primary">Surface Card</div>
              <div className="text-[10px] text-content-muted font-mono">{sbTheme === 'dark' ? '#13151b' : '#ffffff'}</div>
            </div>
            <div className="rounded-2xl border border-surface-border bg-surface-card p-3 shadow-2xs">
              <div className="h-8 rounded-xl mb-2" style={{ backgroundColor: sbAccent }} />
              <div className="text-xs font-semibold text-content-primary">Primary Accent</div>
              <div className="text-[10px] text-content-muted font-mono">{sbAccent}</div>
            </div>
            <div className="rounded-2xl border border-surface-border bg-surface-card p-3 shadow-2xs">
              <div
                className="h-8 rounded-xl mb-2 shadow-2xs"
                style={{
                  background: `linear-gradient(135deg, ${gradColor1}, ${gradColor2}, ${gradColor3})`,
                }}
              />
              <div className="text-xs font-semibold text-content-primary">Ambient Gradient</div>
              <div className="text-[10px] text-content-muted truncate">{gradColor1} → {gradColor3}</div>
            </div>
          </div>

          {/* Ambient Moving Gradient Studio */}
          <div className="rounded-3xl border border-surface-border bg-surface-card/85 p-5 shadow-sm space-y-4 backdrop-blur-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-surface-borderSubtle pb-3">
              <div>
                <div className="flex items-center space-x-2">
                  <Palette className="h-4 w-4 text-brand-blue" />
                  <h3 className="text-sm font-bold text-content-primary">Ambient Moving Gradient Studio</h3>
                </div>
                <p className="text-[11px] text-content-secondary mt-0.5">
                  Customize the 3-stop luminous radial gradient mesh, animation speed, and diffusion blur
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleSyncGradientToApp}
                  className="flex items-center space-x-1.5 rounded-xl bg-brand-blue px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-brand-blueHover active:scale-95 transition-all"
                  title="Apply and save this gradient to the live assistant"
                >
                  {gradientSynced ? (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      <span>Applied to App!</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>Sync to App</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Gradient Presets */}
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-content-secondary">Style Presets:</span>
              <div className="flex flex-wrap gap-2">
                {GRADIENT_PRESETS.map((p) => {
                  const isActive = gradColor1 === p.c1 && gradColor2 === p.c2 && gradColor3 === p.c3;
                  return (
                    <button
                      key={p.name}
                      onClick={() => {
                        setGradColor1(p.c1);
                        setGradColor2(p.c2);
                        setGradColor3(p.c3);
                      }}
                      className={`flex items-center space-x-2 rounded-xl border px-3 py-1.5 text-xs font-medium transition-all ${
                        isActive
                          ? 'border-brand-blue bg-surface-card shadow-xs font-semibold ring-1 ring-brand-blue/30'
                          : 'border-surface-border bg-surface-secondary/50 text-content-secondary hover:bg-surface-secondary'
                      }`}
                    >
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{
                          background: `linear-gradient(135deg, ${p.c1}, ${p.c2}, ${p.c3})`,
                        }}
                      />
                      <span>{p.name}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 3 Color Stop Pickers */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              {[
                { label: 'Stop 1 (Center Glow)', color: gradColor1, setter: setGradColor1 },
                { label: 'Stop 2 (Left Ambient)', color: gradColor2, setter: setGradColor2 },
                { label: 'Stop 3 (Right Accent)', color: gradColor3, setter: setGradColor3 },
              ].map((stop, i) => (
                <div key={i} className="rounded-2xl border border-surface-borderSubtle bg-surface-secondary/40 p-3 space-y-2">
                  <div className="flex items-center justify-between text-xs font-medium text-content-secondary">
                    <span>{stop.label}</span>
                    <span className="font-mono text-[11px] text-content-primary uppercase">{stop.color}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <label className="relative flex items-center justify-center cursor-pointer">
                      <input
                        type="color"
                        value={stop.color.startsWith('#') && stop.color.length === 7 ? stop.color : '#1a73e8'}
                        onChange={(e) => stop.setter(e.target.value)}
                        className="sr-only"
                      />
                      <div
                        className="h-8 w-8 rounded-xl border border-surface-border shadow-2xs flex items-center justify-center overflow-hidden hover:scale-105 transition-transform"
                        style={{ backgroundColor: stop.color }}
                      >
                        <Pipette className="h-3.5 w-3.5 text-white drop-shadow" />
                      </div>
                    </label>
                    <input
                      type="text"
                      value={stop.color}
                      onChange={(e) => stop.setter(e.target.value)}
                      className="flex-1 px-2.5 py-1.5 text-xs font-mono rounded-xl border border-surface-border bg-surface-card text-content-primary focus:outline-none focus:ring-1 focus:ring-brand-blue uppercase"
                      placeholder="#1A73E8"
                      maxLength={7}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Speed & Blur Sliders */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-content-secondary">
                  <span>Orb Motion Cycle</span>
                  <span className="font-mono text-content-primary">{gradSpeed}s</span>
                </div>
                <input
                  type="range"
                  min="6"
                  max="30"
                  step="1"
                  value={gradSpeed}
                  onChange={(e) => setGradSpeed(Number(e.target.value))}
                  className="w-full accent-brand-blue cursor-pointer"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-content-secondary">
                  <span>Orb Blur Diffusion</span>
                  <span className="font-mono text-content-primary">{gradBlur}px</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="80"
                  step="2"
                  value={gradBlur}
                  onChange={(e) => setGradBlur(Number(e.target.value))}
                  className="w-full accent-brand-blue cursor-pointer"
                />
              </div>
            </div>

            {/* Live Interactive Mini Preview Box */}
            <div className="relative h-20 rounded-2xl border border-surface-border overflow-hidden flex items-center justify-between px-4 bg-surface-card">
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: `radial-gradient(ellipse 65% 55% at 50% 100%, ${gradColor1}35 0%, transparent 70%),
                               radial-gradient(ellipse 50% 40% at 20% 90%, ${gradColor2}30 0%, transparent 65%),
                               radial-gradient(ellipse 45% 45% at 80% 85%, ${gradColor3}30 0%, transparent 65%)`,
                  filter: `blur(${Math.min(gradBlur, 30)}px)`,
                }}
              />
              <span className="relative z-10 text-xs font-medium text-content-secondary">
                Live Moving Glow Mesh Preview
              </span>
              <span
                className="relative z-10 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold"
                style={{
                  backgroundColor: `${sbAccent}20`,
                  color: sbAccent,
                  border: `1px solid ${sbAccent}40`,
                }}
              >
                {gradColor1} • {gradColor2} • {gradColor3}
              </span>
            </div>
          </div>

          {/* Material Translucency Swatches */}
          <div className="rounded-2xl border border-surface-border bg-surface-card/60 p-4 backdrop-blur-md shadow-2xs">
            <div className="text-xs font-semibold text-content-primary mb-2">Translucent Materials (Backdrop Blur)</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div
                className="p-3 rounded-xl border border-surface-border bg-surface-card/40"
                style={{ backdropFilter: `blur(${sbBlur * 0.5}px)` }}
              >
                <div className="text-xs font-medium text-content-primary">Subtle Frosted Layer</div>
                <div className="text-[11px] text-content-secondary">{Math.round(sbBlur * 0.5)}px blur</div>
              </div>
              <div
                className="p-3 rounded-xl border border-surface-border bg-surface-card/70"
                style={{ backdropFilter: `blur(${sbBlur}px)` }}
              >
                <div className="text-xs font-medium text-content-primary">Standard Chrome / Pill</div>
                <div className="text-[11px] text-content-secondary">{sbBlur}px blur</div>
              </div>
              <div
                className="p-3 rounded-xl border border-surface-border bg-surface-card/90"
                style={{ backdropFilter: `blur(${sbBlur * 1.5}px)` }}
              >
                <div className="text-xs font-medium text-content-primary">Heavy Modal / Sheet</div>
                <div className="text-[11px] text-content-secondary">{Math.round(sbBlur * 1.5)}px blur</div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 2: TOP BAR & NAVIGATION CHROME */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-content-primary flex items-center space-x-2">
                <Eye className="h-4 w-4 text-brand-blue" />
                <span>2. Top Bar Navigation Chrome</span>
              </h2>
              <p className="text-xs text-content-secondary">
                Edge-to-edge borderless floating header without horizontal divider lines
              </p>
            </div>
            <CommentTriggerButton
              targetId="top_bar_header"
              targetName="Top Bar Navigation Chrome"
              count={getCommentsFor('top_bar_header').length}
              onClick={() =>
                setActiveCommentTarget({
                  id: 'top_bar_header',
                  name: 'Top Bar Navigation Chrome',
                })
              }
            />
          </div>

          {/* Interactive Top Bar Mockup */}
          <div className="rounded-3xl border border-surface-border bg-surface-card/50 overflow-hidden shadow-xs">
            {/* Mock iPhone Status Bar */}
            <div className="flex items-center justify-between px-6 pt-2 pb-1 text-[11px] font-semibold text-content-secondary">
              <span>9:41</span>
              <div className="h-3.5 w-16 rounded-full bg-content-muted/20" />
              <span>5G 100%</span>
            </div>

            {/* The Actual Header */}
            <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-b from-surface-bg/70 via-surface-bg/30 to-transparent backdrop-blur-xs">
              <button className="flex h-9 w-9 items-center justify-center rounded-full text-content-primary hover:bg-surface-secondary active:scale-95 transition-all">
                <Menu className="h-5 w-5" />
              </button>

              <div className="relative">
                <button
                  onClick={() => setShowModelDropdown(!showModelDropdown)}
                  className="flex items-center space-x-2 rounded-full border border-surface-border bg-surface-card/90 px-3.5 py-1.5 text-xs font-semibold text-content-primary shadow-2xs hover:bg-surface-secondary active:scale-98 transition-all"
                >
                  <MascotEntity size="sm" />
                  <span>Life Hub Notion AI</span>
                  <ChevronDown className="h-3 w-3 text-content-muted" />
                </button>

                {showModelDropdown && (
                  <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-56 rounded-2xl border border-surface-border bg-surface-card p-1.5 shadow-xl z-30 animate-in fade-in zoom-in-95">
                    <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
                      Select Assistant
                    </div>
                    <div className="flex items-center space-x-2 rounded-xl bg-brand-blueLight text-brand-blue p-2 text-xs font-medium">
                      <MascotEntity size="sm" />
                      <span>Life Hub Notion AI (Active)</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <button className="flex h-9 w-9 items-center justify-center rounded-full text-content-primary hover:bg-surface-secondary active:scale-95 transition-all">
                  <SquarePen className="h-5 w-5" />
                </button>
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-brand-blue to-brand-indigo text-white text-xs font-bold shadow-xs">
                  AJ
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 3: CONVERSATIONAL STREAM & MESSAGE TYPOGRAPHY */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-content-primary flex items-center space-x-2">
                <Type className="h-4 w-4 text-brand-blue" />
                <span>3. Conversational Stream & Message Layout</span>
              </h2>
              <p className="text-xs text-content-secondary">
                Assistant full-width unbounded prose vs User speech pill
              </p>
            </div>
            <CommentTriggerButton
              targetId="chat_stream"
              targetName="Conversational Stream & Message Layout"
              count={getCommentsFor('chat_stream').length}
              onClick={() =>
                setActiveCommentTarget({
                  id: 'chat_stream',
                  name: 'Conversational Stream & Message Layout',
                })
              }
            />
          </div>

          <div
            className="rounded-3xl border border-surface-border bg-surface-card/40 p-4 sm:p-6 space-y-6 shadow-xs"
            style={{ borderRadius: `${sbRadius}px` }}
          >
            {/* User Message Bubble */}
            <div className="flex w-full justify-end">
              <div className="flex flex-col items-end max-w-[80%]">
                <div
                  className="border border-surface-border bg-surface-secondary/90 px-4 py-2.5 text-sm text-content-primary shadow-2xs leading-relaxed"
                  style={{ borderRadius: `${sbRadius}px`, borderBottomRightRadius: '4px' }}
                >
                  Create a new project named "Q4 Operations" and set up tasks database.
                </div>
                <span className="mt-1 text-[10px] text-content-muted px-2">09:42 AM</span>
              </div>
            </div>

            {/* Assistant Unbounded Prose Message (Zero Mascot Icon, Zero Left Indent) */}
            <div className="flex w-full flex-col py-1">
              <div className="prose-gemini break-words leading-relaxed text-sm space-y-2">
                <p>
                  I’ve created the <strong>Q4 Operations</strong> project page in your Notion workspace.
                  Here is the configured database structure:
                </p>
                <div className="rounded-xl border border-surface-border bg-surface-card p-3 my-2 text-xs space-y-1 font-mono">
                  <div className="text-brand-blue font-semibold">📁 Q4 Operations (Page ID: 1982b...)</div>
                  <div className="text-content-secondary">&nbsp;&nbsp;└── 📊 Tasks Database [Table View]</div>
                  <div className="text-content-muted">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;• Task Name (Title) | Status (Select) | Due Date (Date)</div>
                </div>
                <p className="text-xs text-content-secondary">
                  Would you like me to populate initial sprint milestones or link team members?
                </p>
              </div>

              {/* Action row at bottom */}
              <div className="mt-2.5 flex items-center space-x-3 text-content-muted text-[11px]">
                <button className="flex items-center space-x-1 hover:text-content-primary">
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy</span>
                </button>
                <span className="text-[10px] opacity-70">09:42 AM</span>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 4: FLOATING COMPOSER & MEDIA EXPANDER */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-content-primary flex items-center space-x-2">
                <MessageSquare className="h-4 w-4 text-brand-blue" />
                <span>4. Floating Pill Composer & States</span>
              </h2>
              <p className="text-xs text-content-secondary">
                Normal typing, live audio recording, and media picker bottom sheet
              </p>
            </div>
            <CommentTriggerButton
              targetId="floating_composer"
              targetName="Floating Pill Composer & States"
              count={getCommentsFor('floating_composer').length}
              onClick={() =>
                setActiveCommentTarget({
                  id: 'floating_composer',
                  name: 'Floating Pill Composer & States',
                })
              }
            />
          </div>

          {/* State Picker Tabs */}
          <div className="flex space-x-2">
            {[
              { id: 'normal', label: '1. Normal / Typing' },
              { id: 'recording', label: '2. Voice Recording Note' },
              { id: 'attachment', label: '3. [+] Media Sheet' },
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setComposerMode(st.id as any)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition-all ${
                  composerMode === st.id
                    ? 'bg-brand-blue text-white shadow-xs'
                    : 'bg-surface-card border border-surface-border text-content-secondary hover:bg-surface-secondary'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          <div
            className="rounded-3xl border border-surface-border bg-surface-card/30 p-6 shadow-xs relative overflow-hidden"
            style={{ borderRadius: `${sbRadius}px` }}
          >
            {composerMode === 'normal' && (
              <div
                className="flex items-center rounded-full border border-surface-border bg-surface-card/95 px-3 py-2 shadow-lg backdrop-blur-xl"
                style={{ borderRadius: `${sbRadius * 1.5}px` }}
              >
                <button className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-secondary text-content-primary hover:bg-surface-secondary/80 active:scale-95">
                  <Plus className="h-5 w-5" />
                </button>
                <input
                  readOnly
                  value="Schedule team retro next Monday at 2 PM..."
                  className="flex-1 bg-transparent px-3 text-sm text-content-primary outline-none"
                />
                <button
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white shadow-sm"
                  style={{ backgroundColor: sbAccent }}
                >
                  <ArrowUp className="h-4 w-4 stroke-[2.5]" />
                </button>
              </div>
            )}

            {composerMode === 'recording' && (
              <div
                className="flex items-center justify-between rounded-full border border-red-200 dark:border-red-900/40 bg-surface-card/95 px-4 py-3 shadow-lg backdrop-blur-xl"
                style={{ borderRadius: `${sbRadius * 1.5}px` }}
              >
                <div className="flex items-center space-x-3">
                  <span className="relative flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
                  </span>
                  <span className="text-xs font-semibold text-red-600 dark:text-red-400 font-mono">
                    Recording Voice Note (00:08)
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="flex h-8 w-8 items-center justify-center rounded-full text-content-muted hover:bg-surface-secondary">
                    <X className="h-4 w-4" />
                  </button>
                  <button className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-blue text-white shadow-xs">
                    <Check className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {composerMode === 'attachment' && (
              <div className="rounded-2xl border border-surface-border bg-surface-card p-4 shadow-md space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-content-muted">
                  [+] iOS Half Sheet Expander
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="flex flex-col items-center justify-center p-3 rounded-2xl bg-surface-secondary/70 border border-surface-borderSubtle hover:bg-surface-secondary cursor-pointer">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500 text-white mb-1.5 shadow-2xs">
                      <ImageIcon className="h-5 w-5" />
                    </div>
                    <span className="text-xs font-semibold text-content-primary">Photos</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-3 rounded-2xl bg-surface-secondary/70 border border-surface-borderSubtle hover:bg-surface-secondary cursor-pointer">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500 text-white mb-1.5 shadow-2xs">
                      <Camera className="h-5 w-5" />
                    </div>
                    <span className="text-xs font-semibold text-content-primary">Camera</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-3 rounded-2xl bg-surface-secondary/70 border border-surface-borderSubtle hover:bg-surface-secondary cursor-pointer">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500 text-white mb-1.5 shadow-2xs">
                      <FileText className="h-5 w-5" />
                    </div>
                    <span className="text-xs font-semibold text-content-primary">Files</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* SECTION 5: WOBBLY MASCOT ENTITY STUDIO */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-content-primary flex items-center space-x-2">
                <Sparkles className="h-4 w-4 text-brand-blue" />
                <span>5. Mascot Entity Interactive Studio</span>
              </h2>
              <p className="text-xs text-content-secondary">
                Luminous orb with glowing capsule pill eyes, listening soundwave sonar ripples, and expressive emotions
              </p>
            </div>
            <CommentTriggerButton
              targetId="mascot_entity"
              targetName="Mascot Entity Interactive Studio"
              count={getCommentsFor('mascot_entity').length}
              onClick={() =>
                setActiveCommentTarget({
                  id: 'mascot_entity',
                  name: 'Mascot Entity Interactive Studio',
                })
              }
            />
          </div>

          <div
            className="rounded-3xl border border-surface-border bg-surface-card/40 p-6 shadow-xs flex flex-col sm:flex-row items-center justify-around gap-6"
            style={{ borderRadius: `${sbRadius}px` }}
          >
            {/* Live Mascot Display */}
            <div className="flex flex-col items-center justify-center p-6">
              <MascotEntity size={mascotSize} state={mascotState} />
              <div className="mt-4 text-center">
                <div className="text-xs font-bold text-content-primary capitalize">
                  State: {mascotState}
                </div>
                <div className="text-[11px] text-content-muted uppercase">Size: {mascotSize}</div>
              </div>
            </div>

            {/* Mascot Interactive Control Knobs */}
            <div className="space-y-4 w-full sm:w-64">
              <div>
                <label className="text-xs font-semibold text-content-secondary block mb-1.5">
                  Size Preset
                </label>
                <div className="grid grid-cols-4 gap-1.5">
                  {(['sm', 'md', 'lg', 'xl'] as const).map((s) => (
                    <button
                      key={s}
                      onClick={() => setMascotSize(s)}
                      className={`py-1.5 text-xs font-bold uppercase rounded-lg border transition-all ${
                        mascotSize === s
                          ? 'bg-brand-blue text-white border-brand-blue shadow-xs'
                          : 'bg-surface-card border-surface-border text-content-secondary hover:bg-surface-secondary'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-content-secondary block mb-1.5">
                  Behavioral State
                </label>
                <div className="grid grid-cols-4 gap-1.5">
                  {(['idle', 'thinking', 'listening', 'happy'] as const).map((st) => (
                    <button
                      key={st}
                      onClick={() => setMascotState(st)}
                      className={`py-1.5 text-xs font-semibold capitalize rounded-lg border transition-all ${
                        mascotState === st
                          ? 'bg-brand-blue text-white border-brand-blue shadow-xs'
                          : 'bg-surface-card border-surface-border text-content-secondary hover:bg-surface-secondary'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 6: APPLE SETTINGS & GROUPED INSET LISTS */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-content-primary flex items-center space-x-2">
                <Sliders className="h-4 w-4 text-brand-blue" />
                <span>6. Apple Settings & Grouped Insets</span>
              </h2>
              <p className="text-xs text-content-secondary">
                Cupertino segmented control, clean Apple ID profile, and colored squircle icon rows
              </p>
            </div>
            <CommentTriggerButton
              targetId="apple_settings"
              targetName="Apple Settings & Grouped Insets"
              count={getCommentsFor('apple_settings').length}
              onClick={() =>
                setActiveCommentTarget({
                  id: 'apple_settings',
                  name: 'Apple Settings & Grouped Insets',
                })
              }
            />
          </div>

          <div className="max-w-md mx-auto space-y-4">
            {/* Apple ID Profile Row Preview */}
            {/* Apple ID Profile Row Preview with Custom Photo Upload */}
            <div
              className="rounded-2xl border border-surface-border bg-surface-card p-4 shadow-2xs"
              style={{ borderRadius: `${sbRadius}px` }}
            >
              <div className="flex items-center space-x-3.5">
                <div className="relative group shrink-0">
                  <input
                    type="file"
                    ref={photoInputRef}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file && onUpdatePhoto) {
                        const reader = new FileReader();
                        reader.onload = (ev) => {
                          const res = ev.target?.result as string;
                          if (res) onUpdatePhoto(res);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                    accept="image/*"
                    className="hidden"
                  />
                  <button
                    onClick={() => photoInputRef.current?.click()}
                    className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-tr from-brand-blue to-brand-indigo text-white font-semibold text-lg shadow-xs overflow-hidden hover:opacity-90 active:scale-95 transition-all select-none"
                    title="Tap to change profile picture"
                  >
                    {userPhoto ? (
                      <img src={userPhoto} alt="Profile" className="h-full w-full object-cover" />
                    ) : (
                      <span>AJ</span>
                    )}
                    <div className="absolute inset-0 bg-black/35 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Camera className="h-4 w-4 text-white" />
                    </div>
                  </button>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-[16px] font-semibold text-content-primary tracking-tight truncate">
                      Geronimo, Andrei John P.
                    </h3>
                    <button
                      onClick={() => photoInputRef.current?.click()}
                      className="text-[12px] font-semibold text-brand-blue hover:text-brand-blueHover"
                    >
                      {userPhoto ? 'Change' : 'Add Photo'}
                    </button>
                  </div>
                  <p className="text-[13px] text-content-secondary truncate">geronimojoan002@gmail.com</p>
                  <div className="mt-1 flex items-center justify-between">
                    <div className="flex items-center space-x-1.5 text-[12px] text-emerald-600 dark:text-emerald-400 font-medium">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span>Workspace Connected</span>
                    </div>
                    {userPhoto && onUpdatePhoto && (
                      <button
                        onClick={() => onUpdatePhoto(null)}
                        className="text-[11px] font-medium text-red-500 hover:text-red-600 transition-colors"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Cupertino Segmented Control Preview */}
            <div
              className="rounded-2xl border border-surface-border bg-surface-card p-1.5 shadow-2xs"
              style={{ borderRadius: `${sbRadius}px` }}
            >
              <div className="flex rounded-xl bg-surface-secondary/70 p-1">
                <button
                  onClick={() => setSbTheme('light')}
                  className={`flex flex-1 items-center justify-center space-x-2 rounded-lg py-2 text-[13px] font-medium transition-all ${
                    sbTheme === 'light'
                      ? 'bg-surface-card text-content-primary shadow-xs font-semibold'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  <Sun className="h-4 w-4 text-amber-500" />
                  <span>Light</span>
                </button>
                <button
                  onClick={() => setSbTheme('dark')}
                  className={`flex flex-1 items-center justify-center space-x-2 rounded-lg py-2 text-[13px] font-medium transition-all ${
                    sbTheme === 'dark'
                      ? 'bg-surface-card text-content-primary shadow-xs font-semibold'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  <Moon className="h-4 w-4 text-indigo-400" />
                  <span>Dark</span>
                </button>
              </div>
            </div>

            {/* Apple Grouped Inset List Preview */}
            <div
              className="divide-y divide-surface-borderSubtle rounded-2xl border border-surface-border bg-surface-card shadow-2xs overflow-hidden"
              style={{ borderRadius: `${sbRadius}px` }}
            >
              <div className="flex items-center justify-between p-3.5">
                <div className="flex items-center space-x-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500 text-white shadow-2xs">
                    <Database className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-content-primary">Notion Workspace</div>
                    <div className="text-[12px] text-content-secondary">Connected via official API</div>
                  </div>
                </div>
                <span className="text-[13px] font-medium text-emerald-600 dark:text-emerald-400">
                  Synced
                </span>
              </div>
              <div className="flex items-center justify-between p-3.5">
                <div className="flex items-center space-x-3">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500 text-white shadow-2xs">
                    <Bell className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-content-primary">Daily Briefing & Push</div>
                    <div className="text-[12px] text-content-secondary">06:00 AM (PHT)</div>
                  </div>
                </div>
                <span className="text-xs font-semibold text-brand-blue">Active</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* --- FLOATING REVIEW BAR AT BOTTOM --- */}
      <aside className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 w-[92%] max-w-lg">
        <div className="flex items-center justify-between rounded-full border border-surface-border bg-surface-card/95 px-4 py-2.5 shadow-2xl backdrop-blur-2xl">
          <div className="flex items-center space-x-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold text-content-primary">
              {comments.length} note{comments.length === 1 ? '' : 's'} recorded
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center space-x-1.5 rounded-full bg-brand-blue px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-brand-blueHover active:scale-95 transition-all"
            >
              <Copy className="h-3.5 w-3.5" />
              <span>Export Review</span>
            </button>
          </div>
        </div>
      </aside>

      {/* --- IN-CONTEXT TAP-TO-COMMENT MODAL --- */}
      {activeCommentTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in"
            onClick={() => setActiveCommentTarget(null)}
          />
          <div className="relative w-full max-w-md rounded-3xl border border-surface-border bg-surface-card p-5 shadow-2xl z-10 animate-in zoom-in-95 duration-150 space-y-4">
            <div className="flex items-center justify-between border-b border-surface-borderSubtle pb-3">
              <div>
                <h3 className="text-sm font-bold text-content-primary">Add Note / Change Request</h3>
                <p className="text-xs text-brand-blue font-medium">{activeCommentTarget.name}</p>
              </div>
              <button
                onClick={() => setActiveCommentTarget(null)}
                className="p-1 rounded-full text-content-muted hover:bg-surface-secondary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* List existing comments for this target */}
            {getCommentsFor(activeCommentTarget.id).length > 0 && (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-content-muted">
                  Existing Notes:
                </div>
                {getCommentsFor(activeCommentTarget.id).map((c) => (
                  <div
                    key={c.id}
                    className="flex items-start justify-between rounded-xl bg-surface-secondary/70 p-2.5 text-xs text-content-primary"
                  >
                    <span className="flex-1 mr-2">{c.text}</span>
                    <button
                      onClick={() => handleDeleteComment(c.id)}
                      className="text-red-500 hover:text-red-600 p-1"
                      title="Delete note"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Textarea for new note */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-content-secondary">
                What changes or tweaks do you want made to this component?
              </label>
              <textarea
                rows={3}
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
                placeholder="e.g. Reduce the vertical padding, make the font weight 600, darken the border in dark mode..."
                className="w-full rounded-xl border border-surface-border bg-surface-bg p-3 text-xs text-content-primary outline-none focus:border-brand-blue"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-1">
              <button
                onClick={() => setActiveCommentTarget(null)}
                className="rounded-xl px-3.5 py-2 text-xs font-semibold text-content-muted hover:bg-surface-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleAddComment}
                disabled={!commentInput.trim()}
                className="rounded-xl bg-brand-blue px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-brand-blueHover disabled:opacity-50"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- EXPORT / HAND-OFF MODAL --- */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in"
            onClick={() => setShowExportModal(false)}
          />
          <div className="relative w-full max-w-lg rounded-3xl border border-surface-border bg-surface-card p-5 shadow-2xl z-10 animate-in zoom-in-95 duration-150 space-y-4">
            <div className="flex items-center justify-between border-b border-surface-borderSubtle pb-3">
              <div>
                <h3 className="text-base font-bold text-content-primary">Review & Export Feedback</h3>
                <p className="text-xs text-content-secondary">
                  Ready to copy or hand directly to Andrei's AI assistant
                </p>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                className="p-1 rounded-full text-content-muted hover:bg-surface-secondary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Report Preview Box */}
            <div className="rounded-2xl border border-surface-border bg-surface-bg p-3.5 max-h-64 overflow-y-auto font-mono text-[11px] leading-relaxed text-content-secondary whitespace-pre-wrap">
              {generatedReport}
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-2 pt-2">
              <button
                onClick={handleCopyReport}
                className="flex-1 flex items-center justify-center space-x-2 rounded-2xl border border-surface-border bg-surface-secondary p-3 text-xs font-semibold text-content-primary hover:bg-surface-secondary/80 active:scale-95 transition-all"
              >
                {copiedReport ? (
                  <>
                    <Check className="h-4 w-4 text-emerald-500" />
                    <span className="text-emerald-500 font-bold">Copied to Clipboard!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    <span>Copy Markdown</span>
                  </>
                )}
              </button>

              <button
                onClick={handleSendReport}
                className="flex-1 flex items-center justify-center space-x-2 rounded-2xl bg-brand-blue p-3 text-xs font-semibold text-white shadow-sm hover:bg-brand-blueHover active:scale-95 transition-all"
              >
                <Send className="h-4 w-4" />
                <span>Send Directly to Assistant</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper component for tap-to-comment triggers on sections
const CommentTriggerButton: React.FC<{
  targetId: string;
  targetName: string;
  count: number;
  onClick: () => void;
}> = ({ count, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`flex items-center space-x-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all active:scale-95 ${
        count > 0
          ? 'bg-brand-blue text-white shadow-xs'
          : 'bg-surface-card border border-surface-border text-content-muted hover:text-brand-blue hover:border-brand-blue/40'
      }`}
      title="Add note or change request"
    >
      <MessageSquare className="h-3.5 w-3.5" />
      <span>{count > 0 ? `${count} Note${count === 1 ? '' : 's'}` : 'Note'}</span>
    </button>
  );
};
