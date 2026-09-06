import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { HostAiApiError } from "../../api/client";
import { bibliotecaService } from "../../services/bibliotecaService";
import { articulosService } from "../../services/articulosService";
import type {
  BibliotecaImportSession,
  CatalogArticleDraft,
  ArticleDraftDecision,
  DraftValidationIssue,
  ElaboracionDetalle,
  ImportDraft,
  ImportConfirmationResult,
  IngredientDraft,
  MenuDraftDecision,
  RecipeDraft,
} from "../../types/biblioteca";
import { BibliotecaNav } from "../components/BibliotecaNav";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { SafeCatalogWritePanel } from "../components/SafeCatalogWritePanel";

const ACCEPTED = ".xlsx,.csv,.tsv,.json,.txt,.md";
const ACTIVE_IMPORT_SESSION_KEY = "hostai.active_import_session_id";

export function BibliotecaImportPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const preparedInputRef = useRef<HTMLInputElement>(null);
  const [session, setSession] = useState<BibliotecaImportSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [pastedText, setPastedText] = useState("");
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [sessionNotice, setSessionNotice] = useState("");
  const [excludeLegacyAp, setExcludeLegacyAp] = useState(false);

  useEffect(() => {
    const hintedImportId = sessionStorage.getItem(ACTIVE_IMPORT_SESSION_KEY)
      || localStorage.getItem(ACTIVE_IMPORT_SESSION_KEY);
    let active = true;
    if (hintedImportId) setLoading(true);
    const restoreFromList = async () => {
      const listed = await bibliotecaService.listImports();
      const first = listed.importaciones?.[0];
      if (!first) return { importacion: null };
      return bibliotecaService.importDetail(first.importacion_id);
    };
    const restore = hintedImportId
      ? bibliotecaService.importDetail(hintedImportId).catch(restoreFromList)
      : restoreFromList();
    void restore.then((response) => {
      if (!active) return;
      if (response.importacion) {
        sessionStorage.setItem(ACTIVE_IMPORT_SESSION_KEY, response.importacion.documento.id);
        localStorage.setItem(ACTIVE_IMPORT_SESSION_KEY, response.importacion.documento.id);
        setSession(response.importacion);
        setSessionNotice("");
      } else {
        sessionStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
        localStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
        setSession(null);
      }
    }).catch(() => {
      if (!active) return;
      sessionStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
      localStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
      setSession(null);
      setSessionNotice("No hay una importaciÃ³n activa. Vuelve a analizar o importar el documento.");
    }).finally(() => {
      if (active && hintedImportId) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  function activateSession(next: BibliotecaImportSession) {
    sessionStorage.setItem(ACTIVE_IMPORT_SESSION_KEY, next.documento.id);
    localStorage.setItem(ACTIVE_IMPORT_SESSION_KEY, next.documento.id);
    setSession(next);
    setSessionNotice("");
  }

  function clearActiveSession() {
    const importId = session?.documento.id;
    sessionStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
    localStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
    setSession(null);
    setSessionNotice("No hay una importaciÃ³n activa.");
    if (importId) void bibliotecaService.discardImport(importId).catch(() => undefined);
  }

  function completeActiveSession() {
    sessionStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
    localStorage.removeItem(ACTIVE_IMPORT_SESSION_KEY);
  }

  async function process(selected = files, pasted = pastedText, resolveAmbiguitiesWithAi = false, analyzeDocumentWithAi = false) {
    if (!selected.length && !pasted.trim()) return;
    setLoading(true);
    setError(null);
    setSession(null);
    try {
      const response = await bibliotecaService.importRestaurantData(selected, pasted, resolveAmbiguitiesWithAi, analyzeDocumentWithAi, excludeLegacyAp);
      activateSession(response.importacion);
    } catch (reason) {
      const apiError = reason as HostAiApiError;
      setError({ message: apiError.message, requestId: apiError.requestId });
    } finally {
      setLoading(false);
    }
  }

  async function processPrepared(file: File) {
    setLoading(true); setError(null); setSession(null);
    try {
      const response = await bibliotecaService.importPreparedData(file);
      setFiles([file]);
      activateSession(response.importacion);
    } catch (reason) {
      const apiError = reason as HostAiApiError;
      setError({ message: apiError.message || "El paquete preparado no contiene JSON válido.", requestId: apiError.requestId });
    } finally { setLoading(false); }
  }

  async function prepareForAi() {
    if (files.length !== 1) {
      setError({ message: "Selecciona un único documento para preparar el ZIP." });
      return;
    }
    setLoading(true); setError(null);
    try {
      const { blob, filename } = await bibliotecaService.prepareForExternalAi(files[0]);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = filename;
      document.body.appendChild(link); link.click(); link.remove();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError({ message: reason instanceof Error ? reason.message : "No se pudo preparar el ZIP para IA." });
    } finally { setLoading(false); }
  }

  return <section className="panel">
    <p className="eyebrow">Biblioteca Culinaria</p>
    <h2>Importador Inteligente</h2>
    <BibliotecaNav />
    <section className="catalog-section" aria-labelledby="restaurant-import-title">
    <p className="eyebrow">Entrada principal</p>
    <h3 id="restaurant-import-title">Importar datos del restaurante</h3>
    <p>Sube uno o varios archivos, arrástralos o pega datos. Se analizan juntos y no se aplican cambios hasta la confirmación explícita.</p>
    <div
      className="panel-state"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        setFiles(Array.from(event.dataTransfer.files));
      }}
    >
      <p><strong>Arrastra aquí tus archivos</strong></p>
      <p>XLSX, CSV, TSV o JSON · uno o varios · máximo 10 MB por archivo</p>
      <button type="button" onClick={() => inputRef.current?.click()}>Subir archivo o varios archivos</button>
      <input
        ref={inputRef}
        aria-label="Seleccionar documento"
        accept={ACCEPTED}
        hidden
        multiple
        type="file"
        onChange={(event) => {
          const selected = Array.from(event.target.files ?? []);
          setFiles(selected);
          void process(selected, pastedText);
        }}
      />
      <button className="secondary-action" disabled={loading || files.length !== 1} type="button" onClick={() => void prepareForAi()}>
        Preparar para IA
      </button>
      <button className="secondary-action" type="button" onClick={() => preparedInputRef.current?.click()}>
        Importar resultado de IA
      </button>
      <input
        ref={preparedInputRef}
        aria-label="Seleccionar paquete Host AI preparado"
        accept="application/json,.json"
        hidden
        type="file"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void processPrepared(file);
        }}
      />
    </div>
    {files.length ? <section aria-label="Archivos preparados"><h4>Archivos preparados</h4><ul>
      {files.map((file) => <li key={`${file.name}-${file.size}`}><strong>{file.name}</strong> · {file.type || "tipo por extensión"} · {formatBytes(file.size)} · pendiente de análisis</li>)}
    </ul></section> : null}
    <label>Pegar datos<textarea aria-label="Pegar datos del restaurante" placeholder="Pega una tabla de Excel, CSV, TSV, JSON o Markdown" rows={7} value={pastedText} onChange={(event) => setPastedText(event.target.value)} /></label>
    <label>
      <input
        type="checkbox"
        checked={excludeLegacyAp}
        onChange={(event) => setExcludeLegacyAp(event.target.checked)}
      />
      Excluir los A.P antiguos solo de esta importación
    </label>
    <p className="muted">Esta decisión no borra A.P existentes ni cambia cómo se interpretarán en futuros documentos.</p>
    <p className="muted">“Importar exportación de otro sistema” usa esta misma subida segura. No ejecuta SQL ni conecta con bases externas.</p>
    <button disabled={loading || (!files.length && !pastedText.trim())} type="button" onClick={() => void process()}>{loading ? "Analizando..." : "Analizar datos"}</button>
    </section>
    <section className="catalog-section" aria-labelledby="price-import-title">
      <p className="eyebrow">Flujo específico</p><h3 id="price-import-title">Importar referencias de precios</h3>
      <p>Las referencias externas de precios siguen separadas del catálogo y de las recetas.</p>
      <Link className="button-link" to="/articulos?panel=referencias">Abrir importador de referencias</Link>
    </section>
    {loading ? <LoadingState label="Subiendo · Analizando · Preparando resumen..." /> : null}
    {error ? <>
      <ErrorState title="No se pudo interpretar el documento." detail={error.message} />
      {error.requestId ? <p className="muted">Referencia: {error.requestId}</p> : null}
      {files.length ? <button type="button" className="secondary-action" onClick={() => void process(files, pastedText)}>
        Usar análisis básico
      </button> : null}
    </> : null}
    {sessionNotice ? <p role="status">{sessionNotice}</p> : null}
    {session ? <ImportPreview
      session={session}
      onResolveAmbiguities={() => void process(files, pastedText, true)}
      onAnalyzeWithAi={() => void process(files, pastedText, false, true)}
      onReanalyze={() => process(files, pastedText)}
      onDiscard={clearActiveSession}
      onConfirmed={completeActiveSession}
    /> : null}
  </section>;
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function ImportPreview({
  session, onResolveAmbiguities, onAnalyzeWithAi, onReanalyze, onDiscard, onConfirmed,
}: {
  session: BibliotecaImportSession;
  onResolveAmbiguities?: () => void;
  onAnalyzeWithAi?: () => void;
  onReanalyze?: () => Promise<void>;
  onDiscard: () => void;
  onConfirmed: () => void;
}) {
  const { documento, resumen, propuestas } = session;
  const analysis = session.analisis_restaurante;
  const recipes = documento.entidades.filter((entity) => entity.kind === "RECETA");
  const [canonicalIncomplete, setCanonicalIncomplete] = useState<number | null>(null);
  const [workingDraft, setWorkingDraft] = useState(session.borrador);
  const [workingPreview, setWorkingPreview] = useState(session.preview_global);
  const [draftError, setDraftError] = useState("");
  const [savingDraft, setSavingDraft] = useState(false);
  const pendingMenuCount = workingPreview?.menus?.pendientes?.length
    ?? workingPreview?.contadores.menus_pendientes
    ?? 0;
  const recipeReviewIds = new Set(session.resolucion_identidad?.recetas.grupos.requieren_revision.map((item) => item.id) ?? []);
  const pendingRecipeCount = workingDraft.recipes.filter((item) => recipeReviewIds.has(item.id)
    && (!item.identity_decision || item.identity_decision === "PENDIENTE")).length;
  const completionRecipeIds = importCompletionRecipeIds(workingDraft.recipes);
  const restoredExternalBatch = (session as BibliotecaImportSession & {
    completado_recetas_activo?: RecipeBatch | null;
  }).completado_recetas_activo;
  const [step, setStep] = useState<"RESUMEN" | "DECISIONES" | "RECETAS" | "ARTICULOS" | "MENUS" | "VARIANTES" | "PENDIENTES" | "CONFIRMAR" | "COMPLETAR_IA" | "COMPLETAR_EXTERNO">(() => {
    const sameSelection = Boolean(restoredExternalBatch?.recipe_ids.length)
      && restoredExternalBatch!.recipe_ids.every((id) => completionRecipeIds.includes(id));
    return restoredExternalBatch?.modo_generacion === "ARCHIVO_EXTERNO" && sameSelection
      ? "COMPLETAR_EXTERNO" : "RESUMEN";
  });
  const [activeExternalBatch, setActiveExternalBatch] = useState<RecipeBatch | null>(() => {
    if (!restoredExternalBatch) return null;
    const sameSelection = restoredExternalBatch.recipe_ids.length > 0
      && restoredExternalBatch.recipe_ids.every((id) => completionRecipeIds.includes(id));
    return restoredExternalBatch.modo_generacion === "ARCHIVO_EXTERNO" && sameSelection
      ? restoredExternalBatch : null;
  });
  async function persistDraftResult(next: ImportDraft): Promise<boolean> {
    setWorkingDraft(next);
    setSavingDraft(true);
    setDraftError("");
    try {
      const response = await bibliotecaService.updateImportDraft(session.documento.id, {
        draft_version: workingDraft.draft_version,
        recipes: next.recipes,
        variant_decisions: next.variant_decisions,
        article_decisions: next.article_decisions,
        menu_decisions: next.menu_decisions,
      });
      setWorkingDraft(response.borrador);
      if (response.preview_global) setWorkingPreview(response.preview_global);
      return true;
    } catch (reason) {
      setWorkingDraft(workingDraft);
      setDraftError((reason as HostAiApiError).message || "No se pudo conservar la decisiÃ³n en el borrador.");
      return false;
    } finally {
      setSavingDraft(false);
    }
  }
  async function persistDraft(next: ImportDraft): Promise<void> {
    await persistDraftResult(next);
  }
  const counts = importCounts({ ...session, preview_global: workingPreview }, workingDraft);
  return <section className="catalog-section">
    <h3>{analysis ? "Importación analizada" : "Documento recibido"}</h3>
    {analysis ? <p><strong>Host AI ha leído el archivo.</strong> {analysis.ai_import?.classification === "KNOWN"
      ? "Formato reconocido. Puedo analizarlo sin IA."
      : analysis.ai_import?.offered
        ? "Este archivo tiene una estructura compleja."
        : "El análisis básico está disponible."}</p> : null}
    <p>Host AI reutilizará lo que ya existe, creará únicamente los elementos nuevos confirmados y dejará pendientes los casos dudosos.</p>
    <section className="import-simple-summary" aria-label="Resumen sencillo de importación">
      <h4>Encontrado</h4>
      <div className="import-summary-grid">
        <ImportMetric label="Recetas" value={counts.recipesFound} />
        <ImportMetric label="Artículos" value={counts.articlesFound} />
        <ImportMetric label="Ya en Biblioteca" value={counts.existingRecipes} detail="recetas" />
        <ImportMetric label="Ya conocidas por Host AI" value={counts.knownLegacyRecipes} detail="recetas" />
        <ImportMetric label="Nuevas reales" value={counts.newRecipes} detail="recetas" />
        <ImportMetric label="Posibles variantes" value={counts.variantRecipes} detail="recetas" />
        <ImportMetric label="Variantes por comparar" value={counts.variantGroupsRequiringDecision} detail="grupos" />
        <ImportMetric label="Necesitan tu decisión" value={counts.humanDecisions} detail="decisiones" />
        <ImportMetric label="Incompletas" value={counts.incompleteRecipes} detail="recetas" />
      </div>
      <dl className="detail-grid" aria-label="Resolución de artículos">
        <dt>Artículos encontrados</dt><dd>{counts.articlesFound}</dd>
        <dt>Ya existen / reutilizar</dt><dd>{counts.existingArticles}</dd>
        <dt>Nuevos reales</dt><dd>{counts.newArticles}</dd>
        <dt>Necesitan revisión</dt><dd>{counts.reviewArticles}</dd>
        {counts.ignoredArticles > 0 ? <><dt>Eliminados de esta importación</dt><dd>{counts.ignoredArticles}</dd></> : null}
        {counts.elaborationArticles > 0 ? <><dt>Clasificados como elaboración/receta</dt><dd>{counts.elaborationArticles}</dd></> : null}
      </dl>
      <div className="import-primary-actions">
        <button type="button" onClick={() => setStep("CONFIRMAR")}>Importar lo seguro</button>
        <button type="button" className="secondary-action" onClick={() => setStep("PENDIENTES")}>Revisar pendientes</button>
        {pendingRecipeCount > 0 ? <button type="button" className="secondary-action" onClick={() => setStep("RECETAS")}>Revisar recetas · {pendingRecipeCount}</button> : null}
        {counts.reviewArticles + counts.ignoredArticles + counts.elaborationArticles + counts.newIngredientArticleGroups > 0 ? <button type="button" className="secondary-action" onClick={() => setStep("ARTICULOS")}>Revisar artículos · {counts.reviewArticles + counts.newIngredientArticleGroups}</button> : null}
        {pendingMenuCount > 0 ? <button type="button" className="secondary-action" onClick={() => setStep("MENUS")}>Revisar menús · {pendingMenuCount}</button> : null}
        {counts.variantRecipes > 0 ? <button type="button" className="secondary-action" onClick={() => setStep("VARIANTES")}>Revisar variantes</button> : null}
        {activeExternalBatch ? <button type="button" onClick={() => setStep("COMPLETAR_EXTERNO")}>Revisar propuestas externas · {activeExternalBatch.progreso.total} recetas</button> : null}
        {analysis?.regiones_ambiguas?.length && !analysis.coste_ia.usada ? <button
          type="button"
          className="secondary-action"
          onClick={onResolveAmbiguities}
        >Intentar resolver con IA · {analysis.regiones_ambiguas.length} bloques</button> : null}
        {analysis?.ai_import?.offered && !analysis.ai_import.used ? <button
          type="button" onClick={onAnalyzeWithAi}
        >Analizar con IA</button> : null}
        <button type="button" className="secondary-action" onClick={onDiscard}>Descartar importación activa</button>
      </div>
      {analysis?.regiones_ambiguas?.length && !analysis.coste_ia.usada ? <p className="muted">
        {analysis.regiones_ambiguas.length} bloques técnicos pueden analizarse opcionalmente con IA. No son decisiones humanas.
      </p> : null}
      {analysis?.ai_import?.offered && !analysis.ai_import.used ? <p className="muted">
        Host AI analizará {analysis.ai_import.structural_summary?.sheets ?? 0} hojas y {analysis.ai_import.structural_summary?.regions ?? 0} regiones relevantes. La IA no se ejecutará sin pulsar el botón.
      </p> : null}
    </section>
    {counts.knownLegacyRecipes > 0 ? <LegacyUpdatePanel session={session} count={counts.knownLegacyRecipes} onReanalyze={onReanalyze} /> : null}
    {counts.identityReviewTotal || counts.humanDecisions || counts.incompleteRecipes ? <AttentionGroups importId={session.documento.id} counts={{ ...counts, incompleteRecipes: canonicalIncomplete ?? counts.incompleteRecipes }} completionRecipeIds={completionRecipeIds} onReview={() => setStep("DECISIONES")} onCompleteAi={() => setStep("COMPLETAR_IA")} onCompleteExternal={() => setStep("COMPLETAR_EXTERNO")} /> : null}
    {step === "COMPLETAR_IA" ? <BulkRecipeCompletion importId={session.documento.id} recipeIds={completionRecipeIds} onClose={() => setStep("RESUMEN")} onCountChange={setCanonicalIncomplete} /> : null}
    {step === "COMPLETAR_EXTERNO" ? <ExternalRecipeCompletion importId={session.documento.id} recipeIds={completionRecipeIds} initialBatch={activeExternalBatch ?? undefined} onBatchChange={setActiveExternalBatch} onClose={() => setStep("RESUMEN")} onCountChange={setCanonicalIncomplete} /> : null}
    {step === "DECISIONES" || step === "RECETAS" ? <DecisionReview
      decisions={session.resolucion_identidad?.recetas.grupos.requieren_revision ?? []}
      draft={workingDraft}
      onDraftChange={persistDraft}
      saving={savingDraft}
      onClose={() => setStep("RESUMEN")}
    /> : null}
    {step === "VARIANTES" ? <VariantReview
      groups={session.resolucion_identidad?.variantes?.items ?? []}
      draft={workingDraft}
      onDraftChange={persistDraft}
      saving={savingDraft}
      onClose={() => setStep("RESUMEN")}
    /> : null}
    {step === "ARTICULOS" ? <ArticleReview
      draft={workingDraft}
      onDraftChange={persistDraft}
      onLinkIngredientArticle={persistDraftResult}
      saving={savingDraft}
      onClose={() => setStep("RESUMEN")}
    /> : null}
    {step === "MENUS" ? <MenuReview preview={workingPreview} draft={workingDraft} onDraftChange={persistDraft} saving={savingDraft} onClose={() => setStep("RESUMEN")} /> : null}
    {draftError ? <p role="alert">{draftError}</p> : null}
    {step === "PENDIENTES" ? <DraftReview initialDraft={workingDraft} catalogBlocked={counts.externalPending > 0} guided onDraftChange={setWorkingDraft} /> : null}
    {step === "CONFIRMAR" ? <DraftReview initialDraft={workingDraft} canonicalPreview={workingPreview} catalogBlocked={false} confirmationOnly counts={counts} onDraftChange={setWorkingDraft} onConfirmed={onConfirmed} /> : null}
    <details className="technical-import-details">
      <summary>Ver detalles técnicos</summary>
      {analysis ? <AnalysisSummary analysis={analysis} /> : null}
      {workingPreview ? <CatalogPreview preview={workingPreview} /> : null}
      <dl className="detail-grid">
        <dt>Nombre</dt><dd>{documento.nombre}</dd>
        <dt>Clasificación</dt><dd>{documento.clasificacion.tipo}</dd>
        <dt>Confianza</dt><dd>{Math.round(documento.clasificacion.confianza.valor * 100)}%</dd>
        <dt>Ingredientes detectados</dt><dd>{resumen.ingredientes_detectados}</dd>
        <dt>Ingredientes relacionados</dt><dd>{resumen.ingredientes_relacionados}</dd>
      </dl>
      {documento.advertencias.length ? <details><summary>Advertencias · {documento.advertencias.length}</summary><ul>{documento.advertencias.map((item) => <li key={item}>{item}</li>)}</ul></details> : null}
      <h4>Entidades detectadas</h4>
      {recipes.length ? <ul>{recipes.map((recipe) => <li key={recipe.id}>{recipe.name} · {recipe.fields.ingredientes_estructurados?.length ?? 0} ingredientes</li>)}</ul> : <p>Sin recetas estructuradas.</p>}
      <h4>Propuestas · {propuestas.length}</h4>
      <ul>{propuestas.map((proposal) => <li key={proposal.id}>{proposal.titulo || proposalLabel(proposal.tipo)} · {proposal.explicacion}</li>)}</ul>
      {session.limitaciones.length ? <details><summary>Limitaciones · {session.limitaciones.length}</summary><ul>{session.limitaciones.map((item) => <li key={item}>{item}</li>)}</ul></details> : null}
    </details>
  </section>;
}

