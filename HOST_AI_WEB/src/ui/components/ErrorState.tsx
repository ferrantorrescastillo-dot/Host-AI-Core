export function ErrorState({
  title = "No se pudo cargar la informacion.",
  detail,
}: {
  title?: string;
  detail?: string;
}) {
  return (
    <div className="panel-state panel-error" role="alert">
      <p className="panel-error-title">{title}</p>
      {detail ? <p className="panel-error-detail">{detail}</p> : null}
    </div>
  );
}
