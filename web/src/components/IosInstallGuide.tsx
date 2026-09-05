import React from 'react';
import { Share, PlusSquare, X, Smartphone } from 'lucide-react';

interface IosInstallGuideProps {
  isOpen: boolean;
  onClose: () => void;
}

export const IosInstallGuide: React.FC<IosInstallGuideProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
      <div className="w-full max-w-sm rounded-3xl border border-notion-border bg-notion-card p-6 shadow-notion-float animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-3 border-b border-notion-borderSubtle">
          <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-notion-blueLight text-notion-blue">
              <Smartphone className="h-4 w-4" />
            </div>
            <h3 className="text-sm font-semibold text-notion-text">Install on iPhone / iPad</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-notion-secondary hover:bg-notion-paper">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-3.5 text-xs text-notion-text">
          <p className="text-notion-secondary leading-relaxed">
            Install <strong>Andrei’s Life Hub</strong> on your iPhone to run it full-screen without Safari bars, with instant startup and Web Push notifications.
          </p>

          <div className="space-y-3 rounded-2xl bg-notion-bg p-3.5 border border-notion-borderSubtle">
            <div className="flex items-start space-x-3">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-notion-blue text-white text-[11px] font-bold">
                1
              </div>
              <div>
                <p className="font-semibold text-notion-text flex items-center">
                  Tap Share in Safari
                  <Share className="ml-1.5 h-3.5 w-3.5 text-notion-blue inline" />
                </p>
                <p className="text-[11px] text-notion-secondary mt-0.5">
                  Tap the box with arrow at the bottom of your screen.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-notion-blue text-white text-[11px] font-bold">
                2
              </div>
              <div>
                <p className="font-semibold text-notion-text flex items-center">
                  Select "Add to Home Screen"
                  <PlusSquare className="ml-1.5 h-3.5 w-3.5 text-notion-secondary inline" />
                </p>
                <p className="text-[11px] text-notion-secondary mt-0.5">
                  Scroll down the share sheet and tap Add to Home Screen.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-notion-blue text-white text-[11px] font-bold">
                3
              </div>
              <div>
                <p className="font-semibold text-notion-text">
                  Tap "Add" in Top-Right
                </p>
                <p className="text-[11px] text-notion-secondary mt-0.5">
                  Confirm the name "Life Hub" and tap Add.
                </p>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-notion-muted text-center pt-1">
            Now open Life Hub directly from your Home Screen!
          </p>
        </div>

        <div className="mt-5">
          <button
            onClick={onClose}
            className="w-full rounded-xl bg-notion-paper border border-notion-border py-2 text-xs font-semibold text-notion-text hover:bg-notion-borderSubtle transition-colors"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
