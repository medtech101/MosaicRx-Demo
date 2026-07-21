import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, DocumentReviewOut } from "../api/client";

export function ReviewPage() {
  const { id } = useParams();
  const documentId = Number(id);
  const navigate = useNavigate();

  const [review, setReview] = useState<DocumentReviewOut | null>(null);
  const [redactionApprove, setRedactionApprove] = useState<Record<number, boolean>>({});
  const [imageAction, setImageAction] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .getReview(documentId)
      .then((r) => {
        setReview(r);
        setRedactionApprove(Object.fromEntries(r.redactions.map((x) => [x.id, x.status !== "rejected"])));
        setImageAction(Object.fromEntries(r.image_flags.map((x) => [x.id, x.action]))); // "removed" | "pending"
      })
      .catch((e) => setError(e.message));
  }, [documentId]);

  if (error && !review) return <div className="page error">{error}</div>;
  if (!review) return <div className="page">Loading review...</div>;

  async function handleConfirm() {
    setBusy(true);
    setError(null);
    try {
      const redactionDecisions = Object.entries(redactionApprove).map(([rid, approve]) => ({
        id: Number(rid),
        approve,
      }));
      const imageDecisions = Object.entries(imageAction).map(([fid, action]) => ({
        id: Number(fid),
        action: action === "pending" ? "removed" : action,
      }));
      await api.confirmDocument(documentId, redactionDecisions, imageDecisions);
      navigate("/documents");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!window.confirm("Discard this upload? The original file will be permanently deleted.")) return;
    setBusy(true);
    try {
      await api.rejectDocument(documentId);
      navigate("/documents");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const grouped = review.redactions.reduce<Record<string, typeof review.redactions>>((acc, r) => {
    (acc[r.category] ||= []).push(r);
    return acc;
  }, {});

  return (
    <div className="page">
      <h1>Review sanitization - {review.document.original_filename}</h1>
      <p className="muted">
        Everything below was redacted automatically. Approve keeps it redacted (default); reject
        restores the original text in case of a false positive. Nothing is stored until you confirm,
        and the original file is deleted immediately afterward.
      </p>

      {error && <p className="error">{error}</p>}

      <section>
        <h2>Text redactions ({review.redactions.length})</h2>
        {Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="redaction-group">
            <h3>{category}</h3>
            {items.map((r) => (
              <div key={r.id} className="diff-row">
                <div className="diff-location">{r.location}</div>
                <div className="diff-text">
                  <span className="diff-original">{r.original_text}</span>
                  <span className="diff-arrow">→</span>
                  <span className="diff-replacement">{r.replacement_text || "(removed)"}</span>
                </div>
                <label className="diff-toggle">
                  <input
                    type="checkbox"
                    checked={redactionApprove[r.id] ?? true}
                    onChange={(e) =>
                      setRedactionApprove((prev) => ({ ...prev, [r.id]: e.target.checked }))
                    }
                  />
                  Keep redacted
                </label>
              </div>
            ))}
          </div>
        ))}
        {review.redactions.length === 0 && <p className="muted">No text redactions found.</p>}
      </section>

      <section>
        <h2>Flagged images ({review.image_flags.length})</h2>
        {review.image_flags.map((f) => (
          <div key={f.id} className="image-flag-row">
            <img
              src={api.imageThumbnailUrl(documentId, f.id)}
              alt={f.reason}
              className="image-flag-thumb"
            />
            <div>
              <div>
                <strong>{f.location}</strong> — {f.reason === "logo_heuristic" ? "detected logo/watermark" : "OCR matched blocklist"}
              </div>
              {f.matched_terms && f.matched_terms.length > 0 && (
                <div className="muted">Matched: {f.matched_terms.join(", ")}</div>
              )}
              <select
                value={imageAction[f.id] === "pending" ? "removed" : imageAction[f.id]}
                onChange={(e) => setImageAction((prev) => ({ ...prev, [f.id]: e.target.value }))}
              >
                <option value="removed">Remove from sanitized notes</option>
                <option value="kept">Keep (I've verified it's safe)</option>
              </select>
            </div>
          </div>
        ))}
        {review.image_flags.length === 0 && <p className="muted">No images required review.</p>}
      </section>

      <section>
        <h2>Sanitized notes preview</h2>
        <pre className="markdown-preview">{review.sanitized_markdown_preview}</pre>
      </section>

      <div className="action-bar">
        <button disabled={busy} className="btn-primary" onClick={handleConfirm}>
          Confirm sanitized version
        </button>
        <button disabled={busy} className="btn-danger" onClick={handleReject}>
          Discard upload
        </button>
      </div>
    </div>
  );
}
