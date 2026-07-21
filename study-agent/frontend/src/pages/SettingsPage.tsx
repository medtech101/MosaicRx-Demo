import { useEffect, useState } from "react";
import { api, BlocklistTerm } from "../api/client";

const CATEGORIES = ["institution", "campus", "course_code", "person", "custom"];

export function SettingsPage() {
  const [terms, setTerms] = useState<BlocklistTerm[]>([]);
  const [newTerm, setNewTerm] = useState("");
  const [newCategory, setNewCategory] = useState("institution");
  const [examDate, setExamDate] = useState("");
  const [weeklyHours, setWeeklyHours] = useState<number>(10);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    api.listBlocklist().then(setTerms).catch((e) => setError(e.message));
    api
      .getAppSettings()
      .then((s) => {
        if (typeof s.exam_date === "string") setExamDate(s.exam_date);
        if (typeof s.weekly_hours === "number") setWeeklyHours(s.weekly_hours);
      })
      .catch(() => {});
  }

  useEffect(refresh, []);

  async function addTerm() {
    if (!newTerm.trim()) return;
    await api.addBlocklistTerm(newTerm.trim(), newCategory);
    setNewTerm("");
    refresh();
  }

  async function removeTerm(id: number) {
    await api.deleteBlocklistTerm(id);
    refresh();
  }

  async function saveExamDate(value: string) {
    setExamDate(value);
    await api.setAppSetting("exam_date", value);
  }

  async function saveWeeklyHours(value: number) {
    setWeeklyHours(value);
    await api.setAppSetting("weekly_hours", value);
  }

  return (
    <div className="page">
      <h1>Settings</h1>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>Blocklist</h2>
        <p className="muted">
          Institution names, campuses, course codes, and known names to redact everywhere - on
          top of automatic person/org name detection.
        </p>
        <div className="form-row">
          <input
            placeholder="Term to block"
            value={newTerm}
            onChange={(e) => setNewTerm(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addTerm()}
          />
          <select value={newCategory} onChange={(e) => setNewCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <button onClick={addTerm}>Add</button>
        </div>
        <ul className="blocklist">
          {terms.map((t) => (
            <li key={t.id}>
              <span className="badge">{t.category}</span> {t.term}
              <button className="link-btn" onClick={() => removeTerm(t.id)}>
                remove
              </button>
            </li>
          ))}
          {terms.length === 0 && <li className="muted">No blocklist terms yet.</li>}
        </ul>
      </section>

      <section>
        <h2>Exam &amp; workload</h2>
        <div className="form-row">
          <label>
            Exam date
            <input type="date" value={examDate} onChange={(e) => saveExamDate(e.target.value)} />
          </label>
          <label>
            Weekly study hours
            <input
              type="number"
              min={1}
              max={100}
              value={weeklyHours}
              onChange={(e) => saveWeeklyHours(Number(e.target.value))}
            />
          </label>
        </div>
      </section>
    </div>
  );
}