function importCounts(session: BibliotecaImportSession, draft = session.borrador) {
  const preview = session.preview_global?.contadores;
  const identity = session.resolucion_identidad;
  const recipes = draft.recipes;
  const newIngredientArticleGroups = groupNewIngredientArticles(recipes).length;
  const decidedRecipeIdentity = recipes.some((recipe) => Boolean(recipe.identity_decision));
  const incompleteRecipes = recipes.filter((recipe) => !recipe.procedure.some((step) => step.trim()) || !(Number(recipe.servings ?? recipe.yield_value) > 0)).length;
  const duplicateRecipes = recipes.filter((recipe) => recipe.proposed_action === "REQUIERE_REVISION" || (recipe.duplicate_candidates.length > 0 && recipe.proposed_action !== "REUTILIZAR_EXISTENTE")).length;
  const doubtfulArticles = recipes.reduce((total, recipe) => total + recipe.ingredients.filter((ingredient) => ingredient.relation_status === "REVISAR_COINCIDENCIA").length, 0);
  const relationIssues = session.analisis_restaurante?.dudas.relaciones.length ?? session.resumen.coincidencias_dudosas;
  const originalDuplicates = session.borrador.recipes.filter((recipe) => recipe.proposed_action === "REQUIERE_REVISION" || recipe.duplicate_candidates.length > 0).length;
  const originalDoubtfulArticles = session.borrador.recipes.reduce((total, recipe) => total + recipe.ingredients.filter((ingredient) => ingredient.relation_status === "REVISAR_COINCIDENCIA").length, 0);
  const externalPending = Math.max(0, (preview?.pendientes ?? 0) - originalDuplicates - originalDoubtfulArticles - relationIssues);
  const computedHumanDecisions = duplicateRecipes + doubtfulArticles + relationIssues;
  const identityDecisionIds = new Set(identity?.recetas.grupos.requieren_revision.map((item) => item.id) ?? []);
  const identityDraftRecipes = recipes.filter((recipe) => identityDecisionIds.has(recipe.id));
  const unresolvedIdentityDrafts = identityDraftRecipes.filter((recipe) => recipe.proposed_action === "REQUIERE_REVISION").length;
  const humanDecisions = identity
    ? (identityDraftRecipes.length ? unresolvedIdentityDrafts : identity.recetas.requieren_revision)
    : session.analisis_restaurante
      ? (session.analisis_restaurante.resumen.decisiones_usuario ?? 0)
      : computedHumanDecisions;
  const blockingPending = preview?.pendientes ?? computedHumanDecisions;
  const decisionLabels: Record<string, string> = {
    POSIBLE_VARIANTE: "Posibles variantes",
    MAPPING_AMBIGUO: "Mappings ambiguos",
    REQUIERE_REVISION: "Casos que requieren revisión",
  };
  const rawDecisions = session.analisis_restaurante?.decisiones_usuario ?? [];
  const groupedDecisions = rawDecisions.reduce<Record<string, number>>((groups, decision) => {
    const type = typeof decision.tipo === "string" ? decision.tipo : "OTRAS_DECISIONES";
    groups[type] = (groups[type] ?? 0) + 1;
    return groups;
  }, {});
  const decisionBreakdown = rawDecisions.length === humanDecisions
    ? Object.entries(groupedDecisions).map(([type, count]) => ({
      label: decisionLabels[type] ?? "Otras decisiones",
      count,
    }))
    : [];
  const documentaryQuestions = session.analisis_restaurante?.resumen.decisiones_usuario ?? 0;
  const otherDocumentQuestions = Math.max(0, documentaryQuestions - (identity?.recetas.requieren_revision ?? 0));
  return {
    recipesFound: identity?.recetas.total ?? (session.resumen.recetas_detectadas || session.analisis_restaurante?.resumen.posibles_recetas || recipes.length),
    articlesFound: identity?.articulos.total ?? session.analisis_restaurante?.resumen.posibles_articulos ?? session.resumen.ingredientes_detectados,
    existingRecipes: decidedRecipeIdentity
      ? recipes.filter((recipe) => recipe.identity_decision !== "PENDIENTE" && recipe.proposed_action === "REUTILIZAR_EXISTENTE").length
      : identity?.recetas.ya_canonicas ?? preview?.recetas_reutilizadas ?? recipes.filter((recipe) => recipe.proposed_action === "REUTILIZAR_EXISTENTE").length,
    knownLegacyRecipes: identity?.recetas.ya_conocidas_legacy ?? 0,
    newRecipes: decidedRecipeIdentity
      ? recipes.filter((recipe) => recipe.identity_decision !== "PENDIENTE" && recipe.proposed_action.startsWith("CREAR_")).length
      : identity?.recetas.nuevas_reales ?? preview?.recetas_nuevas ?? recipes.filter((recipe) => recipe.proposed_action.startsWith("CREAR_") && recipe.duplicate_candidates.length === 0).length,
    variantRecipes: recipes.filter((recipe) => recipe.identity_decision === "VARIANTE").length
      || identity?.recetas.posibles_variantes || 0,
    variantGroupsRequiringDecision: draft.variant_decisions?.filter((item) => item.decision === "PENDIENTE").length
      ?? identity?.variantes?.grupos_requieren_decision ?? identity?.recetas.posibles_variantes ?? 0,
    existingArticles: identity?.articulos.ya_existentes ?? preview?.articulos_reutilizados ?? 0,
    newArticles: identity?.articulos.nuevos_reales ?? preview?.articulos_nuevos ?? 0,
    reviewArticles: draft.article_decisions
      ? draft.article_decisions.filter((item) => item.decision === "PENDIENTE").length
      : identity?.articulos.requieren_revision ?? preview?.articulos_requieren_revision ?? 0,
    ignoredArticles: draft.article_decisions?.filter((item) => item.decision === "IGNORAR").length
      ?? preview?.articulos_ignorados ?? 0,
    elaborationArticles: draft.article_decisions?.filter((item) => item.decision === "ES_ELABORACION").length
      ?? preview?.articulos_reclasificados_elaboracion ?? 0,
    newIngredientArticleGroups,
    incompleteRecipes, duplicateRecipes, doubtfulArticles, relationIssues,
    externalPending, humanDecisions, blockingPending, decisionBreakdown, otherDocumentQuestions,
    identityReviewTotal: identity?.recetas.grupos.requieren_revision.length ?? 0,
  };
}

