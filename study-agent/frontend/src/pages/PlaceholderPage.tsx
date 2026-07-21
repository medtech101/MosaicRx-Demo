export function PlaceholderPage({ title, note }: { title: string; note: string }) {
  return (
    <div className="page">
      <h1>{title}</h1>
      <p className="muted">{note}</p>
    </div>
  );
}
