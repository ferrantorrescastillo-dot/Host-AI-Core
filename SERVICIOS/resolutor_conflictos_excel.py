from __future__ import annotations
from typing import Dict, List, Any
import difflib
from MODELOS.conflictos_excel import ConflictoExcel, InformeConflictosExcel

class ResolutorConflictosExcel:
    """
    Host AI 3.0.2.7 - Resolución Inteligente de Conflictos Excel.

    Analiza antes de importar:
    - duplicados en artículos
    - artículos parecidos
    - cambios fuertes de precio
    - escandallos ya existentes
    - líneas inválidas
    - diferencias de stock fuertes
    - columnas desconocidas / faltantes obligatorias
    """

    def __init__(self, core):
        self.core = core
        self.ultimo_informe: Dict[str, Any] | None = None

    def analizar_archivo(self, ruta_archivo: str, filas_preview: int = 500) -> Dict[str, Any]:
        conflictos: List[ConflictoExcel] = []

        # Análisis general: detección y mapeo
        try:
            deteccion = self.core.detector_excel.detectar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=True)
            mapeo = self.core.mapeador_columnas_excel.mapear_desde_deteccion(deteccion)
            analisis = self.core.lector_excel.analizar_archivo(ruta_archivo, filas_preview=filas_preview, exportar_json=False)
            conflictos.extend(self._conflictos_mapeo(mapeo))
            conflictos.extend(self._conflictos_duplicados_crudos(analisis, mapeo))
        except Exception as exc:
            conflictos.append(ConflictoExcel(
                tipo="error_lectura",
                nivel="critico",
                mensaje=f"No se pudo analizar el Excel: {exc}",
                recomendacion="Revisar archivo o formato.",
                opciones=["cancelar"],
            ))

        # Artículos
        if hasattr(self.core, "importador_articulos_excel"):
            try:
                preview_art = self.core.importador_articulos_excel.vista_previa(ruta_archivo, filas_preview=filas_preview)
                conflictos.extend(self._conflictos_articulos(preview_art))
            except Exception:
                pass

        # Escandallos
        if hasattr(self.core, "importador_escandallos_excel"):
            try:
                preview_esc = self.core.importador_escandallos_excel.vista_previa(ruta_archivo, filas_preview=filas_preview)
                conflictos.extend(self._conflictos_escandallos(preview_esc))
            except Exception:
                pass

        # Inventario
        if hasattr(self.core, "importador_inventario_excel"):
            try:
                preview_inv = self.core.importador_inventario_excel.vista_previa(ruta_archivo, filas_preview=filas_preview)
                conflictos.extend(self._conflictos_inventario(preview_inv))
            except Exception:
                pass

        informe = self._crear_informe(ruta_archivo, conflictos)
        self.ultimo_informe = informe
        return informe

    def resumen_ultimo_informe(self) -> Dict[str, Any]:
        if not self.ultimo_informe:
            return {
                "lectura_host_ai": "No hay informe de conflictos todavía.",
                "total_conflictos": 0,
            }
        return self.ultimo_informe

    def resolver_conflicto(self, conflicto_id: str, decision: str) -> Dict[str, Any]:
        """
        Primera versión: guarda la decisión en el último informe.
        En 3.0.2.8 el asistente de importación usará estas decisiones.
        """
        if not self.ultimo_informe:
            raise ValueError("No hay informe activo.")
        for c in self.ultimo_informe.get("conflictos", []):
            if c.get("id") == conflicto_id:
                c["decision_usuario"] = decision
                return {
                    "conflicto_id": conflicto_id,
                    "decision": decision,
                    "lectura_host_ai": f"Decisión registrada: {decision}.",
                }
        raise ValueError(f"No existe conflicto: {conflicto_id}")

    def _conflictos_mapeo(self, mapeo: Dict[str, Any]) -> List[ConflictoExcel]:
        out = []
        for hoja in mapeo.get("hojas", []):
            for d in hoja.get("desconocidas", []):
                out.append(ConflictoExcel(
                    tipo="columna_desconocida",
                    nivel="aviso",
                    mensaje=f"Columna desconocida en hoja {hoja['hoja']}: {d.get('columna_original')}",
                    entidad=hoja["hoja"],
                    datos=d,
                    opciones=["ignorar", "mapear_manual"],
                    recomendacion="Mapear manualmente si la columna es importante.",
                ))
            for faltante in hoja.get("obligatorias_faltantes", []):
                out.append(ConflictoExcel(
                    tipo="campo_obligatorio_faltante",
                    nivel="critico",
                    mensaje=f"Falta campo obligatorio {faltante} en hoja {hoja['hoja']}.",
                    entidad=hoja["hoja"],
                    datos={"campo": faltante},
                    opciones=["cancelar", "mapear_manual"],
                    recomendacion="No importar hasta resolver el campo obligatorio.",
                ))
        return out


    def _conflictos_duplicados_crudos(self, analisis: Dict[str, Any], mapeo: Dict[str, Any]) -> List[ConflictoExcel]:
        out = []
        hojas_mapeo = {h["hoja"]: h for h in mapeo.get("hojas", [])}
        for hoja in analisis.get("hojas", []):
            map_hoja = hojas_mapeo.get(hoja.get("nombre"))
            if not map_hoja:
                continue
            campos = {
                m["columna_original"]: m["campo_canonico"]
                for m in map_hoja.get("mapeos", [])
                if m.get("campo_canonico") != "DESCONOCIDO"
            }
            vistos = {}
            for idx, fila in enumerate(hoja.get("vista_previa", []), start=2):
                normal = {}
                for col, val in fila.items():
                    campo = campos.get(col)
                    if campo and campo not in normal:
                        normal[campo] = val
                nombre = str(normal.get("ARTICULO") or normal.get("INGREDIENTE") or "").strip()
                codigo = str(normal.get("CODIGO") or "").strip()
                if not nombre and not codigo:
                    continue
                claves = []
                if codigo:
                    claves.append(("codigo", codigo.upper()))
                if nombre:
                    claves.append(("nombre", nombre.lower().strip()))
                for tipo_clave, clave in claves:
                    if clave in vistos:
                        out.append(ConflictoExcel(
                            tipo="duplicado_excel",
                            nivel="critico",
                            mensaje=f"Duplicado en hoja {hoja.get('nombre')}: {tipo_clave} {clave}",
                            entidad="fila_excel",
                            entidad_id=clave,
                            datos={"fila_actual": idx, "fila_anterior": vistos[clave], "fila": fila},
                            opciones=["fusionar", "renombrar", "ignorar"],
                            recomendacion="Revisar duplicado antes de importar.",
                        ))
                        break
                    vistos[clave] = idx
        return out


    def _conflictos_articulos(self, preview: Dict[str, Any]) -> List[ConflictoExcel]:
        out = []
        vistos = {}
        existentes = {}
        if hasattr(self.core.importador_articulos_excel, "articulos"):
            existentes = self.core.importador_articulos_excel.articulos

        nombres_existentes = [(aid, art.nombre) for aid, art in existentes.items()]
        for art in preview.get("articulos", []):
            aid = art.get("articulo_id", "")
            nombre = art.get("nombre", "")

            clave_nombre = nombre.lower().strip()
            if aid in vistos or clave_nombre in vistos:
                anterior = vistos.get(aid) or vistos.get(clave_nombre)
                out.append(ConflictoExcel(
                    tipo="duplicado_excel",
                    nivel="critico",
                    mensaje=f"Artículo duplicado en Excel: {aid or nombre}",
                    entidad="articulo",
                    entidad_id=aid,
                    datos={"actual": art, "anterior": anterior},
                    opciones=["fusionar", "renombrar", "ignorar"],
                    recomendacion="Fusionar si es el mismo producto.",
                ))
            vistos[aid] = art
            vistos[clave_nombre] = art

            precio_nuevo = float(art.get("precio_unitario", 0) or 0)
            if aid in existentes:
                existente = existentes[aid].to_dict()
                precio_ant = float(existente.get("precio_unitario", 0) or 0)
                if precio_ant and precio_nuevo and abs(precio_nuevo - precio_ant) / precio_ant > 0.15:
                    out.append(ConflictoExcel(
                        tipo="cambio_precio_fuerte",
                        nivel="aviso",
                        mensaje=f"Cambio de precio fuerte en {nombre}: {precio_ant} -> {precio_nuevo}",
                        entidad="articulo",
                        entidad_id=aid,
                        datos={"anterior": existente, "nuevo": art},
                        opciones=["actualizar", "mantener_anterior", "revisar"],
                        recomendacion="Revisar factura/proveedor antes de actualizar.",
                    ))
            elif hasattr(self.core, "costes_inteligente"):
                precio_ant = self.core.costes_inteligente.obtener_precio(nombre, aid)
                if precio_ant and precio_nuevo and abs(precio_nuevo - precio_ant) / precio_ant > 0.15:
                    out.append(ConflictoExcel(
                        tipo="cambio_precio_fuerte",
                        nivel="aviso",
                        mensaje=f"Cambio de precio fuerte en {nombre}: {precio_ant} -> {precio_nuevo}",
                        entidad="articulo",
                        entidad_id=aid,
                        datos={"anterior_precio": precio_ant, "nuevo": art},
                        opciones=["actualizar", "mantener_anterior", "revisar"],
                        recomendacion="Revisar factura/proveedor antes de actualizar.",
                    ))

            for eid, enombre in nombres_existentes:
                if eid == aid:
                    continue
                ratio = difflib.SequenceMatcher(None, nombre.lower(), enombre.lower()).ratio()
                if ratio >= 0.86:
                    out.append(ConflictoExcel(
                        tipo="articulo_parecido",
                        nivel="aviso",
                        mensaje=f"Artículo parecido detectado: '{nombre}' se parece a '{enombre}'.",
                        entidad="articulo",
                        entidad_id=aid,
                        datos={"nuevo": art, "existente_id": eid, "existente_nombre": enombre, "similitud": round(ratio, 3)},
                        opciones=["fusionar", "crear_nuevo", "ignorar"],
                        recomendacion="Fusionar si realmente es el mismo artículo.",
                    ))
        return out

    def _conflictos_escandallos(self, preview: Dict[str, Any]) -> List[ConflictoExcel]:
        out = []
        existentes = getattr(self.core.escandallos_inteligente, "escandallos", {})
        for esc in preview.get("escandallos", []):
            rid = esc.get("receta_id", "")
            if rid in existentes:
                out.append(ConflictoExcel(
                    tipo="escandallo_existente",
                    nivel="aviso",
                    mensaje=f"El escandallo ya existe: {rid}",
                    entidad="escandallo",
                    entidad_id=rid,
                    datos={"nuevo": esc, "existente": existentes[rid].to_dict()},
                    opciones=["reemplazar", "duplicar", "ignorar"],
                    recomendacion="Reemplazar solo si el Excel es más reciente.",
                ))
            if not esc.get("lineas"):
                out.append(ConflictoExcel(
                    tipo="escandallo_sin_lineas",
                    nivel="critico",
                    mensaje=f"Escandallo sin líneas: {rid}",
                    entidad="escandallo",
                    entidad_id=rid,
                    datos=esc,
                    opciones=["cancelar", "ignorar_receta"],
                    recomendacion="No importar recetas sin ingredientes.",
                ))
        return out

    def _conflictos_inventario(self, preview: Dict[str, Any]) -> List[ConflictoExcel]:
        out = []
        for cambio in preview.get("cambios", []):
            anterior = float(cambio.get("anterior", 0) or 0)
            nuevo = float(cambio.get("nuevo", 0) or 0)
            if anterior > 0 and abs(nuevo - anterior) / anterior > 0.5:
                out.append(ConflictoExcel(
                    tipo="diferencia_stock_fuerte",
                    nivel="aviso",
                    mensaje=f"Diferencia fuerte de stock en {cambio.get('nombre')}: {anterior} -> {nuevo}",
                    entidad="inventario",
                    entidad_id=cambio.get("articulo_id", ""),
                    datos=cambio,
                    opciones=["aceptar_ajuste", "revisar", "ignorar"],
                    recomendacion="Revisar recuento físico antes de aplicar.",
                ))
        for e in preview.get("errores", []):
            out.append(ConflictoExcel(
                tipo="error_inventario",
                nivel=e.get("nivel", "error"),
                mensaje=e.get("mensaje", "Error de inventario"),
                entidad="inventario",
                datos=e,
                opciones=["revisar", "ignorar_linea"],
                recomendacion="Revisar línea de inventario.",
            ))
        return out

    def _crear_informe(self, archivo: str, conflictos: List[ConflictoExcel]) -> Dict[str, Any]:
        crit = sum(1 for c in conflictos if c.nivel == "critico")
        avisos = sum(1 for c in conflictos if c.nivel == "aviso")
        info = sum(1 for c in conflictos if c.nivel not in ["critico", "aviso"])
        informe = InformeConflictosExcel(
            archivo=str(archivo),
            conflictos=conflictos,
            total_conflictos=len(conflictos),
            criticos=crit,
            avisos=avisos,
            informativos=info,
            puede_importar=crit == 0,
        )
        datos = informe.to_dict()
        if crit:
            datos["lectura_host_ai"] = f"Conflictos detectados: {len(conflictos)} total, {crit} críticos. No conviene importar aún."
        elif conflictos:
            datos["lectura_host_ai"] = f"Conflictos detectados: {len(conflictos)} avisos. Se puede importar con revisión."
        else:
            datos["lectura_host_ai"] = "No se han detectado conflictos importantes. Se puede importar."
        return datos
