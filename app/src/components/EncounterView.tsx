import { useEffect, useState } from 'react';
import { Patient, PointOfCareMode, SuggestedAction } from '../types';
import { formatDate } from '../data/patients';
import MosaicSignalCard from './MosaicSignalCard';
import PhenotypeRiskPanel from './PhenotypeRiskPanel';
import ActionPanel from './ActionPanel';
import { AlertTriangle, FileEdit, FolderOpen, Pill, Send, Stethoscope } from 'lucide-react';

interface ResolvedAction {
  action: SuggestedAction;
  noteText: string;
  dismissReason?: string;
}

interface EncounterViewProps {
  patient: Patient;
  mode: PointOfCareMode;
  chartOpened: boolean;
  onOpenChart: () => void;
  resolvedAction: ResolvedAction | null;
  onResolveAction: (action: SuggestedAction, dismissReason?: string) => void;
  onSignalSurfaced: () => void;
}

const DRAFT_RX: Record<string, string> = {
  'maria-r': 'Meclizine 25 mg tablet — for dizziness',
  'robert-t': 'Vitamin B12 1000 mcg injection — for fatigue',
  'eleanor-k': 'Lorazepam 0.5 mg PRN — for agitation',
};

const labFlagStyle: Record<string, string> = {
  high: 'text-amber-700',
  low: 'text-amber-700',
  normal: 'text-slate-600',
};

const acbStyle: Record<number, string> = {
  0: 'bg-slate-100 text-slate-500',
  1: 'bg-slate-100 text-slate-600',
  2: 'bg-amber-100 text-amber-800',
  3: 'bg-rose-100 text-rose-800',
};

