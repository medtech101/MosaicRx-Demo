import { useState } from 'react';
import { PATIENTS } from './data/patients';
import { AuditEntry, PointOfCareMode, SuggestedAction } from './types';
import TopBar from './components/TopBar';
import PatientRail from './components/PatientRail';
import EncounterView from './components/EncounterView';
import AuditTrail from './components/AuditTrail';
import InvestorView from './components/InvestorView';
import LaunchGate from './components/LaunchGate';

interface ResolvedAction {
  action: SuggestedAction;
  noteText: string;
  dismissReason?: string;
}

const INITIAL_STATE = {
  selectedId: PATIENTS[0].id,
  mode: 'chart-open' as PointOfCareMode,
  view: 'clinical' as 'clinical' | 'investor',
  chartOpenedIds: new Set<string>(),
  resolvedActions: {} as Record<string, ResolvedAction>,
  auditLog: [] as AuditEntry[],
};

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [selectedId, setSelectedId] = useState(INITIAL_STATE.selectedId);
  const [mode, setMode] = useState<PointOfCareMode>(INITIAL_STATE.mode);
  const [view, setView] = useState<'clinical' | 'investor'>(INITIAL_STATE.view);
  const [chartOpenedIds, setChartOpenedIds] = useState<Set<string>>(INITIAL_STATE.chartOpenedIds);
  const [resolvedActions, setResolvedActions] = useState<Record<string, ResolvedAction>>(INITIAL_STATE.resolvedActions);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>(INITIAL_STATE.auditLog);

  const patient = PATIENTS.find((p) => p.id === selectedId)!;
  const resolvedKey = `${patient.id}-${mode}`;

  const handleReset = () => {
    setSelectedId(PATIENTS[0].id);
    setMode('chart-open');
    setView('clinical');
    setChartOpenedIds(new Set());
    setResolvedActions({});
    setAuditLog([]);
  };

  const handleOpenChart = () => {
    setChartOpenedIds((prev) => new Set(prev).add(patient.id));
  };

  const handleSignOut = () => {
    handleReset();
    setAuthenticated(false);
  };

  const handleResolveAction = (action: SuggestedAction, dismissReason?: string) => {
    const resolved: ResolvedAction = { action, noteText: action.noteTemplate, dismissReason };
    setResolvedActions((prev) => ({ ...prev, [resolvedKey]: resolved }));

    const entry: AuditEntry = {
      id: `audit-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      patientName: patient.name,
      mode,
      signalSurfaced: true,
      clinicianEngaged: true,
      action: dismissReason ? `Dismissed — ${dismissReason}` : action.label,
    };
    setAuditLog((prev) => [...prev, entry]);
  };

  if (!authenticated) {
    return <LaunchGate onAuthenticated={() => setAuthenticated(true)} />;
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-50 text-slate-800 font-sans overflow-hidden">
      <TopBar
        mode={mode}
        onModeChange={setMode}
        view={view}
        onViewChange={setView}
        onReset={handleReset}
        clinician={{ name: 'Dr. Alexis Reyes', role: 'Internal Medicine', initials: 'AR' }}
        onSignOut={handleSignOut}
      />

      <div className="flex-1 flex overflow-hidden">
        {view === 'clinical' && (
          <PatientRail
            patients={PATIENTS}
            selectedId={selectedId}
            onSelect={setSelectedId}
            resolvedIds={new Set(PATIENTS.filter((p) => resolvedActions[`${p.id}-${mode}`]).map((p) => p.id))}
          />
        )}

        <main className="flex-1 overflow-y-auto p-6">
          {view === 'clinical' ? (
            <EncounterView
              patient={patient}
              mode={mode}
              chartOpened={chartOpenedIds.has(patient.id)}
              onOpenChart={handleOpenChart}
              resolvedAction={resolvedActions[resolvedKey] || null}
              onResolveAction={handleResolveAction}
              onSignalSurfaced={() => {}}
            />
          ) : (
            <InvestorView />
          )}
        </main>

        {view === 'clinical' && (
          <aside className="w-80 border-l border-slate-200 bg-slate-50/60 p-4 overflow-y-auto shrink-0">
            <AuditTrail entries={auditLog} />
          </aside>
        )}
      </div>
    </div>
  );
}
