from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from dataclasses import asdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from MODELOS.preimportacion_escandallos_555b import (
    FichaPreimportacion555B,
    RelacionArticulo555B,
    ResultadoPreimportacion555B,
)
from SERVICIOS.depurador_fichas_tecnicas_555b import DepuradorFichasTecnicas555B
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.schema_escandallos_555a import normalizar_unidad


def _clave(valor: object) -> str:
    texto = str(valor or "").strip().lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto).split())


def _codigo_receta(nombre: str, hoja: str, fila: int) -> str:
    base = f"{_clave(nombre)}|{_clave(hoja)}|{fila}"
    return "REC-EXCEL-" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:10].upper()


def _firma_escandallo(escandallo: Escandallo) -> str:
    ingredientes = [
        f"{_clave(i.nombre)}:{round(float(i.cantidad), 8)}:{normalizar_unidad(i.unidad)}"
        for i in escandallo.receta.ingredientes
    ]
    base = (
        f"{_clave(escandallo.receta.nombre)}|{escandallo.receta.rendimiento}|"
        f"{normalizar_unidad(escandallo.receta.unidad_rendimiento)}|{'|'.join(sorted(ingredientes))}"
    )
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


class PreimportadorEscandallosExcel555B:
    """Prepara e importa escandallos Excel al modelo canónico 5.5.5A.

    Por defecto solo genera una vista previa. La escritura requiere
    ``confirmar=True`` y siempre crea una copia de seguridad si el repositorio
    canónico ya existe.
    """

    def __init__(
        self,
        ruta_articulos: str | Path = "DATOS/db/articulos.json",
        ruta_destino: str | Path = "DATOS/db/escandallos_canonicos.json",
    ) -> None:
        self.ruta_articulos = Path(ruta_articulos)
        self.ruta_destino = Path(ruta_destino)

    def ejecutar(self, ruta_excel: str | Path, *, confirmar: bool = False) -> dict[str, Any]:
        resultado = ResultadoPreimportacion555B(
            archivo_excel=str(Path(ruta_excel)),
            ruta_destino=str(self.ruta_destino),
            modo="IMPORTACION_CONFIRMADA" if confirmar else "VISTA_PREVIA",
        )
        try:
            depurado = DepuradorFichasTecnicas555B().depurar_archivo(ruta_excel)
        except Exception as exc:
            resultado.errores.append(f"No se pudo analizar el Excel: {exc}")
            return resultado.to_dict()

        if depurado.get("errores"):
            resultado.errores.extend(str(e) for e in depurado["errores"])
            return resultado.to_dict()

        articulos = self._cargar_articulos()
        repo = RepositorioEscandallos(self.ruta_destino)
        existentes = repo.listar()
        por_codigo = {e.receta.codigo.casefold(): e for e in existentes}
        por_nombre = {_clave(e.receta.nombre): e for e in existentes}

        fichas_convertibles: list[tuple[FichaPreimportacion555B, Escandallo]] = []
        duplicados_exactos_vistos: set[str] = set()

        for ficha in depurado.get("fichas", []):
            pre, escandallo = self._preparar_ficha(ficha, articulos)

            if pre.estado == "PREPARADA" and escandallo is not None:
                firma = _firma_escandallo(escandallo)
                if ficha.get("tipo_duplicado") == "DUPLICADO_EXACTO":
                    if firma in duplicados_exactos_vistos:
                        pre.accion = "OMITIR"
                        pre.motivo = "Duplicado exacto ya incluido en esta importación."
                    else:
                        duplicados_exactos_vistos.add(firma)
                elif ficha.get("tipo_duplicado") == "VARIANTES_MISMO_NOMBRE":
                    pre.estado = "REVISAR"
                    pre.accion = "OMITIR"
                    pre.motivo = "Existen variantes con el mismo nombre; requiere elección humana."

                if pre.accion != "OMITIR":
                    actual = por_codigo.get(pre.codigo.casefold()) or por_nombre.get(_clave(pre.nombre))
                    if actual is None:
                        pre.accion = "CREAR"
                        pre.motivo = "No existe en el repositorio canónico."
                    elif _firma_escandallo(actual) == firma:
                        pre.accion = "SIN_CAMBIOS"
                        pre.motivo = "El escandallo canónico ya contiene la misma versión."
                    else:
                        # Mantiene el código del registro existente para una actualización controlada.
                        escandallo.receta.codigo = actual.receta.codigo
                        pre.codigo = actual.receta.codigo
                        pre.accion = "ACTUALIZAR"
                        pre.motivo = "Existe una receta con el mismo nombre y contenido diferente."

            resultado.fichas.append(pre)
            if escandallo is not None and pre.accion in {"CREAR", "ACTUALIZAR"} and pre.estado == "PREPARADA":
                fichas_convertibles.append((pre, escandallo))

        if confirmar and not resultado.errores:
            copia = self._crear_copia_seguridad()
            resultado.copia_seguridad = str(copia) if copia else None
            finales = list(existentes)
            indice = {e.receta.codigo.casefold(): i for i, e in enumerate(finales)}
            for pre, escandallo in fichas_convertibles:
                clave = escandallo.receta.codigo.casefold()
                if clave in indice:
                    finales[indice[clave]] = escandallo
                else:
                    indice[clave] = len(finales)
                    finales.append(escandallo)
            if fichas_convertibles:
                repo.guardar_todos(finales)
                resultado.importados = len(fichas_convertibles)
                resultado.datos_reales_modificados = True

        return resultado.to_dict()

    def _preparar_ficha(
        self, ficha: dict[str, Any], articulos: list[dict[str, Any]]
    ) -> tuple[FichaPreimportacion555B, Escandallo | None]:
        nombre = str(ficha.get("nombre_normalizado") or ficha.get("nombre_original") or "").strip()
        codigo = _codigo_receta(nombre, str(ficha.get("hoja") or ""), int(ficha.get("fila_inicio") or 0))
        estado = str(ficha.get("estado") or "REVISAR")
        motivo = "Ficha depurada y preparada para conversión canónica."
        accion = "PENDIENTE"
        relaciones: list[RelacionArticulo555B] = []
        ingredientes_entidad: list[Ingrediente] = []

        if estado != "PREPARADA":
            pre = FichaPreimportacion555B(
                codigo=codigo,
                nombre=nombre,
                estado="REVISAR",
                accion="OMITIR",
                motivo="La Parte 4 marcó esta ficha para revisión.",
                hoja=str(ficha.get("hoja") or ""),
                fila_inicio=int(ficha.get("fila_inicio") or 0),
                fila_fin=int(ficha.get("fila_fin") or 0),
                rendimiento=float(ficha.get("rendimiento") or 0),
                unidad_rendimiento=str(ficha.get("unidad_rendimiento") or "u"),
                ingredientes=list(ficha.get("ingredientes") or []),
                relaciones_articulos=[],
                grupo_duplicado=ficha.get("grupo_duplicado"),
                tipo_duplicado=ficha.get("tipo_duplicado"),
                confianza=float(ficha.get("confianza_final") or 0),
            )
            return pre, None

        for pos, item in enumerate(ficha.get("ingredientes") or [], start=1):
            relacion = self._relacionar_articulo(str(item.get("nombre") or ""), articulos)
            relaciones.append(relacion)
            unidad = normalizar_unidad(str(item.get("unidad_normalizada") or item.get("unidad_original") or ""))
            if not unidad:
                unidad = "u"
            precio = item.get("precio_unitario")
            try:
                precio_float = float(precio or 0)
            except (TypeError, ValueError):
                precio_float = 0.0
            ingrediente = Ingrediente(
                codigo=relacion.articulo_id or f"ING-{codigo}-{pos:03d}",
                articulo_id=relacion.articulo_id,
                nombre=str(item.get("nombre") or "").strip(),
                cantidad=float(item.get("cantidad") or 0),
                unidad=unidad,
                precio_unitario=precio_float,
                observaciones=(
                    "Elaboración interna referenciada"
                    if item.get("tipo") == "ELABORACION"
                    else "Importado desde Excel 5.5.5B"
                ),
                metadata={
                    "origen": "excel",
                    "fila_origen": item.get("fila_origen"),
                    "tipo": item.get("tipo") or "ARTICULO",
                    "referencia_elaboracion": item.get("referencia_elaboracion"),
                    "confianza_enlace": relacion.confianza,
                },
            )
            ingredientes_entidad.append(ingrediente)

        rendimiento = float(ficha.get("rendimiento") or 0)
        unidad_rendimiento = normalizar_unidad(str(ficha.get("unidad_rendimiento") or "u")) or "u"
        receta = Receta(
            codigo=codigo,
            nombre=nombre,
            rendimiento=rendimiento,
            unidad_rendimiento=unidad_rendimiento,
            ingredientes=ingredientes_entidad,
        )
        coste_total = round(sum(i.cantidad * i.precio_unitario for i in ingredientes_entidad), 6)
        escandallo = Escandallo(receta=receta, coste_total=coste_total)

        pre = FichaPreimportacion555B(
            codigo=codigo,
            nombre=nombre,
            estado="PREPARADA",
            accion=accion,
            motivo=motivo,
            hoja=str(ficha.get("hoja") or ""),
            fila_inicio=int(ficha.get("fila_inicio") or 0),
            fila_fin=int(ficha.get("fila_fin") or 0),
            rendimiento=rendimiento,
            unidad_rendimiento=unidad_rendimiento,
            ingredientes=[asdict(i) for i in ingredientes_entidad],
            relaciones_articulos=relaciones,
            grupo_duplicado=ficha.get("grupo_duplicado"),
            tipo_duplicado=ficha.get("tipo_duplicado"),
            confianza=float(ficha.get("confianza_final") or 0),
        )
        return pre, escandallo

    def _cargar_articulos(self) -> list[dict[str, Any]]:
        if not self.ruta_articulos.exists():
            return []
        try:
            contenido = json.loads(self.ruta_articulos.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(contenido, dict):
            contenido = contenido.get("articulos") or contenido.get("data") or []
        return [a for a in contenido if isinstance(a, dict)]

    def _relacionar_articulo(self, nombre: str, articulos: list[dict[str, Any]]) -> RelacionArticulo555B:
        clave = _clave(nombre)
        exactos = [a for a in articulos if _clave(a.get("nombre") or a.get("articulo")) == clave]
        if len(exactos) == 1:
            art = exactos[0]
            return RelacionArticulo555B(
                ingrediente=nombre,
                estado="ENLAZADO",
                articulo_id=str(art.get("codigo") or "") or None,
                articulo_nombre=str(art.get("nombre") or art.get("articulo") or nombre),
                confianza=100.0,
            )
        if len(exactos) > 1:
            candidatos = [self._resumen_articulo(a, 100.0) for a in exactos[:5]]
            return RelacionArticulo555B(nombre, "CANDIDATOS", confianza=100.0, candidatos=candidatos)

        candidatos: list[tuple[float, dict[str, Any]]] = []
        for art in articulos:
            nombre_art = str(art.get("nombre") or art.get("articulo") or "")
            clave_art = _clave(nombre_art)
            if not clave_art:
                continue
            ratio = SequenceMatcher(None, clave, clave_art).ratio()
            if clave in clave_art or clave_art in clave:
                ratio = max(ratio, 0.88)
            if ratio >= 0.72:
                candidatos.append((ratio, art))
        candidatos.sort(key=lambda x: x[0], reverse=True)
        top = candidatos[:5]
        # Enlace automático solo con evidencia muy alta y separación clara del segundo candidato.
        if top and top[0][0] >= 0.94 and (len(top) == 1 or top[0][0] - top[1][0] >= 0.08):
            ratio, art = top[0]
            return RelacionArticulo555B(
                ingrediente=nombre,
                estado="ENLAZADO",
                articulo_id=str(art.get("codigo") or "") or None,
                articulo_nombre=str(art.get("nombre") or art.get("articulo") or nombre),
                confianza=round(ratio * 100, 2),
            )
        if top:
            return RelacionArticulo555B(
                ingrediente=nombre,
                estado="CANDIDATOS",
                confianza=round(top[0][0] * 100, 2),
                candidatos=[self._resumen_articulo(a, r * 100) for r, a in top],
            )
        return RelacionArticulo555B(ingrediente=nombre, estado="SIN_ENLACE", confianza=0.0)

    @staticmethod
    def _resumen_articulo(articulo: dict[str, Any], confianza: float) -> dict[str, Any]:
        return {
            "codigo": articulo.get("codigo"),
            "nombre": articulo.get("nombre") or articulo.get("articulo"),
            "proveedor": articulo.get("proveedor"),
            "precio": articulo.get("precio"),
            "confianza": round(confianza, 2),
        }

    def _crear_copia_seguridad(self) -> Path | None:
        if not self.ruta_destino.exists():
            return None
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = self.ruta_destino.with_name(f"{self.ruta_destino.stem}.backup_{sello}{self.ruta_destino.suffix}")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.ruta_destino, backup)
        return backup
