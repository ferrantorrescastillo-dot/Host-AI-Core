from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Comprobacion555B74:
    clave: str
    estado: str
    detalle: str
    valor: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditorCierreEscandallos555B74:
    """Auditoría final y de solo lectura del bloque 5.5.5B.

    Verifica la base canónica, relaciones con artículos, cobertura económica,
    copias de seguridad, informes de importación y disponibilidad de los
    conectores conversacionales. No escribe ni corrige datos.
    """

    VERSION = "5.5.5B.7.4.1"

    MODULOS_REQUERIDOS = (
        "SERVICIOS.lector_modelo_canonico_555b72",
        "SERVICIOS.conector_escandallos_real_555",
        "SERVICIOS.enriquecedor_precios_articulos_555b731",
        "SERVICIOS.gestor_precio_venta_rentabilidad_555b732",
    )

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.db_dir = self.base_dir / "DATOS" / "db"
        self.info_dir = self.base_dir / "DATOS" / "informes"
        self.canonico_path = self.db_dir / "escandallos_canonicos.json"
        self.articulos_path = self.db_dir / "articulos.json"

    def auditar(self) -> dict[str, Any]:
        checks: list[Comprobacion555B74] = []
        escandallos = self._cargar_escandallos(checks)
        articulos = self._cargar_articulos(checks)
        self._auditar_modulos(checks)
        self._auditar_contenido(checks, escandallos, articulos)
        self._auditar_seguridad(checks)
        self._auditar_informes(checks)

        ok = sum(1 for c in checks if c.estado == "OK")
        revisar = sum(1 for c in checks if c.estado == "REVISAR")
        error = sum(1 for c in checks if c.estado == "ERROR")
        total = len(checks)
        porcentaje = round((ok / total) * 100, 2) if total else 0.0

        if error:
            estado = "CIERRE_NO_APROBADO"
        elif revisar:
            estado = "CIERRE_APROBADO_CON_PENDIENTES"
        else:
            estado = "CIERRE_APROBADO"

        return {
            "version": self.VERSION,
            "fecha_utc": datetime.now(timezone.utc).isoformat(),
            "base_dir": str(self.base_dir),
            "estado": estado,
            "resultado": {"ok": ok, "revisar": revisar, "error": error, "total": total, "porcentaje_ok": porcentaje},
            "metricas": self._metricas(escandallos, articulos),
            "comprobaciones": [c.to_dict() for c in checks],
            "datos_reales_modificados": False,
        }

    def _cargar_escandallos(self, checks: list[Comprobacion555B74]) -> list[dict[str, Any]]:
        if not self.canonico_path.exists():
            checks.append(Comprobacion555B74("base_canonica", "ERROR", "No existe DATOS/db/escandallos_canonicos.json"))
            return []
        try:
            data = json.loads(self.canonico_path.read_text(encoding="utf-8"))
        except Exception as exc:
            checks.append(Comprobacion555B74("base_canonica", "ERROR", f"JSON canónico inválido: {exc}"))
            return []
        registros = data if isinstance(data, list) else data.get("escandallos", []) if isinstance(data, dict) else []
        if not isinstance(registros, list):
            registros = []
        # Conservamos el registro completo. Algunas propiedades económicas
        # (por ejemplo precio_venta_unitario) se guardan en el envoltorio del
        # escandallo, mientras que nombre/ingredientes viven dentro de "receta".
        # Descartar el envoltorio hacía que la auditoría no viera precios válidos.
        normalizados: list[dict[str, Any]] = []
        for item in registros:
            if isinstance(item, dict):
                normalizados.append(item)
        estado = "OK" if normalizados else "ERROR"
        checks.append(Comprobacion555B74("base_canonica", estado, f"Escandallos canónicos cargados: {len(normalizados)}", len(normalizados)))
        return normalizados

    def _cargar_articulos(self, checks: list[Comprobacion555B74]) -> list[dict[str, Any]]:
        if not self.articulos_path.exists():
            checks.append(Comprobacion555B74("catalogo_articulos", "ERROR", "No existe DATOS/db/articulos.json"))
            return []
        try:
            data = json.loads(self.articulos_path.read_text(encoding="utf-8"))
        except Exception as exc:
            checks.append(Comprobacion555B74("catalogo_articulos", "ERROR", f"Catálogo de artículos inválido: {exc}"))
            return []
        registros = data if isinstance(data, list) else next((data[k] for k in ("articulos", "items", "registros") if isinstance(data.get(k), list)), []) if isinstance(data, dict) else []
        checks.append(Comprobacion555B74("catalogo_articulos", "OK" if registros else "REVISAR", f"Artículos disponibles: {len(registros)}", len(registros)))
        return [x for x in registros if isinstance(x, dict)]

    def _auditar_modulos(self, checks: list[Comprobacion555B74]) -> None:
        fallos: list[str] = []
        for nombre in self.MODULOS_REQUERIDOS:
            try:
                importlib.import_module(nombre)
            except Exception as exc:
                fallos.append(f"{nombre}: {exc}")
        if fallos:
            checks.append(Comprobacion555B74("modulos_importables", "ERROR", " | ".join(fallos)))
        else:
            checks.append(Comprobacion555B74("modulos_importables", "OK", f"Módulos requeridos importables: {len(self.MODULOS_REQUERIDOS)}"))

    @staticmethod
    def _receta_de_registro(registro: dict[str, Any]) -> dict[str, Any]:
        receta = registro.get("receta")
        return receta if isinstance(receta, dict) else registro

    @classmethod
    def _valor_economico(cls, registro: dict[str, Any], clave: str) -> Any:
        """Lee un dato económico tanto del envoltorio como de la receta.

        La 7.3.2 escribe el PVP en el registro canónico exterior para conservar
        compatibilidad. Otros importadores pueden guardarlo dentro de receta.
        La auditoría acepta ambas representaciones sin modificar la base.
        """
        if registro.get(clave) not in (None, ""):
            return registro.get(clave)
        receta = cls._receta_de_registro(registro)
        return receta.get(clave)

    def _auditar_contenido(self, checks: list[Comprobacion555B74], escandallos: list[dict[str, Any]], articulos: list[dict[str, Any]]) -> None:
        ids_articulos = {str(a.get("codigo") or a.get("id") or "").casefold() for a in articulos}
        total_lineas = 0
        enlazadas = 0
        con_precio_venta = 0
        nombres_vacios = 0
        codigos_vacios = 0
        recetas_sin_ingredientes = 0
        nombres_vistos: dict[str, int] = {}
        no_enlazados: list[dict[str, str]] = []

        for registro in escandallos:
            receta = self._receta_de_registro(registro)
            nombre = str(receta.get("nombre") or receta.get("receta") or registro.get("nombre") or "").strip()
            codigo = str(receta.get("codigo") or receta.get("receta_id") or receta.get("id") or registro.get("id") or registro.get("receta_id") or "").strip()
            if not nombre:
                nombres_vacios += 1
            if not codigo:
                codigos_vacios += 1
            if nombre:
                clave = " ".join(nombre.casefold().split())
                nombres_vistos[clave] = nombres_vistos.get(clave, 0) + 1
            ingredientes = receta.get("ingredientes") if isinstance(receta.get("ingredientes"), list) else []
            if not ingredientes:
                recetas_sin_ingredientes += 1
            for ing in ingredientes:
                if not isinstance(ing, dict):
                    continue
                total_lineas += 1
                art_id_raw = ing.get("articulo_id") or ing.get("codigo_articulo") or ""
                art_id = str(art_id_raw).casefold()
                if art_id and art_id in ids_articulos:
                    enlazadas += 1
                else:
                    no_enlazados.append({
                        "receta": nombre or "SIN_NOMBRE",
                        "ingrediente": str(ing.get("nombre") or ing.get("ingrediente") or ing.get("articulo") or "SIN_NOMBRE"),
                        "articulo_id": str(art_id_raw or "SIN_ID"),
                    })
            if self._valor_economico(registro, "precio_venta_unitario") not in (None, ""):
                con_precio_venta += 1

        if nombres_vacios or codigos_vacios or recetas_sin_ingredientes:
            checks.append(Comprobacion555B74("integridad_recetas", "ERROR", f"Nombres vacíos: {nombres_vacios}; códigos vacíos: {codigos_vacios}; recetas sin ingredientes: {recetas_sin_ingredientes}"))
        else:
            checks.append(Comprobacion555B74("integridad_recetas", "OK", "Todas las recetas tienen nombre, código e ingredientes."))

        duplicados = [n for n, c in nombres_vistos.items() if c > 1]
        checks.append(Comprobacion555B74("nombres_duplicados", "REVISAR" if duplicados else "OK", f"Grupos con nombre repetido: {len(duplicados)}", duplicados[:20]))

        cobertura = round((enlazadas / total_lineas) * 100, 2) if total_lineas else 0.0
        detalle_enlaces = f"Ingredientes enlazados por ID: {enlazadas}/{total_lineas} ({cobertura:.2f}%)"
        if no_enlazados:
            muestra = "; ".join(f"{x['ingrediente']} [{x['receta']}] ID={x['articulo_id']}" for x in no_enlazados[:10])
            detalle_enlaces += f". Sin enlace: {len(no_enlazados)} -> {muestra}"
        checks.append(Comprobacion555B74(
            "enlaces_articulos",
            "OK" if cobertura >= 95 else "REVISAR",
            detalle_enlaces,
            {"cobertura_pct": cobertura, "no_enlazados": no_enlazados},
        ))

        checks.append(Comprobacion555B74(
            "precios_venta",
            "OK" if con_precio_venta else "REVISAR",
            f"Recetas con precio de venta definido: {con_precio_venta}/{len(escandallos)}",
            con_precio_venta,
        ))

    def _auditar_seguridad(self, checks: list[Comprobacion555B74]) -> None:
        backups = list((self.db_dir / "backups").glob("*.bak")) if (self.db_dir / "backups").exists() else []
        checks.append(Comprobacion555B74("copias_seguridad", "OK" if backups else "REVISAR", f"Copias de seguridad encontradas: {len(backups)}", len(backups)))
        checks.append(Comprobacion555B74("modo_auditoria", "OK", "Auditoría ejecutada en solo lectura. No escribe ni corrige datos."))

    def _auditar_informes(self, checks: list[Comprobacion555B74]) -> None:
        esperados = (
            "preimportacion_555b.json",
            "resolucion_variantes_555b.json",
            "importacion_555b71.json",
        )
        presentes = [n for n in esperados if (self.info_dir / n).exists()]
        checks.append(Comprobacion555B74("trazabilidad_importacion", "OK" if len(presentes) == len(esperados) else "REVISAR", f"Informes disponibles: {len(presentes)}/{len(esperados)}", presentes))

    @classmethod
    def _metricas(cls, escandallos: list[dict[str, Any]], articulos: list[dict[str, Any]]) -> dict[str, Any]:
        ingredientes = sum(len(cls._receta_de_registro(r).get("ingredientes") or []) for r in escandallos)
        precios_venta = sum(1 for r in escandallos if cls._valor_economico(r, "precio_venta_unitario") not in (None, ""))
        return {
            "escandallos": len(escandallos),
            "ingredientes": ingredientes,
            "articulos": len(articulos),
            "precios_venta_definidos": precios_venta,
        }


