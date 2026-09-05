from __future__ import annotations

import json
import re
import tempfile
from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from SERVICIOS.repository_initialization_policy import should_initialize_persistently


ESTADO_OPERATIVA = "OPERATIVA"
ESTADO_PENDIENTE = "PENDIENTE_DE_COMPLETAR"
ESTADO_ARCHIVADA = "ARCHIVADA"
ESTADOS_VALIDOS = {ESTADO_OPERATIVA, ESTADO_PENDIENTE, ESTADO_ARCHIVADA}

_CAMPOS_COMPLETITUD: list[tuple[str, str, bool]] = [
    ("nombre", "Nombre", True),
    ("codigo", "Código", True),
    ("categoria", "Categoría", True),
    ("tipo", "Tipo", True),
    ("descripcion", "Descripción", False),
    ("ingredientes", "Ingredientes", True),
    ("cantidades", "Cantidades", True),
    ("numero_raciones", "Rendimiento", True),
    ("elaboracion", "Elaboración paso a paso", True),
    ("tecnicas_culinarias", "Técnicas culinarias", False),
    ("coste_por_racion", "Coste por ración", False),
    ("tiempo_activo", "Tiempo activo", True),
    ("tiempo_pasivo", "Tiempo pasivo", False),
    ("tiempo_total", "Tiempo total", False),
    ("produccion_minima", "Producción mínima", False),
    ("produccion_maxima", "Producción máxima por tanda", True),
    ("personal_recomendado", "Personal recomendado", True),
    ("recursos_necesarios", "Recursos necesarios", False),
    ("vida_util_refrigerado", "Vida útil refrigerado", False),
    ("vida_util_congelado", "Vida útil congelada", True),
    ("tiempo_descongelacion", "Tiempo de descongelación", False),
    ("regeneracion", "Tiempo de regeneración", True),
    ("horizonte_recomendado_produccion", "Horizonte recomendado de producción", False),
    ("platos", "Platos donde se utiliza", False),
    ("menus_utilizacion", "Menús donde se utiliza", False),
    ("documentos_adjuntos", "Documentación adjunta", False),
]


@dataclass
class RecetaBiblioteca601:
    id: str
    nombre: str
    codigo: str
    familia: str
    tipo: str
    numero_raciones: float
    ingredientes: list[str]
    cantidades: list[str]
    elaboracion: str
    tiempo_elaboracion: str
    conservacion: str
    alergenos: list[str]
    observaciones: str
    fotografia: str
    estado: str
    version: int
    creado_en: str
    actualizado_en: str


