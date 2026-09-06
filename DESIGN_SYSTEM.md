# Life Hub Assistant — Apple iOS Design System

> **MANDATORY DIRECTIVE FOR ALL AI AGENTS & ENGINEERS:**
> Every feature, modal, sheet, message stream, and navigation bar in Life Hub Assistant MUST strictly adhere to this Design System.
> Deviations into generic, cluttered, or "AI slop" layouts (such as bulky boxed cards, overlapping badges on avatars, hard dividing borders across headers, or prepended mascot headers on every assistant response) are strictly prohibited.

---

## 1. Core Philosophy: Human Interface & Spatial Fluidity
Life Hub Assistant is designed as a seamless, tactile extension of the user. It combines **Apple's Human Interface Guidelines (WWDC 2018 / 2020 / 2026)** with the unbounded spaciousness of modern conversational intelligence.

- **Direct & Unencumbered:** The assistant's voice and thoughts flow without artificial decorative frames.
- **Edge-to-Edge Spatial Canvas:** The app occupies the full screen, extending behind the iOS status bar, notch, and Dynamic Island.
- **Zero Artificial Latency:** The UI responds immediately on pointer-down (`active:scale-[0.98]`).
- **Tactile Material Depth:** Frosted glass translucency (`backdrop-blur`) and grouped insets establish visual hierarchy instead of harsh 1px borders.

---

## 2. Spatial Architecture & Full-Screen Edge-to-Edge Rules

### A. The Top Chrome (Header)
- **NO Hard Dividers:** Never place a horizontal border (`border-b`, `<hr>`, or distinct opaque bar) between the top header and the conversational canvas.
- **Continuous Ambient Background:** The ambient moving glow canvas covers the entire screen from `top: 0` to `bottom: 0`. The header sits transparently above it with subtle blur (`backdrop-blur-xs` or `bg-surface-bg/60` gradient fade).
- **iOS Safe Areas:** Use `pt-[max(0.75rem,env(safe-area-inset-top))]` to ensure interactive controls clear the status bar / Dynamic Island while the background flows behind them.
- **Meta Configuration:** Keep `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />` and dynamic `theme-color` meta tags matching light/dark modes.

### B. Floating Pill Composer
- The composer floats gracefully above the bottom edge with `pb-[max(1rem,env(safe-area-inset-bottom))]`.
- Wrapped in a frosted glass capsule with high-performance blur (`backdrop-blur-xl bg-surface-elevated/95 border border-surface-border`).
- Tap targets (`[+]`, `Send`, `Mic`) are circular with direct touch compression (`active:scale-95`).

---

## 3. Conversational Stream & Message Typography

### A. Assistant Message Rules (Critical)
1. **NO Mascot / Avatar Prepending:** NEVER prepend the mascot icon, name ("Life Hub Assistant"), or status label to every individual response.
2. **Zero Indentation:** Assistant prose must start at `pl-0` (full width of the container). Do NOT indent responses behind a 32px icon column.
3. **Typography & Readability:** Prose must be rendered via `prose-gemini` with optical leading (1.7) and generous paragraph spacing (`margin-bottom: 0.85em`).
4. **Action Placement:** Secondary actions (Copy to clipboard, timestamp, retry) must live unobtrusively at the bottom of the response in `text-[11px] text-content-muted`.

### B. User Message Rules
- Right-aligned rounded speech pills (`rounded-3xl rounded-br-sm border border-surface-border bg-surface-secondary/90`).
- Maximum width bounded to 75–85% of screen width.
- Subtitle timestamp below the bubble.

---

## 4. Settings & Modals: Apple Grouped Inset Standard

All configuration sheets, settings modals, and contextual menus must adopt genuine Apple iOS Settings architecture:

### A. Sheet Presentation
- Mobile: Bottom sheet sliding up from bottom with iOS grab handle (`h-1 w-9 rounded-full bg-content-muted/30`).
- Desktop: Centered modal card with rounded corners (`sm:rounded-3xl sm:max-w-md`).
- Navigation bar: Title centered or left-aligned with a native iOS "Done" action button in `text-brand-blue font-semibold`.

### B. Apple ID Profile Pattern
- Inset card with large (56px) clean circular avatar with smooth gradient and initials.
- **FORBIDDEN:** Do NOT place badges, mini icons, or mascot heads overlapping the avatar circle. Keep the circle pure and balanced.
- User's primary name in `text-[16px] font-semibold tracking-tight`, email in `text-[13px] text-content-secondary`, and active session indicator in a clean row below.

### C. Cupertino Segmented Control (Appearance)
- Binary or ternary mode selectors (Light / Dark) must use an authentic iOS segmented control:
  - Outer pill container: `bg-surface-secondary/70 p-1 rounded-xl`
  - Active segment: `bg-surface-card text-content-primary shadow-xs font-semibold rounded-lg`
  - Tap down feedback: `active:scale-[0.98]`

### D. Grouped Inset Tables & Icon Squircle Squircles
- Inset grouped containers: `rounded-2xl border border-surface-border bg-surface-card divide-y divide-surface-borderSubtle overflow-hidden`.
- Section Headers: `text-[12px] font-semibold uppercase tracking-wider text-content-muted px-3 pb-1.5`.
- Row Icons: Apple Settings colored squircles (`h-7 w-7 rounded-lg text-white shadow-2xs`):
  - **Notion & Data:** `bg-blue-500` (iOS System Blue)
  - **AI & Intelligence:** `bg-purple-500` (iOS System Purple)
  - **Alerts & Notifications:** `bg-amber-500` (iOS System Orange)
  - **Account / Destructive:** `text-red-500` (iOS System Red)
- Disclosure: Standard `ChevronRight` in muted gray for navigable sub-pages.

---

## 5. Motion, Feedback & Physics

- **Response on Pointer-Down:** Always apply `:active` scale (`active:scale-[0.98]` or `active:scale-95`) with `duration-100` so touch feedback is perceived on press rather than release.
- **Springs over Linear Transitions:** Natural interfaces behave like physical springs (`damping: 1.0` critically damped default, `response: 0.3–0.4s`).
- **Interruptible Animations:** Gestures and transitions must be interruptible and redirectable at any moment.

---

## 6. Checklist Before Merging Any UI Work
- [ ] No hard borders dividing the header from the screen.
- [ ] No mascot icons or avatar labels prepended to assistant chat messages.
- [ ] Full width utilized for conversational responses without artificial left padding.
- [ ] Settings and modal views use Apple Grouped Inset tables and Cupertino segmented controls.
- [ ] User profile avatars have zero overlapping badges.
- [ ] Touch feedback is responsive on pointer-down.
- [ ] Dark and Light themes have calibrated contrast without washed-out grays.

---

## 7. Avatar & Procedural Character Roadmap
- **Designated Avatar Lab Engine**: `git@github.com:smontlouis/bible-strong-avatar-lab.git` (Demo: [avatars.bible-strong.app](https://avatars.bible-strong.app))
- **Architecture & Capabilities**: Procedural 2D "fake 3D" SVG rendering, independent eye and expression controls, ambient animations (blinking, breathing), and portable `.avatar.json` export.
- **Planned Integration**: To be used for procedural avatar customization and rich emotion transitions for the assistant mascot and Andrei's user profile avatar.
