import { CalendarClock, FileEdit, MonitorSmartphone, RotateCcw } from 'lucide-react';
import { PointOfCareMode } from '../types';

interface TopBarProps {
  mode: PointOfCareMode;
  onModeChange: (mode: PointOfCareMode) => void;
  view: 'clinical' | 'investor';
  onViewChange: (view: 'clinical' | 'investor') => void;
  onReset: () => void;
}

const MODES: { id: PointOfCareMode; label: string; icon: typeof CalendarClock; description: string }[] = [
  { id: 'previsit', label: 'Pre-visit chart prep', icon: CalendarClock, description: 'Reviewing panel before clinic starts' },
  { id: 'eprescribe', label: 'e-Prescribe intercept', icon: FileEdit, description: 'Writing a new prescription' },
  { id: 'chart-open', label: 'Chart open, patient present', icon: MonitorSmartphone, description: 'During the encounter' },
];

export default function TopBar({ mode, onModeChange, view, onViewChange, onReset }: TopBarProps) {
  return (
    <div className="shrink-0 z-30">
      <div className="bg-amber-50 border-b border-amber-200 text-amber-900 text-[11px] font-semibold tracking-wide text-center py-1.5 px-4">
        DEMO — synthetic data, simulated reasoning, not for clinical use.
      </div>

      <div className="bg-slate-900 text-white flex items-center justify-between px-5 py-2.5">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold tracking-tight">Office Ally</span>
          <span className="text-slate-500">|</span>
          <span className="text-xs text-slate-300 font-medium">Encounter View</span>
        </div>

        <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1 border border-white/10">
          {(['clinical', 'investor'] as const).map((v) => (
            <button
              key={v}
              onClick={() => onViewChange(v)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                view === v ? 'bg-mosaic-500 text-white' : 'text-slate-300 hover:text-white'
              }`}
            >
              {v === 'clinical' ? 'Clinical Workflow' : 'Investor Value View'}
            </button>
          ))}
        </div>

        <button
          onClick={onReset}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white border border-white/15 hover:border-white/30 rounded-lg px-3 py-1.5 cursor-pointer transition-all"
        >
          <RotateCcw className="h-3.5 w-3.5" /> Reset demo
        </button>
      </div>

      {view === 'clinical' && (
        <div className="bg-white border-b border-slate-200 px-5 py-2.5 flex items-center gap-3">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider shrink-0">Point-of-care moment</span>
          <div className="flex items-center gap-1.5 flex-wrap">
            {MODES.map((m) => {
              const Icon = m.icon;
              const active = mode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => onModeChange(m.id)}
                  title={m.description}
                  className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
                    active
                      ? 'bg-mosaic-50 border-mosaic-300 text-mosaic-800'
                      : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {m.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
