// Notion Design System - Sticker Palette Token Maps
export interface StickerColor {
  bg: string;
  text: string;
  border: string;
  dot: string;
}

export const STICKER_PALETTE: StickerColor[] = [
  {
    bg: 'bg-[#eef6fe]',
    text: 'text-[#0075de]',
    border: 'border-[#b9ddfc]',
    dot: 'bg-[#62aef0]',
  },
  {
    bg: 'bg-[#f7f1fd]',
    text: 'text-[#701a75]',
    border: 'border-[#e7d2fb]',
    dot: 'bg-[#d6b6f6]',
  },
  {
    bg: 'bg-[#fbf1f8]',
    text: 'text-[#831843]',
    border: 'border-[#fcd0ec]',
    dot: 'bg-[#ff64c8]',
  },
  {
    bg: 'bg-[#fdf4ec]',
    text: 'text-[#7c2d12]',
    border: 'border-[#f8d4b8]',
    dot: 'bg-[#dd5b00]',
  },
  {
    bg: 'bg-[#eef8f8]',
    text: 'text-[#134e4a]',
    border: 'border-[#bfe6e4]',
    dot: 'bg-[#2a9d99]',
  },
  {
    bg: 'bg-[#edf8ee]',
    text: 'text-[#14532d]',
    border: 'border-[#bee8c3]',
    dot: 'bg-[#1aae39]',
  },
  {
    bg: 'bg-[#f8f4ed]',
    text: 'text-[#523410]',
    border: 'border-[#e6dac7]',
    dot: 'bg-[#523410]',
  },
];

export function getProjectSticker(projectName?: string): StickerColor {
  if (!projectName || projectName === 'Personal') {
    return {
      bg: 'bg-surface-hover',
      text: 'text-ink-secondary',
      border: 'border-hairline',
      dot: 'bg-ink-muted',
    };
  }
  let hash = 0;
  for (let i = 0; i < projectName.length; i++) {
    hash = projectName.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % STICKER_PALETTE.length;
  return STICKER_PALETTE[index];
}

export function formatTodayHeader(): string {
  const now = new Date();
  return now.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });
}