function LegacyUpdatePanel({ session, count, onReanalyze }: {
  session: BibliotecaImportSession; count: number; onReanalyze?: () => Promise<void>;
}) {
  const [preview, setPreview] = useState<{
    preview_token: string;
    entities: Array<{ legacy_source_id: string; nombre: string; ingredientes?: unknown[]; rendimiento?: number | null; unidad_rendimiento?: string | null }>;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const ids = Array.from(new Set(session.resolucion_identidad?.recetas.grupos.ya_conocidas_legacy
    .flatMap((item) => item.legacy_source_ids ?? []) ?? []));
  async function openPreview() {
    setBusy(true); setMessage("");
    try {
      const response = await bibliotecaService.previewLegacyCanonicalization(session.documento.id, ids);
      setPreview({ preview_token: response.preview_token, entities: response.canonicalizaciones });
    } catch (reason) { setMessage((reason as HostAiApiError).message); }
    finally { setBusy(false); }
  }
  async function confirm() {
    if (!preview) return;
    setBusy(true); setMessage("");
    try {
      await bibliotecaService.confirmLegacyCanonicalization(session.documento.id, preview.preview_token);
      await onReanalyze?.();
    } catch (reason) { setMessage((reason as HostAiApiError).message); setBusy(false); }
  }
  return <section className="import-attention" aria-label="Datos que Host AI ya conocía"><section>
    <h4>Host AI ya conocía estos datos</h4>
    <p><strong>{count} elaboraciones ya existen en Host AI.</strong> Están guardadas en el formato anterior y pueden actualizarse al formato actual.</p>
    {!preview ? <button disabled={busy || !ids.length} type="button" onClick={() => void openPreview()}>{busy ? "Preparando vista previa..." : `Actualizar ${count} elaboraciones`}</button>
      : <div className="confirmation-preview" role="dialog" aria-label="Actualizar elaboraciones existentes">
        <h4>Actualizar elaboraciones existentes</h4>
        <p>{preview.entities.length} elaboraciones se actualizarán al formato actual.</p>
        <details open>
          <summary>Ver las {preview.entities.length} elaboraciones</summary>
          <ul>{preview.entities.map((entity) => <li key={entity.legacy_source_id}>
            <strong>{entity.nombre}</strong><br />
            <span>Ya existe en Host AI · actualizar al formato actual</span>
          </li>)}</ul>
        </details>
        <p>Se conservarán ingredientes, cantidades, unidades, rendimiento, artículos relacionados y procedencia histórica.</p>
        <p><strong>No se modificarán:</strong> Stock, lotes, movimientos, recepciones ni compras.</p>
        <p>Los datos documentales que falten se podrán completar después.</p>
        <button disabled={busy} type="button" onClick={() => void confirm()}>{busy ? "Actualizando..." : "Confirmar actualización"}</button>{" "}
        <button disabled={busy} className="secondary-action" type="button" onClick={() => setPreview(null)}>Cancelar</button>
      </div>}
    {message ? <p role="status">{message}</p> : null}
  </section></section>;
}

type ImportCounts = ReturnType<typeof importCounts>;

function ImportMetric({ label, value, detail }: { label: string; value: number; detail?: string }) {
  return <div><strong>{value}</strong><span>{label}{detail ? ` · ${detail}` : ""}</span></div>;
}

function importCompletionRecipeIds(recipes: RecipeDraft[]): string[] {
  return Array.from(new Set(recipes.flatMap((recipe) => {
    const incomplete = !recipe.procedure.some((step) => step.trim())
      || !(Number(recipe.servings ?? recipe.yield_value) > 0);
    if (!incomplete) return [];
    const selected = String(recipe.selected_canonical_recipe_id ?? "").trim();
    if (selected) return [selected];
    if (recipe.proposed_action !== "REUTILIZAR_EXISTENTE") return [];
    const candidates = recipe.duplicate_candidates
      .map((item) => canonicalRecipeId(item))
      .filter((id): id is string => Boolean(id));
    return candidates.length === 1 ? [candidates[0]] : [];
  })));
}

async function downloadRecipeCompletionPackage(recipeIds: string[], importId: string): Promise<string> {
  const response = await bibliotecaService.exportRecipeCompletion(recipeIds, importId);
  const url = URL.createObjectURL(response.blob);
  const link = document.createElement("a");
  try {
    link.href = url;
    link.download = response.filename;
    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();
    URL.revokeObjectURL(url);
  }
  return response.filename;
}

function AttentionGroups({ importId, counts, completionRecipeIds, onReview, onCompleteAi, onCompleteExternal }: { importId: string; counts: ImportCounts; completionRecipeIds: string[]; onReview: () => void; onCompleteAi: () => void; onCompleteExternal: () => void }) {
  const exportingRef = useRef(false);
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState("");
  const [exportError, setExportError] = useState("");

  async function exportExternalPackage() {
    if (exportingRef.current || !completionRecipeIds.length) return;
    exportingRef.current = true;
    setExporting(true);
    setExportMessage("");
    setExportError("");
    try {
      const filename = await downloadRecipeCompletionPackage(completionRecipeIds, importId);
      setExportMessage(`XLSX descargado · ${completionRecipeIds.length} recetas · ${filename}`);
      onCompleteExternal();
    } catch (reason) {
      setExportError((reason as Error).message || "No se pudo preparar el XLSX externo.");
    } finally {
      exportingRef.current = false;
      setExporting(false);
    }
  }

  return <section className="import-attention" aria-label="Revisión de la importación">
    {counts.humanDecisions > 0 ? <section aria-label="Necesito que decidas">
      <h4>Necesito que decidas</h4>
      <p><strong>{counts.humanDecisions}</strong> decisiones necesitan tu revisión.</p>
      {counts.decisionBreakdown.length ? <ul>{counts.decisionBreakdown.map(({ label, count }) => <li key={label}><span>{label}</span><strong>{count}</strong></li>)}</ul> : null}
      <button type="button" onClick={onReview}>Revisar decisiones</button>
    </section> : counts.identityReviewTotal > 0 ? <section aria-label="Decisiones revisadas">
      <h4>Decisiones revisadas</h4>
      <p>Las decisiones de identidad ya estÃ¡n guardadas en el borrador.</p>
      <button type="button" onClick={onReview}>Revisar decisiones</button>
    </section> : null}
    {counts.otherDocumentQuestions > 0 ? <section aria-label="Otras dudas del documento">
      <h4>Otras dudas del documento</h4>
      <p><strong>{counts.otherDocumentQuestions}</strong> {counts.otherDocumentQuestions === 1 ? "duda documental adicional" : "dudas documentales adicionales"}. No forma parte de las decisiones de identidad de recetas.</p>
    </section> : null}
    {counts.incompleteRecipes > 0 ? <section aria-label="Puedes completar después">
      <h4>Puedes completar después</h4>
      <p><strong>{counts.incompleteRecipes} recetas tienen datos pendientes.</strong> Puedes importarlas y completarlas después.</p>
      {completionRecipeIds.length ? <div className="import-primary-actions"><button type="button" onClick={onCompleteAi}>Completar recetas de esta importación con IA · {completionRecipeIds.length}</button><button className="secondary-action" type="button" disabled={exporting} onClick={() => void exportExternalPackage()}>{exporting ? "Preparando XLSX…" : `Completar externamente con XLSX · ${completionRecipeIds.length}`}</button></div> : <p className="muted">Primero importa las recetas nuevas o resuelve su identidad para obtener IDs canónicos.</p>}
      {exportMessage ? <p role="status">{exportMessage}</p> : null}
      {exportError ? <p role="alert">{exportError}</p> : null}
    </section> : null}
  </section>;
}

type RecipeBatch = {
  batch_id: string; estado: string; recipe_ids: string[];
  modo_generacion?: "HOST_AI_API" | "ARCHIVO_EXTERNO";
  validacion_externa?: ExternalValidation;
  archivo_externo?: ExternalFileReceipt | null;
  progreso: { total: number; analizadas: number; exitosas: number; fallidas: number; pendientes: number; con_propuestas: number; necesitan_usuario: number; ya_completas: number; propuestas: number };
  resumen_masivo?: { recetas_procesadas: number; production_ready_provisional: number; production_ready_confirmed: number; criticos_pendientes: number; campos_criticos_individuales?: number; campos_operativos_agrupables?: number; recetas_sin_excepciones_operativas_relevantes?: number; articulos_precios_pendientes: number; baja_confianza: number; errores: number; imposibles_estimar: number; no_aplica: number; escandallos_provisionales?: number; escandallos_parciales?: number; escandallos_sin_coste?: number; datos_reales_modificados: false };
  cola: Array<{ recipe_id: string; estado: "CON_PROPUESTAS" | "NECESITA_USUARIO" | "ERROR_PROVIDER" | "YA_COMPLETA" | "PENDIENTE" | "PROCESANDO" }>;
  resultados: Array<{
    recipe_id: string; nombre: string; estado: string;
    datos_propuestos_ia: Record<string, unknown>;
    datos_propuestos_seguros_masivo: Record<string, unknown>;
    datos_operativos_agrupables?: Record<string, unknown>;
    datos_requieren_revision_individual: Record<string, unknown>;
    propuestas_bloqueadas_revision?: Array<{ campo: string; motivos: string[] }>;
    metadatos_propuestas?: Record<string, RecipeProposalMetadata>;
    completitud?: RecipeCompletionCoverage;
    proyeccion_provisional?: RecipeProvisionalProjection | null;
    estado_operativo?: string;
    excepciones?: { bloqueada: boolean; no_production_ready: boolean; criticos: boolean; baja_confianza: boolean; operativas_agrupables?: boolean; pendientes: boolean; no_aplica: boolean; error: boolean; precios_proveedores: boolean; imposible_estimar: boolean };
    campos_baja_confianza_relevante?: string[];
    campos_pendientes_no_proponibles: string[];
    error?: { code: string; message: string };
    intentos?: number; reintento_disponible?: boolean; backoff_recomendado_segundos?: number;
  }>;
  selecciones: Record<string, Record<string, unknown>>;
  selecciones_agrupadas?: Record<string, Record<string, unknown>>;
  selecciones_individuales: Record<string, Record<string, unknown>>;
  preview?: {
    fingerprint: string; recetas_afectadas: number; cambios_a_aplicar: number;
    items: Array<{
      recipe_id: string; nombre: string; cambios: Record<string, unknown>;
      proposal_source?: RecipeProposalMetadata & { fuente?: string; origen_externo?: string };
      detalle_cambios?: Array<{
        campo: string; valor_actual: unknown; valor_propuesto: unknown;
        procedencia?: RecipeProposalMetadata & { fuente?: string; origen_externo?: string };
        clasificacion: "SELECCION_MASIVA" | "REVISION_AGRUPADA" | "REVISION_INDIVIDUAL";
        sobrescribe: boolean; completa: boolean; estado_campo?: string;
      }>;
      proyeccion_provisional?: RecipeProvisionalProjection | null;
    }>;
  };
  resultado_confirmacion?: { aplicadas: unknown[]; fallidas: unknown[]; recetas_incompletas: number };
};

type RecipeProposalMetadata = {
  origen?: "DOCUMENTO" | "REAL" | "CALCULADO" | "IA_PROPUESTA" | "REFERENCIA_EXTERNA" | "CONFIRMADO" | string;
  confianza?: number | null; motivo?: string; evidencia?: string;
  estado_revision?: string; estado_campo?: "PENDIENTE" | "PROPUESTO" | "NO_APLICA" | "CONFIRMADO" | string;
  fuente?: string; url?: string | null; fecha?: string; modelo?: string;
};

type RecipeCompletionCoverage = {
  documental?: { porcentaje?: number; campos?: number; total?: number };
  propuesta?: { porcentaje?: number; campos?: number; total?: number };
  confirmada?: { porcentaje?: number; campos?: number; total?: number };
  pendientes?: string[]; no_aplica?: string[];
  estados_campos?: Record<string, "PENDIENTE" | "PROPUESTO" | "NO_APLICA" | "CONFIRMADO" | string>;
  production_ready_provisional?: boolean; production_ready_confirmed?: boolean;
  production_ready?: { provisional?: boolean; confirmed?: boolean; campos_requeridos?: string[]; bloqueos_provisionales?: string[]; bloqueos_confirmados?: string[] };
  resolucion_campos?: Record<string, { estado?: string; origen?: string | null; motivo?: string | null }>;
};

type RecipeProvisionalProjection = {
  estado?: string; datos_reales_modificados?: boolean; completitud?: RecipeCompletionCoverage;
  ficha_tecnica?: {
    estado?: string; persistida?: boolean; identificacion?: Record<string, unknown>;
    rendimiento?: number | null; unidad_rendimiento?: string | null; raciones?: number | null;
    tiempos?: Record<string, unknown>; conservacion?: unknown; regeneracion?: unknown; tiempo_descongelacion?: unknown;
    alergenos?: unknown[] | null; campos_pendientes?: string[];
    estados_campos_operativos?: Record<string, RecipeProposalMetadata & { estado?: string; confirmado?: boolean }>;
    produccion?: { indicaciones?: Record<string, unknown> };
  };
  escandallo?: {
    estado_coste?: string; coste_total?: number | null; coste_total_parcial?: number | null; coste_por_racion?: number | null;
    ingredientes_sin_coste?: number; ingredientes_sin_conversion?: number;
    lineas_datos_propuestos?: number; precios_referencia?: number; completitud_coste_porcentaje?: number;
    ingredientes_pendientes_coste?: string[];
    lineas?: Array<{
      nombre_original?: string; nombre_articulo?: string; coste_linea?: number | null;
      precio_unitario?: number | null; unidad_precio?: string | null;
      proveedor_precio?: string | null; precio_provisional?: boolean;
      referencia_precio_externa?: { producto?: string; tienda_referencia?: string; origen?: string };
    }>;
  } | null;
};

type ExternalValidation = {
  filas_recibidas: number; filas_utiles: number; filas_con_propuestas?: number; filas_requieren_revision: number; filas_rechazadas: number;
  campos: { recibidos: number; utiles: number; operativos_agrupables?: number; requieren_revision: number; rechazados: number; bloqueados_criticos: number };
  referencias_precio?: { filas_recibidas: number; referencias_utiles: number; referencias_consolidadas?: number; pendientes: number; rechazadas: number; duplicadas: number; datos_reales_modificados: false };
  filas: Array<{
    fila: number; recipe_id: string; estado: string; errores: string[]; avisos: string[];
    errores_detallados?: string[]; avisos_detallados?: string[];
    rechazos_detallados?: Array<{ campo?: string; estado?: string; motivos?: string[]; mensajes?: string[] }>;
    tiene_propuestas_utiles?: boolean; requiere_revision?: boolean;
  }>;
};

type ExternalFileReceipt = { nombre: string; tamano: number; sha256: string };

function formatRecipePreviewValue(value: unknown): string {
  if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) return "Sin dato";
  if (typeof value === "object" && String((value as { estado?: unknown }).estado ?? "").toUpperCase() === "NO_APLICA") return "NO_APLICA";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function RecipeCoverage({ coverage }: { coverage?: RecipeCompletionCoverage }) {
  if (!coverage) return null;
  const metric = (value?: { porcentaje?: number }) => `${Math.round(Number(value?.porcentaje ?? 0))}%`;
  return <section aria-label="Completitud de receta" className="inline-notice">
    <h5>Completitud operativa</h5>
    <p>Documento: <strong>{metric(coverage.documental)}</strong> · Con propuestas IA: <strong>{metric(coverage.propuesta)}</strong> · Confirmado: <strong>{metric(coverage.confirmada)}</strong></p>
    <p>Production-ready provisional: <strong>{coverage.production_ready_provisional ? "Sí" : "No"}</strong> · Production-ready confirmado: <strong>{coverage.production_ready_confirmed ? "Sí" : "No"}</strong></p>
    {coverage.production_ready?.bloqueos_provisionales?.length ? <p className="muted">Bloqueos para producción provisional: {coverage.production_ready.bloqueos_provisionales.join(", ")}</p> : null}
    {coverage.no_aplica?.length ? <p>Resueltos como NO_APLICA: <strong>{coverage.no_aplica.length}</strong> · {coverage.no_aplica.join(", ")}</p> : null}
    {coverage.pendientes?.length ? <p className="muted">Aún pendientes: {coverage.pendientes.join(", ")}</p> : <p>La proyección cubre todos los campos operativos contemplados.</p>}
  </section>;
}

function OperationalFieldValue({ sheet, coverage, field, value }: {
  sheet?: RecipeProvisionalProjection["ficha_tecnica"];
  coverage?: RecipeCompletionCoverage;
  field: string;
  value: unknown;
}) {
  const state = sheet?.estados_campos_operativos?.[field];
  const isNotApplicable = String(state?.estado ?? coverage?.estados_campos?.[field] ?? "").toUpperCase() === "NO_APLICA";
  if (!isNotApplicable) return <>{formatRecipePreviewValue(value)}</>;
  const source = [state?.origen, state?.fuente].filter(Boolean).join(" · ");
  const reason = state?.motivo || state?.evidencia;
  return <><span>No aplica</span>{state ? <><br /><small className="muted">
    Procedencia: {source || "No informada"} · Confianza: {state.confianza != null ? `${Math.round(state.confianza * 100)}%` : "No informada"} · Motivo: {reason || "No informado"} · Estado de revisión: {state.estado_revision || "No informado"}
  </small></> : null}</>;
}

function ProvisionalRecipeProjection({ projection }: { projection?: RecipeProvisionalProjection | null }) {
  if (!projection) return null;
  const sheet = projection.ficha_tecnica;
  const costing = projection.escandallo;
  const referenceLines = costing?.lineas?.filter((line) => line.precio_provisional || line.referencia_precio_externa) ?? [];
  return <section aria-label="Ficha técnica y escandallo provisionales" className="inline-notice">
    <h5>Ficha técnica provisional</h5>
    <p><strong>Solo lectura.</strong> Las propuestas se proyectan sin modificar la receta canónica.</p>
    <dl className="detail-grid">
      <dt>Rendimiento</dt><dd>{sheet?.rendimiento ?? "Pendiente"} {sheet?.unidad_rendimiento ?? ""}</dd>
      <dt>Raciones</dt><dd>{sheet?.raciones ?? "Pendiente"}</dd>
      <dt>Tiempo total</dt><dd><OperationalFieldValue sheet={sheet} coverage={projection.completitud} field="tiempo_total" value={sheet?.tiempos?.total} /></dd>
      <dt>Tiempo de descongelación</dt><dd><OperationalFieldValue sheet={sheet} coverage={projection.completitud} field="tiempo_descongelacion" value={sheet?.tiempo_descongelacion} /></dd>
      <dt>Conservación</dt><dd><OperationalFieldValue sheet={sheet} coverage={projection.completitud} field="conservacion" value={sheet?.conservacion} /></dd>
      <dt>Regeneración</dt><dd><OperationalFieldValue sheet={sheet} coverage={projection.completitud} field="regeneracion" value={sheet?.regeneracion} /></dd>
      <dt>Producción máxima</dt><dd><OperationalFieldValue sheet={sheet} coverage={projection.completitud} field="produccion_maxima" value={sheet?.produccion?.indicaciones?.produccion_maxima} /></dd>
      <dt>Personal recomendado</dt><dd><OperationalFieldValue sheet={sheet} coverage={projection.completitud} field="personal_recomendado" value={sheet?.produccion?.indicaciones?.personal_recomendado} /></dd>
    </dl>
    <h5>Escandallo provisional</h5>
    {costing ? <>{costing.coste_total == null && costing.coste_total_parcial != null
      ? <p>Estado: <strong>{costing.estado_coste ?? "PARCIAL"}</strong> · Coste total provisional conocido: <strong>{costing.coste_total_parcial}</strong> · Cobertura: <strong>{costing.completitud_coste_porcentaje ?? 0}%</strong> · Coste por ración: <strong>Pendiente hasta completar</strong></p>
      : <p>Estado: <strong>{costing.estado_coste ?? "INCOMPLETO"}</strong> · Coste total: <strong>{costing.coste_total ?? "No calculable"}</strong> · Coste por ración: <strong>{costing.coste_por_racion ?? "No calculable"}</strong></p>}
      <p>{costing.lineas?.length ?? 0} líneas · {costing.lineas_datos_propuestos ?? 0} con datos propuestos · {costing.precios_referencia ?? 0} con precio de referencia.</p>
      {costing.ingredientes_pendientes_coste?.length ? <p>Ingredientes pendientes de coste: <strong>{costing.ingredientes_pendientes_coste.join(", ")}</strong>.</p> : null}
      {referenceLines.length ? <ul aria-label="Referencias externas usadas en el escandallo">{referenceLines.map((line, index) => <li key={`${line.nombre_original ?? line.nombre_articulo ?? "referencia"}-${index}`}><strong>{line.nombre_original ?? line.nombre_articulo ?? "Ingrediente"}</strong>: {line.referencia_precio_externa?.producto ?? "referencia externa"} · proveedor/tienda {line.proveedor_precio ?? line.referencia_precio_externa?.tienda_referencia ?? "no informado"} · {line.precio_unitario ?? "precio no informado"}{line.unidad_precio ? ` €/${line.unidad_precio}` : ""} · REFERENCIA_EXTERNA provisional</li>)}</ul> : null}</> : <p>Estado: <strong>SIN_COSTE</strong>. Aún faltan entradas necesarias.</p>}
    <p className="muted">Procedencias: DOCUMENTO / CALCULADO / IA_PROPUESTA / REFERENCIA_EXTERNA. Nada queda confirmado hasta la acción humana final.</p>
  </section>;
}

function recipeBatchDisplayName(name: string | null | undefined): string {
  return String(name || "").trim() || "Receta sin nombre";
}

function normalizeRecipeSearch(value: string): string {
  return value.trim().toLocaleLowerCase("es").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function recipeMatchesSearch(name: string | null | undefined, recipeId: string, normalizedQuery: string): boolean {
  if (!normalizedQuery) return true;
  return normalizeRecipeSearch(`${name ?? ""} ${recipeId}`).includes(normalizedQuery);
}

function ExternalRecipeCompletion({ importId, recipeIds, initialBatch, onBatchChange, onClose, onCountChange }: { importId: string; recipeIds: string[]; initialBatch?: RecipeBatch; onBatchChange: (batch: RecipeBatch | null) => void; onClose: () => void; onCountChange: (value: number) => void }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [origin, setOrigin] = useState("CHATGPT");
  const [batch, setBatch] = useState<RecipeBatch | null>(initialBatch ?? null);
  const [validation, setValidation] = useState<ExternalValidation | null>(initialBatch?.validacion_externa ?? null);
  const [receipt, setReceipt] = useState<ExternalFileReceipt | null>(initialBatch?.archivo_externo ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function exportPackage() {
    setBusy(true); setError(""); setMessage("");
    try {
      const filename = await downloadRecipeCompletionPackage(recipeIds, importId);
      setMessage(`XLSX descargado · ${recipeIds.length} recetas · ${filename}`);
    } catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); }
  }

  async function importPackage(file: File) {
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await bibliotecaService.importRecipeCompletion(file, recipeIds, importId, origin) as any;
      setValidation(response.validacion as ExternalValidation);
      setReceipt(response.archivo as ExternalFileReceipt);
      const importedBatch = response.batch as RecipeBatch;
      setBatch(importedBatch);
      onBatchChange(importedBatch);
      setMessage(`XLSX completado aceptado · ${importedBatch.progreso.propuestas} propuestas · sin cambios en datos reales`);
    } catch (reason) { setError((reason as Error).message); }
    finally { setBusy(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  const importControls = <>
    <label>Origen de las propuestas externas<select aria-label="Origen de las propuestas externas" value={origin} onChange={(event) => setOrigin(event.target.value)}><option value="CHATGPT">ChatGPT</option><option value="OPENAI_API">OpenAI API</option><option value="OTRO_PROVEEDOR_IA">Otro proveedor IA</option><option value="HUMANO">Completado humano</option><option value="ARCHIVO_EXTERNO">Otro archivo externo</option></select></label>
    <button className="secondary-action" type="button" disabled={busy} onClick={() => fileRef.current?.click()}>{busy ? "Importando…" : "Importar XLSX completado"}</button>
    <input ref={fileRef} hidden type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" aria-label="Seleccionar XLSX completado" onChange={(event) => { const file = event.target.files?.[0]; if (file) void importPackage(file); }} />
    {message ? <p role="status">{message}</p> : null}
    {error ? <p role="alert">{error}</p> : null}
  </>;

  if (batch) return <><section className="catalog-section" aria-label="Importar otro XLSX completado">
    <h4>Actualizar propuestas desde un XLSX completado</h4>
    <p>Selecciona el archivo completado para validarlo y reemplazar el lote de propuestas visible. No se escribirán datos canónicos ni se confirmará ningún cambio.</p>
    {importControls}
  </section><section className="catalog-section" aria-label="Resultado de validación externa">
    <h4>Validación del XLSX externo</h4>
    {receipt ? <p>Archivo procesado: <strong>{receipt.nombre}</strong> · SHA-256 {receipt.sha256.slice(0, 12)}…</p> : null}
    {validation ? <><p role="status">Filas recibidas: {validation.filas_recibidas} · Con propuestas utilizables: {validation.filas_utiles} · Requieren revisión: {validation.filas_requieren_revision} · Rechazadas: {validation.filas_rechazadas}</p><p>Campos seguros: {validation.campos.utiles} · Operativos agrupables: {validation.campos.operativos_agrupables ?? 0} · Críticos individuales: {validation.campos.requieren_revision} · Rechazados: {validation.campos.rechazados} · Contenido crítico bloqueado: {validation.campos.bloqueados_criticos}</p>{validation.referencias_precio ? <p>Referencias externas: {validation.referencias_precio.referencias_utiles} filas válidas · {validation.referencias_precio.referencias_consolidadas ?? validation.referencias_precio.referencias_utiles} identidades reutilizables · {validation.referencias_precio.pendientes} pendientes · {validation.referencias_precio.rechazadas} rechazadas. Son provisionales y nunca modifican precios reales.</p> : null}{validation.campos.recibidos === 0 ? <p role="alert">El archivo seleccionado no contiene valores en las columnas <code>*_propuesto</code>. Comprueba que has elegido el XLSX completado y no la plantilla vacía.</p> : null}{validation.filas.some((row) => row.requiere_revision || row.estado === "RECHAZADA") ? <details><summary>Ver filas que necesitan atención</summary><ul>{validation.filas.filter((row) => row.requiere_revision || row.estado === "RECHAZADA").map((row) => {
      const actionable = [...(row.errores_detallados ?? []), ...(row.avisos_detallados ?? []), ...(row.rechazos_detallados ?? []).flatMap((entry) => entry.mensajes ?? [])];
      const messages = actionable.length ? Array.from(new Set(actionable)) : [...row.errores, ...row.avisos];
      return <li key={`${row.fila}-${row.recipe_id}`}>Fila {row.fila} · {row.recipe_id || "sin ID"} · {row.estado}{messages.length ? <ul>{messages.map((message) => <li key={message}>{message}</li>)}</ul> : null}</li>;
    })}</ul></details> : null}</> : null}
  </section><BulkRecipeCompletion key={batch.batch_id} importId={importId} recipeIds={recipeIds} initialBatch={batch} onBatchChange={onBatchChange} onClose={onClose} onCountChange={onCountChange} /></>;

  return <section className="catalog-section" aria-label="Completar recetas externamente">
    <h4>Completar recetas externamente con XLSX</h4>
    <p>Exporta solo las recetas canónicas incompletas de esta importación. Al volver, Host AI validará el archivo y mostrará una vista previa antes de cualquier escritura.</p>
    <button type="button" disabled={busy || !recipeIds.length} onClick={() => void exportPackage()}>{busy ? "Preparando…" : `Exportar recetas para completar externamente · ${recipeIds.length}`}</button>
    {importControls}
    <button className="secondary-action" type="button" onClick={onClose}>Volver al resumen</button>
  </section>;
}

function BulkRecipeCompletion({ importId, recipeIds, initialBatch, onBatchChange, onClose, onCountChange }: { importId: string; recipeIds: string[]; initialBatch?: RecipeBatch; onBatchChange?: (batch: RecipeBatch | null) => void; onClose: () => void; onCountChange: (value: number) => void }) {
  const [batch, setBatch] = useState<RecipeBatch | null>(initialBatch ?? null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [showPreview, setShowPreview] = useState(Boolean(initialBatch?.preview));
  const [recipeFilter, setRecipeFilter] = useState("TODAS");
  const [recipeSearch, setRecipeSearch] = useState("");
  const cancelRef = useRef(false);
  const confirmRef = useRef(false);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!batch) return;
    if (batch.modo_generacion === "ARCHIVO_EXTERNO") {
      onBatchChange?.(batch);
    }
  }, [batch, onBatchChange]);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    if (initialBatch) return;
    void start();
  }, []);

  async function start() {
    setError(""); setRunning(true); cancelRef.current = false;
    try {
      let current = await bibliotecaService.startRecipeBatch(recipeIds) as unknown as RecipeBatch;
      setBatch(current);
      while (!cancelRef.current && current.progreso.pendientes > 0) {
        current = await bibliotecaService.advanceRecipeBatch(current.batch_id) as unknown as RecipeBatch;
        setBatch(current);
      }
    } catch (reason) { setError((reason as Error).message); }
    finally { setRunning(false); }
  }

  async function selectAndPreview(
    selections: Record<string, Record<string, unknown>>,
    individualSelections?: Record<string, Record<string, unknown>>,
    groupedSelections?: Record<string, Record<string, unknown>>,
  ) {
    if (!batch || selecting) return;
    setSelecting(true); setError("");
    let selectionSaved = false;
    try {
      const body: Record<string, unknown> = { selections };
      if (individualSelections !== undefined) body.individual_selections = individualSelections;
      if (groupedSelections !== undefined) body.grouped_selections = groupedSelections;
      const selected = await bibliotecaService.recipeBatchAction(batch.batch_id, "seleccion", body) as unknown as RecipeBatch;
      selectionSaved = true;
      setShowPreview(false);
      setBatch(selected);
      const selectedFields = [
        ...Object.values(selected.selecciones || {}), ...Object.values(selected.selecciones_agrupadas || {}),
        ...Object.values(selected.selecciones_individuales || {}),
      ].reduce((total, fields) => total + Object.keys(fields).length, 0);
      if (selectedFields > 0) {
        const previewed = await bibliotecaService.recipeBatchAction(selected.batch_id, "preview") as unknown as RecipeBatch;
        setBatch(previewed);
        setShowPreview(true);
      }
    } catch (reason) {
      const message = (reason as Error).message;
      setError(selectionSaved ? `La selección quedó guardada, pero no se pudo generar la vista previa: ${message}` : message);
    } finally { setSelecting(false); }
  }

  async function acceptAll() {
    if (!batch) return;
    const selections = Object.fromEntries(batch.resultados.map((item) => [item.recipe_id, item.datos_propuestos_seguros_masivo]));
    await selectAndPreview(selections, {}, {});
  }

  async function acceptRecipe(recipeId: string) {
    if (!batch) return;
    const item = batch.resultados.find((candidate) => candidate.recipe_id === recipeId);
    if (!item) return;
    await selectAndPreview({ [recipeId]: item.datos_propuestos_seguros_masivo }, {}, {});
  }

  async function selectIndividual(recipeId: string, field: string, value: unknown) {
    if (!batch) return;
    const individualSelections = {
      ...(batch.selecciones_individuales || {}),
      [recipeId]: { ...(batch.selecciones_individuales?.[recipeId] || {}), [field]: value },
    };
    await selectAndPreview(batch.selecciones || {}, individualSelections, batch.selecciones_agrupadas || {});
  }

  async function selectGroupedOperational() {
    if (!batch) return;
    const groupedSelections = Object.fromEntries(
      batch.resultados.map((item) => [item.recipe_id, item.datos_operativos_agrupables || {}]),
    );
    await selectAndPreview(
      batch.selecciones || {}, batch.selecciones_individuales || {}, groupedSelections,
    );
  }

  async function continuePending(current: RecipeBatch) {
    setError(""); setRunning(true); cancelRef.current = false;
    try {
      let nextBatch = current;
      while (!cancelRef.current && nextBatch.progreso.pendientes > 0) {
        nextBatch = await bibliotecaService.advanceRecipeBatch(nextBatch.batch_id) as unknown as RecipeBatch;
        setBatch(nextBatch);
      }
    } catch (reason) { setError((reason as Error).message); }
    finally { setRunning(false); }
  }

  async function retryRecipe(recipeId: string) {
    if (!batch) return;
    setRunning(true);
    try {
      const failedItem = batch.resultados.find((item) => item.recipe_id === recipeId);
      const backoffMs = Math.max(0, failedItem?.backoff_recomendado_segundos || 0) * 1000;
      if (backoffMs) await new Promise((resolve) => window.setTimeout(resolve, backoffMs));
      const retried = await bibliotecaService.recipeBatchAction(batch.batch_id, "reintentar", { recipe_id: recipeId }) as unknown as RecipeBatch;
      setBatch(retried);
      await continuePending(retried);
    } catch (reason) { setError((reason as Error).message); setRunning(false); }
  }

  async function retryFailed() {
    if (!batch) return;
    setRunning(true);
    try {
      const backoffMs = Math.max(0, ...batch.resultados
        .filter((item) => item.estado === "ERROR_PROVIDER" && item.reintento_disponible)
        .map((item) => item.backoff_recomendado_segundos || 0)) * 1000;
      if (backoffMs) await new Promise((resolve) => window.setTimeout(resolve, backoffMs));
      const retried = await bibliotecaService.recipeBatchAction(batch.batch_id, "reintentar-fallidas") as unknown as RecipeBatch;
      setBatch(retried);
      await continuePending(retried);
    } catch (reason) { setError((reason as Error).message); setRunning(false); }
  }

  async function preview() {
    if (!batch || selecting) return;
    setSelecting(true); setError("");
    try {
      setBatch(await bibliotecaService.recipeBatchAction(batch.batch_id, "preview") as unknown as RecipeBatch);
      setShowPreview(true);
    }
    catch (reason) { setError((reason as Error).message); }
    finally { setSelecting(false); }
  }

  async function confirm() {
    if (!batch?.preview || confirmRef.current) return;
    confirmRef.current = true;
    try {
      const result = await bibliotecaService.recipeBatchAction(batch.batch_id, "confirmar", { fingerprint: batch.preview.fingerprint }) as any;
      onCountChange(Math.max(0, recipeIds.length - result.aplicadas.length));
      setBatch({ ...batch, estado: result.estado, resultado_confirmacion: result });
    } catch (reason) { setError((reason as Error).message); }
    finally { confirmRef.current = false; }
  }

  const hasSafeProposals = Boolean(batch?.resultados.some((item) => Object.keys(item.datos_propuestos_seguros_masivo || {}).length));
  const hasRetryableFailures = Boolean(batch?.resultados.some((item) => item.estado === "ERROR_PROVIDER" && item.reintento_disponible));
  const hasSelections = Boolean(batch && [
    ...Object.values(batch.selecciones || {}), ...Object.values(batch.selecciones_agrupadas || {}),
    ...Object.values(batch.selecciones_individuales || {}),
  ].some((fields) => Object.keys(fields).length));
  const safeProposalCount = batch?.resultados.reduce((total, item) => total + Object.keys(item.datos_propuestos_seguros_masivo || {}).length, 0) ?? 0;
  const safeSelectionCount = Object.values(batch?.selecciones || {}).reduce((total, fields) => total + Object.keys(fields).length, 0);
  const groupedProposalCount = batch?.resultados.reduce((total, item) => total + Object.keys(item.datos_operativos_agrupables || {}).length, 0) ?? 0;
  const groupedSelectionCount = Object.values(batch?.selecciones_agrupadas || {}).reduce((total, fields) => total + Object.keys(fields).length, 0);
  const individualSelectionCount = Object.values(batch?.selecciones_individuales || {}).reduce((total, fields) => total + Object.keys(fields).length, 0);
  const allSafeSelected = safeProposalCount > 0 && safeSelectionCount === safeProposalCount;
  const external = batch?.modo_generacion === "ARCHIVO_EXTERNO" || initialBatch?.modo_generacion === "ARCHIVO_EXTERNO";
  const normalizedRecipeSearch = normalizeRecipeSearch(recipeSearch);
  const searchMatchedResults = (batch?.resultados ?? []).filter((item) =>
    recipeMatchesSearch(item.nombre, item.recipe_id, normalizedRecipeSearch));
  const filteredResults = (batch?.resultados ?? []).filter((item) => {
    if (!recipeMatchesSearch(item.nombre, item.recipe_id, normalizedRecipeSearch)) return false;
    if (recipeFilter === "TODAS") return true;
    const keyByFilter: Record<string, keyof NonNullable<typeof item.excepciones>> = {
      BLOQUEADAS: "bloqueada", NO_PRODUCTION_READY: "no_production_ready", CRITICOS: "criticos",
      BAJA_CONFIANZA: "baja_confianza", PENDIENTES: "pendientes", NO_APLICA: "no_aplica",
      ERRORES: "error", PRECIOS_PROVEEDORES: "precios_proveedores", IMPOSIBLES: "imposible_estimar",
    };
    const key = keyByFilter[recipeFilter];
    return key ? Boolean(item.excepciones?.[key]) : true;
  });
  const filteredPreviewItems = (batch?.preview?.items ?? []).filter((item) =>
    recipeMatchesSearch(item.nombre, item.recipe_id, normalizedRecipeSearch));
  const visibleRecipeCount = showPreview && batch?.preview ? filteredPreviewItems.length : filteredResults.length;

  return <section className="catalog-section" aria-label={external ? "Revisar propuestas externas de recetas" : "Completar recetas con IA"}>
    <h4>{external ? "Revisar propuestas externas" : "Completar recetas con IA"}</h4>
    {!batch ? <p role="status">Releyendo Biblioteca y preparando la cola…</p> : <>
      <p role="status">Analizadas: {batch.progreso.analizadas} / {batch.progreso.total} · Propuestas generadas: {batch.progreso.propuestas}</p>
      {batch.resumen_masivo ? <section aria-label="Resumen masivo production-ready" className="inline-notice"><h5>Resumen del lote y excepciones</h5><dl className="detail-grid"><dt>Recetas procesadas</dt><dd>{batch.resumen_masivo.recetas_procesadas}</dd><dt>Production-ready provisional</dt><dd>{batch.resumen_masivo.production_ready_provisional}</dd><dt>Production-ready confirmado</dt><dd>{batch.resumen_masivo.production_ready_confirmed}</dd><dt>Sin excepciones operativas relevantes</dt><dd>{batch.resumen_masivo.recetas_sin_excepciones_operativas_relevantes ?? 0}</dd><dt>Campos operativos agrupables</dt><dd>{batch.resumen_masivo.campos_operativos_agrupables ?? 0}</dd><dt>Campos críticos individuales</dt><dd>{batch.resumen_masivo.campos_criticos_individuales ?? 0}</dd><dt>Recetas con críticos pendientes</dt><dd>{batch.resumen_masivo.criticos_pendientes}</dd><dt>Baja confianza relevante</dt><dd>{batch.resumen_masivo.baja_confianza}</dd><dt>Artículos/precios pendientes</dt><dd>{batch.resumen_masivo.articulos_precios_pendientes}</dd><dt>Escandallos provisionales</dt><dd>{batch.resumen_masivo.escandallos_provisionales ?? 0}</dd><dt>Escandallos parciales</dt><dd>{batch.resumen_masivo.escandallos_parciales ?? 0}</dd><dt>Escandallos sin coste</dt><dd>{batch.resumen_masivo.escandallos_sin_coste ?? 0}</dd><dt>Errores</dt><dd>{batch.resumen_masivo.errores}</dd><dt>Imposibles de estimar</dt><dd>{batch.resumen_masivo.imposibles_estimar}</dd><dt>Con NO_APLICA</dt><dd>{batch.resumen_masivo.no_aplica}</dd></dl><p>Ningún dato real ha sido modificado.</p></section> : null}
      {hasSelections ? <p role="status">{safeSelectionCount} propuestas seguras seleccionadas{groupedSelectionCount ? ` · ${groupedSelectionCount} operativas agrupadas` : ""}{individualSelectionCount ? ` · ${individualSelectionCount} críticas validadas individualmente` : ""}. Aún no se ha escrito ningún dato.</p> : null}
      <div className="recipe-review-toolbar" role="search" aria-label="Buscar recetas en revisión">
        <label className="recipe-review-search">Buscar receta por nombre o ID
          <input value={recipeSearch} placeholder="Buscar receta por nombre o ID…" onChange={(event) => setRecipeSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") event.preventDefault(); if (event.key === "Escape") { event.preventDefault(); setRecipeSearch(""); } }} />
        </label>
        {!showPreview ? <label>Filtrar recetas<select aria-label="Filtrar recetas del lote" value={recipeFilter} onChange={(event) => setRecipeFilter(event.target.value)}><option value="TODAS">Todas</option><option value="BLOQUEADAS">Solo bloqueadas</option><option value="NO_PRODUCTION_READY">Solo no production-ready</option><option value="CRITICOS">Solo críticos</option><option value="BAJA_CONFIANZA">Solo baja confianza</option><option value="PENDIENTES">Solo pendientes</option><option value="NO_APLICA">Solo NO_APLICA</option><option value="ERRORES">Solo errores</option><option value="PRECIOS_PROVEEDORES">Solo precios/proveedores pendientes</option><option value="IMPOSIBLES">Solo imposibles de estimar</option></select></label> : null}
        <button type="button" className="secondary-action" disabled={!recipeSearch} onClick={() => setRecipeSearch("")}>Limpiar</button>
        <p className="muted" aria-live="polite">Mostrando {visibleRecipeCount} de {batch.resultados.length} recetas.</p>
      </div>
      {!showPreview ? <>
      <p>Las propuestas seguras y operativas pueden seleccionarse por grupos para una única vista previa. Esto no las confirma. Los campos sanitarios, alérgenos, ingredientes/artículos y demás críticos reales siguen exigiendo validación individual explícita.</p>
      <dl className="detail-grid"><dt>Exitosas</dt><dd>{batch.progreso.exitosas}</dd><dt>Fallidas</dt><dd>{batch.progreso.fallidas}</dd><dt>Pendientes</dt><dd>{batch.progreso.pendientes}</dd><dt>Con propuestas IA</dt><dd>{batch.progreso.con_propuestas}</dd><dt>Necesitan usuario</dt><dd>{batch.progreso.necesitan_usuario}</dd><dt>Ya completas al releer</dt><dd>{batch.progreso.ya_completas}</dd></dl>
      {!external && running ? <button type="button" onClick={() => { cancelRef.current = true; void bibliotecaService.recipeBatchAction(batch.batch_id, "cancelar"); }}>Cancelar generación</button> : null}
      {!external && !running && batch.progreso.pendientes > 0 && batch.estado !== "CANCELADO" ? <button type="button" onClick={() => void continuePending(batch)}>Reanudar pendientes</button> : null}
      {!external && !running && hasRetryableFailures ? <button type="button" onClick={() => void retryFailed()}>Reintentar todas las fallidas</button> : null}
      {!filteredResults.length && normalizedRecipeSearch && !searchMatchedResults.length ? <p role="status">No se encontraron recetas con ese nombre o ID.</p> : null}
      {filteredResults.map((item) => <details key={item.recipe_id} data-recipe-view="review" data-recipe-id={item.recipe_id}>
        <summary>{recipeBatchDisplayName(item.nombre)} · {item.estado_operativo ?? item.estado} · {Object.keys(item.datos_propuestos_ia || {}).length} propuestas · {item.recipe_id}</summary>
        <p className="muted">{item.recipe_id}</p>
        <RecipeCoverage coverage={item.completitud} />
        <ProvisionalRecipeProjection projection={item.proyeccion_provisional} />
        {item.estado === "ERROR_PROVIDER" ? <><p role="alert">{item.error?.message || "Error del proveedor IA"}</p>{item.reintento_disponible ? (!running ? <button type="button" onClick={() => void retryRecipe(item.recipe_id)}>Reintentar esta receta</button> : null) : <p>Se alcanzó el límite de reintentos.</p>}</> : null}
        {Object.keys(item.datos_propuestos_seguros_masivo || {}).length ? <><h5>Propuestas culinarias aptas para selección masiva</h5><ul>{Object.entries(item.datos_propuestos_seguros_masivo).map(([field, value]) => { const metadata = item.metadatos_propuestas?.[field]; return <li key={field}><strong>{field}</strong>: {formatRecipePreviewValue(value)} <span className="badge">{metadata?.origen ?? "IA_PROPUESTA"}</span>{metadata?.confianza != null ? ` · confianza ${Math.round(metadata.confianza * 100)}%` : ""}</li>; })}</ul>{Object.entries(item.datos_propuestos_seguros_masivo).every(([field, value]) => batch.selecciones?.[item.recipe_id]?.[field] === value) ? (individualSelectionCount > 0 || safeSelectionCount > Object.keys(item.datos_propuestos_seguros_masivo).length ? <button type="button" disabled={selecting} onClick={() => void acceptRecipe(item.recipe_id)}>Usar solo propuestas seguras de esta receta</button> : <p>Propuestas seguras de esta receta seleccionadas.</p>) : <button type="button" disabled={selecting} onClick={() => void acceptRecipe(item.recipe_id)}>Aceptar propuestas seguras de esta receta</button>}</> : null}
        {Object.keys(item.datos_operativos_agrupables || {}).length ? <details><summary>{Object.keys(item.datos_operativos_agrupables || {}).length} propuestas operativas provisionales agrupables</summary><p className="muted">Pueden incorporarse juntas a la vista previa; conservan procedencia y confianza y no quedan confirmadas por seleccionarlas.</p><ul>{Object.entries(item.datos_operativos_agrupables || {}).map(([field, value]) => { const metadata = item.metadatos_propuestas?.[field]; return <li key={field}><strong>{field}</strong>: {formatRecipePreviewValue(value)}{metadata?.confianza != null ? ` · confianza ${Math.round(metadata.confianza * 100)}%` : ""}</li>; })}</ul></details> : null}
        {Object.keys(item.datos_requieren_revision_individual || {}).length ? <><h5>Requieren validación humana individual</h5><p className="muted">Solo quedan aquí sanitario, alérgenos, ingredientes/artículos y otros críticos reales. Participan provisionalmente en la ficha, pero quedan fuera de confirmación hasta validarlos uno a uno.</p><ul>{Object.entries(item.datos_requieren_revision_individual).map(([field, value]) => { const metadata = item.metadatos_propuestas?.[field]; return <li key={field}><strong>{field}</strong>: {formatRecipePreviewValue(value)} <span className="badge">{metadata?.estado_campo ?? metadata?.origen ?? "PROPUESTO"}</span>{metadata?.confianza != null ? ` · confianza ${Math.round(metadata.confianza * 100)}%` : ""}{metadata?.motivo ? ` · ${metadata.motivo}` : ""} {batch.selecciones_individuales?.[item.recipe_id]?.[field] === value ? <span>Seleccionado para confirmación.</span> : <button type="button" disabled={selecting} onClick={() => void selectIndividual(item.recipe_id, field, value)}>Validar y seleccionar este campo</button>}</li>; })}</ul></> : null}
        {item.propuestas_bloqueadas_revision?.length ? <p>Contenido crítico bloqueado: {item.propuestas_bloqueadas_revision.map((entry) => entry.campo).join(", ")}.</p> : null}
        {item.campos_pendientes_no_proponibles?.length ? <p>Necesita usuario: {item.campos_pendientes_no_proponibles.join(", ")}</p> : null}
      </details>)}
      {!running && hasSafeProposals && (!allSafeSelected || individualSelectionCount > 0 || groupedSelectionCount > 0) ? <button type="button" disabled={selecting} onClick={() => void acceptAll()}>{selecting ? "Preparando vista previa…" : allSafeSelected ? "Usar solo propuestas seguras de todas" : "Aceptar propuestas seguras de todas"}</button> : null}
      {allSafeSelected && individualSelectionCount === 0 && groupedSelectionCount === 0 ? <p>Las propuestas seguras disponibles ya están seleccionadas.</p> : null}
      {!running && groupedProposalCount > groupedSelectionCount ? <button type="button" disabled={selecting} onClick={() => void selectGroupedOperational()}>{selecting ? "Preparando vista previa…" : `Revisar y seleccionar operativas provisionales · ${groupedProposalCount}`}</button> : null}
      {hasSelections && !batch.preview ? <button type="button" disabled={selecting} onClick={() => void preview()}>{selecting ? "Preparando vista previa…" : "Revisar cambios antes de guardar"}</button> : null}
      {batch.preview ? <button type="button" onClick={() => setShowPreview(true)}>Volver a vista previa</button> : null}
      </> : null}
      {showPreview && batch.preview ? <section aria-label="Preview consolidado"><h5>Vista previa de cambios</h5><p>Recetas afectadas: {batch.preview.recetas_afectadas} · Cambios a aplicar: {batch.preview.cambios_a_aplicar}</p><p>Aún no se ha escrito ningún dato. Los campos críticos no seleccionados quedan fuera.</p>{!filteredPreviewItems.length ? <p role="status">No se encontraron recetas con ese nombre o ID.</p> : null}{filteredPreviewItems.map((item) => <article key={item.recipe_id} data-recipe-view="preview" data-recipe-id={item.recipe_id}><h6>{recipeBatchDisplayName(item.nombre)}</h6><p className="muted">{item.recipe_id}</p><ProvisionalRecipeProjection projection={item.proyeccion_provisional} /><table><thead><tr><th>Campo</th><th>Valor actual</th><th>Valor propuesto</th><th>Estado</th><th>Procedencia</th><th>Confianza</th><th>Motivo</th><th>Clasificación</th><th>Acción</th></tr></thead><tbody>{(item.detalle_cambios || Object.entries(item.cambios).map(([campo, valor]) => ({ campo, valor_actual: undefined, valor_propuesto: valor, procedencia: item.proposal_source, clasificacion: "SELECCION_MASIVA" as const, sobrescribe: false, completa: true }))).map((change) => <tr key={change.campo}><td>{change.campo}</td><td>{formatRecipePreviewValue(change.valor_actual)}</td><td>{formatRecipePreviewValue(change.valor_propuesto)}</td><td>{change.procedencia?.estado_campo ?? (formatRecipePreviewValue(change.valor_propuesto) === "NO_APLICA" ? "NO_APLICA" : "PROPUESTO")}</td><td>{[change.procedencia?.origen, change.procedencia?.fuente, change.procedencia?.origen_externo].filter(Boolean).join(" · ") || "No informada"}</td><td>{change.procedencia?.confianza != null ? `${Math.round(change.procedencia.confianza * 100)}%` : "No informada"}</td><td>{change.procedencia?.motivo || "No informado"}</td><td>{change.clasificacion === "REVISION_INDIVIDUAL" ? "Revisión individual" : change.clasificacion === "REVISION_AGRUPADA" ? "Revisión agrupada" : "Selección masiva"}</td><td>{change.sobrescribe ? "Sobrescribe" : change.completa ? "Completa" : "Actualiza"}</td></tr>)}</tbody></table></article>)}<button type="button" className="secondary-action" onClick={() => setShowPreview(false)}>Volver a propuestas</button><button type="button" onClick={() => void confirm()}>Confirmar cambios</button></section> : null}
      {batch.resultado_confirmacion ? <p role="status">Completado: {batch.resultado_confirmacion.aplicadas.length} recetas actualizadas; {batch.resultado_confirmacion.fallidas.length} fallidas.</p> : null}
    </>}
    {error ? <p role="alert">{error}</p> : null}
    <button className="secondary-action" type="button" onClick={onClose}>Volver al resumen</button>
  </section>;
}

