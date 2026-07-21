import { useEffect, useState } from "react";
import { api, CurrentWeek, ScheduleBlockItem } from "../api/client";

const BLOCK_TYPE_LABEL: Record<string, string> = {
  new: "New material",
  review: "Spaced review",
  taper: "Exam taper",
};

const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function dayKey(iso: string): string {
  return iso.slice(0, 10);
}

function dayLabel(iso: string): string {
  const d = new Date(iso);
  return `${DAY_NAMES[d.getDay()]}, ${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
}

export function SchedulePage() {
  const [week, setWeek] = useState<CurrentWeek | null>(null);
  const [blocks, setBlocks] = useState<ScheduleBlockItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function load() {
    api
      .getCurrentWeek()
      .then((w) => {
        setWeek(w);
        return api.getWeekBlocks(w.id);
      })
      .then(setBlocks)
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  async function regenerate() {
    if (!week) return;
    setBusy(true);
    try {
      const result = await api.generateSchedule(week.id);
      setBlocks(result.blocks);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function rate(blockId: number, rating: number) {
    try {
      const updated = await api.submitConfidence(blockId, rating);
      setBlocks((prev) => prev.map((b) => (b.id === blockId ? updated : b)));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (error) return <div className="page error">{error}</div>;
  if (!week) return <div className="page">Loading schedule...</div>;

  const byDay = new Map<string, ScheduleBlockItem[]>();
  for (const b of blocks) {
    const key = dayKey(b.day);
    if (!byDay.has(key)) byDay.set(key, []);
    byDay.get(key)!.push(b);
  }
  const sortedDays = Array.from(byDay.keys()).sort();

  return (
    <div className="page">
      <h1>Study schedule - {week.label}</h1>
      <p className="muted">
        New material is front-loaded onto the earliest days; spaced-repetition review of prior
        weeks is interleaved across the rest. Rate your confidence after each block to reschedule
        it automatically.
      </p>

      <div className="action-bar">
        <button disabled={busy} onClick={regenerate}>
          Regenerate remaining days
        </button>
        <a className="btn-primary" href={api.icsExportUrl()} download="study-schedule.ics">
          Download .ics
        </a>
      </div>

      {week.topics.length > 0 && (
        <section>
          <h2>This week's topics</h2>
          <div className="chip-row">
            {week.topics.map((t) => (
              <span key={t.concept_id} className="chip">
                {t.name}
              </span>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2>Plan</h2>
        {sortedDays.length === 0 && (
          <p className="muted">
            No blocks yet - confirm a sanitized lecture or click Regenerate to build this week's plan.
          </p>
        )}
        {sortedDays.map((day) => (
          <div key={day} className="schedule-day">
            <h3>{dayLabel(byDay.get(day)![0].day)}</h3>
            {byDay.get(day)!.map((b) => (
              <div key={b.id} className={`schedule-block block-${b.block_type}`}>
                <div>
                  <span className="badge">{BLOCK_TYPE_LABEL[b.block_type]}</span>{" "}
                  <strong>{b.label}</strong>
                  <div className="muted">{b.duration_minutes} min</div>
                </div>
                {b.status === "planned" ? (
                  <div className="confidence-row">
                    <span className="muted">Confidence:</span>
                    {[1, 2, 3, 4].map((r) => (
                      <button key={r} onClick={() => rate(b.id, r)}>
                        {r}
                      </button>
                    ))}
                  </div>
                ) : (
                  <span className="badge badge-confirmed">
                    done{b.confidence_rating ? ` - confidence ${b.confidence_rating}/4` : ""}
                  </span>
                )}
              </div>
            ))}
          </div>
        ))}
      </section>
    </div>
  );
}
