import { useRef, useState } from "react";
import { HostAiApiError } from "../../api/client";
import { bibliotecaService } from "../../services/bibliotecaService";
import type {
  BibliotecaImportSession,
  DraftValidationIssue,
  ImportDraft,
  ImportConfirmationResult,
  IngredientDraft,
  RecipeDraft,
} from "../../types/biblioteca";
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
    <p>Host AI transforma documentos en conocimiento estructurado. Solo una confirmación explícita aplica el borrador revisado.</p>
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
  const recipes = documento.entidades.filter((entity) => entity.kind === "RECETA");
  return <section className="catalog-section">
    <h3>Documento recibido</h3>
    <dl className="detail-grid">
      <dt>Nombre</dt><dd>{documento.nombre}</dd>
      <dt>Clasificación</dt><dd>{documento.clasificacion.tipo}</dd>
      <dt>Confianza</dt><dd>{Math.round(documento.clasificacion.confianza.valor * 100)}%</dd>
      <dt>Estado</dt><dd>Pendiente de revisión</dd>
      <dt>Recetas detectadas</dt><dd>{resumen.recetas_detectadas}</dd>
      <dt>Ingredientes detectados</dt><dd>{resumen.ingredientes_detectados}</dd>
      <dt>Ingredientes relacionados</dt><dd>{resumen.ingredientes_relacionados}</dd>
      <dt>Coincidencias dudosas</dt><dd>{resumen.coincidencias_dudosas}</dd>
      <dt>Ingredientes sin relacionar</dt><dd>{resumen.ingredientes_sin_relacionar}</dd>
      <dt>Posibles duplicados</dt><dd>{resumen.duplicados_detectados}</dd>
      <dt>Propuestas</dt><dd>{resumen.propuestas}</dd>
    </dl>
    <p>{documento.clasificacion.confianza.explicacion}</p>
    {documento.advertencias.length ? <><h4>Advertencias</h4><ul>{documento.advertencias.map((item) => <li key={item}>{item}</li>)}</ul></> : null}
    <h3>Entidades detectadas</h3>
    {recipes.length ? <ul className="operational-checks">{recipes.map((recipe) => <li key={recipe.id}>
      <strong>{recipe.name}</strong>
      <span> · {recipe.fields.ingredientes_estructurados?.length ?? 0} ingredientes</span>
      {recipe.fields.ingredientes_estructurados?.length ? <ul>
        {recipe.fields.ingredientes_estructurados.map((ingredient, index) => <li key={`${recipe.id}-${index}`}>
          {ingredient.cantidad_texto} {ingredient.unidad ?? ""} {ingredient.nombre_original}
          {" · "}{relationLabel(ingredient.estado_relacion)}
        </li>)}
      </ul> : <p>Sin ingredientes estructurados.</p>}
    </li>)}</ul> : <p>No se detectaron recetas con estructura suficiente.</p>}
    <DraftReview initialDraft={session.borrador} />
    <h3>Propuestas detectadas</h3>
    <ul className="operational-checks">{propuestas.map((proposal) => <li key={proposal.id}>
      <strong>{proposal.titulo || proposalLabel(proposal.tipo)}</strong>
      <span> · {Math.round(proposal.confianza.valor * 100)}% · Pendiente de revisión</span>
      <p>{proposal.explicacion}</p>
    </li>)}</ul>
    {session.limitaciones.length ? <><h4>Limitaciones</h4><ul>{session.limitaciones.map((item) => <li key={item}>{item}</li>)}</ul></> : null}
  </section>;
}