class RepositorioBibliotecaRecetas601:
    """Persistencia local exclusiva de la Biblioteca de Recetas 6.0.1."""

    VERSION_MODELO = "6.0.1"

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.path = self.base_dir / "DATOS" / "db" / "biblioteca_recetas_601.json"
        if should_initialize_persistently():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._asegurar_archivo()

    def _asegurar_archivo(self) -> None:
        if self.path.exists():
            return
        payload = {
            "version_modelo": self.VERSION_MODELO,
            "actualizado_en": datetime.now().isoformat(timespec="seconds"),
            "recetas": [],
        }
        self._guardar_payload(payload)

    def _leer_payload(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            data = {}
        recetas = None
        if isinstance(data, dict):
            recetas = data.get("fichas_tecnicas") or data.get("recetas")
        if not isinstance(recetas, list):
            recetas = []
        recetas = [self._asegurar_ficha_tecnica(r) for r in recetas if isinstance(r, dict)]
        return {
            "version_modelo": str(data.get("version_modelo") or self.VERSION_MODELO),
            "actualizado_en": str(data.get("actualizado_en") or ""),
            "recetas": recetas,
        }

    def _guardar_payload(self, payload: dict[str, Any]) -> None:
        payload["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
        payload["version_modelo"] = self.VERSION_MODELO
        payload["fichas_tecnicas"] = list(payload.get("recetas") or [])
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent, suffix=".tmp") as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            temp_path = Path(tmp.name)
        temp_path.replace(self.path)

    @staticmethod
    def _normalizar_texto(texto: Any) -> str:
        return " ".join(str(texto or "").strip().split())

    def _normalizar_lista(self, valor: Any) -> list[str]:
        if isinstance(valor, list):
            return [self._normalizar_texto(v) for v in valor if self._normalizar_texto(v)]
        texto = self._normalizar_texto(valor)
        if not texto:
            return []
        return [self._normalizar_texto(v) for v in texto.split(",") if self._normalizar_texto(v)]

    @staticmethod
    def _campo_presente(valor: Any) -> bool:
        if isinstance(valor, list):
            return bool(valor)
        if isinstance(valor, dict):
            return bool(valor)
        return bool(str(valor or "").strip())

    def _valor_extendido(self, origen: dict[str, Any], existente: Optional[dict[str, Any]], campo: str, default: str = "") -> str:
        if campo in origen:
            return self._normalizar_texto(origen.get(campo))
        if existente:
            return self._normalizar_texto(existente.get(campo))
        return self._normalizar_texto(default)

    def _lista_extendida(self, origen: dict[str, Any], existente: Optional[dict[str, Any]], campo: str) -> list[str]:
        if campo in origen:
            return self._normalizar_lista(origen.get(campo))
        if existente:
            return self._normalizar_lista(existente.get(campo))
        return []

    @staticmethod
    def _valor_estructurado(
        origen: dict[str, Any], existente: Optional[dict[str, Any]], campo: str,
        default: Any = None,
    ) -> Any:
        """Conserva bool/0/dict/list; `_valor_extendido` se reserva para texto."""
        if campo in origen:
            return deepcopy(origen.get(campo))
        if existente and campo in existente:
            return deepcopy(existente.get(campo))
        return deepcopy(default)

    def _calcular_completitud(self, ficha: dict[str, Any]) -> dict[str, Any]:
        confirmados = 0
        pendientes: list[str] = []
        for campo, etiqueta, obligatorio in _CAMPOS_COMPLETITUD:
            if self._campo_presente(ficha.get(campo)):
                confirmados += 1
            elif obligatorio:
                pendientes.append(etiqueta)
        total = len(_CAMPOS_COMPLETITUD)
        porcentaje = int(round((confirmados / total) * 100)) if total else 0
        propuestas = list(ficha.get("propuestas_ia_pendientes") or [])
        return {
            "porcentaje": porcentaje,
            "campos_confirmados": confirmados,
            "total_campos_controlados": total,
            "propuestas_ia_pendientes": len(propuestas),
            "campos_obligatorios_pendientes": pendientes,
        }

    def _construir_ficha_tecnica(self, receta_base: dict[str, Any], receta_fuente: dict[str, Any], receta_existente: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        ficha = dict(receta_base)
        pending_import = list(
            receta_fuente.get("campos_pendientes_importacion")
            if "campos_pendientes_importacion" in receta_fuente
            else (receta_existente or {}).get("campos_pendientes_importacion") or []
        )
        try:
            informed_yield = float(receta_base.get("numero_raciones") or 0) > 0
        except (TypeError, ValueError):
            informed_yield = False
        if informed_yield:
            pending_import = [field for field in pending_import if field != "rendimiento"]
        if self._normalizar_texto(receta_base.get("elaboracion")):
            pending_import = [field for field in pending_import if field != "procedimiento"]
        ficha["campos_pendientes_importacion"] = list(dict.fromkeys(pending_import))
        structured_source = receta_fuente.get("ingredientes_estructurados")
        if structured_source is None and receta_existente:
            structured_source = receta_existente.get("ingredientes_estructurados")
        ficha["ingredientes_estructurados"] = [
            dict(item) for item in (structured_source or []) if isinstance(item, dict)
        ]
        ficha["categoria"] = self._valor_extendido(receta_fuente, receta_existente, "categoria")
        ficha["tipo_elaboracion"] = self._valor_extendido(
            receta_fuente, receta_existente, "tipo_elaboracion", receta_base.get("tipo") or "",
        )
        ficha["descripcion"] = self._valor_extendido(receta_fuente, receta_existente, "descripcion")
        ficha["tecnicas_culinarias"] = self._lista_extendida(receta_fuente, receta_existente, "tecnicas_culinarias")
        ficha["coste_total"] = self._valor_extendido(receta_fuente, receta_existente, "coste_total")
        ficha["precio"] = self._valor_extendido(receta_fuente, receta_existente, "precio")
        ficha["margen"] = self._valor_extendido(receta_fuente, receta_existente, "margen")
        ficha["rendimiento"] = self._valor_extendido(receta_fuente, receta_existente, "rendimiento", str(receta_base.get("numero_raciones") or ""))
        ficha["unidad_rendimiento"] = self._valor_extendido(
            receta_fuente, receta_existente, "unidad_rendimiento",
            "raciones" if receta_base.get("numero_raciones") else "",
        )
        ficha["cantidad_por_racion"] = (
            receta_fuente.get("cantidad_por_racion")
            if "cantidad_por_racion" in receta_fuente
            else deepcopy((receta_existente or {}).get("cantidad_por_racion"))
        )
        ficha["rendimiento_neto"] = self._valor_estructurado(receta_fuente, receta_existente, "rendimiento_neto")
        ficha["merma"] = self._valor_estructurado(receta_fuente, receta_existente, "merma")
        ficha["coste_por_racion"] = self._valor_extendido(receta_fuente, receta_existente, "coste_por_racion")
        ficha["tiempo_activo"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_activo")
        ficha["tiempo_pasivo"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_pasivo")
        ficha["tiempo_preparacion"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_preparacion")
        ficha["tiempo_coccion"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_coccion")
        ficha["tiempo_reposo"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_reposo")
        ficha["tiempo_enfriamiento"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_enfriamiento")
        ficha["tiempo_total"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_total", receta_base.get("tiempo_elaboracion") or "")
        ficha["produccion_minima"] = self._valor_extendido(receta_fuente, receta_existente, "produccion_minima")
        ficha["produccion_maxima"] = self._valor_extendido(receta_fuente, receta_existente, "produccion_maxima")
        ficha["unidad_tanda"] = self._valor_extendido(receta_fuente, receta_existente, "unidad_tanda")
        ficha["rendimiento_por_tanda"] = self._valor_estructurado(receta_fuente, receta_existente, "rendimiento_por_tanda")
        ficha["limitacion_tanda"] = self._valor_extendido(receta_fuente, receta_existente, "limitacion_tanda")
        ficha["personal_recomendado"] = self._valor_estructurado(receta_fuente, receta_existente, "personal_recomendado", "")
        ficha["intervencion_activa"] = self._valor_extendido(receta_fuente, receta_existente, "intervencion_activa")
        ficha["recursos_necesarios"] = self._lista_extendida(receta_fuente, receta_existente, "recursos_necesarios")
        ficha["estacion_zona"] = self._valor_extendido(receta_fuente, receta_existente, "estacion_zona")
        ficha["cuello_botella"] = self._valor_extendido(receta_fuente, receta_existente, "cuello_botella")
        ficha["puede_congelarse"] = self._valor_estructurado(receta_fuente, receta_existente, "puede_congelarse", "")
        ficha["puede_refrigerarse"] = self._valor_estructurado(receta_fuente, receta_existente, "puede_refrigerarse", "")
        ficha["vida_util_refrigerado"] = self._valor_extendido(receta_fuente, receta_existente, "vida_util_refrigerado")
        ficha["vida_util_congelado"] = self._valor_extendido(receta_fuente, receta_existente, "vida_util_congelado")
        ficha["tiempo_descongelacion"] = self._valor_extendido(receta_fuente, receta_existente, "tiempo_descongelacion")
        ficha["regeneracion"] = self._valor_extendido(receta_fuente, receta_existente, "regeneracion")
        ficha["puede_producirse_con_antelacion"] = self._valor_extendido(receta_fuente, receta_existente, "puede_producirse_con_antelacion")
        ficha["horizonte_recomendado_produccion"] = self._valor_extendido(receta_fuente, receta_existente, "horizonte_recomendado_produccion")
        ficha["mejora_con_reposo"] = self._valor_extendido(receta_fuente, receta_existente, "mejora_con_reposo")
        ficha["debe_elaborarse_mismo_dia"] = self._valor_extendido(receta_fuente, receta_existente, "debe_elaborarse_mismo_dia")
        ficha["necesita_horno"] = self._valor_extendido(receta_fuente, receta_existente, "necesita_horno")
        ficha["necesita_fuego"] = self._valor_extendido(receta_fuente, receta_existente, "necesita_fuego")
        ficha["necesita_abatidor"] = self._valor_extendido(receta_fuente, receta_existente, "necesita_abatidor")
        ficha["necesita_envasado_vacio"] = self._valor_extendido(receta_fuente, receta_existente, "necesita_envasado_vacio")
        ficha["espacio_camara"] = self._valor_extendido(receta_fuente, receta_existente, "espacio_camara")
        ficha["espacio_congelador"] = self._valor_extendido(receta_fuente, receta_existente, "espacio_congelador")
        ficha["elaboraciones_previas"] = self._lista_extendida(receta_fuente, receta_existente, "elaboraciones_previas")
        ficha["fondos"] = self._lista_extendida(receta_fuente, receta_existente, "fondos")
        ficha["salsas"] = self._lista_extendida(receta_fuente, receta_existente, "salsas")
        ficha["pures"] = self._lista_extendida(receta_fuente, receta_existente, "pures")
        ficha["otras_dependencias"] = self._lista_extendida(receta_fuente, receta_existente, "otras_dependencias")
        ficha["platos"] = self._lista_extendida(receta_fuente, receta_existente, "platos")
        ficha["menus_utilizacion"] = self._lista_extendida(receta_fuente, receta_existente, "menus_utilizacion")
        ficha["eventos_utilizacion"] = self._lista_extendida(receta_fuente, receta_existente, "eventos_utilizacion")
        ficha["otras_elaboraciones"] = self._lista_extendida(receta_fuente, receta_existente, "otras_elaboraciones")
        ficha["documentos_word"] = self._lista_extendida(receta_fuente, receta_existente, "documentos_word")
        ficha["documentos_pdf"] = self._lista_extendida(receta_fuente, receta_existente, "documentos_pdf")
        ficha["documentos_fotografias"] = self._lista_extendida(receta_fuente, receta_existente, "documentos_fotografias")
        ficha["notas_documentacion"] = self._valor_extendido(receta_fuente, receta_existente, "notas_documentacion")
        ficha["propuestas_ia_pendientes"] = self._lista_extendida(receta_fuente, receta_existente, "propuestas_ia_pendientes")
        ficha["procedencia_campos"] = dict(receta_fuente.get("procedencia_campos") if "procedencia_campos" in receta_fuente else (receta_existente or {}).get("procedencia_campos") or {})
        ficha["historial_procedencia"] = list(receta_fuente.get("historial_procedencia") if "historial_procedencia" in receta_fuente else (receta_existente or {}).get("historial_procedencia") or [])
        ficha["estados_campos_operativos"] = deepcopy(
            receta_fuente.get("estados_campos_operativos")
            if "estados_campos_operativos" in receta_fuente
            else (receta_existente or {}).get("estados_campos_operativos") or {}
        )
        ficha["documentos_adjuntos"] = (
            list(ficha.get("documentos_word") or [])
            + list(ficha.get("documentos_pdf") or [])
            + list(ficha.get("documentos_fotografias") or [])
        )
        ficha["ficha_tecnica"] = {
            "informacion_general": {
                "nombre": ficha.get("nombre", ""),
                "codigo": ficha.get("codigo", ""),
                "categoria": ficha.get("categoria", ""),
                "tipo": ficha.get("tipo", ""),
                "descripcion": ficha.get("descripcion", ""),
                "fotografias": [f for f in [ficha.get("fotografia", "")] if f] + list(ficha.get("documentos_fotografias") or []),
                "estado": ficha.get("estado", ""),
                "version": ficha.get("version", 1),
            },
            "receta": {
                "ingredientes": list(ficha.get("ingredientes") or []),
                "cantidades": list(ficha.get("cantidades") or []),
                "elaboracion": ficha.get("elaboracion", ""),
                "observaciones": ficha.get("observaciones", ""),
                "tecnicas_culinarias": list(ficha.get("tecnicas_culinarias") or []),
            },
            "escandallo": {
                "coste": ficha.get("coste_total", ""),
                "precio": ficha.get("precio", ""),
                "margen": ficha.get("margen", ""),
                "rendimiento": ficha.get("rendimiento", ""),
                "unidad_rendimiento": ficha.get("unidad_rendimiento", ""),
                "cantidad_por_racion": deepcopy(ficha.get("cantidad_por_racion")),
                "coste_por_racion": ficha.get("coste_por_racion", ""),
            },
            "produccion": {
                "tiempo_preparacion": ficha.get("tiempo_preparacion", ""),
                "tiempo_activo": ficha.get("tiempo_activo", ""),
                "tiempo_pasivo": ficha.get("tiempo_pasivo", ""),
                "tiempo_coccion": ficha.get("tiempo_coccion", ""),
                "tiempo_reposo": ficha.get("tiempo_reposo", ""),
                "tiempo_enfriamiento": ficha.get("tiempo_enfriamiento", ""),
                "tiempo_total": ficha.get("tiempo_total", ""),
                "produccion_minima": ficha.get("produccion_minima", ""),
                "produccion_maxima": ficha.get("produccion_maxima", ""),
                "unidad_tanda": ficha.get("unidad_tanda", ""),
                "rendimiento_por_tanda": ficha.get("rendimiento_por_tanda"),
                "limitacion_tanda": ficha.get("limitacion_tanda", ""),
                "personal_recomendado": ficha.get("personal_recomendado", ""),
                "intervencion_activa": ficha.get("intervencion_activa", ""),
                "recursos_necesarios": list(ficha.get("recursos_necesarios") or []),
                "estacion_zona": ficha.get("estacion_zona", ""),
                "cuello_botella": ficha.get("cuello_botella", ""),
            },
            "estados_campos_operativos": deepcopy(ficha.get("estados_campos_operativos") or {}),
            "conservacion": {
                "puede_congelarse": ficha.get("puede_congelarse", ""),
                "puede_refrigerarse": ficha.get("puede_refrigerarse", ""),
                "vida_util_refrigerado": ficha.get("vida_util_refrigerado", ""),
                "vida_util_congelado": ficha.get("vida_util_congelado", ""),
                "tiempo_descongelacion": ficha.get("tiempo_descongelacion", ""),
                "regeneracion": ficha.get("regeneracion", ""),
            },
            "planificacion": {
                "puede_producirse_con_antelacion": ficha.get("puede_producirse_con_antelacion", ""),
                "horizonte_recomendado_produccion": ficha.get("horizonte_recomendado_produccion", ""),
                "mejora_con_reposo": ficha.get("mejora_con_reposo", ""),
                "debe_elaborarse_mismo_dia": ficha.get("debe_elaborarse_mismo_dia", ""),
                "necesita_horno": ficha.get("necesita_horno", ""),
                "necesita_fuego": ficha.get("necesita_fuego", ""),
                "necesita_abatidor": ficha.get("necesita_abatidor", ""),
                "necesita_envasado_vacio": ficha.get("necesita_envasado_vacio", ""),
                "espacio_camara": ficha.get("espacio_camara", ""),
                "espacio_congelador": ficha.get("espacio_congelador", ""),
            },
            "dependencias": {
                "elaboraciones_previas": list(ficha.get("elaboraciones_previas") or []),
                "fondos": list(ficha.get("fondos") or []),
                "salsas": list(ficha.get("salsas") or []),
                "pures": list(ficha.get("pures") or []),
                "otras": list(ficha.get("otras_dependencias") or []),
            },
            "utilizacion": {
                "platos": list(ficha.get("platos") or []),
                "menus": list(ficha.get("menus_utilizacion") or []),
                "eventos": list(ficha.get("eventos_utilizacion") or []),
                "otras_elaboraciones": list(ficha.get("otras_elaboraciones") or []),
            },
            "documentacion": {
                "word": list(ficha.get("documentos_word") or []),
                "pdf": list(ficha.get("documentos_pdf") or []),
                "fotografias": list(ficha.get("documentos_fotografias") or []),
                "notas": ficha.get("notas_documentacion", ""),
            },
        }
        ficha["completitud"] = self._calcular_completitud(ficha)
        return ficha

    def _asegurar_ficha_tecnica(self, receta: dict[str, Any]) -> dict[str, Any]:
        receta = dict(receta or {})
        receta.setdefault("categoria", "")
        receta.setdefault("descripcion", "")
        receta.setdefault("tecnicas_culinarias", [])
        receta.setdefault("tiempo_activo", "")
        receta.setdefault("tiempo_pasivo", "")
        receta.setdefault("tiempo_total", self._normalizar_texto(receta.get("tiempo_elaboracion") or ""))
        receta.setdefault("unidad_rendimiento", "raciones" if receta.get("numero_raciones") else "")
        receta.setdefault("cantidad_por_racion", None)
        receta.setdefault("produccion_minima", "")
        receta.setdefault("produccion_maxima", "")
        receta.setdefault("personal_recomendado", "")
        receta.setdefault("recursos_necesarios", [])
        receta.setdefault("puede_congelarse", "")
        receta.setdefault("puede_refrigerarse", "")
        receta.setdefault("vida_util_refrigerado", "")
        receta.setdefault("vida_util_congelado", "")
        receta.setdefault("tiempo_descongelacion", "")
        receta.setdefault("regeneracion", "")
        receta.setdefault("puede_producirse_con_antelacion", "")
        receta.setdefault("horizonte_recomendado_produccion", "")
        receta.setdefault("mejora_con_reposo", "")
        receta.setdefault("debe_elaborarse_mismo_dia", "")
        receta.setdefault("necesita_horno", "")
        receta.setdefault("necesita_fuego", "")
        receta.setdefault("necesita_abatidor", "")
        receta.setdefault("necesita_envasado_vacio", "")
        receta.setdefault("espacio_camara", "")
        receta.setdefault("espacio_congelador", "")
        receta.setdefault("elaboraciones_previas", [])
        receta.setdefault("fondos", [])
        receta.setdefault("salsas", [])
        receta.setdefault("pures", [])
        receta.setdefault("otras_dependencias", [])
        receta.setdefault("platos", [])
        receta.setdefault("menus_utilizacion", [])
        receta.setdefault("eventos_utilizacion", [])
        receta.setdefault("otras_elaboraciones", [])
        receta.setdefault("documentos_word", [])
        receta.setdefault("documentos_pdf", [])
        receta.setdefault("documentos_fotografias", [])
        receta.setdefault("notas_documentacion", "")
        receta.setdefault("propuestas_ia_pendientes", [])
        receta.setdefault("procedencia_campos", {})
        receta.setdefault("historial_procedencia", [])
        return self._construir_ficha_tecnica(receta, receta, receta)

    def _siguiente_id(self, recetas: list[dict[str, Any]]) -> str:
        ultimo = 0
        for receta in recetas:
            texto_id = str(receta.get("id") or "")
            if texto_id.startswith("REC601-"):
                try:
                    ultimo = max(ultimo, int(texto_id.split("-")[-1]))
                except ValueError:
                    continue
        return f"REC601-{ultimo + 1:06d}"

    def _slug_codigo(self, nombre: str) -> str:
        base = re.sub(r"[^A-Z0-9]+", "-", self._normalizar_texto(nombre).upper()).strip("-")
        return base or "RECETA"

    def _siguiente_codigo(self, nombre: str, recetas: list[dict[str, Any]]) -> str:
        base = self._slug_codigo(nombre)
        usados = {str(r.get("codigo") or "").upper() for r in recetas}
        if base not in usados:
            return base
        idx = 2
        while f"{base}-{idx}" in usados:
            idx += 1
        return f"{base}-{idx}"

    def _estado_por_campos(self, receta: dict[str, Any], estado_forzado: Optional[str] = None) -> str:
        if estado_forzado == ESTADO_ARCHIVADA:
            return ESTADO_ARCHIVADA
        secundarios = [
            receta.get("familia"),
            receta.get("tipo"),
            receta.get("tiempo_elaboracion"),
            receta.get("conservacion"),
            receta.get("alergenos"),
            receta.get("observaciones"),
            receta.get("fotografia"),
        ]
        completo = True
        for valor in secundarios:
            if isinstance(valor, list):
                if not valor:
                    completo = False
                    break
            elif not self._normalizar_texto(valor):
                completo = False
                break
        return ESTADO_OPERATIVA if completo else ESTADO_PENDIENTE

    def _normalizar_receta(self, receta: dict[str, Any], recetas: list[dict[str, Any]], receta_existente: Optional[dict[str, Any]] = None) -> RecetaBiblioteca601:
        ahora = datetime.now().isoformat(timespec="seconds")
        nombre = self._normalizar_texto(receta.get("nombre"))
        ingredientes = self._normalizar_lista(receta.get("ingredientes"))
        cantidades = self._normalizar_lista(receta.get("cantidades"))
        alergenos = self._normalizar_lista(receta.get("alergenos"))

        if len(ingredientes) != len(cantidades):
            raise ValueError("Ingredientes y cantidades deben tener la misma longitud.")

        try:
            numero_raciones = float(receta.get("numero_raciones") or 0)
        except (TypeError, ValueError):
            numero_raciones = 0

        if receta_existente:
            receta_id = str(receta_existente.get("id") or self._siguiente_id(recetas))
            codigo = self._normalizar_texto(receta.get("codigo")) or str(receta_existente.get("codigo") or "")
            version = int(receta_existente.get("version") or 1) + 1
            creado_en = str(receta_existente.get("creado_en") or ahora)
        else:
            receta_id = self._siguiente_id(recetas)
            codigo = self._normalizar_texto(receta.get("codigo")) or self._siguiente_codigo(nombre, recetas)
            version = 1
            creado_en = ahora

        receta_norm = {
            "id": receta_id,
            "nombre": nombre,
            "codigo": codigo,
            "familia": self._normalizar_texto(receta.get("familia")),
            "tipo": self._normalizar_texto(receta.get("tipo")),
            "numero_raciones": numero_raciones,
            "ingredientes": ingredientes,
            "cantidades": cantidades,
            "elaboracion": self._normalizar_texto(receta.get("elaboracion")),
            "tiempo_elaboracion": self._normalizar_texto(receta.get("tiempo_elaboracion")),
            "conservacion": self._normalizar_texto(receta.get("conservacion")),
            "alergenos": alergenos,
            "observaciones": self._normalizar_texto(receta.get("observaciones")),
            "fotografia": self._normalizar_texto(receta.get("fotografia")),
            "version": version,
            "creado_en": creado_en,
            "actualizado_en": ahora,
        }

        estado_forzado = self._normalizar_texto(receta.get("estado")).upper() or None
        if estado_forzado and estado_forzado not in ESTADOS_VALIDOS:
            estado_forzado = None
        receta_norm["estado"] = self._estado_por_campos(receta_norm, estado_forzado)
        return RecetaBiblioteca601(**receta_norm)

    def _validar_obligatorios(self, receta: dict[str, Any]) -> list[str]:
        errores: list[str] = []
        if not self._normalizar_texto(receta.get("nombre")):
            errores.append("El nombre es obligatorio.")
        if not self._normalizar_texto(receta.get("elaboracion")):
            errores.append("La elaboración es obligatoria.")
        ingredientes = self._normalizar_lista(receta.get("ingredientes"))
        cantidades = self._normalizar_lista(receta.get("cantidades"))
        if not ingredientes:
            errores.append("Debes indicar al menos un ingrediente.")
        if not cantidades:
            errores.append("Debes indicar al menos una cantidad.")
        if ingredientes and cantidades and len(ingredientes) != len(cantidades):
            errores.append("Ingredientes y cantidades deben tener el mismo número de elementos.")
        try:
            raciones = float(receta.get("numero_raciones") or 0)
        except (TypeError, ValueError):
            raciones = 0
        if raciones <= 0:
            errores.append("El número de raciones debe ser mayor que cero.")
        return errores

    def validar_borrador_incompleto(self, receta: dict[str, Any]) -> list[str]:
        errores: list[str] = []
        if not self._normalizar_texto(receta.get("nombre")):
            errores.append("El nombre es obligatorio.")
        ingredientes = self._normalizar_lista(receta.get("ingredientes"))
        cantidades = self._normalizar_lista(receta.get("cantidades"))
        if not ingredientes:
            errores.append("Debes indicar al menos un ingrediente.")
        if not cantidades:
            errores.append("Debes indicar al menos una cantidad.")
        if ingredientes and cantidades and len(ingredientes) != len(cantidades):
            errores.append("Ingredientes y cantidades deben tener el mismo número de elementos.")
        return errores

    def listar(self, incluir_archivadas: bool = False) -> list[dict[str, Any]]:
        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        if incluir_archivadas:
            return recetas
        return [r for r in recetas if str(r.get("estado") or "") != ESTADO_ARCHIVADA]

    def buscar(self, *, nombre: str = "", ingrediente: str = "", familia: str = "", incluir_archivadas: bool = False) -> list[dict[str, Any]]:
        recetas = self.listar(incluir_archivadas=incluir_archivadas)
        n = self._normalizar_texto(nombre).lower()
        i = self._normalizar_texto(ingrediente).lower()
        f = self._normalizar_texto(familia).lower()
        resultado: list[dict[str, Any]] = []
        for receta in recetas:
            nombre_ok = not n or n in self._normalizar_texto(receta.get("nombre")).lower() or n in self._normalizar_texto(receta.get("codigo")).lower()
            ingrediente_ok = True
            if i:
                ingrediente_ok = any(i in self._normalizar_texto(x).lower() for x in receta.get("ingredientes", []))
            familia_ok = not f or f in self._normalizar_texto(receta.get("familia")).lower()
            if nombre_ok and ingrediente_ok and familia_ok:
                resultado.append(receta)
        return resultado

    def obtener(self, id_o_codigo: str) -> Optional[dict[str, Any]]:
        clave = self._normalizar_texto(id_o_codigo).lower()
        if not clave:
            return None
        for receta in self.listar(incluir_archivadas=True):
            if clave in {
                self._normalizar_texto(receta.get("id")).lower(),
                self._normalizar_texto(receta.get("codigo")).lower(),
            }:
                return receta
        return None

    def crear(self, receta: dict[str, Any]) -> dict[str, Any]:
        errores = self._validar_obligatorios(receta)
        if errores:
            return {"ok": False, "errores": errores}

        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        receta_norm = self._normalizar_receta(receta, recetas)

        codigo_nuevo = str(receta_norm.codigo).lower()
        if any(str(r.get("codigo") or "").lower() == codigo_nuevo for r in recetas):
            return {"ok": False, "errores": ["Ya existe una receta con ese código."]}

        recetas.append(self._construir_ficha_tecnica(asdict(receta_norm), receta))
        payload["recetas"] = recetas
        self._guardar_payload(payload)
        return {"ok": True, "receta": recetas[-1]}

    def crear_incompleta_desde_importacion(self, receta: dict[str, Any]) -> dict[str, Any]:
        """Persiste un borrador histórico sin inventar procedimiento ni rendimiento."""
        errores = self.validar_borrador_incompleto(receta)
        if errores:
            return {"ok": False, "errores": errores}

        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        receta_norm = self._normalizar_receta({
            **receta,
            "elaboracion": self._normalizar_texto(receta.get("elaboracion")),
            "numero_raciones": receta.get("numero_raciones") or 0,
            "estado": ESTADO_PENDIENTE,
        }, recetas)
        codigo_nuevo = str(receta_norm.codigo).lower()
        if any(str(item.get("codigo") or "").lower() == codigo_nuevo for item in recetas):
            return {"ok": False, "errores": ["Ya existe una receta con ese código."]}
        stored = self._construir_ficha_tecnica(asdict(receta_norm), receta)
        stored["estado"] = ESTADO_PENDIENTE
        stored["campos_pendientes_importacion"] = [
            field for field, value in (
                ("procedimiento", receta.get("elaboracion")),
                ("rendimiento", receta.get("numero_raciones")),
            ) if not value
        ]
        recetas.append(stored)
        payload["recetas"] = recetas
        self._guardar_payload(payload)
        return {"ok": True, "receta": stored}

    def editar_borrador_incompleto(self, id_o_codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        objetivo = self.obtener(id_o_codigo)
        if not objetivo:
            return {"ok": False, "errores": ["No se encontró la receta."]}
        if str(objetivo.get("estado") or "") != ESTADO_PENDIENTE:
            return {"ok": False, "errores": ["La receta no es un borrador incompleto."]}
        actualizada = {**objetivo, **cambios}
        errores = self.validar_borrador_incompleto(actualizada)
        if errores:
            return {"ok": False, "errores": errores}
        receta_norm = self._normalizar_receta(actualizada, recetas, receta_existente=objetivo)
        stored = self._construir_ficha_tecnica(asdict(receta_norm), actualizada, objetivo)
        for index, recipe in enumerate(recetas):
            if recipe.get("id") == objetivo.get("id"):
                recetas[index] = stored
                break
        payload["recetas"] = recetas
        self._guardar_payload(payload)
        return {"ok": True, "receta": stored}

    def editar(self, id_o_codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        objetivo = self.obtener(id_o_codigo)
        if not objetivo:
            return {"ok": False, "errores": ["No se encontró la receta."]}

        receta_actualizada = dict(objetivo)
        receta_actualizada.update(cambios)
        if str(receta_actualizada.get("estado") or "") == ESTADO_ARCHIVADA:
            receta_actualizada["estado"] = ESTADO_ARCHIVADA

        errores = self._validar_obligatorios(receta_actualizada)
        if errores:
            return {"ok": False, "errores": errores}

        receta_norm = self._normalizar_receta(receta_actualizada, recetas, receta_existente=objetivo)
        codigo_nuevo = str(receta_norm.codigo).lower()
        for r in recetas:
            if r.get("id") == objetivo.get("id"):
                continue
            if str(r.get("codigo") or "").lower() == codigo_nuevo:
                return {"ok": False, "errores": ["Ya existe otra receta con ese código."]}

        for i, r in enumerate(recetas):
            if r.get("id") == objetivo.get("id"):
                recetas[i] = self._construir_ficha_tecnica(asdict(receta_norm), receta_actualizada, objetivo)
                break

        payload["recetas"] = recetas
        self._guardar_payload(payload)
        return {"ok": True, "receta": recetas[i]}

    def duplicar(self, id_o_codigo: str) -> dict[str, Any]:
        original = self.obtener(id_o_codigo)
        if not original:
            return {"ok": False, "errores": ["No se encontró la receta a duplicar."]}
        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        copia = dict(original)
        copia["id"] = self._siguiente_id(recetas)
        copia["codigo"] = self._siguiente_codigo(f"{original.get('nombre', 'Receta')} copia", recetas)
        copia["nombre"] = f"{self._normalizar_texto(original.get('nombre'))} (Copia)".strip()
        copia["version"] = 1
        ahora = datetime.now().isoformat(timespec="seconds")
        copia["creado_en"] = ahora
        copia["actualizado_en"] = ahora
        copia["estado"] = self._estado_por_campos(copia)
        copia = self._construir_ficha_tecnica(copia, copia, original)
        recetas.append(copia)
        payload["recetas"] = recetas
        self._guardar_payload(payload)
        return {"ok": True, "receta": copia}

    def archivar(self, id_o_codigo: str) -> dict[str, Any]:
        payload = self._leer_payload()
        recetas = list(payload["recetas"])
        objetivo = self.obtener(id_o_codigo)
        if not objetivo:
            return {"ok": False, "errores": ["No se encontró la receta a archivar."]}
        for receta in recetas:
            if receta.get("id") == objetivo.get("id"):
                receta["estado"] = ESTADO_ARCHIVADA
                receta["actualizado_en"] = datetime.now().isoformat(timespec="seconds")
                receta["version"] = int(receta.get("version") or 1) + 1
                break
        payload["recetas"] = recetas
        self._guardar_payload(payload)
        return {"ok": True}

    def pendientes(self) -> list[dict[str, Any]]:
        pendientes: list[dict[str, Any]] = []
        for receta in self.listar(incluir_archivadas=False):
            faltantes = list(((receta.get("completitud") or {}).get("campos_obligatorios_pendientes") or []))
            if faltantes or str(receta.get("estado") or "") == ESTADO_PENDIENTE:
                pendientes.append(receta)
        return pendientes

    def listar_fichas_tecnicas(self, incluir_archivadas: bool = False) -> list[dict[str, Any]]:
        return self.listar(incluir_archivadas=incluir_archivadas)

    def obtener_ficha_tecnica(self, id_o_codigo: str) -> Optional[dict[str, Any]]:
        return self.obtener(id_o_codigo)

    def crear_ficha_tecnica(self, ficha: dict[str, Any]) -> dict[str, Any]:
        return self.crear(ficha)

    def editar_ficha_tecnica(self, id_o_codigo: str, cambios: dict[str, Any]) -> dict[str, Any]:
        return self.editar(id_o_codigo, cambios)

    def duplicar_ficha_tecnica(self, id_o_codigo: str) -> dict[str, Any]:
        return self.duplicar(id_o_codigo)

    def archivar_ficha_tecnica(self, id_o_codigo: str) -> dict[str, Any]:
        return self.archivar(id_o_codigo)

    def pendientes_fichas_tecnicas(self) -> list[dict[str, Any]]:
        return self.pendientes()


class BibliotecaRecetasUI601:
    def __init__(self, base_dir: Path):
        self.repo = RepositorioBibliotecaRecetas601(base_dir)

    def ejecutar(self) -> None:
        while True:
            self._imprimir_menu()
            op = input("Elige una opción: ").strip()
            if op == "1":
                self.buscar_receta()
            elif op == "2":
                self.nueva_receta()
            elif op == "3":
                self.editar_receta()
            elif op == "4":
                self.duplicar_receta()
            elif op == "5":
                self.archivar_receta()
            elif op == "6":
                self.ver_ficha_tecnica()
            elif op == "7":
                self.ver_pendientes()
            elif op == "0":
                return
            else:
                print("Opción no válida.")

    @staticmethod
    def _imprimir_menu() -> None:
        print("\nBIBLIOTECA DE RECETAS")
        print("1. Buscar receta")
        print("2. Nueva receta")
        print("3. Editar receta")
        print("4. Duplicar receta")
        print("5. Archivar receta")
        print("6. Ver ficha técnica")
        print("7. Recetas pendientes de completar")
        print("0. Volver")

    @staticmethod
    def _seleccionar_por_lista(recetas: list[dict[str, Any]]) -> Optional[str]:
        if not recetas:
            print("No hay recetas para mostrar.")
            return None
        for i, receta in enumerate(recetas, 1):
            print(f"{i}. {receta.get('nombre')} | {receta.get('codigo')} | {receta.get('estado')}")
        sel = input("Selecciona número (Enter=cancelar): ").strip()
        if not sel or not sel.isdigit():
            return None
        idx = int(sel)
        if idx < 1 or idx > len(recetas):
            return None
        return str(recetas[idx - 1].get("codigo") or "")

    @staticmethod
    def _pedir_lista(etiqueta: str) -> list[str]:
        print(f"{etiqueta} (una por línea, Enter vacío para terminar):")
        valores: list[str] = []
        while True:
            valor = input("- ").strip()
            if not valor:
                break
            valores.append(valor)
        return valores

    def _pedir_datos_receta(self, base: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        base = base or {}

        def pedir(campo: str, texto: str) -> str:
            anterior = str(base.get(campo) or "")
            prompt = f"{texto} [{anterior}]: " if anterior else f"{texto}: "
            valor = input(prompt).strip()
            return valor if valor else anterior

        ingredientes_base = list(base.get("ingredientes") or [])
        cantidades_base = list(base.get("cantidades") or [])
        alergenos_base = list(base.get("alergenos") or [])

        print("Ingredientes actuales:" if ingredientes_base else "")
        for item in ingredientes_base:
            print(f"- {item}")
        ingredientes = self._pedir_lista("Ingredientes") or ingredientes_base

        print("Cantidades actuales:" if cantidades_base else "")
        for item in cantidades_base:
            print(f"- {item}")
        cantidades = self._pedir_lista("Cantidades") or cantidades_base

        print("Alérgenos actuales:" if alergenos_base else "")
        for item in alergenos_base:
            print(f"- {item}")
        alergenos = self._pedir_lista("Alérgenos") or alergenos_base

        return {
            "nombre": pedir("nombre", "Nombre"),
            "codigo": pedir("codigo", "Código"),
            "familia": pedir("familia", "Familia"),
            "tipo": pedir("tipo", "Tipo"),
            "numero_raciones": pedir("numero_raciones", "Número de raciones"),
            "ingredientes": ingredientes,
            "cantidades": cantidades,
            "elaboracion": pedir("elaboracion", "Elaboración"),
            "tiempo_elaboracion": pedir("tiempo_elaboracion", "Tiempo de elaboración"),
            "conservacion": pedir("conservacion", "Conservación"),
            "alergenos": alergenos,
            "observaciones": pedir("observaciones", "Observaciones"),
            "fotografia": pedir("fotografia", "Fotografía (ruta o referencia)"),
            "estado": str(base.get("estado") or ""),
        }

    @staticmethod
    def _mostrar_lista(etiqueta: str, valores: list[str]) -> None:
        print(f"{etiqueta}:")
        if not valores:
            print("- Sin datos")
            return
        for valor in valores:
            print(f"- {valor}")

    def buscar_receta(self) -> None:
        print("\nBUSCAR RECETA")
        nombre = input("Nombre o código (vacío=sin filtro): ").strip()
        ingrediente = input("Ingrediente (vacío=sin filtro): ").strip()
        familia = input("Familia (vacío=sin filtro): ").strip()
        recetas = self.repo.buscar(nombre=nombre, ingrediente=ingrediente, familia=familia, incluir_archivadas=False)
        if not recetas:
            print("No se encontraron recetas.")
            return
        print(f"Se encontraron {len(recetas)} recetas:")
        for receta in recetas:
            print(f"- {receta.get('nombre')} | {receta.get('codigo')} | {receta.get('estado')}")

    def nueva_receta(self) -> None:
        print("\nNUEVA RECETA")
        datos = self._pedir_datos_receta()
        resultado = self.repo.crear(datos)
        if not resultado.get("ok"):
            print("No se pudo crear la receta:")
            for e in resultado.get("errores", []):
                print(f"- {e}")
            return
        receta = resultado["receta"]
        print(f"Receta guardada: {receta['nombre']} | {receta['codigo']} | Estado: {receta['estado']}")

    def editar_receta(self) -> None:
        print("\nEDITAR RECETA")
        recetas = self.repo.listar(incluir_archivadas=False)
        codigo = self._seleccionar_por_lista(recetas)
        if not codigo:
            print("Edición cancelada.")
            return
        actual = self.repo.obtener(codigo)
        if not actual:
            print("No se encontró la receta.")
            return
        cambios = self._pedir_datos_receta(base=actual)
        resultado = self.repo.editar(codigo, cambios)
        if not resultado.get("ok"):
            print("No se pudo editar la receta:")
            for e in resultado.get("errores", []):
                print(f"- {e}")
            return
        receta = resultado["receta"]
        print(f"Receta actualizada: {receta['nombre']} | Versión: {receta['version']} | Estado: {receta['estado']}")

    def duplicar_receta(self) -> None:
        print("\nDUPLICAR RECETA")
        recetas = self.repo.listar(incluir_archivadas=True)
        codigo = self._seleccionar_por_lista(recetas)
        if not codigo:
            print("Duplicado cancelado.")
            return
        resultado = self.repo.duplicar(codigo)
        if not resultado.get("ok"):
            print("No se pudo duplicar la receta:")
            for e in resultado.get("errores", []):
                print(f"- {e}")
            return
        receta = resultado["receta"]
        print(f"Receta duplicada: {receta['nombre']} | {receta['codigo']}")

    def archivar_receta(self) -> None:
        print("\nARCHIVAR RECETA")
        recetas = self.repo.listar(incluir_archivadas=False)
        codigo = self._seleccionar_por_lista(recetas)
        if not codigo:
            print("Archivado cancelado.")
            return
        confirmar = input("Escribe ARCHIVAR para confirmar: ").strip()
        if confirmar != "ARCHIVAR":
            print("Archivado cancelado.")
            return
        resultado = self.repo.archivar(codigo)
        if resultado.get("ok"):
            print("Receta archivada correctamente.")
        else:
            print("No se pudo archivar la receta.")

    def ver_ficha_tecnica(self) -> None:
        print("\nVER FICHA TÉCNICA")
        recetas = self.repo.listar(incluir_archivadas=True)
        codigo = self._seleccionar_por_lista(recetas)
        if not codigo:
            print("Consulta cancelada.")
            return
        receta = self.repo.obtener(codigo)
        if not receta:
            print("No se encontró la receta.")
            return
        print("\nFICHA TÉCNICA")
        print(f"Nombre: {receta.get('nombre')}")
        print(f"Código: {receta.get('codigo')}")
        print(f"Familia: {receta.get('familia')}")
        print(f"Tipo: {receta.get('tipo')}")
        print(f"Número de raciones: {receta.get('numero_raciones')}")
        print(f"Estado: {receta.get('estado')}")
        print(f"Versión: {receta.get('version')}")
        print(f"Tiempo elaboración: {receta.get('tiempo_elaboracion')}")
        print(f"Conservación: {receta.get('conservacion')}")
        print(f"Alérgenos: {', '.join(receta.get('alergenos', []))}")
        print(f"Fotografía: {receta.get('fotografia')}")
        print("Descripción:")
        print(receta.get("descripcion") or "")
        print("Ingredientes:")
        for ing, cant in zip(receta.get("ingredientes", []), receta.get("cantidades", [])):
            print(f"- {ing}: {cant}")
        print("Elaboración:")
        print(receta.get("elaboracion") or "")
        print("Observaciones:")
        print(receta.get("observaciones") or "")
        self._mostrar_lista("Técnicas culinarias", list(receta.get("tecnicas_culinarias") or []))
        print("Producción:")
        print(f"- Tiempo activo: {receta.get('tiempo_activo')}")
        print(f"- Tiempo pasivo: {receta.get('tiempo_pasivo')}")
        print(f"- Tiempo total: {receta.get('tiempo_total')}")
        print(f"- Producción mínima: {receta.get('produccion_minima')}")
        print(f"- Producción máxima por tanda: {receta.get('produccion_maxima')}")
        print(f"- Personal recomendado: {receta.get('personal_recomendado')}")
        self._mostrar_lista("Recursos necesarios", list(receta.get("recursos_necesarios") or []))
        print("Conservación:")
        print(f"- Puede congelarse: {receta.get('puede_congelarse')}")
        print(f"- Puede refrigerarse: {receta.get('puede_refrigerarse')}")
        print(f"- Vida útil refrigerado: {receta.get('vida_util_refrigerado')}")
        print(f"- Vida útil congelada: {receta.get('vida_util_congelado')}")
        print(f"- Tiempo de descongelación: {receta.get('tiempo_descongelacion')}")
        print(f"- Tiempo de regeneración: {receta.get('regeneracion')}")
        print("Planificación:")
        print(f"- Puede producirse con antelación: {receta.get('puede_producirse_con_antelacion')}")
        print(f"- Horizonte recomendado: {receta.get('horizonte_recomendado_produccion')}")
        print(f"- Mejora con reposo: {receta.get('mejora_con_reposo')}")
        print(f"- Debe elaborarse el mismo día: {receta.get('debe_elaborarse_mismo_dia')}")
        print(f"- Necesita horno: {receta.get('necesita_horno')}")
        print(f"- Necesita fuego: {receta.get('necesita_fuego')}")
        print(f"- Necesita abatidor: {receta.get('necesita_abatidor')}")
        print(f"- Necesita envasado al vacío: {receta.get('necesita_envasado_vacio')}")
        print(f"- Espacio en cámara: {receta.get('espacio_camara')}")
        print(f"- Espacio en congelador: {receta.get('espacio_congelador')}")
        self._mostrar_lista("Elaboraciones previas", list(receta.get("elaboraciones_previas") or []))
        self._mostrar_lista("Fondos", list(receta.get("fondos") or []))
        self._mostrar_lista("Salsas", list(receta.get("salsas") or []))
        self._mostrar_lista("Purés", list(receta.get("pures") or []))
        self._mostrar_lista("Otras dependencias", list(receta.get("otras_dependencias") or []))
        self._mostrar_lista("Platos", list(receta.get("platos") or []))
        self._mostrar_lista("Menús", list(receta.get("menus_utilizacion") or []))
        self._mostrar_lista("Eventos", list(receta.get("eventos_utilizacion") or []))
        self._mostrar_lista("Otras elaboraciones", list(receta.get("otras_elaboraciones") or []))
        self._mostrar_lista("Documentos Word", list(receta.get("documentos_word") or []))
        self._mostrar_lista("Documentos PDF", list(receta.get("documentos_pdf") or []))
        self._mostrar_lista("Fotografías adjuntas", list(receta.get("documentos_fotografias") or []))
        print("Notas de documentación:")
        print(receta.get("notas_documentacion") or "")
        completitud = dict(receta.get("completitud") or {})
        print("Completitud:")
        print(f"- {completitud.get('porcentaje', 0)} % completada")
        print(f"- {completitud.get('campos_confirmados', 0)} campos confirmados")
        print(f"- {completitud.get('propuestas_ia_pendientes', 0)} propuestas de IA pendientes")
        pendientes = list(completitud.get("campos_obligatorios_pendientes") or [])
        if pendientes:
            self._mostrar_lista("Campos obligatorios pendientes", pendientes)

    def ver_pendientes(self) -> None:
        print("\nRECETAS PENDIENTES DE COMPLETAR")
        pendientes = self.repo.pendientes()
        if not pendientes:
            print("No hay recetas pendientes.")
            return
        for receta in pendientes:
            faltantes = list(((receta.get("completitud") or {}).get("campos_obligatorios_pendientes") or []))
            if faltantes:
                print(f"- {receta.get('nombre')} | Pendiente de completar: {', '.join(faltantes)}")
        codigo = self._seleccionar_por_lista(pendientes)
        if not codigo:
            return
        abrir = input("¿Quieres abrirla para completar? [s/N]: ").strip().lower()
        if abrir in {"s", "si", "sí"}:
            actual = self.repo.obtener(codigo)
            if not actual:
                print("No se encontró la receta.")
                return
            cambios = self._pedir_datos_receta(base=actual)
            resultado = self.repo.editar(codigo, cambios)
            if resultado.get("ok"):
                receta = resultado["receta"]
                print(f"Receta actualizada: {receta['nombre']} | Estado: {receta['estado']}")
            else:
                print("No se pudo actualizar la receta pendiente.")
                for e in resultado.get("errores", []):
                    print(f"- {e}")


class BibliotecaFichasTecnicasUI601(BibliotecaRecetasUI601):
    def ejecutar(self) -> None:
        while True:
            self._imprimir_menu_fichas()
            op = input("Elige una opción: ").strip()
            if op == "1":
                self.buscar_ficha_tecnica()
            elif op == "2":
                self.nueva_ficha_tecnica()
            elif op == "3":
                self.editar_ficha_tecnica()
            elif op == "4":
                self.duplicar_ficha_tecnica()
            elif op == "5":
                self.archivar_ficha_tecnica()
            elif op == "6":
                self.ver_ficha_tecnica()
            elif op == "7":
                self.ver_pendientes_fichas_tecnicas()
            elif op == "0":
                return
            else:
                print("Opción no válida.")

    @staticmethod
    def _imprimir_menu_fichas() -> None:
        print("\nFICHAS TÉCNICAS")
        print("1. Buscar ficha técnica")
        print("2. Nueva ficha técnica")
        print("3. Editar ficha técnica")
        print("4. Duplicar ficha técnica")
        print("5. Archivar ficha técnica")
        print("6. Ver ficha técnica completa")
        print("7. Fichas pendientes de completar")
        print("0. Volver")

    def _pedir_datos_ficha_tecnica(self, base: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        base = base or {}
        datos = self._pedir_datos_receta(base=base)

        def pedir(campo: str, texto: str, default: str = "") -> str:
            anterior = str(base.get(campo) or default or "")
            prompt = f"{texto} [{anterior}]: " if anterior else f"{texto}: "
            valor = input(prompt).strip()
            return valor if valor else anterior

        def pedir_lista(campo: str, texto: str) -> list[str]:
            actuales = list(base.get(campo) or [])
            if actuales:
                print(f"{texto} actuales:")
                for item in actuales:
                    print(f"- {item}")
            return self._pedir_lista(texto) or actuales

        datos.update(
            {
                "categoria": pedir("categoria", "Categoría", datos.get("familia") or ""),
                "descripcion": pedir("descripcion", "Descripción"),
                "tecnicas_culinarias": pedir_lista("tecnicas_culinarias", "Técnicas culinarias"),
                "coste_total": pedir("coste_total", "Coste total"),
                "precio": pedir("precio", "Precio"),
                "margen": pedir("margen", "Margen"),
                "rendimiento": pedir("rendimiento", "Rendimiento", str(datos.get("numero_raciones") or "")),
                "coste_por_racion": pedir("coste_por_racion", "Coste por ración"),
                "tiempo_activo": pedir("tiempo_activo", "Tiempo activo"),
                "tiempo_pasivo": pedir("tiempo_pasivo", "Tiempo pasivo"),
                "tiempo_total": pedir("tiempo_total", "Tiempo total", datos.get("tiempo_elaboracion") or ""),
                "produccion_minima": pedir("produccion_minima", "Producción mínima"),
                "produccion_maxima": pedir("produccion_maxima", "Producción máxima por tanda"),
                "personal_recomendado": pedir("personal_recomendado", "Personal recomendado"),
                "recursos_necesarios": pedir_lista("recursos_necesarios", "Recursos necesarios"),
                "puede_congelarse": pedir("puede_congelarse", "Puede congelarse (si/no)"),
                "puede_refrigerarse": pedir("puede_refrigerarse", "Puede refrigerarse (si/no)"),
                "vida_util_refrigerado": pedir("vida_util_refrigerado", "Vida útil refrigerado"),
                "vida_util_congelado": pedir("vida_util_congelado", "Vida útil congelada"),
                "tiempo_descongelacion": pedir("tiempo_descongelacion", "Tiempo de descongelación"),
                "regeneracion": pedir("regeneracion", "Tiempo de regeneración"),
                "puede_producirse_con_antelacion": pedir("puede_producirse_con_antelacion", "Puede producirse con antelación (si/no)"),
                "horizonte_recomendado_produccion": pedir("horizonte_recomendado_produccion", "Horizonte recomendado de producción"),
                "mejora_con_reposo": pedir("mejora_con_reposo", "Mejora con reposo (si/no)"),
                "debe_elaborarse_mismo_dia": pedir("debe_elaborarse_mismo_dia", "Debe elaborarse el mismo día (si/no)"),
                "necesita_horno": pedir("necesita_horno", "Necesita horno (si/no)"),
                "necesita_fuego": pedir("necesita_fuego", "Necesita fuego (si/no)"),
                "necesita_abatidor": pedir("necesita_abatidor", "Necesita abatidor (si/no)"),
                "necesita_envasado_vacio": pedir("necesita_envasado_vacio", "Necesita envasado al vacío (si/no)"),
                "espacio_camara": pedir("espacio_camara", "Espacio aproximado en cámara"),
                "espacio_congelador": pedir("espacio_congelador", "Espacio aproximado en congelador"),
                "elaboraciones_previas": pedir_lista("elaboraciones_previas", "Elaboraciones previas"),
                "fondos": pedir_lista("fondos", "Fondos"),
                "salsas": pedir_lista("salsas", "Salsas"),
                "pures": pedir_lista("pures", "Purés"),
                "otras_dependencias": pedir_lista("otras_dependencias", "Otras dependencias"),
                "platos": pedir_lista("platos", "Platos"),
                "menus_utilizacion": pedir_lista("menus_utilizacion", "Menús"),
                "eventos_utilizacion": pedir_lista("eventos_utilizacion", "Eventos"),
                "otras_elaboraciones": pedir_lista("otras_elaboraciones", "Otras elaboraciones"),
                "documentos_word": pedir_lista("documentos_word", "Documentos Word"),
                "documentos_pdf": pedir_lista("documentos_pdf", "Documentos PDF"),
                "documentos_fotografias": pedir_lista("documentos_fotografias", "Fotografías adjuntas"),
                "notas_documentacion": pedir("notas_documentacion", "Notas de documentación"),
                "propuestas_ia_pendientes": pedir_lista("propuestas_ia_pendientes", "Propuestas IA pendientes"),
            }
        )
        return datos

    def buscar_ficha_tecnica(self) -> None:
        print("\nBUSCAR FICHA TÉCNICA")
        self.buscar_receta()

    def nueva_ficha_tecnica(self) -> None:
        print("\nNUEVA FICHA TÉCNICA")
        datos = self._pedir_datos_ficha_tecnica()
        resultado = self.repo.crear_ficha_tecnica(datos)
        if not resultado.get("ok"):
            print("No se pudo crear la ficha técnica:")
            for e in resultado.get("errores", []):
                print(f"- {e}")
            return
        ficha = resultado["receta"]
        print(f"Ficha técnica guardada: {ficha['nombre']} | {ficha['codigo']} | Estado: {ficha['estado']}")

    def editar_ficha_tecnica(self) -> None:
        print("\nEDITAR FICHA TÉCNICA")
        fichas = self.repo.listar_fichas_tecnicas(incluir_archivadas=False)
        codigo = self._seleccionar_por_lista(fichas)
        if not codigo:
            print("Edición cancelada.")
            return
        actual = self.repo.obtener_ficha_tecnica(codigo)
        if not actual:
            print("No se encontró la ficha técnica.")
            return
        cambios = self._pedir_datos_ficha_tecnica(base=actual)
        resultado = self.repo.editar_ficha_tecnica(codigo, cambios)
        if not resultado.get("ok"):
            print("No se pudo editar la ficha técnica:")
            for e in resultado.get("errores", []):
                print(f"- {e}")
            return
        ficha = resultado["receta"]
        print(f"Ficha técnica actualizada: {ficha['nombre']} | Versión: {ficha['version']} | Estado: {ficha['estado']}")

    def duplicar_ficha_tecnica(self) -> None:
        print("\nDUPLICAR FICHA TÉCNICA")
        fichas = self.repo.listar_fichas_tecnicas(incluir_archivadas=True)
        codigo = self._seleccionar_por_lista(fichas)
        if not codigo:
            print("Duplicado cancelado.")
            return
        resultado = self.repo.duplicar_ficha_tecnica(codigo)
        if not resultado.get("ok"):
            print("No se pudo duplicar la ficha técnica:")
            for e in resultado.get("errores", []):
                print(f"- {e}")
            return
        ficha = resultado["receta"]
        print(f"Ficha técnica duplicada: {ficha['nombre']} | {ficha['codigo']}")

    def archivar_ficha_tecnica(self) -> None:
        print("\nARCHIVAR FICHA TÉCNICA")
        fichas = self.repo.listar_fichas_tecnicas(incluir_archivadas=False)
        codigo = self._seleccionar_por_lista(fichas)
        if not codigo:
            print("Archivado cancelado.")
            return
        confirmar = input("Escribe ARCHIVAR para confirmar: ").strip()
        if confirmar != "ARCHIVAR":
            print("Archivado cancelado.")
            return
        resultado = self.repo.archivar_ficha_tecnica(codigo)
        if resultado.get("ok"):
            print("Ficha técnica archivada correctamente.")
        else:
            print("No se pudo archivar la ficha técnica.")

    def ver_pendientes_fichas_tecnicas(self) -> None:
        print("\nFICHAS TÉCNICAS PENDIENTES DE COMPLETAR")
        pendientes = self.repo.pendientes_fichas_tecnicas()
        if not pendientes:
            print("No hay fichas pendientes.")
            return
        for ficha in pendientes:
            faltantes = list(((ficha.get("completitud") or {}).get("campos_obligatorios_pendientes") or []))
            print(f"- {ficha.get('nombre')} | Pendiente de completar: {', '.join(faltantes) if faltantes else 'Revisión manual'}")
        codigo = self._seleccionar_por_lista(pendientes)
        if not codigo:
            return
        abrir = input("¿Quieres abrirla para completar? [s/N]: ").strip().lower()
        if abrir in {"s", "si", "sí"}:
            actual = self.repo.obtener_ficha_tecnica(codigo)
            if not actual:
                print("No se encontró la ficha técnica.")
                return
            cambios = self._pedir_datos_ficha_tecnica(base=actual)
            resultado = self.repo.editar_ficha_tecnica(codigo, cambios)
            if resultado.get("ok"):
                ficha = resultado["receta"]
                print(f"Ficha técnica actualizada: {ficha['nombre']} | Estado: {ficha['estado']}")
            else:
                print("No se pudo actualizar la ficha técnica pendiente.")
                for e in resultado.get("errores", []):
                    print(f"- {e}")


__all__ = [
    "BibliotecaFichasTecnicasUI601",
    "BibliotecaRecetasUI601",
    "RecetaBiblioteca601",
    "RepositorioBibliotecaRecetas601",
    "ESTADO_OPERATIVA",
    "ESTADO_PENDIENTE",
    "ESTADO_ARCHIVADA",
]
