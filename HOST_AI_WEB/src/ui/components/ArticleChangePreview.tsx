import type { ArticleChangePreview as ArticleChangePreviewData } from "../../types/api";

export function ArticleChangePreview({ preview }: { preview: ArticleChangePreviewData }) {
  return (
    <section className="article-change-preview" aria-label="Vista previa del cambio de artículo">
      <header><h3>{preview.title}</h3><p className="meta-line">{preview.entity_id} · {preview.operation}</p></header>
      {preview.changes.length ? <table>
        <caption>Cambios propuestos</caption>
        <thead><tr><th scope="col">Campo</th><th scope="col">Antes</th><th scope="col">Después</th></tr></thead>
        <tbody>{preview.changes.map((change) => <tr key={change.field}><th scope="row">{change.label}</th><td>{change.before}</td><td>{change.after}</td></tr>)}</tbody>
      </table> : null}
      {preview.unchanged.length ? <div><h4>Valores relevantes sin cambios</h4>{preview.unchanged.map((item) => <p key={item.label}><strong>{item.label}:</strong> {item.value} <span className="preview-status">{item.status}</span></p>)}</div> : null}
      {preview.derived.length ? <div><h4>Valores derivados</h4>{preview.derived.map((item) => <p key={item.label}><strong>{item.label}:</strong> {item.value}{item.formula ? <> · Fórmula: {item.formula}</> : null}{item.status ? <span className="preview-status">{item.status}</span> : null}</p>)}</div> : null}
      <p className="article-change-notice" role="status">{preview.notice}</p>
    </section>
  );
}
