type Props = { form: Record<string, string>; busy: boolean; proposals: Record<string, string>; onGenerate: () => void; onChange: (field: string, value: string) => void; onAccept: (field: string) => void; onReject: (field: string) => void };

export function DraftArticleAi({ form, busy, proposals, onGenerate, onChange, onAccept, onReject }: Props) {
  const enabled = Boolean(String(form.nombre || "").trim());
  return <section className="recipe-card" aria-label="IA para borrador de artículo">
    <button type="button" disabled={!enabled || busy} onClick={onGenerate}>Completar campos con IA</button>
    {!enabled ? <p>Indica primero el nombre del artículo.</p> : null}
    {Object.keys(proposals).length ? <><h4>Propuestas IA</h4>{Object.entries(proposals).map(([field, value]) => <div key={field}>
      <label>{field}<input value={value} onChange={(event) => onChange(field, event.target.value)} /></label>
      <button type="button" onClick={() => onAccept(field)}>Aceptar</button>
      <button type="button" className="secondary" onClick={() => onReject(field)}>Rechazar</button>
    </div>)}</> : null}
  </section>;
}
