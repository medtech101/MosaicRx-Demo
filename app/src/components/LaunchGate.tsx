import { useEffect, useState } from 'react';
import { BadgeCheck, Check, FileCheck2, KeyRound, Loader2, Lock, ShieldCheck } from 'lucide-react';

interface LaunchGateProps {
  onAuthenticated: () => void;
}

const HANDSHAKE_STEPS = [
  'Redirecting to Office Ally single sign-on',
  'Exchanging OAuth 2.0 authorization code',
  'Establishing encrypted session (TLS 1.3)',
  'Loading clinician context and patient panel',
];

const BADGES = [
  { icon: ShieldCheck, label: 'HIPAA compliant', sub: 'PHI safeguards' },
  { icon: BadgeCheck, label: 'SOC 2 Type II', sub: 'Audited controls' },
  { icon: KeyRound, label: 'OAuth 2.0 / OIDC', sub: 'Federated SSO' },
  { icon: FileCheck2, label: '21st Century Cures Act', sub: 'CDS-exempt posture' },
];

type Phase = 'idle' | 'authenticating' | 'ready';

export default function LaunchGate({ onAuthenticated }: LaunchGateProps) {
  const [phase, setPhase] = useState<Phase>('idle');
  const [stepIndex, setStepIndex] = useState(-1);

  useEffect(() => {
    if (phase !== 'authenticating') return;
    if (stepIndex >= HANDSHAKE_STEPS.length) {
      const t = setTimeout(() => setPhase('ready'), 350);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setStepIndex((i) => i + 1), 620);
    return () => clearTimeout(t);
  }, [phase, stepIndex]);

  const startAuth = () => {
    setPhase('authenticating');
    setStepIndex(0);
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-mosaic-900 text-white overflow-y-auto">
      <div className="bg-amber-50 border-b border-amber-200 text-amber-900 text-[11px] font-semibold tracking-wide text-center py-1.5 px-4">
        DEMO — synthetic data, simulated reasoning, not for clinical use.
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          {/* Brand */}
          <div className="flex items-center gap-3 mb-8 justify-center">
            <div className="w-11 h-11 rounded-xl bg-mosaic-500 flex items-center justify-center text-lg font-bold shrink-0">
              Rx
            </div>
            <div>
              <p className="text-lg font-bold leading-tight">MosaicRx</p>
              <p className="text-[12px] text-mosaic-200 leading-tight">Embedded clinical signal layer</p>
            </div>
          </div>

          {/* Sign-in card */}
          <div className="bg-white rounded-2xl p-6 text-slate-800 shadow-2xl">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
              <Lock className="h-3.5 w-3.5 text-mosaic-600" /> Secure clinical sign-in
            </div>
            <h1 className="text-xl font-bold text-slate-900">Sign in to continue</h1>
            <p className="text-sm text-slate-500 mt-1">
              MosaicRx is launched from within your EHR session. Authentication is federated to your Office Ally
              identity provider.
            </p>

            {phase === 'idle' && (
              <button
                onClick={startAuth}
                className="mt-5 w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold py-3 rounded-xl transition-all cursor-pointer"
              >
                <KeyRound className="h-4 w-4" /> Sign in with Office Ally (SSO)
              </button>
            )}

            {phase === 'authenticating' && (
              <div className="mt-5 space-y-2.5">
                {HANDSHAKE_STEPS.map((step, i) => {
                  const done = i < stepIndex;
                  const active = i === stepIndex;
                  return (
                    <div
                      key={step}
                      className={`flex items-center gap-2.5 text-[13px] transition-opacity ${
                        done || active ? 'opacity-100' : 'opacity-40'
                      }`}
                    >
                      <span className="shrink-0">
                        {done ? (
                          <span className="w-5 h-5 rounded-full bg-mosaic-500 flex items-center justify-center">
                            <Check className="h-3 w-3 text-white" />
                          </span>
                        ) : active ? (
                          <Loader2 className="h-5 w-5 text-mosaic-600 animate-spin" />
                        ) : (
                          <span className="w-5 h-5 rounded-full border border-slate-200" />
                        )}
                      </span>
                      <span className={done ? 'text-slate-500' : 'text-slate-700 font-medium'}>{step}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {phase === 'ready' && (
              <div className="mt-5">
                <div className="flex items-center gap-2.5 bg-mosaic-50 border border-mosaic-200 rounded-xl p-3">
                  <div className="w-9 h-9 rounded-full bg-mosaic-500 text-white flex items-center justify-center text-xs font-bold shrink-0">
                    AR
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-800 leading-tight">Dr. Alexis Reyes</p>
                    <p className="text-[12px] text-slate-500 leading-tight">Internal Medicine · Office Ally SSO</p>
                  </div>
                  <ShieldCheck className="h-4 w-4 text-mosaic-600 ml-auto shrink-0" />
                </div>
                <button
                  onClick={onAuthenticated}
                  className="mt-3 w-full bg-mosaic-500 hover:bg-mosaic-600 text-white text-sm font-semibold py-3 rounded-xl transition-all cursor-pointer"
                >
                  Enter encounter view
                </button>
              </div>
            )}

            <p className="text-[11px] text-slate-400 mt-4 leading-relaxed">
              Simulated sign-in for this demo. No real authentication, credentials, or patient data are involved.
            </p>
          </div>

          {/* Compliance badges */}
          <div className="grid grid-cols-2 gap-2 mt-5">
            {BADGES.map((b) => {
              const Icon = b.icon;
              return (
                <div key={b.label} className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5">
                  <Icon className="h-4 w-4 text-mosaic-200 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-[12px] font-semibold leading-tight truncate">{b.label}</p>
                    <p className="text-[10.5px] text-mosaic-200/80 leading-tight truncate">{b.sub}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <p className="text-center text-[11px] text-mosaic-200/70 mt-4">
            Data encrypted in transit and at rest. Access logged to the audit trail.
          </p>
        </div>
      </div>
    </div>
  );
}
