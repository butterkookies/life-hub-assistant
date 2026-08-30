import React from 'react';
import { Search } from 'lucide-react';
import { NotionProject } from '../lib/types';
import { getProjectSticker } from '../lib/notion-theme';

interface FilterBarProps {
  filterMode: 'today' | 'active' | 'all';
  searchQuery: string;
  selectedProjectId: string | null;
  projects: NotionProject[];
  onFilterModeChange: (mode: 'today' | 'active' | 'all') => void;
  onSearchChange: (query: string) => void;
  onProjectSelect: (projectId: string | null) => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filterMode,
  searchQuery,
  selectedProjectId,
  projects,
  onFilterModeChange,
  onSearchChange,
  onProjectSelect,
}) => {
  return (
    <div className="px-3 pt-2.5 pb-1 flex flex-col gap-2">
      {/* 1. Filter Tabs + Search Row */}
      <div className="flex items-center justify-between gap-2">
        {/* Segmented Button (Pill style) */}
        <div className="flex items-center bg-[#eae9e6] p-0.5 rounded-md border border-hairline">
          <button
            onClick={() => onFilterModeChange('today')}
            className={`notion-btn-press px-2.5 py-1 text-[11px] font-semibold rounded-[5px] transition-all ${
              filterMode === 'today'
                ? 'bg-white text-ink shadow-sm'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Today
          </button>
          <button
            onClick={() => onFilterModeChange('active')}
            className={`notion-btn-press px-2.5 py-1 text-[11px] font-semibold rounded-[5px] transition-all ${
              filterMode === 'active'
                ? 'bg-white text-ink shadow-sm'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => onFilterModeChange('all')}
            className={`notion-btn-press px-2.5 py-1 text-[11px] font-semibold rounded-[5px] transition-all ${
              filterMode === 'all'
                ? 'bg-white text-ink shadow-sm'
                : 'text-ink-muted hover:text-ink'
            }`}
          >
            All
          </button>
        </div>

        {/* Compact Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-ink-faint" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Filter tasks..."
            className="w-full pl-6 pr-2 py-1 text-[11px] bg-white border border-hairline rounded-xs text-ink placeholder:text-ink-faint focus:outline-none focus:border-primary transition-colors"
          />
        </div>
      </div>

      {/* 2. Project Sticker Filter Chips (Horizontal Scrollable) */}
      {projects.length > 0 && (
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-0.5">
          <button
            onClick={() => onProjectSelect(null)}
            className={`notion-btn-press shrink-0 px-2 py-0.5 text-[10px] font-medium rounded-full transition-colors ${
              selectedProjectId === null
                ? 'bg-ink text-white'
                : 'bg-white border border-hairline text-ink-muted hover:text-ink'
            }`}
          >
            All Projects
          </button>
          {projects.map((proj) => {
            const sticker = getProjectSticker(proj.name);
            const isSelected = selectedProjectId === proj.id;
            return (
              <button
                key={proj.id}
                onClick={() => onProjectSelect(isSelected ? null : proj.id)}
                className={`notion-btn-press shrink-0 flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full border transition-all ${
                  isSelected
                    ? `${sticker.bg} ${sticker.text} ${sticker.border} ring-1 ring-primary`
                    : 'bg-white border-hairline text-ink-secondary hover:bg-surface-hover'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${sticker.dot}`} />
                {proj.name}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
