export function PlaceholderPage({ modulo }: { modulo: string }) {
  return (
    <section className="panel" data-testid={`placeholder-${modulo.toLowerCase()}`}>
      <h2>{modulo}</h2>
      <p>Modulo disponible proximamente.</p>
    </section>
  );
}
