import { Clock3, DollarSign, ShieldCheck, ThumbsUp } from 'lucide-react';

const KPIS = [
  {
    label: 'Cascade interception rate',
    value: '62%',
    note: 'of high-risk prescribing cascades flagged before harm, modeled',
    icon: ShieldCheck,
  },
  {
    label: 'Alert acceptance rate',
    value: '74%',
    note: 'of MosaicRx signals acted on by the clinician, modeled',
    icon: ThumbsUp,
  },
  {
    label: 'Time recovered per encounter',
    value: '3.4 min',
    note: 'estimated vs manual polypharmacy chart review, modeled',
    icon: Clock3,
  },
  {
    label: 'Modeled cost avoided',
    value: '$186K',
    note: 'per 1,000 patients annualized, illustrative estimate',
    icon: DollarSign,
  },
];

const OUTCOMES = [
  { label: 'Falls', before: 42, after: 27 },
  { label: 'ED visits', before: 58, after: 39 },
  { label: 'Hospital readmissions', before: 24, after: 15 },
];

const CHART_MAX = 60;
const GRID_STEPS = [0, 20, 40, 60];

export default function InvestorView() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-10">
      <div>
        <h2 className="text-lg font-bold text-slate-900">Modeled impact and business case</h2>
        <p className="text-sm text-slate-500 mt-0.5">
          All figures below are illustrative, modeled estimates for this demo and are labeled as such throughout.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {KPIS.map((k) => {
          const Icon = k.icon;
          return (
            <div key={k.label} className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="flex items-center gap-1.5 text-slate-400">
                <Icon className="h-3.5 w-3.5" />
                <span className="text-[11px] font-semibold uppercase tracking-wide">{k.label}</span>
              </div>
              <p className="text-2xl font-semibold text-slate-900 mt-2">{k.value}</p>
              <p className="text-[11px] text-slate-500 mt-1 leading-snug">{k.note}</p>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-sm font-bold text-slate-800">Patient outcome trajectory, before vs after MosaicRx</h3>
        </div>
        <p className="text-[11px] text-slate-400 mb-4">Rate per 1,000 patient-months, illustrative modeled estimate</p>

        {/* Legend */}
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-slate-300" />
            <span className="text-[11px] font-medium text-slate-600">Before MosaicRx</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-mosaic-500" />
            <span className="text-[11px] font-medium text-slate-600">After MosaicRx</span>
          </div>
        </div>

        <div className="flex">
          {/* y axis */}
          <div className="flex flex-col justify-between text-right pr-2 shrink-0 w-8" style={{ height: 176 }}>
            {GRID_STEPS.slice()
              .reverse()
              .map((step) => (
                <span key={step} className="text-[10px] text-slate-400 leading-none">
                  {step}
                </span>
              ))}
          </div>

          {/* plot area */}
          <div className="flex-1 relative border-l border-slate-200" style={{ height: 176 }}>
            {GRID_STEPS.map((step) => (
              <div
                key={step}
                className="absolute left-0 right-0 border-t border-slate-100"
                style={{ bottom: `${(step / CHART_MAX) * 100}%` }}
              />
            ))}
            <div className="absolute inset-0 flex items-stretch justify-around">
              {OUTCOMES.map((o) => (
                <div key={o.label} className="flex items-end gap-[2px]">
                  <Bar value={o.before} max={CHART_MAX} colorClass="bg-slate-300" />
                  <Bar value={o.after} max={CHART_MAX} colorClass="bg-mosaic-500" />
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex pl-8">
          <div className="flex-1 flex justify-around mt-2">
            {OUTCOMES.map((o) => (
              <span key={o.label} className="text-[11px] font-medium text-slate-600 text-center leading-tight w-20">
                {o.label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-mosaic-900 text-white rounded-2xl p-5">
        <p className="text-sm leading-relaxed">
          MosaicRx surfaces the culprit medication behind a new symptom before it cascades into a fall, an ED visit, or a
          readmission. The clinical workflow view shows the reasoning; this view shows why that reasoning is worth paying
          for at the population level.
        </p>
      </div>
    </div>
  );
}

function Bar({ value, max, colorClass }: { value: number; max: number; colorClass: string }) {
  const heightPct = (value / max) * 100;
  return (
    <div className="flex flex-col items-center justify-end h-full w-6">
      <span className="text-[10.5px] font-semibold text-slate-500 mb-1">{value}</span>
      <div className={`w-full rounded-t-[4px] ${colorClass}`} style={{ height: `${heightPct}%` }} />
    </div>
  );
}
