import { useState } from 'react';
import { MosaicSignal, PointOfCareMode } from '../types';
import GlassBoxPanel from './GlassBoxPanel';
import { ChevronDown, ChevronUp, MessageCircleQuestion, ShieldCheck, Sparkles } from 'lucide-react';

interface MosaicSignalCardProps {
  signal: MosaicSignal;
  mode: PointOfCareMode;
}

const confidenceStyle: Record<string, string> = {
  high: 'bg-mosaic-500 text-white',
  moderate: 'bg-amber-500 text-white',
  low: 'bg-slate-400 text-white',
};

const modeFraming: Record<PointOfCareMode, { eyebrow: string; tone: string }> = {
  previsit: { eyebrow: 'Surfaced during pre-visit chart prep', tone: 'Reviewed before today’s visit, ahead of the patient arriving.' },
  eprescribe: { eyebrow: 'Surfaced at the moment of prescribing', tone: 'Flagged before this new order is sent to the pharmacy.' },
  'chart-open': { eyebrow: 'Surfaced on chart open, patient present', tone: 'Visible now, while the patient is in the room.' },
};

export default function MosaicSignalCard({ signal, mode }: MosaicSignalCardProps) {
  const [glassBoxOpen, setGlassBoxOpen] = useState(false);
  const framing = modeFraming[mode];

  if (signal.status === 'no-cascade') {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
          <ShieldCheck className="h-3.5 w-3.5 text-mosaic-500" /> {framing.eyebrow}
        </div>
        <h3 className="text-base font-semibold text-slate-800">{signal.headline}</h3>
        <p className="text-sm text-slate-600 mt-1.5 leading-relaxed">{signal.clinicalQuestion}</p>

        <button
          onClick={() => setGlassBoxOpen(!glassBoxOpen)}
          className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-mosaic-700 hover:text-mosaic-800 cursor-pointer"
        >
          {glassBoxOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          Glass Box: what MosaicRx checked
        </button>
        {glassBoxOpen && (
          <div className="mt-3 pt-3 border-t border-slate-200">
            <GlassBoxPanel glassBox={signal.glassBox} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-mosaic-200 bg-gradient-to-br from-mosaic-50/70 to-white p-5 shadow-sm">
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-mosaic-600 mb-2">
        <Sparkles className="h-3.5 w-3.5" /> {framing.eyebrow}
      </div>
      <h3 className="text-lg font-semibold text-slate-900">{signal.headline}</h3>
      <p className="text-xs text-slate-500 mt-0.5">{framing.tone}</p>

      {/* Ranked causes */}
      <div className="mt-4 space-y-3">
        {signal.rankedCauses.map((cause, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-3.5">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">
                {i + 1}. {cause.drug}
              </p>
              <span className={`shrink-0 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${confidenceStyle[cause.confidence]}`}>
                {cause.confidence} confidence
              </span>
            </div>
            {cause.source === 'patient-reported-otc' && (
              <span className="inline-block mt-1.5 text-[10px] font-semibold text-violet-700 bg-violet-50 border border-violet-200 rounded px-1.5 py-0.5">
                Reconciled from patient-reported OTC use
              </span>
            )}
            <p className="text-[13px] text-slate-600 leading-relaxed mt-2">{cause.rationale}</p>
            <p className="text-[12px] text-slate-500 mt-2 border-t border-slate-100 pt-2">
              <span className="font-semibold text-slate-600">Temporal link: </span>
              {cause.temporalLink}
            </p>
          </div>
        ))}
      </div>

      {/* Burden score */}
      <div className="mt-4 bg-white rounded-xl border border-slate-200 p-3.5">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Anticholinergic burden score (illustrative)</p>
        <div className="flex items-center gap-4">
          <div>
            <p className="text-[10px] text-slate-400 font-medium">Conventional (static)</p>
            <p className="text-2xl font-semibold text-slate-400">{signal.burden.conventional}</p>
          </div>
          <div className="text-slate-300">→</div>
          <div>
            <p className="text-[10px] text-mosaic-600 font-medium">Comorbidity-adjusted</p>
            <p className="text-2xl font-semibold text-mosaic-600">{signal.burden.adjusted}</p>
          </div>
        </div>
        <p className="text-[12.5px] text-slate-600 leading-relaxed mt-2">{signal.burden.driverExplanation}</p>
      </div>

      {/* Glass box toggle */}
      <button
        onClick={() => setGlassBoxOpen(!glassBoxOpen)}
        className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-mosaic-700 hover:text-mosaic-800 cursor-pointer"
      >
        {glassBoxOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        Glass Box: show evidence, reasoning, and what was ruled out
      </button>
      {glassBoxOpen && (
        <div className="mt-3 bg-white rounded-xl border border-slate-200 p-4">
          <GlassBoxPanel glassBox={signal.glassBox} />
        </div>
      )}

      <div className="mt-4 bg-mosaic-900 text-white rounded-xl p-3.5 flex items-start gap-2.5">
        <MessageCircleQuestion className="h-4 w-4 text-mosaic-200 shrink-0 mt-0.5" />
        <p className="text-[13px] leading-relaxed">{signal.clinicalQuestion}</p>
      </div>
    </div>
  );
}