export default function EncounterView({ patient, mode, chartOpened, onOpenChart, resolvedAction, onResolveAction, onSignalSurfaced }: EncounterViewProps) {
  const [prescribeStage, setPrescribeStage] = useState<'idle' | 'drafting' | 'intercepted'>('idle');

  useEffect(() => {
    setPrescribeStage('idle');
  }, [patient.id, mode]);

  const showChart = mode !== 'chart-open' || chartOpened;
  const showSignal =
    mode === 'previsit' ? showChart : mode === 'eprescribe' ? prescribeStage === 'intercepted' : showChart;

  useEffect(() => {
    if (showSignal) onSignalSurfaced();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showSignal, patient.id, mode]);

  return (
    <div className="max-w-4xl mx-auto space-y-5 pb-10">
      {/* Demographics */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900">{patient.name}</h2>
            <p className="text-sm text-slate-500">{patient.age} year old {patient.sex}</p>
          </div>
          {mode === 'previsit' && (
            <span className="text-[11px] font-semibold text-mosaic-700 bg-mosaic-50 border border-mosaic-200 rounded-full px-2.5 py-1">
              Pre-visit prep · reviewed 6:45 AM
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5 mt-3">
          {patient.diagnoses.map((d) => (
            <span key={d} className="text-[11px] font-medium text-slate-600 bg-slate-100 rounded-full px-2.5 py-1">
              {d}
            </span>
          ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-100">
          {patient.comorbidities.ckdStage && (
            <Stat label="Renal function" value={`${patient.comorbidities.ckdStage} (eGFR ${patient.comorbidities.egfr})`} />
          )}
          <Stat label="Diabetes" value={patient.comorbidities.diabetes ? 'Yes' : 'No'} />
          <Stat label="Heart failure" value={patient.comorbidities.heartFailure ? 'Yes' : 'No'} />
          <Stat label="BMI" value={patient.comorbidities.bmi ? String(patient.comorbidities.bmi) : '—'} />
        </div>
      </div>

      {mode === 'chart-open' && !chartOpened && (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center">
          <FolderOpen className="h-6 w-6 text-slate-400 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-600">Chart is closed. The patient is checked in and waiting.</p>
          <button
            onClick={onOpenChart}
            className="mt-3 bg-mosaic-500 hover:bg-mosaic-600 text-white text-sm font-semibold px-4 py-2 rounded-lg cursor-pointer transition-all"
          >
            Open encounter (patient present)
          </button>
        </div>
      )}

      {showChart && (
        <>
          {/* Presenting complaint */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Today's presenting complaint</h3>
            <p className="text-base font-semibold text-slate-800">{patient.complaint.text}</p>
            <p className="text-sm text-slate-500 mt-1">{patient.complaint.onsetDescription}</p>
          </div>

          {/* Medications */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-3">
              <Pill className="h-3.5 w-3.5" /> Active medications
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-left text-[10.5px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th className="pb-2 pr-3 font-semibold">Medication</th>
                    <th className="pb-2 pr-3 font-semibold">Class</th>
                    <th className="pb-2 pr-3 font-semibold">Start date</th>
                    <th className="pb-2 pr-3 font-semibold">ACB</th>
                  </tr>
                </thead>
                <tbody>
                  {patient.medications.map((m) => (
                    <tr key={m.id} className="border-b border-slate-50 last:border-0">
                      <td className="py-2 pr-3">
                        <span className="font-medium text-slate-800">{m.name}</span>
                        <span className="text-slate-400"> · {m.dose}</span>
                        {m.source === 'patient-reported-otc' && (
                          <span className="ml-1.5 text-[10px] font-semibold text-violet-700 bg-violet-50 border border-violet-200 rounded px-1.5 py-0.5">
                            OTC, self-reported
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-3 text-slate-500">{m.className}</td>
                      <td className="py-2 pr-3 text-slate-500">{formatDate(m.startDate)}</td>
                      <td className="py-2 pr-3">
                        <span className={`text-[10.5px] font-bold px-1.5 py-0.5 rounded ${acbStyle[m.acb]}`}>{m.acb}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Labs */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">Relevant labs</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {patient.labs.map((l) => (
                <div key={l.name} className="bg-slate-50 rounded-lg p-2.5">
                  <p className="text-[10.5px] text-slate-400 font-semibold uppercase tracking-wide">{l.name}</p>
                  <p className={`text-sm font-semibold ${labFlagStyle[l.flag || 'normal']}`}>
                    {l.value} <span className="text-[11px] font-normal text-slate-400">{l.unit}</span>
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Phenotype risk: fall-risk stratification + predicted adverse events */}
          <PhenotypeRiskPanel phenotypeRisk={patient.phenotypeRisk} />

          {/* e-Prescribe widget */}
          {mode === 'eprescribe' && (
            <div className="bg-white rounded-2xl border border-slate-200 p-5">
              <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-3">
                <FileEdit className="h-3.5 w-3.5" /> New prescription
              </h3>
              {prescribeStage === 'idle' && (
                <button
                  onClick={() => setPrescribeStage('drafting')}
                  className="text-sm font-semibold text-mosaic-700 bg-mosaic-50 hover:bg-mosaic-100 border border-mosaic-200 rounded-lg px-3.5 py-2 cursor-pointer transition-all"
                >
                  Write new prescription for today's complaint
                </button>
              )}
              {prescribeStage !== 'idle' && (
                <div className="flex items-center gap-2">
                  <div className="flex-1 text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-700">
                    {DRAFT_RX[patient.id]}
                  </div>
                  {prescribeStage === 'drafting' && (
                    <button
                      onClick={() => setPrescribeStage('intercepted')}
                      className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold px-3.5 py-2 rounded-lg cursor-pointer transition-all shrink-0"
                    >
                      <Send className="h-3.5 w-3.5" /> Send to pharmacy
                    </button>
                  )}
                </div>
              )}
              {prescribeStage === 'intercepted' && (
                <div className="flex items-center gap-1.5 text-amber-700 text-xs font-semibold mt-3">
                  <AlertTriangle className="h-3.5 w-3.5" /> Held before sending. Review the signal below.
                </div>
              )}
            </div>
          )}

          {/* MosaicRx signal */}
          {showSignal && (
            <>
              <MosaicSignalCard signal={patient.signal} mode={mode} />
              <ActionPanel actions={patient.signal.suggestedActions} resolved={resolvedAction} onResolve={onResolveAction} />
            </>
          )}
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10.5px] text-slate-400 font-semibold uppercase tracking-wide">{label}</p>
      <p className="text-sm font-medium text-slate-700">{value}</p>
    </div>
  );
}
