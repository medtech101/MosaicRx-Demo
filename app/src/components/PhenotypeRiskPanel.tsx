import { PhenotypeRisk, RiskTier } from '../types';
import { Activity, CheckCircle2, PersonStanding, TrendingUp } from 'lucide-react';

interface PhenotypeRiskPanelProps {
  phenotypeRisk: PhenotypeRisk;
}

const tierMeterFill: Record<RiskTier, string> = {
  low: 'bg-mosaic-500',
  moderate: 'bg-amber-500',
  high: 'bg-rose-500',
};

const tierPill: Record<RiskTier, string> = {
  low: 'bg-mosaic-50 text-mosaic-700 border-mosaic-200',
  moderate: 'bg-amber-50 text-amber-800 border-amber-200',
  high: 'bg-rose-50 text-rose-700 border-rose-200',
};

const likelihoodPill: Record<RiskTier, string> = {
  low: 'bg-slate-100 text-slate-600',
  moderate: 'bg-amber-100 text-amber-800',
  high: 'bg-rose-100 text-rose-800',
};

export default function PhenotypeRiskPanel({ phenotypeRisk }: PhenotypeRiskPanelProps) {
  const { fallRisk, predictedAdverseEvents } = phenotypeRisk;
  const fillPct = Math.round((fallRisk.score / fallRisk.scaleMax) * 100);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-mosaic-600 mb-3">
        <Activity className="h-3.5 w-3.5" /> MosaicRx phenotype risk
      </div>

      {/* Fall risk stratification */}
      <div className="rounded-xl border border-slate-200 p-3.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
            <PersonStanding className="h-4 w-4 text-slate-500" /> Fall risk stratification
          </span>
          <span className={`text-[11px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full border ${tierPill[fallRisk.tier]}`}>
            {fallRisk.bandLabel}
          </span>
        </div>

        <div className="flex items-center gap-3 mt-3">
          <div className="flex-1">
            <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
              <div className={`h-full rounded-full ${tierMeterFill[fallRisk.tier]}`} style={{ width: `${fillPct}%` }} />
            </div>
          </div>
          <span className="text-sm font-semibold text-slate-700 tabular-nums shrink-0">
            {fallRisk.score}
            <span className="text-slate-400 font-normal">/{fallRisk.scaleMax}</span>
          </span>
        </div>

        <ul className="mt-3 space-y-1">
          {fallRisk.factors.map((f, i) => (
            <li key={i} className="flex gap-2 text-[12.5px] text-slate-600 leading-relaxed">
              <span className="text-slate-400 font-bold mt-0.5">•</span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
        <p className="text-[11px] text-slate-400 italic mt-2">{fallRisk.instrumentNote}</p>
      </div>

      {/* Predicted adverse events */}
      <div className="mt-3">
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <TrendingUp className="h-3.5 w-3.5" /> Predicted phenotype-specific adverse events
        </h4>

        {predictedAdverseEvents.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 text-mosaic-500 shrink-0 mt-0.5" />
            <p className="text-[13px] text-slate-600 leading-relaxed">
              None of concern in this scope. No phenotype-specific adverse event rises above routine monitoring for this
              patient right now.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {predictedAdverseEvents.map((ae, i) => (
              <div key={i} className="rounded-xl border border-slate-200 p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[13.5px] font-semibold text-slate-800">{ae.condition}</p>
                  <span className={`shrink-0 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${likelihoodPill[ae.likelihood]}`}>
                    {ae.likelihood} likelihood
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-medium mt-0.5">{ae.timeframe}</p>
                <p className="text-[12.5px] text-slate-600 leading-relaxed mt-1.5">{ae.rationale}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
