import { useEffect, useState } from "react";
import { api, ResourceItem } from "../api/client";

const SOURCE_LABELS: Record<string, string> = {
  pubmed: "PubMed review",
  bookshelf: "NCBI Bookshelf / StatPearls",
  openstax: "OpenStax A&P",
  medlineplus: "MedlinePlus",
  amboss: "AMBOSS",
  boards_and_beyond: "Boards and Beyond",
  bootcamp: "Bootcamp",
};

const OPEN_SOURCES = new Set(["pubmed", "bookshelf", "openstax", "medlineplus"]);

export function ResourcesPanel({ conceptId }: { conceptId: number }) {
  const [resources, setResources] = useState<ResourceItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function load() {
    api
      .getRankedResources(conceptId)
      .then((r) => setResources(r.resources))
      .catch((e) => setError(e.message));
  }

  useEffect(load, [conceptId]);

  async function refresh() {
    setBusy(true);
    try {
      await api.refreshResources(conceptId);
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function rate(resourceId: number, helpful: boolean) {
    await api.rateResource(resourceId, conceptId, helpful);
    load();
  }

  if (error) return <p className="error">{error}</p>;
  if (!resources) return <p className="muted">Loading resources...</p>;

  const open = resources.filter((r) => OPEN_SOURCES.has(r.source));
  const commercial = resources.filter((r) => !OPEN_SOURCES.has(r.source));

  return (
    <div>
      <div className="graph-toolbar">
        <h3>Resources</h3>
        <button disabled={busy} onClick={refresh}>
          Refresh
        </button>
      </div>

      <h4 className="resources-subhead">Open sources</h4>
      <ul className="resource-list">
        {open.map((r) => (
          <ResourceRow key={r.id} resource={r} onRate={rate} />
        ))}
        {open.length === 0 && <li className="muted">None found yet.</li>}
      </ul>

      <h4 className="resources-subhead">Commercial platforms (link-only)</h4>
      <ul className="resource-list">
        {commercial.map((r) => (
          <ResourceRow key={r.id} resource={r} onRate={rate} />
        ))}
      </ul>
    </div>
  );
}

function ResourceRow({
  resource,
  onRate,
}: {
  resource: ResourceItem;
  onRate: (id: number, helpful: boolean) => void;
}) {
  return (
    <li className="resource-row">
      <div>
        <a href={resource.url} target="_blank" rel="noreferrer">
          {resource.title}
        </a>
        <div className="muted">
          {SOURCE_LABELS[resource.source] || resource.source}
          {resource.summary ? ` - ${resource.summary}` : ""}
        </div>
      </div>
      <div className="resource-rate">
        <button
          className={resource.helpful_count > 0 ? "rate-active" : ""}
          onClick={() => onRate(resource.id, true)}
          title="Mark helpful"
        >
          👍 {resource.helpful_count || ""}
        </button>
        <button
          className={resource.not_helpful_count > 0 ? "rate-active-neg" : ""}
          onClick={() => onRate(resource.id, false)}
          title="Mark not helpful"
        >
          👎 {resource.not_helpful_count || ""}
        </button>
      </div>
    </li>
  );
}
