import { Patient } from '../types';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface PatientRailProps {
  patients: Patient[];
  selectedId: string;
  onSelect: (id: string) => void;
  resolvedIds: Set<string>;
}

function riskDot(risk: Patient['riskLevel']) {
  switch (risk) {
    case 'elevated':
      return 'bg-amber-500';
    case 'moderate':
      return 'bg-slate-400';
    default:
      return 'bg-mosaic-400';
  }
}

export default function PatientRail({ patients, selectedId, onSelect, resolvedIds }: PatientRailProps) {
  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-full shrink-0">
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-mosaic-500 text-white flex items-center justify-center text-xs font-bold shrink-0">
            Rx
          </div>
          <div>
            <p className="text-sm font-bold text-slate-900 leading-tight">MosaicRx</p>
            <p className="text-[10px] text-slate-400 font-medium leading-tight">Embedded clinical signal layer</p>
          </div>
        </div>
      </div>

      <div className="px-4 pt-3 pb-1">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Today's panel</span>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1.5">
        {patients.map((p) => {
          const active = p.id === selectedId;
          const resolved = resolvedIds.has(p.id);
          return (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              className={`w-full text-left rounded-xl border p-3 transition-all cursor-pointer ${
                active ? 'border-mosaic-400 bg-mosaic-50/60 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${riskDot(p.riskLevel)}`} />
                  <span className="text-sm font-semibold text-slate-800">{p.name}</span>
                </div>
                {resolved && <CheckCircle2 className="h-3.5 w-3.5 text-mosaic-500 shrink-0" />}
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5 ml-4">{p.age} yr {p.sex}</p>
              <p className="text-[11px] text-slate-600 mt-1.5 ml-4 leading-snug">{p.complaint.text}</p>
              {p.riskLevel === 'elevated' && (
                <div className="flex items-center gap-1 mt-2 ml-4 text-[10px] font-semibold text-amber-700">
                  <AlertTriangle className="h-3 w-3" /> Signal available
                </div>
              )}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
