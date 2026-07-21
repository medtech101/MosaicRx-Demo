import { useEffect, useState } from "react";
import { api, DocumentOut } from "../api/client";

export function ExportPage() {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.listDocuments().then(setDocs).catch((e) => setError(e.message));
  }, []);

  const confirmed = docs.filter((d) => d.status === "confirmed");

  async function downloadBundle() {
    setBusy(true);
    setError(null);
    try {
      await api.downloadBundle();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <h1>Export center</h1>
      <p className="muted">
        Everything here is sanitized content only, re-checked against your blocklist right before
        download. Nothing is ever shared or published from this app - export is for your own use
        (Anki, backups, other tools).
      </p>

      {error && <p className="error">{error}</p>}

      <section>
        <h2>Full bundle</h2>
        <p className="muted">Every export below, packaged as one ZIP.</p>
        <button className="btn-primary" disabled={busy} onClick={downloadBundle}>
          {busy ? "Building..." : "Download ZIP bundle"}
        </button>
      </section>

      <section>
        <h2>Study notes per lecture</h2>
        {confirmed.length === 0 && <p className="muted">No confirmed lectures yet.</p>}
        <ul className="export-list">
          {confirmed.map((d) => (
            <li key={d.id}>
              {d.original_filename}
              <a href={api.exportUrl(`/notes/${d.id}/markdown`)}>Markdown</a>
              <a href={api.exportUrl(`/notes/${d.id}/pdf`)}>PDF</a>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Knowledge graph</h2>
        <ul className="export-list">
          <li>
            Full graph
            <a href={api.exportUrl("/graph/graphml")}>GraphML</a>
            <a href={api.exportUrl("/graph/json")}>JSON</a>
            <a href={api.exportUrl("/graph/png")}>PNG snapshot</a>
          </li>
        </ul>
      </section>

      <section>
        <h2>Reports</h2>
        <ul className="export-list">
          <li>
            Bridge concepts &amp; clusters
            <a href={api.exportUrl("/reports/bridge-concepts")}>Bridge concepts (MD)</a>
            <a href={api.exportUrl("/reports/cluster-summary")}>Cluster summary (MD)</a>
          </li>
        </ul>
      </section>

      <section>
        <h2>Flashcards</h2>
        <ul className="export-list">
          <li>
            Generated from concepts &amp; relationships
            <a href={api.exportUrl("/flashcards.csv")}>Anki-compatible CSV</a>
          </li>
        </ul>
      </section>

      <section>
        <h2>Schedule</h2>
        <ul className="export-list">
          <li>
            Current + historical weekly plans
            <a href={api.exportUrl("/schedule.ics")}>ICS</a>
            <a href={api.exportUrl("/schedule.csv")}>CSV</a>
          </li>
        </ul>
      </section>

      <section>
        <h2>Resources</h2>
        <ul className="export-list">
          <li>
            Resource mapping table with your ratings
            <a href={api.exportUrl("/resource-ratings.csv")}>CSV</a>
          </li>
        </ul>
      </section>
    </div>
  );
}