function DraftReview({ initialDraft }: { initialDraft: ImportDraft }) {
  const [draft, setDraft] = useState(initialDraft);
  const [selectedId, setSelectedId] = useState(initialDraft.recipes[0]?.id ?? "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [dirty, setDirty] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<ImportConfirmationResult | null>(null);
  const selected = draft.recipes.find((recipe) => recipe.id === selectedId);
  const blockingErrors = dirty ? [] : (draft.validation?.blocking_errors ?? []);
  const warnings = dirty ? [] : (draft.validation?.warnings ?? []);

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
    setDraft((current) => ({
      ...current,
      recipes: current.recipes.map((recipe) => recipe.id === id ? {
        ...recipe,
        ...changes,
        validation_errors: recipe.validation_errors.filter(
          (issue) => !(issue.field in changes),
        ),
      } : recipe),
    }));
  }

  function updateIngredient(recipeId: string, ingredientId: string, changes: Partial<IngredientDraft>) {
    setDirty(true);
    setAccepted(false);
    setDraft((current) => ({
      ...current,
      recipes: current.recipes.map((recipe) => recipe.id !== recipeId ? recipe : {
        ...recipe,
        ingredients: recipe.ingredients.map((ingredient) =>
          ingredient.id === ingredientId
            ? { ...ingredient, ...changes, validation_errors: [] }
            : ingredient
        ),
      }),
    }));
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
        draft.document_id, draft.version, "usuario_web",
      );
      setResult(response.resultado);
      setMessage("Importación confirmada y aplicada a la Biblioteca.");
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
    <h3>Revisar borrador</h3>
    <p>Host AI propone la estructura. Tú decides qué es principal, subelaboración, componente o información que debe ignorarse.</p>
    {!dirty && blockingErrors.length ? <section aria-label="Errores que impiden confirmar">
      <h4>Errores que impiden confirmar</h4>
      <ul>{blockingErrors.map((issue, index) => <li key={`${issue.code}-${issue.recipe_id}-${issue.ingredient_id}-${index}`}>
        <strong>Error bloqueante · {issue.recipe_title}</strong>: {issue.message}{" "}
        <button type="button" onClick={() => focusIssue(issue)}>Revisar campo</button>
      </li>)}</ul>
    </section> : null}
    {!dirty && warnings.length ? <section aria-label="Advertencias del borrador">
      <h4>Advertencias</h4>
      <ul>{warnings.map((issue, index) => <li key={`${issue.code}-${issue.recipe_id}-${issue.ingredient_id}-${index}`}>
        <strong>Advertencia · {issue.recipe_title}</strong>: {issue.message}{" "}
        <button type="button" onClick={() => focusIssue(issue)}>Revisar campo</button>
      </li>)}</ul>
    </section> : null}
    <div className="draft-review-layout">
      <aside aria-label="Secciones detectadas">
        {draft.recipes.map((recipe) => <button
          className={recipe.id === selectedId ? "active" : ""}
          key={recipe.id}
          onClick={() => setSelectedId(recipe.id)}
          type="button"
        >
          <strong>{recipe.title || "Sin título"}</strong>
          <span>{entityLabel(recipe.entity_type)} · {recipe.ingredients.length} ingredientes</span>
          {issueCount(recipe) ? <small>{issueCount(recipe)} avisos</small> : null}
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
            <option value="ACTUALIZAR_ELABORACION">Actualizar elaboración existente</option>
            <option value="ACTUALIZAR_RECETA">Actualizar receta existente</option>
            <option value="CREAR_SUBELABORACION">Crear como subelaboración</option>
            <option value="MANTENER_COMPONENTE">Mantener como componente</option>
            <option value="IGNORAR">Ignorar</option>
          </select>
        </label>
        {selected.duplicate_candidates.length ? <p className="draft-warning">Hay posibles duplicados. Revísalos antes de crear una elaboración nueva.</p> : null}
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
    </div>
    <button disabled={saving} type="button" onClick={() => void save()}>
      {saving ? "Guardando..." : "Guardar borrador"}
    </button>
    {message ? <p role="status">{message}</p> : null}
    <p><strong>Modo seguro:</strong> guardar este borrador no aplica ninguna propuesta.</p>
    {dirty ? <p className="draft-warning">Guarda el borrador revisado antes de confirmar la importación.</p> : null}
    <section className="confirmation-preview">
      <h4>Confirmación final</h4>
      <p>Se aplicarán {draft.recipes.filter((item) =>
        item.entity_type !== "DESCARTAR" && item.proposed_action !== "IGNORAR"
      ).length} elaboraciones revisadas en una única transacción.</p>
      <label>
        <input checked={accepted} onChange={(event) => setAccepted(event.target.checked)} type="checkbox" />
        He revisado el borrador y autorizo aplicar estos cambios.
      </label>
      <button disabled={dirty || blockingErrors.length > 0 || !accepted || confirming || Boolean(result)} type="button" onClick={() => void confirm()}>
        {confirming ? "Aplicando transacción..." : "Confirmar e importar"}
      </button>
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
    <label>Relación con Artículos
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
        <option value="SIN_RELACIONAR">Sin relacionar</option>
        <option value="CREAR_ARTICULO_PROPUESTO">Proponer crear artículo</option>
        <option value="IGNORADO">Ignorar</option>
        {ingredient.article_candidates.map((candidate) => <option
          key={candidate.articulo_id}
          value={candidate.articulo_id}
        >{candidate.nombre} · {candidate.motivo}</option>)}
      </select>
    </label>
    {ingredient.article_candidates.length ? <ul>
      {ingredient.article_candidates.map((candidate) => <li key={candidate.articulo_id}>
        {candidate.nombre} · {candidate.codigo} · {candidate.unidad || "unidad no indicada"}
        {candidate.precio == null ? "" : ` · ${candidate.precio} €`} · {candidate.motivo}
      </li>)}
    </ul> : <p>Sin candidatos en el Catálogo de Artículos.</p>}
    <button type="button" onClick={onDelete}>Eliminar ingrediente</button>
  </article>;
}

function issueCount(recipe: RecipeDraft) {
  return recipe.validation_errors.length
    + recipe.ingredients.reduce((total, ingredient) => total + ingredient.validation_errors.length, 0);
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
