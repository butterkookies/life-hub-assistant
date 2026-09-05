import React, { useState } from 'react';
import { AlertCircle, Check, Edit2, X, Activity } from 'lucide-react';
import { PendingScan } from '../types';

interface PendingScanCardProps {
  scan: PendingScan;
  onConfirm: (token: string) => void;
  onCorrect: (token: string, text: string) => void;
  onCancel: (token: string) => void;
  disabled?: boolean;
}

export const PendingScanCard: React.FC<PendingScanCardProps> = ({
  scan,
  onConfirm,
  onCorrect,
  onCancel,
  disabled = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [correctionText, setCorrectionText] = useState('');

  const metrics = [
    { label: 'Duration', val: scan.metrics.duration_minutes ? `${scan.metrics.duration_minutes} min` : null, key: 'duration_minutes' },
    { label: 'Distance', val: scan.metrics.distance_km ? `${scan.metrics.distance_km} km` : null, key: 'distance_km' },
    { label: 'Steps', val: scan.metrics.steps ? `${scan.metrics.steps}` : null, key: 'steps' },
    { label: 'Calories', val: scan.metrics.calories_kcal ? `${scan.metrics.calories_kcal} kcal` : null, key: 'calories_kcal' },
    { label: 'Speed', val: scan.metrics.speed_kmh ? `${scan.metrics.speed_kmh} km/h` : null, key: 'speed_kmh' },
    { label: 'Heart Rate', val: scan.metrics.heart_rate_bpm ? `${scan.metrics.heart_rate_bpm} bpm` : null, key: 'heart_rate_bpm' },
  ].filter((m) => m.val !== null);

  const handleCorrectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!correctionText.trim()) return;
    onCorrect(scan.token, correctionText.trim());
    setIsEditing(false);
    setCorrectionText('');
  };

  return (
    <div className="my-3 rounded-2xl border border-notion-border bg-notion-card p-4 shadow-notion-card transition-all">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-notion-borderSubtle pb-2.5 mb-3">
        <div className="flex items-center space-x-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-notion-text">Review Treadmill Scan</h3>
            <p className="text-[11px] text-notion-secondary">Date: {scan.date}</p>
          </div>
        </div>
        <div className="text-[11px] font-medium text-notion-secondary">
          Confidence: <span className="font-semibold text-notion-text">{Math.round(scan.confidence * 100)}%</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
        {metrics.map((m) => {
          const isUncertain = scan.uncertain_fields.includes(m.key);
          return (
            <div
              key={m.key}
              className={`rounded-xl p-2.5 border ${
                isUncertain
                  ? 'border-amber-200 bg-amber-50/50'
                  : 'border-notion-borderSubtle bg-notion-bg'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-medium text-notion-secondary">
                  {m.label}
                </span>
                {isUncertain && (
                  <span className="text-[10px] text-amber-700 font-semibold" title="Uncertain extraction">
                    ⚠️ Uncertain
                  </span>
                )}
              </div>
              <div className="text-sm font-semibold text-notion-text mt-0.5">{m.val}</div>
            </div>
          );
        })}
      </div>

      {/* Conflict Warning if existing record in Notion differs */}
      {scan.conflicts && Object.keys(scan.conflicts).length > 0 && (
        <div className="mb-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
          <div className="flex items-center space-x-1.5 font-semibold text-amber-950 mb-1">
            <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
            <span>Existing Notion Values Differ:</span>
          </div>
          <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
            {Object.entries(scan.conflicts).map(([field, [existing, incoming]]) => (
              <li key={field}>
                <strong>{field}:</strong> {String(existing)} → <span className="font-medium text-blue-700">{String(incoming)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-1.5 text-[10px] text-amber-800">Saving will update the record with the new values.</p>
        </div>
      )}

      {/* Plausibility Validation Errors */}
      {scan.validation_errors.length > 0 && (
        <div className="mb-3 rounded-xl border border-red-200 bg-red-50 p-2.5 text-xs text-red-800">
          <div className="font-semibold mb-0.5">⚠️ Plausibility Warning:</div>
          <ul className="list-disc pl-4 text-[11px]">
            {scan.validation_errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Inline Correction Form */}
      {isEditing && (
        <form onSubmit={handleCorrectSubmit} className="mb-3 space-y-2 rounded-xl bg-notion-bg p-3 border border-notion-border">
          <label className="block text-xs font-medium text-notion-text">
            Tell me what to correct (e.g. "Distance was 3.1 km, 220 calories"):
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={correctionText}
              onChange={(e) => setCorrectionText(e.target.value)}
              placeholder="e.g. Distance is 3.1 km"
              className="flex-1 rounded-lg border border-notion-border bg-white px-3 py-1.5 text-xs text-notion-text focus:border-notion-blue focus:outline-none"
              autoFocus
            />
            <button
              type="submit"
              disabled={disabled || !correctionText.trim()}
              className="rounded-lg bg-notion-blue px-3 py-1.5 text-xs font-medium text-white hover:bg-notion-blueHover disabled:opacity-50"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="rounded-lg border border-notion-border px-3 py-1.5 text-xs text-notion-secondary hover:bg-notion-paper"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-end space-x-2 pt-1">
        <button
          onClick={() => onCancel(scan.token)}
          disabled={disabled}
          className="flex items-center space-x-1 rounded-xl px-3 py-2 text-xs font-medium text-notion-secondary hover:bg-notion-paper hover:text-notion-text transition-colors"
        >
          <X className="h-3.5 w-3.5" />
          <span>Cancel</span>
        </button>

        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            disabled={disabled}
            className="flex items-center space-x-1 rounded-xl border border-notion-border bg-notion-card px-3 py-2 text-xs font-medium text-notion-text hover:bg-notion-paper transition-colors"
          >
            <Edit2 className="h-3.5 w-3.5 text-notion-secondary" />
            <span>Edit</span>
          </button>
        )}

        <button
          onClick={() => onConfirm(scan.token)}
          disabled={disabled || !scan.can_save}
          className="flex items-center space-x-1 rounded-xl bg-notion-blue px-4 py-2 text-xs font-medium text-white shadow-sm hover:bg-notion-blueHover transition-colors disabled:opacity-50"
        >
          <Check className="h-3.5 w-3.5" />
          <span>Save to Notion</span>
        </button>
      </div>
    </div>
  );
};