def formatear_auditoria_555b74(resultado: dict[str, Any]) -> str:
    r = resultado.get("resultado", {})
    m = resultado.get("metricas", {})
    lines = [
        "HOST AI 5.5.5B.7.4.1",
        "CIERRE, VERSIONADO Y AUDITORÍA DEL IMPORTADOR DE ESCANDALLOS",
        "",
        f"Estado: {resultado.get('estado')}",
        f"Resultado: {r.get('ok', 0)}/{r.get('total', 0)} OK ({r.get('porcentaje_ok', 0):.2f}%)",
        f"A revisar: {r.get('revisar', 0)}",
        f"Errores: {r.get('error', 0)}",
        "",
        "MÉTRICAS",
        f"- Escandallos canónicos: {m.get('escandallos', 0)}",
        f"- Ingredientes: {m.get('ingredientes', 0)}",
        f"- Artículos: {m.get('articulos', 0)}",
        f"- Precios de venta definidos: {m.get('precios_venta_definidos', 0)}",
        "",
        "COMPROBACIONES",
    ]
    for c in resultado.get("comprobaciones", []):
        lines.append(f"- {c.get('clave')}: {c.get('estado')} | {c.get('detalle')}")
    lines += ["", "SEGURIDAD", "- Datos reales modificados: NO", "- Auditoría ejecutada en modo solo lectura."]
    return "\n".join(lines)
