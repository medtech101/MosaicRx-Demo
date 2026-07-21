import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export function UploadPage() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        const doc = await api.uploadDocument(file);
        navigate(`/documents/${doc.id}/review`);
        return; // review one at a time
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <h1>Upload lecture files</h1>
      <p className="muted">
        PPTX, PDF, or DOCX. Every file runs through the mandatory de-identification pass
        (blocklist + name/org detection, metadata scrubbing, logo/watermark removal, OCR scan)
        before anything is stored. You'll review every redaction before it's confirmed.
      </p>
      <label className="dropzone">
        <input
          type="file"
          accept=".pptx,.pdf,.docx"
          multiple
          disabled={busy}
          onChange={(e) => handleFiles(e.target.files)}
        />
        {busy ? "Sanitizing..." : "Choose a file or drop it here"}
      </label>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