function articleReviewGroup(item: CatalogArticleDraft) {
  const semantic = `${item.tipo_semantico ?? ""} ${item.tipo_entidad ?? ""}`.toUpperCase();
  if (/ELABORACION|SUBELABORACION|PRODUCTO_VENDIBLE|MENU|CONTEXTO|PLATO|APERITIVO/.test(semantic)) return "No es un artículo de compra";
  if (/receta/i.test(item.motivo ?? "")) return "Colisión artículo ↔ receta/elaboración";
  if ((item.candidatos?.length ?? 0) > 1) return "Artículo comprado con match ambiguo";
  return "Otros casos pendientes";
}

type MenuPreviewItem = {
  id?: string; nombre: string; nombre_importado?: string; accion: string; menu_id?: string | null; tipo?: string;
  origen?: Record<string, unknown>; motivos?: string[];
  lineas?: Array<{ indice?: number; nombre: string; seccion: string; estado: string; tipo_referencia?: string | null; referencia?: string | null; origen?: Record<string, unknown> }>;
};

function MenuReview({ preview, draft, onDraftChange, saving, onClose }: {
  preview: BibliotecaImportSession["preview_global"];
  draft: ImportDraft;
  onDraftChange: (draft: ImportDraft) => void;
  saving: boolean;
  onClose: () => void;
}) {
  const pending = ((preview?.menus?.pendientes ?? []) as MenuPreviewItem[]);
  const decisions = draft.menu_decisions ?? [];
  function updateMenu(menu: MenuPreviewItem, changes: Partial<MenuDraftDecision>) {
    const id = String(menu.id ?? "");
    const current = decisions.find((item) => item.menu_draft_id === id) ?? {
      menu_draft_id: id, decision: "PENDIENTE" as const, nombre_final: menu.nombre, line_decisions: [],
    };
    onDraftChange({ ...draft, menu_decisions: [...decisions.filter((item) => item.menu_draft_id !== id), { ...current, nombre_final: current.nombre_final || menu.nombre, ...changes }] });
  }
  function updateLine(menu: MenuPreviewItem, lineIndex: number, line: MenuDraftDecision["line_decisions"][number]) {
    const id = String(menu.id ?? "");
    const current = decisions.find((item) => item.menu_draft_id === id) ?? {
      menu_draft_id: id, decision: "PENDIENTE" as const, nombre_final: menu.nombre, line_decisions: [],
    };
    updateMenu(menu, { decision: "PENDIENTE", line_decisions: [...current.line_decisions.filter((item) => item.line_index !== lineIndex), line] });
  }
  return <section className="draft-review" aria-label="Revisar menús">
    <p className="eyebrow">Revisión humana</p><h4>Revisar menús · {pending.length}</h4>
    <p>Solo se muestran menús pendientes del borrador actual. Los menús ya existentes quedan fuera de esta revisión.</p>
    {pending.map((menu) => {
      const origin = menu.origen ?? {};
      return <article className="import-review-card" key={menu.id ?? menu.nombre}>
        <p><strong>NOMBRE IMPORTADO:</strong> {menu.nombre_importado ?? menu.nombre}</p>
        <MenuFinalNameEditor
          key={`${menu.id}-${decisions.find((item) => item.menu_draft_id === menu.id)?.nombre_final ?? menu.nombre}`}
          initialValue={decisions.find((item) => item.menu_draft_id === menu.id)?.nombre_final ?? menu.nombre}
          disabled={saving}
          onSave={(nombre_final) => updateMenu(menu, { nombre_final })}
        />
        <p><strong>IDENTIFICADOR DRAFT:</strong> {menu.id}</p>
        <p><strong>ORIGEN / HOJA:</strong> {String(origin.sheet ?? origin.hoja ?? origin.source_filename ?? origin.archivo ?? "No informado")}</p>
        <p><strong>ESTADO:</strong> PENDIENTE</p>
        {menu.motivos?.length ? <ul>{menu.motivos.map((reason) => <li key={reason}>{reason}</li>)}</ul> : null}
        <h5>Líneas</h5>
        <ul>{(menu.lineas ?? []).map((line, offset) => {
          const index = Number(line.indice ?? offset + 1);
          return <li key={`${menu.id}-${index}`}>
            <strong>{line.nombre || "Línea sin texto"}</strong> · {line.seccion} · {line.estado}
            {line.referencia ? <> · {line.tipo_referencia}: <code>{line.referencia}</code></> : null}
            {line.estado === "PENDIENTE" ? <MenuLineDecisionEditor index={index} disabled={saving} onChange={(choice) => updateLine(menu, index, choice)} /> : null}
          </li>;
        })}</ul>
        <div className="import-primary-actions">
          <button type="button" disabled={saving} onClick={() => updateMenu(menu, { decision: "CREAR_MENU" })}>Confirmar menú resuelto</button>
          <button type="button" className="secondary-action" disabled={saving} onClick={() => updateMenu(menu, { decision: "PENDIENTE" })}>Dejar menú pendiente</button>
          <button type="button" className="secondary-action" disabled={saving} onClick={() => updateMenu(menu, { decision: "EXCLUIR_MENU_DOCUMENTAL" })}>Excluir menú documental</button>
        </div>
      </article>;
    })}
    <button type="button" className="secondary-action" onClick={onClose}>Volver al resumen</button>
  </section>;
}

