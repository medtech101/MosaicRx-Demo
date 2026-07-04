import { GlassBox } from '../types';
import { BookOpen, Clock3, HelpCircle, ListChecks, Microscope, XCircle } from 'lucide-react';

interface GlassBoxPanelProps {
  glassBox: GlassBox;
}

const uncertaintyStyle: Record<GlassBox['uncertainty'], string> = {
  high: 'bg-rose-50 text-rose-700 border-rose-200',
  moderate: 'bg-amber-50 text-amber-800 border-amber-200',
  low: 'bg-mosaic-50 text-mosaic-700 border-mosaic-200',
};

export default function GlassBoxPanel({ glassBox }: GlassBoxPanelProps) {
  return (
    <div className="space-y-4 text-sm">
      <div>
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <Microscope className="h-3.5 w-3.5" /> Supporting evidence
        </h4>
        <ul className="space-y-1.5">
          {glassBox.evidence.map((e, i) => (
            <li key={i} className="flex gap-2 text-slate-700 leading-relaxed text-[13px]">
              <span className="text-mosaic-500 font-bold mt-0.5">•</span>
              <span>{e}</span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <Clock3 className="h-3.5 w-3.5" /> Temporal reasoning
        </h4>
        <p className="text-[13px] text-slate-700 leading-relaxed">{glassBox.temporalReasoning}</p>
      </div>

      <div>
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <BookOpen className="h-3.5 w-3.5" /> Literature basis
        </h4>
        <p className="text-[13px] text-slate-500 italic leading-relaxed">{glassBox.literature}</p>
      </div>

      <div>
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <HelpCircle className="h-3.5 w-3.5" /> Uncertainty level
        </h4>
        <div className={`inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide px-2 py-1 rounded-full border ${uncertaintyStyle[glassBox.uncertainty]}`}>
          {glassBox.uncertainty}
        </div>
        <p className="text-[13px] text-slate-600 leading-relaxed mt-1.5">{glassBox.uncertaintyNote}</p>
      </div>

      <div className="border-t border-slate-200 pt-3.5">
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <ListChecks className="h-3.5 w-3.5" /> Considered and ruled out
        </h4>
        <div className="space-y-2">
          {glassBox.ruledOut.map((r, i) => (
            <div key={i} className="bg-slate-50 border border-slate-200/70 rounded-lg p-2.5">
              <div className="flex items-center gap-1.5 text-[12.5px] font-semibold text-slate-700">
                <XCircle className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                {r.candidate}
              </div>
              <p className="text-[12.5px] text-slate-500 leading-relaxed mt-1 ml-5">{r.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
