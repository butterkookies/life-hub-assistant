import React from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';

interface DailyProgressProps {
  total: number;
  completed: number;
}

export const DailyProgress: React.FC<DailyProgressProps> = ({ total, completed }) => {
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  const isAllDone = total > 0 && completed === total;

  return (
    <div className="mx-3 mt-2.5 p-2.5 bg-surface rounded-lg border border-hairline shadow-notion-soft">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-1.5">
          {isAllDone ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-sticker-green" />
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-primary" />
          )}
          <span className="text-[12px] font-semibold text-ink">
            {isAllDone ? 'All tasks completed!' : `${completed} of ${total} Completed`}
          </span>
        </div>
        <span className="text-[11px] font-bold px-1.5 py-0.5 rounded-full bg-primary-subtle text-primary">
          {percentage}%
        </span>
      </div>

      {/* Progress Track */}
      <div className="w-full h-1.5 bg-[#f0f0f0] rounded-full overflow-hidden">
        <div
          className="h-full bg-sticker-green rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
