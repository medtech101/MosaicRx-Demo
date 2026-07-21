import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DocumentOut } from "../api/client";

export function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listDocuments().then(setDocs).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <h1>Documents</h1>
      {error && <p className="error">{error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Type</th>
            <th>Status</th>
            <th>Units</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td>{d.original_filename}</td>
              <td>{d.doc_type}</td>
              <td>
                <span className={`badge badge-${d.status}`}>{d.status}</span>
              </td>
              <td>{d.unit_count}</td>
              <td>
                {d.status === "pending_review" && (
                  <Link to={`/documents/${d.id}/review`}>Review</Link>
                )}
              </td>
            </tr>
          ))}
          {docs.length === 0 && (
            <tr>
              <td colSpan={5} className="muted">
                No documents yet. Upload a lecture file to get started.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