function MenuFinalNameEditor({ initialValue, disabled, onSave }: { initialValue: string; disabled: boolean; onSave: (value: string) => void }) {
  const [value, setValue] = useState(initialValue);
  return <label>NOMBRE FINAL:
    <input aria-label="Nombre final del menú" disabled={disabled} value={value} onChange={(event) => setValue(event.target.value)} onBlur={() => { const finalValue = value.trim(); if (finalValue && finalValue !== initialValue) onSave(finalValue); }} />
  </label>;
}

function MenuLineDecisionEditor({ index, disabled, onChange }: { index: number; disabled: boolean; onChange: (decision: MenuDraftDecision["line_decisions"][number]) => void }) {
  const [reference, setReference] = useState("");
  const [referenceType, setReferenceType] = useState<"RECETA" | "PRODUCTO">("RECETA");
  return <div className="inline-actions">
    <MenuCanonicalRecipeSearch disabled={disabled} onSelect={(recipeId) => onChange({ line_index: index, decision: "USAR_REFERENCIA", tipo_referencia: "RECETA", referencia: recipeId })} />
    <select aria-label={`Tipo canónico línea ${index}`} value={referenceType} onChange={(event) => setReferenceType(event.target.value as "RECETA" | "PRODUCTO")}><option value="RECETA">Receta</option><option value="PRODUCTO">Artículo</option></select>
    <input aria-label={`ID canónico línea ${index}`} placeholder="REC601-… o ART…" value={reference} onChange={(event) => setReference(event.target.value)} />
    <button type="button" disabled={disabled || !reference.trim()} onClick={() => onChange({ line_index: index, decision: "USAR_REFERENCIA", tipo_referencia: referenceType, referencia: reference.trim() })}>Usar referencia canónica</button>
    <button type="button" className="secondary-action" disabled={disabled} onClick={() => onChange({ line_index: index, decision: "EXCLUIR" })}>Excluir línea documental</button>
  </div>;
}

