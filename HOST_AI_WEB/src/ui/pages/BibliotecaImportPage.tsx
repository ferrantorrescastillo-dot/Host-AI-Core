import { useRef, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { bibliotecaService } from "../../services/bibliotecaService";
import type { BibliotecaImportSession } from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";

const ACCEPTED = ".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.txt";

export function BibliotecaImportPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [session, setSession] = useState<BibliotecaImportSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);

  async function process(file?: File) {
    if (!file) return;
    setLoading(true);
    setError(null);
    setSession(null);
    try {
      const response = await bibliotecaService.importDocument(file);
      setSession(response.importacion);
    } catch (reason) {
      const apiError = reason as HostAiApiError;
      setError({ message: apiError.message, requestId: apiError.requestId });
    } finally {
      setLoading(false);
    }
  }

  return <section className="panel">
    <p className="eyebrow">Biblioteca Culinaria</p>
    <h2>Importador Inteligente</h2>
    <BibliotecaNav />
    <p>Host AI transforma documentos en conocimiento estructurado y propone cambios para revisión. En esta fase no modifica la Biblioteca.</p>
    <div
      className="panel-state"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        void process(event.dataTransfer.files[0]);
      }}
    >
      <p><strong>Arrastra aquí un documento</strong></p>
      <p>PDF, Word, Excel, imagen o texto · máximo 10 MB</p>
      <button type="button" onClick={() => inputRef.current?.click()}>Seleccionar archivo</button>
      <input
        ref={inputRef}
        aria-label="Seleccionar documento"
        accept={ACCEPTED}
        hidden
        type="file"
        onChange={(event) => void process(event.target.files?.[0])}
      />
    </div>
    {loading ? <LoadingState label="Interpretando documento..." /> : null}
    {error ? <>
      <ErrorState title="No se pudo interpretar el documento." detail={error.message} />
      {error.requestId ? <p className="muted">Referencia: {error.requestId}</p> : null}
    </> : null}
    {session ? <ImportPreview session={session} /> : null}
  </section>;
}

function ImportPreview({ session }: { session: BibliotecaImportSession }) {
  const { documento, resumen, propuestas } = session;
  return <section className="catalog-section">
    <h3>Documento recibido</h3>
    <dl className="detail-grid">
      <dt>Nombre</dt><dd>{documento.nombre}</dd>
      <dt>Clasificación</dt><dd>{documento.clasificacion.tipo}</dd>
      <dt>Confianza</dt><dd>{Math.round(documento.clasificacion.confianza.valor * 100)}%</dd>
      <dt>Estado</dt><dd>Pendiente de revisión</dd>
      <dt>Entidades detectadas</dt><dd>{resumen.entidades}</dd>
      <dt>Propuestas</dt><dd>{resumen.propuestas}</dd>
    </dl>
    <p>{documento.clasificacion.confianza.explicacion}</p>
    {documento.advertencias.length ? <><h4>Advertencias</h4><ul>{documento.advertencias.map((item) => <li key={item}>{item}</li>)}</ul></> : null}
    <h3>Propuestas detectadas</h3>
    <ul className="operational-checks">{propuestas.map((proposal) => <li key={proposal.id}>
      <strong>{proposalLabel(proposal.tipo)}</strong>
      <span> · {Math.round(proposal.confianza.valor * 100)}% · Pendiente de revisión</span>
      <p>{proposal.explicacion}</p>
    </li>)}</ul>
    <p><strong>Pendiente de implementar:</strong> revisión, edición y confirmación. Ninguna propuesta ha sido aplicada.</p>
  </section>;
}

function proposalLabel(value: string) {
  return value.toLowerCase().replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}
