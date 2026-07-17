from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from MODELOS.escandallos_inteligentes import EscandalloReceta, LineaEscandallo, NecesidadEscandallo


class MotorEscandallosInteligente:
    """Motor canónico de escandallos de Host AI Base.

    ES1 añade gestión manual completa y persistencia automática.
    """

    def __init__(self, db=None):
        self.db = db
        self.escandallos: Dict[str, EscandalloReceta] = {}
        self._cargar()

    @staticmethod
    def _limpiar_linea(linea: Dict[str, Any]) -> Dict[str, Any]:
        permitidos = {
            "nombre", "cantidad", "unidad", "tipo", "articulo_id", "elaboracion_id",
            "merma_porcentaje", "familia", "proveedor_preferente", "coste_unitario", "notas", "id",
        }
        return {k: v for k, v in linea.items() if k in permitidos}

    @classmethod
    def _desde_dict(cls, datos: Dict[str, Any]) -> EscandalloReceta:
        return EscandalloReceta(
            receta_id=str(datos.get("receta_id", "")).strip(),
            nombre=str(datos.get("nombre", "")).strip(),
            raciones_base=int(datos.get("raciones_base", 1) or 1),
            lineas=[LineaEscandallo(**cls._limpiar_linea(l)) for l in datos.get("lineas", []) or []],
            grupo=str(datos.get("grupo", "")),
            subgrupo=str(datos.get("subgrupo", "")),
            observaciones=str(datos.get("observaciones", datos.get("notas", ""))),
            activo=bool(datos.get("activo", True)),
            id=str(datos.get("id", "")),
            creado_en=str(datos.get("creado_en", "")),
            actualizado_en=str(datos.get("actualizado_en", datos.get("creado_en", ""))),
        )

    def _cargar(self) -> None:
        if not self.db:
            return
        for datos in self.db.cargar("escandallos"):
            try:
                esc = self._desde_dict(datos)
                if esc.receta_id:
                    self.escandallos[esc.receta_id] = esc
            except Exception:
                continue

    def _guardar(self) -> None:
        if self.db:
            self.db.guardar("escandallos", [e.to_dict() for e in self.escandallos.values()])

    @staticmethod
    def _tocar(esc: EscandalloReceta) -> None:
        esc.actualizado_en = datetime.now().isoformat(timespec="seconds")

    def registrar_escandallo(self, receta_id: str, nombre: str, raciones_base: int,
                              lineas: List[Dict[str, Any]], grupo: str = "", subgrupo: str = "",
                              observaciones: str = "", activo: bool = True) -> Dict[str, Any]:
        receta_id = (receta_id or "").strip().upper()
        if not receta_id:
            raise ValueError("La receta necesita un código.")
        if receta_id in self.escandallos:
            raise ValueError(f"Ya existe un escandallo con código {receta_id}.")
        if not (nombre or "").strip():
            raise ValueError("La receta necesita un nombre.")
        if int(raciones_base or 0) <= 0:
            raise ValueError("Las raciones base deben ser mayores que cero.")
        esc = EscandalloReceta(
            receta_id=receta_id,
            nombre=nombre.strip(),
            raciones_base=int(raciones_base),
            grupo=(grupo or "").strip(),
            subgrupo=(subgrupo or "").strip(),
            observaciones=(observaciones or "").strip(),
            activo=bool(activo),
            lineas=[LineaEscandallo(**self._limpiar_linea(linea)) for linea in lineas],
        )
        self.escandallos[receta_id] = esc
        self._guardar()
        return esc.to_dict()

    def obtener(self, receta_id: str) -> EscandalloReceta:
        receta_id = (receta_id or "").strip().upper()
        if receta_id not in self.escandallos:
            raise ValueError(f"No existe escandallo para receta: {receta_id}")
        return self.escandallos[receta_id]

    def listar(self, incluir_inactivos: bool = False) -> List[Dict[str, Any]]:
        datos = [e for e in self.escandallos.values() if incluir_inactivos or e.activo]
        datos.sort(key=lambda e: (not e.activo, e.nombre.lower(), e.receta_id))
        return [e.to_dict() for e in datos]

    def buscar(self, texto: str = "", incluir_inactivos: bool = True) -> List[Dict[str, Any]]:
        termino = (texto or "").strip().lower()
        resultados = []
        for e in self.escandallos.values():
            if not incluir_inactivos and not e.activo:
                continue
            hay = " ".join([e.receta_id, e.nombre, e.grupo, e.subgrupo, e.observaciones]).lower()
            if not termino or termino in hay:
                resultados.append(e)
        resultados.sort(key=lambda e: (not e.activo, e.nombre.lower()))
        return [e.to_dict() for e in resultados]

    def editar_escandallo(self, receta_id: str, **cambios: Any) -> Dict[str, Any]:
        esc = self.obtener(receta_id)
        for campo in ("nombre", "grupo", "subgrupo", "observaciones"):
            if campo in cambios and cambios[campo] is not None:
                setattr(esc, campo, str(cambios[campo]).strip())
        if cambios.get("raciones_base") is not None:
            raciones = int(cambios["raciones_base"])
            if raciones <= 0:
                raise ValueError("Las raciones base deben ser mayores que cero.")
            esc.raciones_base = raciones
        if cambios.get("activo") is not None:
            esc.activo = bool(cambios["activo"])
        self._tocar(esc)
        self._guardar()
        return esc.to_dict()

    def agregar_linea(self, receta_id: str, linea: Dict[str, Any]) -> Dict[str, Any]:
        esc = self.obtener(receta_id)
        limpia = self._limpiar_linea(linea)
        if not str(limpia.get("nombre", "")).strip():
            raise ValueError("El ingrediente necesita un nombre.")
        if float(limpia.get("cantidad", 0) or 0) <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        nueva = LineaEscandallo(**limpia)
        esc.lineas.append(nueva)
        self._tocar(esc)
        self._guardar()
        return nueva.to_dict()

    def editar_linea(self, receta_id: str, linea_id: str, **cambios: Any) -> Dict[str, Any]:
        esc = self.obtener(receta_id)
        linea = next((l for l in esc.lineas if l.id == linea_id), None)
        if not linea:
            raise ValueError(f"No existe la línea {linea_id}.")
        campos = {"nombre", "cantidad", "unidad", "tipo", "articulo_id", "elaboracion_id",
                  "merma_porcentaje", "familia", "proveedor_preferente", "coste_unitario", "notas"}
        for campo, valor in cambios.items():
            if campo not in campos or valor is None:
                continue
            if campo in {"cantidad", "merma_porcentaje", "coste_unitario"}:
                valor = float(valor)
            setattr(linea, campo, valor)
        if linea.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        self._tocar(esc)
        self._guardar()
        return linea.to_dict()

    def eliminar_linea(self, receta_id: str, linea_id: str) -> bool:
        esc = self.obtener(receta_id)
        antes = len(esc.lineas)
        esc.lineas = [l for l in esc.lineas if l.id != linea_id]
        if len(esc.lineas) == antes:
            return False
        self._tocar(esc)
        self._guardar()
        return True

    def duplicar(self, receta_id: str, nuevo_id: str, nuevo_nombre: str = "") -> Dict[str, Any]:
        origen = self.obtener(receta_id)
        nuevo_id = (nuevo_id or "").strip().upper()
        if not nuevo_id:
            raise ValueError("Indica el nuevo código.")
        if nuevo_id in self.escandallos:
            raise ValueError(f"Ya existe un escandallo con código {nuevo_id}.")
        lineas = []
        for l in origen.lineas:
            d = l.to_dict()
            d.pop("cantidad_bruta", None)
            d.pop("coste_total", None)
            d.pop("id", None)
            lineas.append(d)
        return self.registrar_escandallo(
            receta_id=nuevo_id,
            nombre=(nuevo_nombre or f"{origen.nombre} (copia)").strip(),
            raciones_base=origen.raciones_base,
            lineas=lineas,
            grupo=origen.grupo,
            subgrupo=origen.subgrupo,
            observaciones=origen.observaciones,
            activo=True,
        )

    def eliminar(self, receta_id: str) -> bool:
        receta_id = (receta_id or "").strip().upper()
        if receta_id not in self.escandallos:
            return False
        del self.escandallos[receta_id]
        self._guardar()
        return True

    def calcular_necesidades_receta(self, receta_id: str, raciones: int, origen: str = "") -> Dict[str, Any]:
        esc = self.obtener(receta_id)
        if not esc.activo:
            raise ValueError(f"El escandallo {receta_id} está desactivado.")
        factor = float(raciones) / float(esc.raciones_base or 1)
        necesidades: List[NecesidadEscandallo] = []
        for linea in esc.lineas:
            cantidad_neta = round(float(linea.cantidad or 0.0) * factor, 4)
            cantidad_bruta = round(linea.cantidad_bruta() * factor, 4)
            coste_estimado = round(cantidad_bruta * float(linea.coste_unitario or 0.0), 4)
            necesidades.append(NecesidadEscandallo(
                receta_id=esc.receta_id, receta=esc.nombre, nombre=linea.nombre,
                cantidad_neta=cantidad_neta, cantidad_bruta=cantidad_bruta, unidad=linea.unidad,
                tipo=linea.tipo, articulo_id=linea.articulo_id, elaboracion_id=linea.elaboracion_id,
                familia=linea.familia, proveedor_preferente=linea.proveedor_preferente,
                coste_estimado=coste_estimado, origen=origen,
            ))
        coste_total = round(sum(n.coste_estimado for n in necesidades), 4)
        return {
            "receta_id": esc.receta_id, "receta": esc.nombre,
            "raciones_base": esc.raciones_base, "raciones_calculadas": int(raciones),
            "factor": round(factor, 4), "necesidades": [n.to_dict() for n in necesidades],
            "coste_total_estimado": coste_total,
            "coste_por_racion_estimado": round(coste_total / int(raciones), 4) if int(raciones) else 0.0,
            "lectura_host_ai": f"Escandallo calculado para {esc.nombre}: {int(raciones)} raciones, {len(necesidades)} necesidades.",
        }

    def calcular_necesidades_evento(self, evento: Dict[str, Any]) -> Dict[str, Any]:
        pax = int(evento.get("pax", 0) or 0)
        necesidades_agregadas: Dict[str, Dict[str, Any]] = {}
        recetas_calculadas, recetas_sin_escandallo = [], []
        for servicio in evento.get("servicios", []):
            for pase in servicio.get("pases", []):
                platos = [p for p in list(pase.get("platos", []) or []) if isinstance(p, dict)]
                referencias: List[Dict[str, Any]] = []
                if platos:
                    for plato in platos:
                        receta_id = str(plato.get("escandallo_id") or "").strip().upper()
                        if not receta_id:
                            continue
                        usar_pax = bool(plato.get("usar_pax_evento", True))
                        raciones = pax if usar_pax else int(plato.get("raciones", 0) or 0)
                        if raciones <= 0:
                            raciones = pax
                        referencias.append({
                            "receta_id": receta_id,
                            "raciones": raciones,
                            "origen": f"Evento {evento.get('nombre')} / Pase {pase.get('nombre')} / Plato {plato.get('id') or receta_id}",
                        })
                else:
                    for receta_id in pase.get("recetas", []):
                        rid = str(receta_id or "").strip().upper()
                        if not rid:
                            continue
                        referencias.append({
                            "receta_id": rid,
                            "raciones": pax,
                            "origen": f"Evento {evento.get('nombre')} / Pase {pase.get('nombre')}",
                        })

                for referencia in referencias:
                    receta_id = referencia["receta_id"]
                    if receta_id not in self.escandallos or not self.escandallos[receta_id].activo:
                        recetas_sin_escandallo.append(receta_id)
                        continue
                    calculo = self.calcular_necesidades_receta(receta_id, int(referencia["raciones"]), referencia["origen"])
                    recetas_calculadas.append(calculo)
                    for nec in calculo["necesidades"]:
                        clave = nec.get("articulo_id") or nec.get("elaboracion_id") or f"{nec['nombre'].lower().strip()}|{nec['unidad']}"
                        item = necesidades_agregadas.setdefault(clave, {**nec, "cantidad_neta": 0.0, "cantidad_bruta": 0.0, "coste_estimado": 0.0, "origenes": []})
                        item["cantidad_neta"] += float(nec["cantidad_neta"])
                        item["cantidad_bruta"] += float(nec["cantidad_bruta"])
                        item["coste_estimado"] += float(nec["coste_estimado"])
                        item["origenes"].append(nec["origen"])
        agregadas = []
        for item in necesidades_agregadas.values():
            for k in ("cantidad_neta", "cantidad_bruta", "coste_estimado"):
                item[k] = round(item[k], 4)
            agregadas.append(item)
        coste_total = round(sum(i["coste_estimado"] for i in agregadas), 4)
        texto = f"Escandallo de evento calculado para '{evento.get('nombre')}' con {len(agregadas)} necesidades agregadas."
        if recetas_sin_escandallo:
            texto += f" Faltan escandallos para {len(recetas_sin_escandallo)} recetas."
        return {
            "evento_id": evento.get("id"), "evento": evento.get("nombre"), "pax": pax,
            "recetas_calculadas": recetas_calculadas, "recetas_sin_escandallo": recetas_sin_escandallo,
            "necesidades_agregadas": agregadas, "coste_total_estimado": coste_total,
            "coste_por_pax_estimado": round(coste_total / pax, 4) if pax else 0.0,
            "lectura_host_ai": texto,
        }