function MenuCanonicalRecipeSearch({ disabled, onSelect }: { disabled: boolean; onSelect: (recipeId: string) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ElaboracionDetalle[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  async function search() {
    const term = query.trim();
    if (!term) return;
    setSearching(true); setSearchError("");
    try {
      const response = await bibliotecaService.list({ q: term, page_size: 100, orden: "nombre" });
      const summaries = response.elaboraciones.items;
      const canonicalSummaries = summaries.filter((item) => /^REC601-\d+$/.test(item.id));
      const details = await Promise.all(canonicalSummaries.map(async (item) => (await bibliotecaService.detail(item.id)).elaboracion));
      setResults(details);
    } catch (reason) {
      setResults([]);
      setSearchError((reason as HostAiApiError).message || "No se pudo consultar la Biblioteca canónica.");
    } finally { setSearching(false); }
  }
  return <section className="menu-canonical-search" aria-label="Buscar receta canónica">
    <label>Buscar receta existente
      <input aria-label="Buscar receta canónica por nombre, alias o recipe_id" disabled={disabled} value={query} onChange={(event) => setQuery(event.target.value)} />
    </label>
    <button type="button" className="secondary-action" disabled={disabled || searching || !query.trim()} onClick={() => void search()}>{searching ? "Buscando..." : "Buscar en Biblioteca"}</button>
    {searchError ? <p role="alert">{searchError}</p> : null}
    {!searching && query.trim() && !results.length && !searchError ? <p className="muted">Sin coincidencias canónicas.</p> : null}
    {results.length ? <ul>{results.map((recipe) => {
      const provenance = (recipe.historial_procedencia?.[0] ?? recipe.procedencia_campos?.nombre ?? {}) as Record<string, unknown>;
      return <li key={recipe.id}>
        <strong>{recipe.nombre}</strong> · <code>{recipe.id}</code> · {recipe.estado}<br />
        {recipe.receta.ingredientes.length} ingredientes · rendimiento {recipe.rendimiento ?? recipe.receta.rendimiento ?? "no informado"} · origen {String(provenance.origen ?? provenance.tipo ?? provenance.fuente ?? "no informado")}
        <button type="button" disabled={disabled} onClick={() => onSelect(recipe.id)}>Elegir {recipe.id}</button>
      </li>;
    })}</ul> : null}
  </section>;
}

type NewIngredientArticleGroup = {
  key: string;
  name: string;
  normalizedName: string;
  unit?: string | null;
  occurrences: Array<{ recipeId: string; recipeTitle: string; ingredientId: string }>;
};

function ingredientUnitGroup(unit?: string | null): string {
  const normalized = String(unit || "").toLowerCase();
  if (["kg", "g"].includes(normalized)) return "masa";
  if (["l", "ml", "cl"].includes(normalized)) return "volumen";
  return normalized || "sin-unidad";
}

function groupNewIngredientArticles(recipes: RecipeDraft[]): NewIngredientArticleGroup[] {
  const groups = new Map<string, NewIngredientArticleGroup>();
  for (const recipe of recipes) {
    for (const ingredient of recipe.ingredients) {
      if (ingredient.article_id || !["SIN_RELACIONAR", "CREAR_ARTICULO_PROPUESTO"].includes(ingredient.relation_status)) continue;
      const normalizedName = ingredient.normalized_name || ingredient.name_raw.trim().toLocaleLowerCase("es");
      if (!normalizedName) continue;
      const key = `${normalizedName}|${ingredientUnitGroup(ingredient.unit)}`;
      const group = groups.get(key) ?? {
        key, name: ingredient.name_raw.trim(), normalizedName, unit: ingredient.unit,
        occurrences: [],
      };
      group.occurrences.push({ recipeId: recipe.id, recipeTitle: recipe.title, ingredientId: ingredient.id });
      groups.set(key, group);
    }
  }
  return Array.from(groups.values()).sort((left, right) => left.name.localeCompare(right.name, "es"));
}

function linkIngredientGroup(draft: ImportDraft, group: NewIngredientArticleGroup, articleId: string): ImportDraft {
  const occurrenceIds = new Set(group.occurrences.map((item) => `${item.recipeId}|${item.ingredientId}`));
  return {
    ...draft,
    recipes: draft.recipes.map((recipe) => ({
      ...recipe,
      ingredients: recipe.ingredients.map((ingredient) => occurrenceIds.has(`${recipe.id}|${ingredient.id}`)
        ? { ...ingredient, article_id: articleId, relation_status: "RELACIONADO" as const }
        : ingredient),
    })),
  };
}

function suggestedArticleCode(group: NewIngredientArticleGroup): string {
  const slug = group.normalizedName.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toUpperCase().slice(0, 26) || "NUEVO";
  let hash = 2166136261;
  for (const character of group.key) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  return `ART-${slug}-${(hash >>> 0).toString(36).toUpperCase().slice(0, 6)}`;
}

function NewIngredientArticleCard({ group, draft, saving, onLink }: {
  group: NewIngredientArticleGroup;
  draft: ImportDraft;
  saving: boolean;
  onLink: (draft: ImportDraft) => Promise<boolean>;
}) {
  const [creating, setCreating] = useState(false);
  const [checkingExisting, setCheckingExisting] = useState(false);
  const [createdId, setCreatedId] = useState("");
  const [message, setMessage] = useState("");
  const initial = useMemo(() => ({
    nombre: group.name,
    codigo: suggestedArticleCode(group),
    unidad_base: group.unit || "",
    unidad_compra: group.unit || "",
    estado: "PENDIENTE_DE_COMPLETAR",
    observaciones: `Alta autorizada desde importación; usado inicialmente en ${group.occurrences.length} receta(s).`,
  }), [group.key]);
  async function link(articleId: string) {
    setMessage("");
    const saved = await onLink(linkIngredientGroup(draft, group, articleId));
    if (saved) {
      setCreating(false);
      setMessage(`Artículo ${articleId} creado y vinculado a ${group.occurrences.length} apariciones.`);
    } else {
      setCreatedId(articleId);
      setMessage(`El artículo ${articleId} se creó, pero el enlace al borrador sigue pendiente. Puedes reintentarlo sin repetir el alta.`);
    }
  }
  async function prepareCreate() {
    setCheckingExisting(true);
    setMessage("");
    try {
      const result = await articulosService.list({ q: initial.codigo, page_size: 20 });
      const existing = result.catalogo.items.find((item) =>
        String(item.codigo || "").trim().toLocaleUpperCase("es") === initial.codigo.toLocaleUpperCase("es")
        && String(item.nombre || "").trim().localeCompare(group.name.trim(), undefined, { sensitivity: "base" }) === 0
      );
      if (existing) {
        const identity = String(existing.id || existing.codigo || "");
        setCreatedId(identity);
        setMessage(`El artículo ${identity} ya existe con el código esperado. Puedes enlazarlo sin repetir el alta.`);
      } else {
        setCreating(true);
      }
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "No se pudo comprobar si el artículo ya existe.");
    } finally {
      setCheckingExisting(false);
    }
  }
  return <article className="draft-warning">
    <h5>{group.name}</h5>
    <p>{group.occurrences.length} apariciones · {Array.from(new Set(group.occurrences.map((item) => item.recipeTitle))).join(", ")} · unidad {group.unit || "pendiente"}</p>
    <p>No existe un artículo canónico compatible. El alta no incluirá precio ni proveedor reales.</p>
    {!creating && !createdId ? <button type="button" disabled={saving || checkingExisting} onClick={() => void prepareCreate()}>{checkingExisting ? "Comprobando artículo existente…" : "Preparar alta autorizada"}</button> : null}
    {creating ? <SafeCatalogWritePanel
      domain="ARTICULO"
      operation="CREAR"
      initial={initial}
      culinaryContext={{ ingrediente_original: group.name, unidad_receta: group.unit || "", uso_culinario: group.occurrences.map((item) => item.recipeTitle).join(", ") }}
      onCancel={() => setCreating(false)}
      onConfirmed={(record) => {
        const identity = String(record.id || record.codigo || "");
        if (!identity) setMessage("El alta no devolvió una identidad canónica verificable.");
        else void link(identity);
      }}
    /> : null}
    {createdId ? <button type="button" disabled={saving} onClick={() => void link(createdId)}>Enlazar artículo existente {createdId}</button> : null}
    {message ? <p role="status">{message}</p> : null}
  </article>;
}

function ArticleReview({ draft, onDraftChange, onLinkIngredientArticle, saving, onClose }: {
  draft: ImportDraft;
  onDraftChange: (draft: ImportDraft) => void | Promise<void>;
  onLinkIngredientArticle: (draft: ImportDraft) => Promise<boolean>;
  saving: boolean;
  onClose: () => void;
}) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedIgnoredIds, setSelectedIgnoredIds] = useState<string[]>([]);
  const [selectedElaborationIds, setSelectedElaborationIds] = useState<string[]>([]);
  const articles = draft.catalogo?.articulos ?? [];
  const decisions = new Map((draft.article_decisions ?? []).map((item) => [item.article_draft_id, item]));
  const reviewArticles = articles.filter((item) => decisions.has(item.id));
  const activeArticles = reviewArticles.filter((item) => decisions.get(item.id)?.decision === "PENDIENTE");
  const ignoredArticles = reviewArticles.filter((item) => decisions.get(item.id)?.decision === "IGNORAR");
  const elaborationArticles = reviewArticles.filter((item) => decisions.get(item.id)?.decision === "ES_ELABORACION");
  const newIngredientGroups = groupNewIngredientArticles(draft.recipes);
  const groups = Object.entries(activeArticles.reduce<Record<string, CatalogArticleDraft[]>>((result, item) => {
    (result[articleReviewGroup(item)] ??= []).push(item);
    return result;
  }, {}));
  function decide(articleIds: string[], decision: ArticleDraftDecision["decision"], articleId?: string | null) {
    const selected = new Set(articleIds);
    void onDraftChange({
      ...draft,
      article_decisions: (draft.article_decisions ?? []).map((item) => selected.has(item.article_draft_id)
        ? { ...item, decision, article_id: articleId ?? null }
        : item),
    });
  }
  const pending = (draft.article_decisions ?? []).filter((item) => item.decision === "PENDIENTE").length;
  const visibleIds = activeArticles.map((item) => item.id);
  const activeSelectedIds = selectedIds.filter((id) => visibleIds.includes(id));
  const ignoredSelectedIds = selectedIgnoredIds.filter((id) => ignoredArticles.some((item) => item.id === id));
  const elaborationSelectedIds = selectedElaborationIds.filter((id) => elaborationArticles.some((item) => item.id === id));
  function toggleSelected(id: string) {
    setSelectedIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }
  return <section className="draft-review" aria-label="Revisar artículos">
    <p className="eyebrow">Revisión humana</p><h4>Revisar artículos</h4>
    <section aria-label="Ingredientes nuevos y artículos candidatos">
      <h5>Ingredientes nuevos · {newIngredientGroups.length}</h5>
      <p>Las apariciones equivalentes se consolidan por nombre y unidad. Cada artículo se prepara, previsualiza y solo se crea tras confirmación humana.</p>
      {newIngredientGroups.map((group) => <NewIngredientArticleCard key={group.key} group={group} draft={draft} saving={saving} onLink={onLinkIngredientArticle} />)}
      {!newIngredientGroups.length ? <p>Todos los ingredientes nuevos ya tienen un artículo vinculado.</p> : null}
      <Link className="button-link" to="/articulos?panel=referencias">Exportar y enriquecer artículos incompletos</Link>
      <p className="muted">El enriquecimiento externo crea referencias de precio y proveedor/tienda. No sustituye el precio ni el proveedor reales del restaurante.</p>
    </section>
    <p role="status"><strong>{pending}</strong> requieren revisión. Son decisiones de catálogo, separadas de las relaciones de ingredientes.</p>
    <p><strong>No es artículo de compra</strong> conserva la posibilidad de tratarlo con otra identidad. <strong>Eliminar</strong> no incluirá este registro en Host AI.</p>
    <div className="import-primary-actions">
      <label><input type="checkbox" checked={visibleIds.length > 0 && visibleIds.every((id) => selectedIds.includes(id))}
        onChange={(event) => setSelectedIds(event.target.checked ? visibleIds : [])} /> Seleccionar todos los visibles</label>
      <button disabled={saving || activeSelectedIds.length === 0} type="button" onClick={() => {
        decide(activeSelectedIds, "IGNORAR"); setSelectedIds([]);
      }}>Eliminar seleccionados · {activeSelectedIds.length}</button>
      <button disabled={saving || activeSelectedIds.length === 0} type="button" onClick={() => {
        decide(activeSelectedIds, "ES_ELABORACION"); setSelectedIds([]);
      }}>Marcar seleccionados como elaboración/receta · {activeSelectedIds.length}</button>
      <button disabled={saving || activeSelectedIds.length === 0} className="secondary-action" type="button" onClick={() => {
        decide(activeSelectedIds, "PENDIENTE"); setSelectedIds([]);
      }}>Dejar seleccionados pendientes · {activeSelectedIds.length}</button>
    </div>
    {groups.map(([label, items]) => <details key={label} open>
      <summary>{label} · {items.filter((item) => decisions.get(item.id)?.decision === "PENDIENTE").length} pendientes / {items.length}</summary>
      <p>{label === "No es un artículo de compra"
        ? "Host AI no los trata automáticamente como compra porque la semántica del documento indica elaboración, plato, menú o contexto."
        : label === "Artículo comprado con match ambiguo"
          ? "Host AI encontró varios artículos compatibles. La identidad debe elegirse individualmente."
          : "Host AI necesita una decisión explícita antes de incluir estos elementos en la importación."}</p>
      <label><input type="checkbox" checked={items.length > 0 && items.every((item) => selectedIds.includes(item.id))}
        onChange={(event) => setSelectedIds((current) => event.target.checked
          ? [...new Set([...current, ...items.map((item) => item.id)])]
          : current.filter((id) => !items.some((item) => item.id === id)))} /> Seleccionar todos los visibles de {label}</label>
      {label === "No es un artículo de compra" ? <button disabled={saving} type="button" onClick={() => decide(items.map((item) => item.id), "NO_ARTICULO_COMPRA")}>Marcar el grupo como no comprado</button> : null}
      <ul>{items.map((item) => {
        const current = decisions.get(item.id);
        return <li key={item.id}><article className="draft-warning">
          <label><input type="checkbox" aria-label={`Seleccionar ${item.nombre}`} checked={selectedIds.includes(item.id)} onChange={() => toggleSelected(item.id)} /> Seleccionar</label>
          <h5>{item.nombre || "Artículo sin nombre"}</h5>
          <p>{item.motivo || "La identidad o el tipo de este elemento no se pudo resolver con seguridad."}</p>
          <p><strong>Tipo importado:</strong> {item.tipo_semantico || item.tipo_entidad || "No determinado"}</p>
          <p><strong>Decisión actual:</strong> {current?.decision === "PENDIENTE" ? "Pendiente" : current?.decision?.replaceAll("_", " ")}</p>
          {item.candidatos?.length ? <div><strong>Candidatos de Biblioteca:</strong>{item.candidatos.map((candidate) => {
            const candidateId = candidate.article_id || candidate.articulo_id;
            return <button disabled={!candidateId || saving} type="button" key={candidateId || candidate.nombre}
              onClick={() => candidateId && decide([item.id], "REUTILIZAR_ARTICULO", candidateId)}>
              Reutilizar {candidate.nombre || candidateId}
            </button>;
          })}</div> : null}
          <div className="import-primary-actions">
            <button disabled={saving} type="button" onClick={() => decide([item.id], "NO_ARTICULO_COMPRA")}>No es artículo de compra</button>
            <button disabled={saving} type="button" onClick={() => decide([item.id], "ES_ELABORACION")}>Es elaboración/receta</button>
            <button disabled={saving} type="button" onClick={() => decide([item.id], "PRODUCTO_VENDIBLE")}>Es producto vendible</button>
            <button disabled={saving} type="button" onClick={() => decide([item.id], "IGNORAR")}>Eliminar</button>
            <button disabled={saving} className="secondary-action" type="button" onClick={() => decide([item.id], "PENDIENTE")}>Dejar pendiente</button>
          </div>
          {current?.decision === "IGNORAR" ? <p>No se incluirá este registro en Host AI. No se borrará ningún candidato existente.</p> : null}
          <details><summary>Ver evidencia</summary><p>ID de borrador: {item.id}</p><pre>{JSON.stringify({ origen: item.origen, evidencia_tipo: item.evidencia_tipo, evidencia_identidad: item.evidencia_identidad }, null, 2)}</pre></details>
        </article></li>;
      })}</ul>
    </details>)}
    {ignoredArticles.length ? <details>
      <summary>Eliminados de esta importación · {ignoredArticles.length}</summary>
      <p>Estos registros no se incluirán en Host AI.</p>
      <div className="import-primary-actions">
        <label><input type="checkbox" checked={ignoredArticles.length > 0 && ignoredArticles.every((item) => selectedIgnoredIds.includes(item.id))}
          onChange={(event) => setSelectedIgnoredIds(event.target.checked ? ignoredArticles.map((item) => item.id) : [])} /> Seleccionar todos los eliminados</label>
        <button disabled={saving || ignoredSelectedIds.length === 0} type="button" onClick={() => {
          decide(ignoredSelectedIds, "PENDIENTE"); setSelectedIgnoredIds([]);
        }}>Restaurar seleccionados · {ignoredSelectedIds.length}</button>
      </div>
      <ul>{ignoredArticles.map((item) => <li key={item.id}>
        <label><input type="checkbox" aria-label={`Seleccionar eliminado ${item.nombre}`} checked={selectedIgnoredIds.includes(item.id)}
          onChange={() => setSelectedIgnoredIds((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : [...current, item.id])} /> Seleccionar</label>{" "}
        <span>{item.nombre || "Registro sin nombre"}</span>{" "}
        <button disabled={saving} type="button" onClick={() => decide([item.id], "PENDIENTE")}>Restaurar</button>
      </li>)}</ul>
    </details> : null}
    {elaborationArticles.length ? <details>
      <summary>Clasificados como elaboración/receta · {elaborationArticles.length}</summary>
      <p>Se excluyen únicamente del catálogo de compra. Las recetas ya presentes en el borrador conservan su identidad.</p>
      <div className="import-primary-actions">
        <label><input type="checkbox" checked={elaborationArticles.length > 0 && elaborationArticles.every((item) => selectedElaborationIds.includes(item.id))}
          onChange={(event) => setSelectedElaborationIds(event.target.checked ? elaborationArticles.map((item) => item.id) : [])} /> Seleccionar todas las elaboraciones</label>
        <button disabled={saving || elaborationSelectedIds.length === 0} type="button" onClick={() => {
          decide(elaborationSelectedIds, "PENDIENTE"); setSelectedElaborationIds([]);
        }}>Restaurar seleccionados a pendiente · {elaborationSelectedIds.length}</button>
      </div>
      <ul>{elaborationArticles.map((item) => <li key={item.id}>
        <label><input type="checkbox" aria-label={`Seleccionar elaboración ${item.nombre}`} checked={selectedElaborationIds.includes(item.id)}
          onChange={() => setSelectedElaborationIds((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : [...current, item.id])} /> Seleccionar</label>{" "}
        <span>{item.nombre || "Registro sin nombre"}</span>{" "}
        <button disabled={saving} type="button" onClick={() => decide([item.id], "PENDIENTE")}>Restaurar a pendiente</button>
      </li>)}</ul>
    </details> : null}
    <button type="button" className="secondary-action" onClick={onClose}>Volver al resumen</button>
  </section>;
}

function canonicalRecipeId(candidate?: Record<string, unknown>): string | null {
  const value = String(candidate?.recipe_id ?? candidate?.receta_id ?? candidate?.id ?? "").trim();
  return /^REC601-\d+$/.test(value) ? value : null;
}

function DecisionReview({ decisions, draft, onDraftChange, saving, onClose }: {
  decisions: Array<{ id: string; nombre: string }>;
  draft: ImportDraft;
  onDraftChange: (draft: ImportDraft) => void | Promise<void>;
  saving: boolean;
  onClose: () => void;
}) {
  const [index, setIndex] = useState(0);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const current = decisions[index];
  const recipe = current ? draft.recipes.find((item) => item.id === current.id) : undefined;
  const canonicalCandidates = recipe?.duplicate_candidates.filter((item) => canonicalRecipeId(item)) ?? [];
  const candidate = (canonicalCandidates.length === 1 ? canonicalCandidates[0] : recipe?.duplicate_candidates[0]) as Record<string, unknown> | undefined;
  const differences = Array.isArray(candidate?.diferencias)
    ? candidate.diferencias as Array<Record<string, unknown>> : [];
  const provenance = recipe?.source_blocks.map((source) => {
    if (typeof source === "string") return source;
    return [source.archivo ?? source.file, source.hoja ?? source.sheet, source.fila ?? source.row, source.region]
      .filter((value) => value != null && value !== "")
      .map(String)
      .join(" · ");
  }).filter(Boolean).join(" · ");
  function decide(identityDecision: NonNullable<RecipeDraft["identity_decision"]>, proposedAction: string, selectedCanonicalId?: string) {
    if (!recipe) return;
    if (identityDecision === "MISMA_RECETA" && !(selectedCanonicalId || canonicalRecipeId(candidate))) return;
    onDraftChange({
      ...draft,
      recipes: draft.recipes.map((item) => item.id === recipe.id
        ? { ...item, identity_decision: identityDecision, proposed_action: proposedAction,
          selected_canonical_recipe_id: selectedCanonicalId ?? canonicalRecipeId(candidate) }
        : item),
    });
  }
  const pendingDecisions = decisions.filter((item) => {
    const decision = draft.recipes.find((recipeItem) => recipeItem.id === item.id)?.identity_decision;
    return !decision || decision === "PENDIENTE";
  });
  const selectedRecipes = draft.recipes.filter((item) => selectedIds.includes(item.id));
  const canReuseSelected = selectedRecipes.length > 0 && selectedRecipes.every((item) => {
    const candidates = item.duplicate_candidates.filter((candidateItem) => canonicalRecipeId(candidateItem));
    return Boolean(item.selected_canonical_recipe_id || candidates.length === 1);
  });
  function decideMany(identityDecision: NonNullable<RecipeDraft["identity_decision"]>, proposedAction: string) {
    const selected = new Set(selectedIds);
    void onDraftChange({
      ...draft,
      recipes: draft.recipes.map((item) => selected.has(item.id)
        ? { ...item, identity_decision: identityDecision, proposed_action: proposedAction,
          selected_canonical_recipe_id: identityDecision === "MISMA_RECETA"
            ? item.selected_canonical_recipe_id ?? canonicalRecipeId(item.duplicate_candidates.find((candidateItem) => canonicalRecipeId(candidateItem)))
            : item.selected_canonical_recipe_id }
        : item),
    });
    setSelectedIds([]);
  }
  if (!current) return <section className="draft-review" aria-label="Revisar decisiones">
    <h3>Revisar recetas</h3>
    <p>No hay decisiones humanas pendientes.</p>
    <button type="button" onClick={onClose}>Volver al resumen</button>
  </section>;
  return <section className="draft-review" aria-label="Revisar decisiones">
    <h3>Revisar recetas · {pendingDecisions.length}</h3>
    <div className="import-primary-actions">
      <label><input type="checkbox" checked={pendingDecisions.length > 0 && pendingDecisions.every((item) => selectedIds.includes(item.id))}
        onChange={(event) => setSelectedIds(event.target.checked ? pendingDecisions.map((item) => item.id) : [])} /> Seleccionar todas las recetas pendientes</label>
      <button disabled={saving || !canReuseSelected} type="button" onClick={() => decideMany("MISMA_RECETA", "REUTILIZAR_EXISTENTE")}>Usar candidato canónico en seleccionadas · {selectedIds.length}</button>
      <button disabled={saving || selectedIds.length === 0} type="button" onClick={() => decideMany("RECETA_NUEVA", "CREAR_RECETA")}>Crear como nuevas · {selectedIds.length}</button>
      <button disabled={saving || selectedIds.length === 0} type="button" onClick={() => decideMany("VARIANTE", "CREAR_RECETA")}>Crear como variantes · {selectedIds.length}</button>
      <button disabled={saving || selectedIds.length === 0} className="secondary-action" type="button" onClick={() => decideMany("PENDIENTE", "REQUIERE_REVISION")}>Dejar pendientes · {selectedIds.length}</button>
    </div>
    <ul>{decisions.map((item) => {
      const itemRecipe = draft.recipes.find((recipeItem) => recipeItem.id === item.id);
      const isPending = !itemRecipe?.identity_decision || itemRecipe.identity_decision === "PENDIENTE";
      const itemCandidate = itemRecipe?.duplicate_candidates.find((candidateItem) => canonicalRecipeId(candidateItem));
      const itemOrigin = itemRecipe?.source_blocks.map(formatImportValue).filter(Boolean).join(" · ") || "package importado";
      const relatedIngredients = itemRecipe?.ingredients.filter((ingredient) => Boolean(ingredient.article_id)).length ?? 0;
      return <li key={item.id}><label><input type="checkbox" aria-label={`Seleccionar receta ${item.nombre}`}
        disabled={!isPending} checked={selectedIds.includes(item.id)} onChange={() => setSelectedIds((selected) => selected.includes(item.id)
          ? selected.filter((id) => id !== item.id) : [...selected, item.id])} /> <strong>{item.nombre}</strong> · <code>{item.id}</code></label>
        <span> · origen {itemOrigin} · {itemRecipe?.ingredients.length ?? 0} ingredientes ({relatedIngredients} relacionados) · rendimiento {formatYield(itemRecipe?.yield_value ?? itemRecipe?.servings)}</span>
        <span> · candidato {String(itemCandidate?.nombre ?? "sin candidato canónico único")} {canonicalRecipeId(itemCandidate) ?? ""} · decisión {itemRecipe?.identity_decision ?? "PENDIENTE"}</span>
      </li>;
    })}</ul>
    <p><strong>Decisión {index + 1} de {decisions.length}</strong></p>
    <article className="draft-warning">
      <h4>{current.nombre}</h4>
      <p>Host AI necesita que revises la identidad de esta elaboración antes de aplicarla.</p>
      <dl className="detail-grid">
        <dt>Importado</dt><dd>{recipe?.title ?? current.nombre}</dd>
        <dt>Posible coincidencia</dt><dd>{String(candidate?.nombre ?? "Sin candidato único")}</dd>
        <dt>Tipo de candidato</dt><dd>{candidate?.estado_identidad === "EXISTE_EN_LEGACY_SIN_CANONICALIZAR" ? "Legacy" : "Biblioteca"}</dd>
      </dl>
      <h5>Evidencia</h5>
      <ul>
        <li>Nombre: {candidate?.coincidencia_linguistica ? "coincidencia lingüística" : "nombre o alias relacionado"}</li>
        <li>Ingredientes coincidentes: {candidate?.coincidencia_ingredientes == null ? "no calculados" : `${Math.round(Number(candidate.coincidencia_ingredientes) * 100)}%`}</li>
        <li>Estructura: {candidate?.estructura_compatible ? "compatible" : "diferente o insuficiente"}</li>
        <li>Rendimiento: {differences.some((item) => item.campo === "rendimiento") ? "diferente" : "sin diferencia demostrada"}</li>
        <li>Procedencia: {provenance || "package importado"}</li>
      </ul>
      {differences.length ? <details open><summary>Diferencias · {differences.length}</summary><ul>{differences.map((difference, differenceIndex) => <li key={differenceIndex}>
        <strong>{String(difference.campo ?? "Campo")}</strong>: existente {JSON.stringify(difference.actual)} · importado {JSON.stringify(difference.importado)}
      </li>)}</ul></details> : <p>No hay diferencias estructurales detalladas disponibles.</p>}
      <div className="import-primary-actions">
        <button aria-pressed={recipe?.identity_decision === "MISMA_RECETA"} disabled={!canonicalRecipeId(candidate) || saving} type="button" onClick={() => decide("MISMA_RECETA", "REUTILIZAR_EXISTENTE")}>Es la misma receta</button>
        <button aria-pressed={recipe?.identity_decision === "VARIANTE"} disabled={saving} type="button" onClick={() => decide("VARIANTE", "CREAR_RECETA")}>Es una variante</button>
        <button aria-pressed={recipe?.identity_decision === "RECETA_NUEVA"} disabled={saving} type="button" onClick={() => decide("RECETA_NUEVA", "CREAR_RECETA")}>Es una receta nueva</button>
      </div>
      <MenuCanonicalRecipeSearch disabled={saving} onSelect={(recipeId) => decide("MISMA_RECETA", "REUTILIZAR_EXISTENTE", recipeId)} />
      {recipe?.identity_decision && recipe.identity_decision !== "PENDIENTE" ? <p role="status">Decisión guardada en el borrador: {recipe.identity_decision}. No se ha escrito ningún dato real.</p> : null}
      <p>Ninguna selección en esta pantalla modifica datos reales.</p>
    </article>
    <div className="import-primary-actions">
      <button disabled={index === 0} type="button" onClick={() => setIndex((value) => value - 1)}>Anterior</button>
      <button disabled={index === decisions.length - 1} type="button" onClick={() => setIndex((value) => value + 1)}>Siguiente</button>
      <button aria-pressed={recipe?.identity_decision === "PENDIENTE"} disabled={saving} className="secondary-action" type="button" onClick={() => decide("PENDIENTE", "REQUIERE_REVISION")}>Dejar pendiente</button>
      <button className="secondary-action" type="button" onClick={onClose}>Volver al resumen</button>
    </div>
  </section>;
}

function VariantReview({ groups, draft, onDraftChange, saving, onClose }: {
  groups: NonNullable<NonNullable<BibliotecaImportSession["resolucion_identidad"]>["variantes"]>["items"];
  draft: ImportDraft;
  onDraftChange: (draft: ImportDraft) => void | Promise<void>;
  saving: boolean;
  onClose: () => void;
}) {
  const [index, setIndex] = useState(0);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const reviewable = groups.filter((group) => group.versiones_estructurales > 1);
  const decisions = new Map((draft.variant_decisions ?? []).map((item) => [item.group_id, item.decision]));
  const current = reviewable[index];
  const resolution = current ? decisions.get(current.id) ?? "PENDIENTE" : "PENDIENTE";
  const pendingCount = reviewable.filter((group) => (decisions.get(group.id) ?? "PENDIENTE") === "PENDIENTE").length;
  function decide(decision: "MISMA_RECETA" | "RECETAS_DIFERENTES" | "PENDIENTE") {
    if (!current) return;
    const currentDecisions = draft.variant_decisions
      ?? reviewable.map((group) => ({ group_id: group.id, decision: "PENDIENTE" as const }));
    void onDraftChange({
      ...draft,
      variant_decisions: currentDecisions.map((item) => item.group_id === current.id ? { ...item, decision } : item),
    });
  }
  const pendingGroups = reviewable.filter((group) => (decisions.get(group.id) ?? "PENDIENTE") === "PENDIENTE");
  function decideMany(decision: "MISMA_RECETA" | "RECETAS_DIFERENTES" | "PENDIENTE") {
    const selected = new Set(selectedIds);
    const currentDecisions = draft.variant_decisions
      ?? reviewable.map((group) => ({ group_id: group.id, decision: "PENDIENTE" as const }));
    void onDraftChange({
      ...draft,
      variant_decisions: currentDecisions.map((item) => selected.has(item.group_id) ? { ...item, decision } : item),
    });
    setSelectedIds([]);
  }
  return <section className="draft-review" aria-label="Revisar variantes">
    <h3>Posibles variantes</h3>
    <p>{groups.reduce((total, group) => total + group.apariciones, 0)} apariciones agrupadas en {groups.length} recetas o contextos.</p>
    <p><strong>{pendingCount} grupos requieren comparación.</strong> Los duplicados estructuralmente idénticos ya están consolidados.</p>
    <div className="import-primary-actions">
      <label><input type="checkbox" checked={pendingGroups.length > 0 && pendingGroups.every((group) => selectedIds.includes(group.id))}
        onChange={(event) => setSelectedIds(event.target.checked ? pendingGroups.map((group) => group.id) : [])} /> Seleccionar todos los grupos pendientes</label>
      <button disabled={saving || selectedIds.length === 0} type="button" onClick={() => decideMany("MISMA_RECETA")}>Marcar como misma receta · {selectedIds.length}</button>
      <button disabled={saving || selectedIds.length === 0} type="button" onClick={() => decideMany("RECETAS_DIFERENTES")}>Marcar como recetas diferentes · {selectedIds.length}</button>
      <button disabled={saving || selectedIds.length === 0} className="secondary-action" type="button" onClick={() => decideMany("PENDIENTE")}>Dejar grupos pendientes · {selectedIds.length}</button>
    </div>
    <ul>{reviewable.map((group) => {
      const isPending = (decisions.get(group.id) ?? "PENDIENTE") === "PENDIENTE";
      return <li key={group.id}><label><input type="checkbox" aria-label={`Seleccionar grupo ${group.nombre}`}
        disabled={!isPending} checked={selectedIds.includes(group.id)} onChange={() => setSelectedIds((selected) => selected.includes(group.id)
          ? selected.filter((id) => id !== group.id) : [...selected, group.id])} /> {group.nombre} · {decisions.get(group.id) ?? "PENDIENTE"}</label></li>;
    })}</ul>
    {current ? <article className="confirmation-preview">
      <p><strong>Grupo {index + 1} de {reviewable.length}</strong></p>
      <h4>{current.nombre}</h4>
      <p>{current.apariciones} apariciones · {current.versiones_estructurales} versiones estructurales · {current.duplicados_exactos} repeticiones exactas consolidadas</p>
      {current.tipo_entidad_propuesto === "MENU_O_CONTENEDOR" ? <p className="draft-warning">Parece un menú o contenedor. No se convertirá automáticamente en una receta.</p> : null}
      {current.tipo_entidad_propuesto === "ETIQUETA_CONTEXTO_POR_REVISAR" ? <p className="draft-warning">El nombre parece una etiqueta de contexto y no identifica por sí solo una receta.</p> : null}
      <div className="import-variant-versions">{current.versiones.map((version, versionIndex) => <section key={version.id}>
        <h5>Versión {String.fromCharCode(65 + versionIndex)}</h5>
        <p><strong>Origen:</strong> {version.origenes.map(formatImportValue).join(" · ") || "No indicado"}</p>
        <p><strong>Ingredientes:</strong> {version.ingredientes.length}</p>
        <ul>{version.ingredientes.map((ingredient, ingredientIndex) => <li key={`${version.id}-${ingredientIndex}`}>
          {String(ingredient.nombre_original ?? "Ingrediente")}
          {ingredient.cantidad_texto != null ? ` · ${String(ingredient.cantidad_texto)} ${String(ingredient.unidad ?? "")}` : ""}
        </li>)}</ul>
        <p><strong>Rendimiento:</strong> {formatYield(version.rendimiento, version.unidad_rendimiento)}</p>
      </section>)}</div>
      <details open><summary>Diferencias reales · {current.diferencias.length}</summary>
        {current.diferencias.length ? <ul>{current.diferencias.map((difference, differenceIndex) => <li key={`${difference.tipo}-${differenceIndex}`}>
          {variantDifferenceLabel(difference)}
        </li>)}</ul> : <p>Sin diferencias materiales.</p>}
      </details>
      <div className="import-primary-actions">
        <button aria-pressed={resolution === "MISMA_RECETA"} disabled={saving} type="button" onClick={() => decide("MISMA_RECETA")}>Son la misma receta</button>
        <button aria-pressed={resolution === "RECETAS_DIFERENTES"} disabled={saving} type="button" onClick={() => decide("RECETAS_DIFERENTES")}>Son recetas diferentes</button>
        <button aria-pressed={resolution === "PENDIENTE"} disabled={saving} className="secondary-action" type="button" onClick={() => decide("PENDIENTE")}>Dejar pendiente</button>
      </div>
      {resolution !== "PENDIENTE" ? <p role="status">Decisión guardada en el borrador: {resolution === "MISMA_RECETA" ? "consolidar conservando todos los orígenes" : "mantener recetas separadas y solicitar nombres antes de crear"}. No se ha escrito ningún dato.</p> : <p role="status">Decisión pendiente.</p>}
      <div className="import-primary-actions">
        <button disabled={index === 0} type="button" onClick={() => setIndex((value) => value - 1)}>Anterior</button>
        <button disabled={index === reviewable.length - 1} type="button" onClick={() => setIndex((value) => value + 1)}>Siguiente</button>
      </div>
    </article> : <p>No quedan grupos con diferencias estructurales.</p>}
    <button className="secondary-action" type="button" onClick={onClose}>Volver al resumen</button>
  </section>;
}

function variantDifferenceLabel(difference: { tipo: string; nombre?: string; antes?: unknown; despues?: unknown }) {
  if (difference.tipo === "INGREDIENTE_ANADIDO") return `+ Ingrediente en otra versión: ${difference.nombre}`;
  if (difference.tipo === "INGREDIENTE_RETIRADO") return `- Ingrediente respecto a la primera versión: ${difference.nombre}`;
  if (difference.tipo === "CANTIDAD_CAMBIA") return `Cantidad de ${difference.nombre}: ${JSON.stringify(difference.antes)} → ${JSON.stringify(difference.despues)}`;
  if (difference.tipo === "RENDIMIENTO_CAMBIA") return `Rendimiento: ${String(difference.antes ?? "no informado")} → ${String(difference.despues ?? "no informado")}`;
  return difference.tipo;
}

function formatImportValue(value: unknown): string {
  if (value == null || value === "") return "";
  if (typeof value !== "object") return String(value);
  const item = value as Record<string, unknown>;
  return [item.archivo ?? item.file, item.hoja ?? item.sheet, item.fila ?? item.row, item.region]
    .filter((part) => part != null && part !== "").map(String).join(" · ") || "Origen estructurado";
}

function formatYield(value: unknown, unit?: string | null): string {
  if (value == null || value === "") return "No informado";
  if (typeof value === "object") {
    const item = value as Record<string, unknown>;
    const amount = item.valor ?? item.value ?? item.cantidad ?? item.amount;
    const resolvedUnit = item.unidad ?? item.unit ?? unit;
    return amount == null ? "Pendiente / ambiguo" : `${String(amount)} ${String(resolvedUnit ?? "")}`.trim();
  }
  return `${String(value)} ${unit ?? ""}`.trim();
}

function CatalogPreview({ preview }: { preview: NonNullable<BibliotecaImportSession["preview_global"]> }) {
  const sections = [
    ["Proveedores", preview.proveedores],
    ["Artículos", preview.articulos],
    ["Elaboraciones", preview.elaboraciones],
    ["Relaciones", preview.relaciones],
    ["Menús", preview.menus ?? {}],
  ] as const;
  const pending = preview.contadores.pendientes_desglose;
  return <section aria-label="Preview global de importación">
    <h4>Preview global</h4>
    {(preview.contadores.menus_recibidos ?? 0) > 0 ? <section aria-label="Resumen de menús a importar" className="inline-notice">
      <h4>Menús</h4>
      <p><strong>{preview.contadores.menus_recibidos} detectados</strong></p>
      <p>{preview.contadores.menus_crear ?? 0} crear · {preview.contadores.menus_reutilizar ?? 0} reutilizar · {preview.contadores.menus_pendientes ?? 0} pendientes</p>
      {(preview.contadores.menus_pendientes ?? 0) > 0 ? <p><strong>{preview.contadores.menus_pendientes} menús quedarán sin importar.</strong></p> : null}
    </section> : null}
    <dl className="detail-grid">
      <dt>Proveedores nuevos</dt><dd>{preview.contadores.proveedores_nuevos}</dd>
      <dt>Proveedores reutilizados</dt><dd>{preview.contadores.proveedores_reutilizados}</dd>
      <dt>Artículos nuevos</dt><dd>{preview.contadores.articulos_nuevos}</dd>
      <dt>Artículos reutilizados</dt><dd>{preview.contadores.articulos_reutilizados}</dd>
      <dt>Eliminados / ignorados de esta importación</dt><dd>{preview.contadores.articulos_ignorados ?? preview.articulos.ignorar?.length ?? 0}</dd>
      <dt>Clasificados como elaboración/receta</dt><dd>{preview.contadores.articulos_reclasificados_elaboracion ?? preview.articulos.es_elaboracion?.length ?? 0}</dd>
      <dt>Recetas/elaboraciones</dt><dd>{preview.contadores.recetas_elaboraciones}</dd>
      <dt>Relaciones artículo–proveedor a escribir</dt><dd>{preview.contadores.relaciones_a_escribir ?? 0}</dd>
      <dt>Relaciones artículo–proveedor reutilizadas</dt><dd>{preview.contadores.relaciones_reutilizadas ?? 0}</dd>
      <dt>Relaciones artículo–proveedor pendientes</dt><dd>{preview.contadores.relaciones_pendientes ?? 0}</dd>
      <dt>Ingredientes con artículo canónico</dt><dd>{preview.contadores.ingredientes_relacionados ?? 0}</dd>
      <dt>Ingredientes sin artículo canónico</dt><dd>{preview.contadores.ingredientes_sin_relacionar ?? 0}</dd>
      <dt>Menús recibidos</dt><dd>{preview.contadores.menus_recibidos ?? 0}</dd>
      <dt>Menús a crear</dt><dd>{preview.contadores.menus_crear ?? 0}</dd>
      <dt>Menús a reutilizar</dt><dd>{preview.contadores.menus_reutilizar ?? 0}</dd>
      <dt>Menús pendientes</dt><dd>{preview.contadores.menus_pendientes ?? 0}</dd>
      <dt>Líneas de menú resueltas</dt><dd>{preview.contadores.menu_lineas_resueltas ?? 0}</dd>
      <dt>Líneas de menú pendientes</dt><dd>{preview.contadores.menu_lineas_pendientes ?? 0}</dd>
      <dt>Pendientes bloqueantes totales</dt><dd>{preview.contadores.pendientes}</dd>
      {pending ? <>
        <dt>Pendientes · identidad de receta</dt><dd>{pending.identidad_receta}</dd>
        <dt>Pendientes · artículos</dt><dd>{pending.articulo}</dd>
        <dt>Pendientes · relaciones</dt><dd>{pending.relacion}</dd>
        <dt>Pendientes · proveedores</dt><dd>{pending.proveedor}</dd>
        <dt>Pendientes · documentación</dt><dd>{pending.documentacion}</dd>
        <dt>Pendientes · menús</dt><dd>{pending.menu ?? 0}</dd>
        <dt>Pendientes · otros</dt><dd>{pending.otro}</dd>
      </> : null}
    </dl>
    {sections.map(([title, groups]) => <div key={title}><h5>{title}</h5>
      {Object.entries(groups).map(([action, rawItems]) => {
        const items = rawItems as Array<{ id?: string; nombre?: string; articulo?: string; proveedor?: string; article_id?: string | null; proveedor_id?: string | null; motivo?: string; motivos?: string[]; menu_id?: string | null; lineas_resueltas?: number; lineas_pendientes?: number; tipo_semantico?: string | null; coincidencia?: { id?: string; codigo?: string; nombre?: string } | null }>;
        return items.length ? <details key={action} open={action === "crear" || action === "reutilizar"}>
        <summary>{action.replaceAll("_", " ")} · {items.length}</summary>
        <ul>{items.map((item, index) => <li key={`${action}-${index}`}>
          {item.nombre || (item.articulo ? `${item.articulo} → ${item.proveedor || "sin proveedor"}` : item.id || "Caso pendiente sin nombre")}
          {"article_id" in item && item.article_id ? ` → ${item.article_id}` : ""}
          {"proveedor_id" in item && item.proveedor_id ? ` → ${item.proveedor_id}` : ""}
          {item.coincidencia ? ` · Biblioteca: ${item.coincidencia.codigo || item.coincidencia.id || item.coincidencia.nombre}` : ""}
          {item.tipo_semantico ? ` · ${item.tipo_semantico}` : ""}
          {item.motivo ? ` · ${item.motivo}` : ""}
          {item.menu_id ? ` · ${item.menu_id}` : ""}
          {item.lineas_resueltas != null ? ` · ${item.lineas_resueltas} líneas resueltas` : ""}
          {item.lineas_pendientes ? ` · ${item.lineas_pendientes} líneas pendientes` : ""}
          {item.motivos?.length ? <ul>{item.motivos.map((reason) => <li key={reason}>{reason}</li>)}</ul> : null}
        </li>)}</ul>
      </details> : null;
      })}
    </div>)}
    <p><strong>PREVIEW:</strong> todavía no se ha modificado ningún dato operativo.</p>
  </section>;
}

function AnalysisSummary({ analysis }: { analysis: NonNullable<BibliotecaImportSession["analisis_restaurante"]> }) {
  const summary = analysis.resumen;
  const recordedAiCost = analysis.ai_import?.cost_breakdown?.total_cost;
  const sheets = Object.values((analysis.hojas ?? []).reduce<Record<string, NonNullable<typeof analysis.hojas>>>((groups, region) => {
    const key = `${region.archivo}:${region.nombre}`;
    (groups[key] ??= []).push(region);
    return groups;
  }, {}));
  return <section aria-label="Resumen del análisis conjunto">
    <dl className="detail-grid">
      <dt>Archivos analizados</dt><dd>{summary.archivos_analizados}</dd>
      <dt>Hojas</dt><dd>{summary.hojas_analizadas}</dd>
      <dt>Filas</dt><dd>{summary.filas_analizadas}</dd>
      <dt>Posibles artículos</dt><dd>{summary.posibles_articulos}</dd>
      <dt>Posibles recetas</dt><dd>{summary.posibles_recetas}</dd>
      <dt>Posibles menús</dt><dd>{summary.posibles_menus ?? 0}</dd>
      <dt>Posibles subelaboraciones</dt><dd>{summary.posibles_subelaboraciones}</dd>
      <dt>Posibles productos vendibles</dt><dd>{summary.posibles_productos_vendibles}</dd>
      <dt>Proveedores</dt><dd>{summary.proveedores}</dd>
      <dt>Relaciones detectadas</dt><dd>{summary.relaciones_detectadas}</dd>
      <dt>Duplicados posibles</dt><dd>{summary.duplicados_posibles}</dd>
      <dt>Dudas documentales totales</dt><dd>{summary.decisiones_usuario ?? summary.ambiguedades}</dd>
      <dt>Avisos técnicos</dt><dd>{summary.warnings_tecnicos ?? 0}</dd>
      <dt>Artículos sin coste</dt><dd>{summary.articulos_sin_coste}</dd>
    </dl>
    {analysis.exclusiones_sesion?.length ? <details open>
      <summary>Excluidos solo de esta importación · {analysis.exclusiones_sesion.length}</summary>
      <ul>{analysis.exclusiones_sesion.map((item, index) => <li key={`${item.nombre}-${index}`}>
        <strong>{item.nombre}</strong> · {item.motivo}
      </li>)}</ul>
      <p className="muted">No se ha borrado ninguna entidad existente y esta decisión no se reutiliza en futuras importaciones.</p>
    </details> : null}
    <h4>Fuentes analizadas</h4>
    <ul>{(analysis.archivos ?? []).map((file) => <li key={file.nombre}><strong>{file.nombre}</strong> · {file.hojas} hojas · {file.filas} filas · {file.estado}</li>)}</ul>
    <h4>Detección por hoja</h4>
    {sheets.map((regions) => <details key={`${regions[0].archivo}-${regions[0].nombre}`}>
      <summary>{regions[0].nombre} · {regions.length} {regions.length === 1 ? "región" : "regiones"} · {regions.map((item) => item.tipo_propuesto).join(", ")}</summary>
      {regions.map((region) => <section key={region.region ?? `${region.fila_inicial}-${region.fila_final}`}>
        <h5>{region.region ?? "Región"} · filas {region.fila_inicial ?? "?"}–{region.fila_final ?? "?"}</h5>
        <p>Tipo: <strong>{region.tipo_propuesto}</strong> · Confianza: {Math.round((region.confianza ?? 0) * 100)}%</p>
        <p>Dimensiones: {region.dimensiones || "—"} · celdas no vacías: {region.celdas_no_vacias ?? "—"} · combinadas: {region.merged_cells?.length ?? 0}</p>
        <p>Encabezado: {region.fila_encabezado ? `fila ${region.fila_encabezado}` : "no determinado"}{region.titulo_contexto ? ` · contexto: ${region.titulo_contexto}` : ""}</p>
        <p>{region.motivo || "No puedo determinar con seguridad la estructura de esta región."}</p>
        {(region.mapping ?? []).length ? <ul>{(region.mapping ?? []).map((item) => <li key={item.columna}><strong>{item.columna}</strong> → {item.destino === "sin_mapear" ? "DESCONOCIDO / REQUIERE_REVISION" : item.destino}{item.requiere_revision ? " · duda pendiente" : ""}</li>)}</ul> : <p>No hay mapping fiable.</p>}
      </section>)}
    </details>)}
    {(summary.decisiones_usuario ?? summary.ambiguedades) ? <details><summary>Dudas documentales agrupadas · {summary.decisiones_usuario ?? summary.ambiguedades}</summary>
      <p>Clasificación: {analysis.dudas?.clasificacion?.length ?? 0} · Precio: {analysis.dudas?.precio?.length ?? 0} · Duplicados: {analysis.dudas?.duplicados?.length ?? 0} · Relaciones: {analysis.dudas?.relaciones?.length ?? 0}</p>
      <p>Este total documental puede incluir dudas que no son decisiones de identidad de recetas.</p>
    </details> : null}
    {(summary.warnings_tecnicos ?? 0) > 0 ? <details><summary>Detalles técnicos · {summary.warnings_tecnicos}</summary>
      <p>Son avisos de parser y trazabilidad; no aumentan por sí solos las decisiones que debe tomar el usuario.</p>
    </details> : null}
    <p><strong>Coste IA:</strong> {analysis.ai_import?.used
      ? (recordedAiCost == null ? "Registrado por Host AI" : String(recordedAiCost))
      : analysis.coste_ia?.usada ? analysis.coste_ia.total : "$0 · análisis determinista"}</p>
    <p><strong>Modo seguro:</strong> analizar y preparar el borrador no modifica datos operativos.</p>
  </section>;
}

function DraftReview({
  initialDraft, catalogBlocked = false, guided = false, confirmationOnly = false, counts,
  canonicalPreview, onDraftChange, onConfirmed,
}: {
  initialDraft: ImportDraft; catalogBlocked?: boolean; guided?: boolean;
  confirmationOnly?: boolean; counts?: ImportCounts; onDraftChange?: (draft: ImportDraft) => void;
  canonicalPreview?: BibliotecaImportSession["preview_global"];
  onConfirmed?: () => void;
}) {
  const [draft, setDraft] = useState(initialDraft);
  const [selectedId, setSelectedId] = useState(initialDraft.recipes[0]?.id ?? "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [dirty, setDirty] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<ImportConfirmationResult | null>(null);
  const selected = draft.recipes.find((recipe) => recipe.id === selectedId);
  const blockingErrors = dirty ? [] : (draft.validation?.blocking_errors ?? []).filter((issue) =>
    !(confirmationOnly && issue.code === "RECETA_REQUIERE_REVISION")
  );
  const warnings = dirty ? [] : (draft.validation?.warnings ?? []);
  const guidedPending = draft.recipes.reduce((total, recipe) => total
    + Number(recipe.proposed_action === "REQUIERE_REVISION" || (recipe.duplicate_candidates.length > 0 && recipe.proposed_action !== "REUTILIZAR_EXISTENTE"))
    + recipe.ingredients.filter((ingredient) => ingredient.relation_status === "REVISAR_COINCIDENCIA").length, 0);

  function focusIssue(issue: DraftValidationIssue) {
    setSelectedId(issue.recipe_id);
    window.setTimeout(() => {
      const targetId = issue.ingredient_id
        ? ingredientFieldId(issue.ingredient_id, issue.field)
        : recipeFieldId(issue.recipe_id, issue.field);
      document.getElementById(targetId)?.focus();
    }, 0);
  }

  function updateRecipe(id: string, changes: Partial<RecipeDraft>) {
    setDirty(true);
    setAccepted(false);
    const next = {
      ...draft, recipes: draft.recipes.map((recipe) => recipe.id === id ? {
        ...recipe,
        ...changes,
        validation_errors: recipe.validation_errors.filter(
          (issue) => !(issue.field in changes),
        ),
      } : recipe),
    };
    setDraft(next);
    onDraftChange?.(next);
  }

  function updateIngredient(recipeId: string, ingredientId: string, changes: Partial<IngredientDraft>) {
    setDirty(true);
    setAccepted(false);
    const next = {
      ...draft, recipes: draft.recipes.map((recipe) => recipe.id !== recipeId ? recipe : {
        ...recipe,
        ingredients: recipe.ingredients.map((ingredient) =>
          ingredient.id === ingredientId
            ? { ...ingredient, ...changes, validation_errors: [] }
            : ingredient
        ),
      }),
    };
    setDraft(next);
    onDraftChange?.(next);
  }

  function addIngredient(recipeId: string) {
    const ingredient: IngredientDraft = {
      id: `NEW-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      original_text: "",
      quantity_raw: "",
      quantity: null,
      unit_raw: "",
      unit: null,
      name_raw: "",
      normalized_name: "",
      observations: "",
      article_id: null,
      article_candidates: [],
      relation_status: "SIN_RELACIONAR",
      confidence: 0,
      validation_errors: [],
    };
    setDirty(true);
    setAccepted(false);
    setDraft((current) => ({
      ...current,
      recipes: current.recipes.map((recipe) => recipe.id === recipeId
        ? { ...recipe, ingredients: [...recipe.ingredients, ingredient] }
        : recipe),
    }));
  }

  function removeIngredient(recipeId: string, ingredientId: string) {
    setDirty(true);
    setAccepted(false);
    setDraft((current) => ({
      ...current,
      recipes: current.recipes.map((recipe) => recipe.id === recipeId
        ? {
          ...recipe,
          ingredients: recipe.ingredients.filter((ingredient) => ingredient.id !== ingredientId),
        }
        : recipe),
    }));
  }

  async function save() {
    setSaving(true);
    setMessage("");
    try {
      const response = await bibliotecaService.updateImportDraft(draft.document_id, {
        draft_version: draft.version,
        recipes: draft.recipes,
      });
      setDraft(response.borrador);
      onDraftChange?.(response.borrador);
      setDirty(false);
      setMessage("Borrador guardado. Ningún dato de la Biblioteca ha sido modificado.");
    } catch (reason) {
      const error = reason as HostAiApiError;
      setMessage(error.statusCode === 409
        ? "El borrador cambió en otra revisión. Vuelve a cargarlo antes de guardar."
        : error.message);
    } finally {
      setSaving(false);
    }
  }

  async function confirm() {
    setConfirming(true);
    setMessage("");
    try {
      const response = await bibliotecaService.confirmImport(
        draft.document_id, draft.version, "usuario_web", canonicalPreview?.draft_fingerprint,
      );
      setResult(response.resultado);
      setMessage("Importación confirmada y aplicada a la Biblioteca.");
      onConfirmed?.();
    } catch (reason) {
      const error = reason as HostAiApiError;
      const details = error.details as {
        errores?: Array<{ message?: string; mensaje?: string }>;
      } | undefined;
      const concrete = details?.errores
        ?.map((issue) => issue.message || issue.mensaje)
        .filter(Boolean)
        .join(" ");
      setMessage(concrete || error.message);
    } finally {
      setConfirming(false);
    }
  }

  return <section className="draft-review">
    <h3>{confirmationOnly ? "Listo para importar" : "Revisar pendientes"}</h3>
    {guided && selected ? <><p><strong>Problema {Math.max(1, draft.recipes.findIndex((item) => item.id === selected.id) + 1)} de {draft.recipes.length}</strong> · {selected.title}</p><p role="status">Pendientes por resolver: {guidedPending}</p></> : null}
    {!confirmationOnly ? <p>Revisa una decisión cada vez. Puedes resolverla ahora o dejarla pendiente.</p> : null}
    {!confirmationOnly && !dirty && blockingErrors.length ? <details aria-label="Errores que impiden confirmar">
      <summary>Decisiones obligatorias · {blockingErrors.length}</summary>
      <ul>{blockingErrors.map((issue, index) => <li key={`${issue.code}-${issue.recipe_id}-${issue.ingredient_id}-${index}`}>
        <strong>{issue.recipe_title}</strong>: {issue.message}{" "}
        <button type="button" onClick={() => focusIssue(issue)}>Revisar</button>
      </li>)}</ul>
    </details> : null}
    {!confirmationOnly && !dirty && warnings.length ? <details aria-label="Advertencias del borrador">
      <summary>Otras revisiones · {warnings.length}</summary>
      <ul>{warnings.map((issue, index) => <li key={`${issue.code}-${issue.recipe_id}-${issue.ingredient_id}-${index}`}>
        <strong>{issue.recipe_title}</strong>: {issue.message}{" "}
        <button type="button" onClick={() => focusIssue(issue)}>Revisar</button>
      </li>)}</ul>
    </details> : null}
    {!confirmationOnly ? <div className="draft-review-layout">
      <aside aria-label="Secciones detectadas">
        {draft.recipes.map((recipe) => <button
          className={recipe.id === selectedId ? "active" : ""}
          key={recipe.id}
          onClick={() => setSelectedId(recipe.id)}
          type="button"
        >
          <strong>{recipe.title || "Sin título"}</strong>
          <span>{entityLabel(recipe.entity_type)} · {recipe.ingredients.length} ingredientes</span>
          <small>{humanRecipeState(recipe)}</small>
        </button>)}
      </aside>
      {selected ? <div className="draft-editor">
        <label>Título
          <input
            aria-label="Título de la sección"
            id={recipeFieldId(selected.id, "title")}
            value={selected.title}
            onChange={(event) => updateRecipe(selected.id, { title: event.target.value })}
          />
        </label>
        {selected.validation_errors.filter((issue) => issue.field === "title")
          .map((issue) => <p className="draft-error" key={issue.code}><strong>Error bloqueante:</strong> {issue.message}</p>)}
        <label>Tipo culinario
          <select
            aria-label="Tipo culinario"
            value={selected.entity_type}
            onChange={(event) => updateRecipe(selected.id, {
              entity_type: event.target.value as RecipeDraft["entity_type"],
            })}
          >
            <option value="PRINCIPAL">Elaboración principal</option>
            <option value="SUBELABORACION">Subelaboración</option>
            <option value="COMPONENTE">Componente</option>
            <option value="SECCION">Sección informativa</option>
            <option value="DESCARTAR">Ignorar</option>
          </select>
        </label>
        {selected.entity_type === "SUBELABORACION" ? <label>Elaboración principal
          <select
            aria-label="Elaboración principal"
            value={selected.parent_recipe_id ?? ""}
            onChange={(event) => updateRecipe(selected.id, {
              parent_recipe_id: event.target.value || null,
            })}
          >
            <option value="">Seleccionar...</option>
            {draft.recipes.filter((recipe) =>
              recipe.id !== selected.id && recipe.entity_type === "PRINCIPAL"
            ).map((recipe) => <option key={recipe.id} value={recipe.id}>{recipe.title}</option>)}
          </select>
        </label> : null}
        <label>Acción propuesta
          <select
            aria-label="Acción propuesta"
            value={selected.proposed_action}
            onChange={(event) => updateRecipe(selected.id, { proposed_action: event.target.value })}
          >
            <option value="CREAR_ELABORACION">Crear elaboración</option>
            <option value="CREAR_RECETA">Crear receta</option>
            <option value="REUTILIZAR_EXISTENTE">Reutilizar existente</option>
            <option value="REQUIERE_REVISION">Requiere revisión</option>
            <option value="ACTUALIZAR_ELABORACION">Actualizar elaboración existente</option>
            <option value="ACTUALIZAR_RECETA">Actualizar receta existente</option>
            <option value="CREAR_SUBELABORACION">Crear como subelaboración</option>
            <option value="MANTENER_COMPONENTE">Mantener como componente</option>
            <option value="IGNORAR">Ignorar</option>
          </select>
        </label>
        {selected.proposed_action === "REUTILIZAR_EXISTENTE" ? <p className="draft-success">✓ Ya existe en tu Biblioteca. No se creará otra copia.</p> : null}
        {selected.duplicate_candidates.length ? <section className="draft-warning">
          <p>Hemos encontrado una receta parecida en tu Biblioteca.</p>
          <div className="import-primary-actions">
            <button type="button" onClick={() => updateRecipe(selected.id, { proposed_action: "REUTILIZAR_EXISTENTE" })}>Usar la existente</button>
            <button type="button" onClick={() => updateRecipe(selected.id, { proposed_action: "CREAR_RECETA" })}>Crear como nueva</button>
          </div>
          <details><summary>Comparar</summary><p>Importada: {selected.title}</p><p>Coincidencias encontradas: {selected.duplicate_candidates.length}</p></details>
        </section> : null}
        {(!selected.procedure.some((step) => step.trim()) || !(Number(selected.servings ?? selected.yield_value) > 0)) ? <section className="draft-warning">
          <p>Se puede importar, pero faltan:</p>
          <ul>{!selected.procedure.some((step) => step.trim()) ? <li>Procedimiento</li> : null}{!(Number(selected.servings ?? selected.yield_value) > 0) ? <li>Rendimiento</li> : null}</ul>
          <p>Puedes completarlos después.</p>
        </section> : null}
        <h4>Ingredientes</h4>
        {selected.validation_errors.filter((issue) => issue.field === "ingredients")
          .map((issue) => <p className="draft-error" key={issue.code}><strong>Error bloqueante:</strong> {issue.message}</p>)}
        {!selected.ingredients.length
          ? <p>No hay ingredientes. Añade al menos uno para poder confirmar.</p>
          : null}
        <div className="draft-ingredients">{selected.ingredients.map((ingredient) =>
          <IngredientEditor
            ingredient={ingredient}
            key={ingredient.id}
            onChange={(changes) => updateIngredient(selected.id, ingredient.id, changes)}
            onDelete={() => removeIngredient(selected.id, ingredient.id)}
          />
        )}</div>
        <button type="button" onClick={() => addIngredient(selected.id)}>Añadir ingrediente</button>
        <label>Procedimiento
          <textarea
            aria-label="Procedimiento"
            id={recipeFieldId(selected.id, "procedure")}
            rows={5}
            value={selected.procedure.join("\n")}
            onChange={(event) => updateRecipe(selected.id, {
              procedure: event.target.value.split("\n"),
            })}
          />
        </label>
        {selected.validation_errors.filter((issue) => issue.field === "procedure")
          .map((issue) => <p className="draft-error" key={issue.code}><strong>Error bloqueante:</strong> {issue.message}</p>)}
        <label>Número de raciones
          <input
            aria-label="Número de raciones"
            id={recipeFieldId(selected.id, "servings")}
            min="0"
            step="any"
            type="number"
            value={selected.servings ?? ""}
            onChange={(event) => updateRecipe(selected.id, {
              servings: event.target.value === "" ? null : Number(event.target.value),
            })}
          />
        </label>
        {selected.validation_errors.filter((issue) => issue.field === "servings")
          .map((issue) => <p className="draft-error" key={issue.code}><strong>Error bloqueante:</strong> {issue.message}</p>)}
        <label>Observaciones
          <textarea
            aria-label="Observaciones de la sección"
            rows={3}
            value={selected.notes}
            onChange={(event) => updateRecipe(selected.id, { notes: event.target.value })}
          />
        </label>
        {selected.validation_errors.filter((issue) =>
          !["ingredients", "procedure", "servings", "title"].includes(issue.field)
        ).map((issue, index) => <p
          className={issue.level === "ERROR" ? "draft-error" : "draft-warning"}
          key={`${issue.code}-${index}`}
        ><strong>{issue.level === "ERROR" ? "Error bloqueante" : "Advertencia"}:</strong> {issue.message}</p>)}
      </div> : <p>No hay secciones editables.</p>}
    </div> : null}
    {!confirmationOnly ? <>
    <button disabled={saving} type="button" onClick={() => void save()}>
      {saving ? "Guardando..." : "Guardar borrador"}
    </button>
    {message ? <p role="status">{message}</p> : null}
    <p><strong>Modo seguro:</strong> guardar este borrador no aplica ninguna propuesta.</p>
    {catalogBlocked ? <p className="draft-error">Resuelve los artículos, proveedores o relaciones pendientes antes de confirmar.</p> : null}
    {dirty ? <p className="draft-warning">Guarda el borrador revisado antes de confirmar la importación.</p> : null}
    </> : null}
    <section className="confirmation-preview">
      <h4>Confirmación final</h4>
      {canonicalPreview ? <CatalogPreview preview={canonicalPreview} /> : null}
      {counts ? <dl className="detail-grid">
        <dt>Se crearán</dt><dd>{counts.newRecipes} recetas</dd>
        <dt>Se reutilizarán</dt><dd>{counts.existingRecipes} recetas existentes</dd>
        <dt>Se importarán incompletas</dt><dd>{counts.incompleteRecipes} recetas</dd>
        <dt>Pendientes excluidos de esta confirmación</dt><dd>{counts.blockingPending}</dd>
      </dl> : <p>Se aplicarán {draft.recipes.filter((item) => item.entity_type !== "DESCARTAR" && item.proposed_action !== "IGNORAR").length} elaboraciones revisadas.</p>}
      <p>Host AI reutilizará lo que ya existe, creará únicamente los elementos nuevos confirmados y dejará pendientes los casos dudosos.</p>
      <label>
        <input checked={accepted} onChange={(event) => setAccepted(event.target.checked)} type="checkbox" />
        He revisado el resumen y autorizo aplicar estos cambios.
      </label>
      <button disabled={catalogBlocked || dirty || blockingErrors.length > 0 || !accepted || confirming || Boolean(result)} type="button" onClick={() => void confirm()}>
        {confirming ? "Aplicando importación..." : "Confirmar importación"}
      </button>
      {confirmationOnly && message ? <p className="draft-error" role="status">{message}</p> : null}
      {result ? <div role="status">
        <strong>Importación completada</strong>
        <p>{result.acciones.length} acciones · {result.entidades.length} entidades · sin rollback.</p>
      </div> : null}
    </section>
  </section>;
}

function IngredientEditor({
  ingredient,
  onChange,
  onDelete,
}: {
  ingredient: IngredientDraft;
  onChange: (changes: Partial<IngredientDraft>) => void;
  onDelete: () => void;
}) {
  return <article className="draft-ingredient">
    <small>Texto original: {ingredient.original_text}</small>
    <div className="draft-ingredient-fields">
      <label>Cantidad
        <input
          aria-label={`Cantidad ${ingredient.name_raw}`}
          id={ingredientFieldId(ingredient.id, "quantity")}
          value={ingredient.quantity_raw}
          onChange={(event) => onChange({ quantity_raw: event.target.value })}
        />
        {ingredient.validation_errors.filter((issue) => issue.field === "quantity").map((issue) =>
          <span className={issue.level === "ERROR" ? "draft-error" : "draft-warning"} key={issue.code}>
            {issue.level === "ERROR" ? "Error bloqueante: " : "Advertencia: "}{issue.message}
          </span>
        )}
      </label>
      <label>Unidad
        <input
          aria-label={`Unidad ${ingredient.name_raw}`}
          id={ingredientFieldId(ingredient.id, "unit")}
          value={ingredient.unit_raw}
          onChange={(event) => onChange({ unit_raw: event.target.value })}
        />
        {ingredient.validation_errors.filter((issue) => issue.field === "unit").map((issue) =>
          <span className="draft-warning" key={issue.code}>Advertencia: {issue.message}</span>
        )}
      </label>
      <label>Ingrediente
        <input
          aria-label={`Ingrediente ${ingredient.name_raw}`}
          id={ingredientFieldId(ingredient.id, "name")}
          value={ingredient.name_raw}
          onChange={(event) => onChange({ name_raw: event.target.value })}
        />
        {ingredient.validation_errors.filter((issue) => issue.field === "name").map((issue) =>
          <span className={issue.level === "ERROR" ? "draft-error" : "draft-warning"} key={issue.code}>
            {issue.level === "ERROR" ? "Error bloqueante: " : "Advertencia: "}{issue.message}
          </span>
        )}
      </label>
    </div>
    <label>Observaciones
      <input
        aria-label={`Observaciones ${ingredient.name_raw}`}
        value={ingredient.observations}
        onChange={(event) => onChange({ observations: event.target.value })}
      />
    </label>
    {ingredient.relation_status === "REVISAR_COINCIDENCIA" ? <p className="draft-warning">He encontrado varias opciones. ¿Cuál corresponde?</p> : null}
    <label>Artículo correspondiente
      <select
        aria-label={`Relación ${ingredient.name_raw}`}
        id={ingredientFieldId(ingredient.id, "article_id")}
        value={ingredient.article_id ?? ingredient.relation_status}
        onChange={(event) => {
          const candidate = ingredient.article_candidates.find((item) => item.articulo_id === event.target.value);
          onChange(candidate
            ? { article_id: candidate.articulo_id, relation_status: "RELACIONADO" }
            : { article_id: null, relation_status: event.target.value as IngredientDraft["relation_status"] });
        }}
      >
        <option value="SIN_RELACIONAR">Dejar pendiente</option>
        <option value="CREAR_ARTICULO_PROPUESTO">Crear artículo nuevo</option>
        <option value="IGNORADO">No importar este ingrediente</option>
        {ingredient.article_candidates.map((candidate) => <option
          key={candidate.articulo_id}
          value={candidate.articulo_id}
        >{candidate.nombre} · {candidate.motivo}</option>)}
      </select>
    </label>
    {ingredient.article_candidates.length ? <details><summary>Ver detalles de las opciones</summary><ul>
      {ingredient.article_candidates.map((candidate) => <li key={candidate.articulo_id}>
        {candidate.nombre} · {candidate.codigo} · {candidate.unidad || "unidad no indicada"}
        {candidate.precio == null ? "" : ` · ${candidate.precio} €`} · {candidate.motivo}
      </li>)}
    </ul></details> : <p>No hemos encontrado opciones en Artículos.</p>}
    <button type="button" onClick={onDelete}>Eliminar ingrediente</button>
  </article>;
}

function issueCount(recipe: RecipeDraft) {
  return recipe.validation_errors.length
    + recipe.ingredients.reduce((total, ingredient) => total + ingredient.validation_errors.length, 0);
}

function humanRecipeState(recipe: RecipeDraft) {
  if (recipe.entity_type === "DESCARTAR" || recipe.proposed_action === "IGNORAR") return "No se importará";
  if (recipe.proposed_action === "REUTILIZAR_EXISTENTE") return "Ya existe";
  if (recipe.duplicate_candidates.length || recipe.proposed_action === "REQUIERE_REVISION") return "Necesita revisión";
  if (!recipe.procedure.some((step) => step.trim()) || !(Number(recipe.servings ?? recipe.yield_value) > 0)) return "Se puede importar, faltan datos";
  return "Listo";
}

function recipeFieldId(recipeId: string, field: string) {
  return `recipe-${recipeId}-${field}`;
}

function ingredientFieldId(ingredientId: string, field: string) {
  return `ingredient-${ingredientId}-${field}`;
}

function entityLabel(value: RecipeDraft["entity_type"]) {
  return {
    PRINCIPAL: "Elaboración principal",
    SUBELABORACION: "Subelaboración",
    COMPONENTE: "Componente",
    SECCION: "Sección informativa",
    DESCARTAR: "Ignorado",
  }[value];
}

function relationLabel(value: string) {
  return {
    relacionado: "Relacionado",
    coincidencia_dudosa: "Revisar coincidencia",
    sin_relacionar: "Sin relacionar",
  }[value] ?? value;
}

function proposalLabel(value: string) {
  return value.toLowerCase().replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}
