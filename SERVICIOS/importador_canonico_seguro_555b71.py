from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from CORE.entidades.escandallo import Escandallo
from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from MODELOS.importacion_canonica_555b71 import (
    FichaPlanImportacion555B71,
    ResultadoImportacionCanonica555B71,
)
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.validador_escandallos_555a import validar_escandallo


def _leer_json(ruta: Path) -> dict[str, Any]:
    with ruta.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"El archivo {ruta} no contiene un objeto JSON válido.")
    return data


def _normalizar(texto: object) -> str:
    return " ".join(str(texto or "").strip().casefold().split())


def _firma_ficha(ficha: dict[str, Any]) -> str:
    ingredientes = []
    for ing in ficha.get("ingredientes") or []:
        ingredientes.append(
            f"{_normalizar(ing.get('nombre'))}|{float(ing.get('cantidad') or 0):.8f}|{_normalizar(ing.get('unidad'))}"
        )
    base = "|".join(
        [
            _normalizar(ficha.get("nombre")),
            f"{float(ficha.get('rendimiento') or 0):.8f}",
            _normalizar(ficha.get("unidad_rendimiento")),
            *sorted(ingredientes),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class ImportadorCanonicoSeguro555B71:
    """Motor de escritura segura de la Parte 7.1.

    Solo aplica decisiones automáticas de alta confianza provenientes de las
    Partes 5 y 6. Las variantes reales, títulos dudosos y fusiones manuales
    quedan pendientes. La escritura exige ``confirmar=True`` y se realiza de
    forma atómica, con copia de seguridad y diario de transacción.
    """

    def __init__(self, ruta_destino: str | Path = "DATOS/db/escandallos_canonicos.json") -> None:
        self.ruta_destino = Path(ruta_destino)

    def ejecutar(
        self,
        ruta_preimportacion: str | Path,
        ruta_resolucion: str | Path,
        *,
        confirmar: bool = False,
        ruta_diario: str | Path = "DATOS/informes/importacion_555b71.json",
    ) -> dict[str, Any]:
        pre_path = Path(ruta_preimportacion)
        res_path = Path(ruta_resolucion)
        resultado = ResultadoImportacionCanonica555B71(
            modo="IMPORTACION_CONFIRMADA" if confirmar else "VISTA_PREVIA",
            ruta_preimportacion=str(pre_path),
            ruta_resolucion=str(res_path),
            ruta_destino=str(self.ruta_destino),
        )

        try:
            pre = _leer_json(pre_path)
            resolucion = _leer_json(res_path)
            self._validar_fuentes(pre, resolucion)
            plan, candidatos = self._crear_plan(pre, resolucion)
            resultado.fichas.extend(plan)
        except Exception as exc:
            resultado.errores.append(str(exc))
            return resultado.to_dict()

        if confirmar and not resultado.errores:
            try:
                backup = self._crear_backup()
                if backup:
                    resultado.copia_seguridad = str(backup)
                self._aplicar_candidatos(candidatos)
                resultado.datos_reales_modificados = bool(candidatos)
                diario = self._guardar_diario(Path(ruta_diario), resultado.to_dict())
                resultado.diario_transaccion = str(diario)
            except Exception as exc:
                resultado.errores.append(f"Importación cancelada: {exc}")
                resultado.datos_reales_modificados = False

        return resultado.to_dict()

    @staticmethod
    def _validar_fuentes(pre: dict[str, Any], resolucion: dict[str, Any]) -> None:
        if not isinstance(pre.get("fichas"), list):
            raise ValueError("El informe de preimportación no contiene la lista 'fichas'.")
        if not isinstance(resolucion.get("decisiones"), list):
            raise ValueError("El informe de resolución no contiene la lista 'decisiones'.")
        if pre.get("errores"):
            raise ValueError("La preimportación contiene errores pendientes.")
        if resolucion.get("errores"):
            raise ValueError("La resolución de variantes contiene errores pendientes.")

    def _crear_plan(
        self, pre: dict[str, Any], resolucion: dict[str, Any]
    ) -> tuple[list[FichaPlanImportacion555B71], list[Escandallo]]:
        fichas = [f for f in pre.get("fichas", []) if isinstance(f, dict)]
        por_codigo = {str(f.get("codigo") or ""): f for f in fichas}

        recomendadas: set[str] = set()
        grupos_variantes: set[str] = set()
        for decision in resolucion.get("decisiones", []):
            if not isinstance(decision, dict):
                continue
            accion = decision.get("accion_propuesta")
            if accion == "SELECCIONAR_MEJOR_FICHA" and not decision.get("requiere_confirmacion", True):
                codigo = str(decision.get("ficha_recomendada") or "")
                if codigo:
                    recomendadas.add(codigo)
            elif accion in {"MANTENER_COMO_VARIANTES", "FUSIONAR_DUPLICADOS"}:
                grupos_variantes.add(_normalizar(decision.get("nombre")))

        invalidas = {
            str(f.get("codigo") or "")
            for f in resolucion.get("fichas_individuales", [])
            if isinstance(f, dict) and f.get("accion_propuesta") in {"REVISAR_TITULO", "REVISAR_FICHA"}
        }

        repo = RepositorioEscandallos(self.ruta_destino)
        existentes = repo.listar()
        por_codigo_existente = {e.receta.codigo.casefold(): e for e in existentes}
        por_nombre_existente = {_normalizar(e.receta.nombre): e for e in existentes}

        plan: list[FichaPlanImportacion555B71] = []
        candidatos: list[Escandallo] = []
        firmas_vistas: set[str] = set()

        for ficha in fichas:
            codigo = str(ficha.get("codigo") or "").strip()
            nombre = str(ficha.get("nombre") or "").strip()
            origen = f"{ficha.get('hoja', '')}:{ficha.get('fila_inicio', '')}"

            if codigo in invalidas or ficha.get("estado") != "PREPARADA":
                plan.append(FichaPlanImportacion555B71(codigo, nombre, "OMITIR", "Ficha pendiente de revisión humana.", origen))
                continue

            grupo = _normalizar(nombre)
            es_variante = grupo in grupos_variantes
            if es_variante:
                plan.append(FichaPlanImportacion555B71(codigo, nombre, "PENDIENTE_CONFIRMACION", "Variante real o fusión que requiere decisión humana.", origen))
                continue

            tipo_dup = ficha.get("tipo_duplicado")
            if tipo_dup == "DUPLICADO_EXACTO" and codigo not in recomendadas:
                plan.append(FichaPlanImportacion555B71(codigo, nombre, "OMITIR", "Duplicado equivalente; se conserva la ficha recomendada.", origen))
                continue

            escandallo = self._a_escandallo(ficha)
            validacion = validar_escandallo(escandallo)
            if not validacion.valido:
                plan.append(FichaPlanImportacion555B71(codigo, nombre, "OMITIR", "Escandallo inválido: " + " | ".join(validacion.errores), origen))
                continue

            firma = _firma_ficha(ficha)
            if firma in firmas_vistas:
                plan.append(FichaPlanImportacion555B71(codigo, nombre, "OMITIR", "Duplicado exacto dentro del lote de importación.", origen))
                continue
            firmas_vistas.add(firma)

            existente = por_codigo_existente.get(codigo.casefold()) or por_nombre_existente.get(_normalizar(nombre))
            if existente is None:
                accion = "CREAR"
                motivo = "Ficha válida y sin conflicto en la base canónica."
            else:
                existente_dict = {
                    "nombre": existente.receta.nombre,
                    "rendimiento": existente.receta.rendimiento,
                    "unidad_rendimiento": existente.receta.unidad_rendimiento,
                    "ingredientes": [
                        {"nombre": i.nombre, "cantidad": i.cantidad, "unidad": i.unidad}
                        for i in existente.receta.ingredientes
                    ],
                }
                if _firma_ficha(existente_dict) == firma:
                    plan.append(FichaPlanImportacion555B71(codigo, nombre, "SIN_CAMBIOS", "Ya existe la misma versión en la base canónica.", origen))
                    continue
                accion = "ACTUALIZAR"
                motivo = "Existe una receta con el mismo código o nombre y contenido distinto."
                escandallo.receta.codigo = existente.receta.codigo

            plan.append(
                FichaPlanImportacion555B71(
                    escandallo.receta.codigo,
                    nombre,
                    accion,
                    motivo,
                    origen,
                    self._escandallo_a_dict(escandallo),
                )
            )
            candidatos.append(escandallo)

        return plan, candidatos

    @staticmethod
    def _a_escandallo(ficha: dict[str, Any]) -> Escandallo:
        ingredientes: list[Ingrediente] = []
        for pos, item in enumerate(ficha.get("ingredientes") or [], start=1):
            ingredientes.append(
                Ingrediente(
                    codigo=str(item.get("codigo") or f"ING-{ficha.get('codigo')}-{pos:03d}"),
                    nombre=str(item.get("nombre") or "").strip(),
                    cantidad=float(item.get("cantidad") or 0),
                    unidad=str(item.get("unidad") or "u").strip(),
                    merma_pct=float(item.get("merma_pct") or 0),
                    articulo_id=item.get("articulo_id"),
                    proveedor_habitual=item.get("proveedor_habitual"),
                    precio_unitario=float(item.get("precio_unitario") or 0),
                    observaciones=str(item.get("observaciones") or "Importado por 5.5.5B.7.1"),
                    metadata=dict(item.get("metadata") or {}),
                )
            )
        receta = Receta(
            codigo=str(ficha.get("codigo") or "").strip(),
            nombre=str(ficha.get("nombre") or "").strip(),
            rendimiento=float(ficha.get("rendimiento") or 0),
            unidad_rendimiento=str(ficha.get("unidad_rendimiento") or "u").strip(),
            ingredientes=ingredientes,
        )
        coste = round(sum(i.cantidad * i.precio_unitario for i in ingredientes), 6)
        return Escandallo(receta=receta, coste_total=coste)

    @staticmethod
    def _escandallo_a_dict(escandallo: Escandallo) -> dict[str, Any]:
        return {
            "receta": {
                "codigo": escandallo.receta.codigo,
                "nombre": escandallo.receta.nombre,
                "rendimiento": escandallo.receta.rendimiento,
                "unidad_rendimiento": escandallo.receta.unidad_rendimiento,
                "ingredientes": [
                    {
                        "codigo": i.codigo,
                        "nombre": i.nombre,
                        "cantidad": i.cantidad,
                        "unidad": i.unidad,
                        "merma_pct": i.merma_pct,
                        "articulo_id": i.articulo_id,
                        "proveedor_habitual": i.proveedor_habitual,
                        "precio_unitario": i.precio_unitario,
                        "observaciones": i.observaciones,
                        "metadata": i.metadata,
                    }
                    for i in escandallo.receta.ingredientes
                ],
            },
            "coste_total": escandallo.coste_total,
        }

    def _aplicar_candidatos(self, candidatos: list[Escandallo]) -> None:
        if not candidatos:
            return
        repo = RepositorioEscandallos(self.ruta_destino)
        actuales = repo.listar()
        indice = {e.receta.codigo.casefold(): i for i, e in enumerate(actuales)}
        for candidato in candidatos:
            clave = candidato.receta.codigo.casefold()
            if clave in indice:
                actuales[indice[clave]] = candidato
            else:
                indice[clave] = len(actuales)
                actuales.append(candidato)
        self._guardar_atomico_verificado(repo, actuales)

    def _guardar_atomico_verificado(self, repo: RepositorioEscandallos, escandallos: list[Escandallo]) -> None:
        destino = self.ruta_destino
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(destino.parent)) as tmp_dir:
            temporal = Path(tmp_dir) / destino.name
            repo_temporal = RepositorioEscandallos(temporal)
            repo_temporal.guardar_todos(escandallos)
            verificados = repo_temporal.listar()
            if len(verificados) != len(escandallos):
                raise RuntimeError("La verificación del archivo temporal no coincide con el lote previsto.")
            os.replace(temporal, destino)

    def _crear_backup(self) -> Path | None:
        if not self.ruta_destino.exists():
            return None
        sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_dir = self.ruta_destino.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{self.ruta_destino.stem}_{sello}{self.ruta_destino.suffix}.bak"
        shutil.copy2(self.ruta_destino, backup)
        return backup

    @staticmethod
    def _guardar_diario(ruta: Path, payload: dict[str, Any]) -> Path:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(payload)
        payload["fecha_utc"] = datetime.now(timezone.utc).isoformat()
        temporal = ruta.with_suffix(ruta.suffix + ".tmp")
        temporal.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporal, ruta)
        return ruta
