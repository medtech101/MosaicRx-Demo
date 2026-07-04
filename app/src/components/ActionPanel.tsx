import { useState } from 'react';
import { SuggestedAction } from '../types';
import { CheckCircle2, ClipboardList, Copy, FilePlus2 } from 'lucide-react';

interface ResolvedAction {
  action: SuggestedAction;
  noteText: string;
  dismissReason?: string;
}

interface ActionPanelProps {
  actions: SuggestedAction[];
  resolved: ResolvedAction | null;
  onResolve: (action: SuggestedAction, dismissReason?: string) => void;
}

const DISMISS_REASONS = [
  'Discussed with patient, deferring to next visit',
  'Clinically not applicable in this case',
  'Will monitor and reassess',
];

export default function ActionPanel({ actions, resolved, onResolve }: ActionPanelProps) {
  const [pendingDismiss, setPendingDismiss] = useState(false);
  const [copied, setCopied] = useState(false);

  if (resolved) {
    return (
      <div className="rounded-2xl border border-mosaic-200 bg-white p-5">
        <div className="flex items-center gap-2 text-mosaic-700 font-semibold text-sm">
          <CheckCircle2 className="h-4 w-4" /> Action recorded: {resolved.action.label}
        </div>
        {resolved.dismissReason && (
          <p className="text-xs text-slate-500 mt-1">Reason: {resolved.dismissReason}</p>
        )}
        <div className="mt-3 bg-slate-50 border border-slate-200 rounded-xl p-3.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <FilePlus2 className="h-3.5 w-3.5" /> Drafted chart note
            </span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(resolved.noteText);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
              className="text-[11px] font-semibold text-slate-500 hover:text-mosaic-700 flex items-center gap-1 cursor-pointer"
            >
              <Copy className="h-3 w-3" /> {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="text-[13px] text-slate-700 leading-relaxed whitespace-pre-wrap font-mono">{resolved.noteText}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-3">
        <ClipboardList className="h-3.5 w-3.5" /> Clinician action
      </h4>
      <p className="text-xs text-slate-500 mb-3">MosaicRx surfaces a signal and a question. The clinician always decides.</p>

      <div className="flex flex-col gap-2">
        {actions
          .filter((a) => a.kind !== 'dismiss')
          .map((a) => (
            <button
              key={a.id}
              onClick={() => onResolve(a)}
              className="text-left text-sm font-medium text-slate-700 bg-slate-50 hover:bg-mosaic-50 hover:text-mosaic-800 border border-slate-200 hover:border-mosaic-300 rounded-lg px-3.5 py-2.5 transition-all cursor-pointer"
            >
              {a.label}
            </button>
          ))}

        {!pendingDismiss ? (
          <button
            onClick={() => setPendingDismiss(true)}
            className="text-left text-sm font-medium text-slate-500 hover:text-slate-700 border border-dashed border-slate-300 rounded-lg px-3.5 py-2.5 transition-all cursor-pointer"
          >
            Dismiss (with reason)
          </button>
        ) : (
          <div className="border border-slate-300 rounded-lg p-3 bg-slate-50">
            <p className="text-xs font-semibold text-slate-600 mb-2">Select a reason to dismiss</p>
            <div className="flex flex-col gap-1.5">
              {DISMISS_REASONS.map((reason) => {
                const dismissAction = actions.find((a) => a.kind === 'dismiss')!;
                return (
                  <button
                    key={reason}
                    onClick={() => onResolve(dismissAction, reason)}
                    className="text-left text-xs text-slate-600 hover:text-mosaic-800 hover:bg-white border border-transparent hover:border-mosaic-200 rounded px-2.5 py-1.5 cursor-pointer transition-all"
                  >
                    {reason}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setPendingDismiss(false)}
              className="text-[11px] text-slate-400 hover:text-slate-600 mt-2 cursor-pointer"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
