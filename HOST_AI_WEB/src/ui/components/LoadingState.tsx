export function LoadingState({ label = "Cargando..." }: { label?: string }) {
  return (
    <div className="panel-state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}
