import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { NodeObject, LinkObject } from "react-force-graph-2d";
import { api, ConceptDetail, GraphResponse } from "../api/client";
import { ResourcesPanel } from "../components/ResourcesPanel";

const COMMUNITY_COLORS = [
  "#5b8cff", "#ff8a5b", "#35c46f", "#e35bff", "#ffcf6b",
  "#5bd8ff", "#ff5b6a", "#a4ff5b", "#c45bff", "#5bffb0",
];

function communityColor(community: number | null): string {
  if (community === null || community === undefined) return "#9aa1ac";
  return COMMUNITY_COLORS[community % COMMUNITY_COLORS.length];
}

export function GraphPage() {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [selected, setSelected] = useState<ConceptDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [width, setWidth] = useState(360);
  const containerRef = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    api.getGraph().then(setGraph).catch((e) => setError(e.message));
  }, []);

  useEffect(load, [load]);

  useEffect(() => {
    function onResize() {
      if (containerRef.current) setWidth(containerRef.current.clientWidth);
    }
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const graphData = useMemo(() => {
    if (!graph) return { nodes: [], links: [] };
    return {
      nodes: graph.nodes.map((n) => ({ ...n })),
      links: graph.edges.map((e) => ({ ...e })),
    };
  }, [graph]);

  async function selectConcept(id: number) {
    try {
      const detail = await api.getConceptDetail(id);
      setSelected(detail);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function recompute() {
    await api.recomputeGraph();
    load();
  }

  return (
    <div className="page">
      <h1>Knowledge graph</h1>
      <p className="muted">
        Every confirmed lecture grows this cumulative graph - nodes are concepts, edges are
        co-occurrence within a slide or lecture. Click a node to see where it came from.
      </p>

      {error && <p className="error">{error}</p>}

      {graph && (
        <section>
          <h2>Bridge concepts</h2>
          <p className="muted">
            Ranked by betweenness centrality - the concepts most likely to connect otherwise
            separate topics (e.g. a renal concept that also shows up in cardiovascular and
            pharmacology material).
          </p>
          <ol className="bridge-list">
            {graph.bridge_concepts.slice(0, 10).map((b) => (
              <li key={b.concept_id}>
                <button className="link-btn bridge-link" onClick={() => selectConcept(b.concept_id)}>
                  {b.name}
                </button>
                <span className="muted"> betweenness {b.betweenness.toFixed(3)}</span>
              </li>
            ))}
            {graph.bridge_concepts.length === 0 && (
              <li className="muted">No bridge concepts yet - confirm more than one lecture to see cross-topic links.</li>
            )}
          </ol>
        </section>
      )}

      <section>
        <div className="graph-toolbar">
          <h2>Concept map</h2>
          <button onClick={recompute}>Recompute</button>
        </div>
        <div className="graph-container" ref={containerRef}>
          {graph && graph.nodes.length > 0 ? (
            <ForceGraph2D
              width={width}
              height={420}
              graphData={graphData}
              nodeLabel={(n: NodeObject) => (n as any).name}
              nodeColor={(n: NodeObject) => communityColor((n as any).community)}
              nodeRelSize={4}
              nodeVal={(n: NodeObject) => 1 + ((n as any).degree || 0)}
              linkWidth={(l: LinkObject) => Math.max(0.5, Math.min(4, (l as any).weight))}
              linkColor={() => "rgba(154,161,172,0.35)"}
              onNodeClick={(n: NodeObject) => selectConcept((n as any).id)}
              cooldownTicks={100}
            />
          ) : (
            <p className="muted">No concepts yet. Confirm a sanitized lecture to build the graph.</p>
          )}
        </div>
      </section>

      {selected && (
        <section>
          <h2>{selected.concept.canonical_name}</h2>
          <h3>Appears in</h3>
          <ul>
            {selected.occurrences.map((o, i) => (
              <li key={i}>
                {o.filename} - {o.location}
              </li>
            ))}
            {selected.occurrences.length === 0 && <li className="muted">No recorded occurrences.</li>}
          </ul>
          <h3>Related concepts</h3>
          <div className="chip-row">
            {selected.related_concepts.map((r) => (
              <button key={r.id} className="chip" onClick={() => selectConcept(r.id)}>
                {r.name}
              </button>
            ))}
            {selected.related_concepts.length === 0 && <span className="muted">None yet.</span>}
          </div>

          <ResourcesPanel conceptId={selected.concept.id} />
        </section>
      )}
    </div>
  );
}
