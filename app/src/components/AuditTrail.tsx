import { AuditEntry } from '../types';
import { History } from 'lucide-react';

interface AuditTrailProps {
  entries: AuditEntry[];
}

const modeLabel: Record<AuditEntry['mode'], string> = {
  previsit: 'Pre-visit prep',
  eprescribe: 'e-Prescribe intercept',
  'chart-open': 'Chart open',
};

export default function AuditTrail({ entries }: AuditTrailProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-3">
        <History className="h-3.5 w-3.5" /> Audit trail
      </h4>
      {entries.length === 0 ? (
        <p className="text-xs text-slate-400">No clinician interactions recorded yet this session.</p>
      ) : (
        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {entries
            .slice()
            .reverse()
            .map((e) => (
              <div key={e.id} className="text-[12px] bg-slate-50 border border-slate-200/70 rounded-lg p-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-700">{e.patientName}</span>
                  <span className="text-slate-400 font-mono text-[10.5px]">{e.timestamp}</span>
                </div>
                <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-slate-500">
                  <span>Mode: {modeLabel[e.mode]}</span>
                  <span>Signal surfaced: {e.signalSurfaced ? 'Yes' : 'No'}</span>
                  <span>Clinician engaged: {e.clinicianEngaged ? 'Yes' : 'No'}</span>
                </div>
                <p className="text-slate-700 mt-1">{e.action}</p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
