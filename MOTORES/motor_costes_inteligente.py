from __future__ import annotations

from typing import Dict, List, Any
from MODELOS.costes_inteligentes import PrecioArticulo, CosteLinea, CosteReceta, CosteEvento, SimulacionPrecio


class MotorCostesInteligente:
    """
    Módulo Costes Inteligente v2.0.6.

    Calcula:
    - precios de artículos
    - coste de receta desde escandallo
    - coste por ración
    - food cost
    - margen bruto
    - coste de evento
    - extras de evento
    - simulaciones de variación de precios
    """

    def __init__(self, core):
        self.core = core
        self.precios: Dict[str, PrecioArticulo] = {}
        self.costes_recetas: Dict[str, CosteReceta] = {}
        self.costes_eventos: Dict[str, CosteEvento] = {}
        self.historial_escandallos: List[Dict[str, Any]] = []
        self._cargar_historial_escandallos()
        self.historial_costes_eventos: List[Dict[str, Any]] = []
        self._cargar_historial_costes_eventos()
        self.historial_rentabilidad: List[Dict[str, Any]] = []
        self._cargar_historial_rentabilidad()



    def _cargar_historial_costes_eventos(self) -> None:
        db = getattr(self.core, "db", None)
        if not db:
            return
        try:
            self.historial_costes_eventos = list(db.cargar("historial_costes_eventos") or [])
        except Exception:
            self.historial_costes_eventos = []

    def _guardar_historial_costes_eventos(self) -> None:
        db = getattr(self.core, "db", None)
        if db:
            db.guardar("historial_costes_eventos", self.historial_costes_eventos)

    def calcular_coste_evento_operativo(
        self, evento_id: str, precio_venta_por_pax: float = 0.0,
        horas_personal: float = 0.0, coste_hora: float = 0.0,
        costes_indirectos: float = 0.0, otros_costes: float = 0.0,
        coste_real_materia: float | None = None, registrar_historial: bool = True,
    ) -> Dict[str, Any]:
        base = self.calcular_coste_evento(evento_id, precio_venta_por_pax, extras=[])
        materia_prevista = float(base.get("coste_materia_prima", 0.0))
        materia_real = materia_prevista if coste_real_materia is None else float(coste_real_materia)
        mano_obra = round(float(horas_personal) * float(coste_hora), 4)
        indirectos = round(float(costes_indirectos), 4)
        otros = round(float(otros_costes), 4)
        previsto = round(materia_prevista + mano_obra + indirectos + otros, 4)
        real = round(materia_real + mano_obra + indirectos + otros, 4)
        venta = float(base.get("precio_venta_total", 0.0))
        beneficio_previsto = round(venta - previsto, 4) if venta else 0.0
        beneficio_real = round(venta - real, 4) if venta else 0.0
        margen_previsto = round((beneficio_previsto / venta) * 100, 2) if venta else 0.0
        margen_real = round((beneficio_real / venta) * 100, 2) if venta else 0.0
        pax = int(base.get("pax", 0) or 0)
        resultado = {
            **base,
            "coste_materia_previsto": materia_prevista,
            "coste_materia_real": materia_real,
            "coste_mano_obra": mano_obra,
            "costes_indirectos": indirectos,
            "otros_costes": otros,
            "coste_total_previsto": previsto,
            "coste_total_real": real,
            "desviacion": round(real - previsto, 4),
            "coste_previsto_por_pax": round(previsto / pax, 4) if pax else 0.0,
            "coste_real_por_pax": round(real / pax, 4) if pax else 0.0,
            "beneficio_previsto": beneficio_previsto,
            "beneficio_real": beneficio_real,
            "margen_previsto_porcentaje": margen_previsto,
            "margen_real_porcentaje": margen_real,
        }
        if registrar_historial:
            from datetime import datetime
            item = {k: resultado.get(k) for k in [
                "evento_id", "evento", "pax", "precio_venta_total",
                "coste_materia_previsto", "coste_materia_real", "coste_mano_obra",
                "costes_indirectos", "otros_costes", "coste_total_previsto",
                "coste_total_real", "desviacion", "beneficio_previsto",
                "beneficio_real", "margen_previsto_porcentaje", "margen_real_porcentaje"
            ]}
            item["fecha"] = datetime.now().isoformat(timespec="seconds")
            self.historial_costes_eventos.append(item)
            self.historial_costes_eventos = self.historial_costes_eventos[-500:]
            self._guardar_historial_costes_eventos()
        return resultado

    def listar_historial_costes_eventos(self, evento_id: str = "") -> List[Dict[str, Any]]:
        datos = self.historial_costes_eventos
        if evento_id:
            datos = [x for x in datos if x.get("evento_id") == evento_id]
        return sorted(datos, key=lambda x: x.get("fecha", ""), reverse=True)

    def _cargar_historial_escandallos(self) -> None:
        db = getattr(self.core, "db", None)
        if not db:
            return
        try:
            self.historial_escandallos = list(db.cargar("historial_escandallos_costes") or [])
        except Exception:
            self.historial_escandallos = []

    def _guardar_historial_escandallos(self) -> None:
        db = getattr(self.core, "db", None)
        if db:
            db.guardar("historial_escandallos_costes", self.historial_escandallos)

    def _registrar_historial_escandallo(self, datos: Dict[str, Any], tipo: str = "calculo") -> None:
        from datetime import datetime
        item = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "tipo": tipo,
            "receta_id": datos.get("receta_id", ""),
            "receta": datos.get("receta", ""),
            "raciones": datos.get("raciones", 0),
            "coste_total": datos.get("coste_total", 0.0),
            "coste_por_racion": datos.get("coste_por_racion", 0.0),
            "precio_venta_por_racion": datos.get("precio_venta_por_racion", 0.0),
            "margen_bruto": datos.get("margen_bruto", 0.0),
            "food_cost_porcentaje": datos.get("food_cost_porcentaje", 0.0),
            "avisos": list(datos.get("avisos", []) or []),
        }
        self.historial_escandallos.append(item)
        self.historial_escandallos = self.historial_escandallos[-500:]
        self._guardar_historial_escandallos()

    def listar_historial_escandallo(self, receta_id: str = "") -> List[Dict[str, Any]]:
        rid = (receta_id or "").strip().upper()
        datos = [h for h in self.historial_escandallos if not rid or str(h.get("receta_id", "")).upper() == rid]
        return sorted(datos, key=lambda x: x.get("fecha", ""), reverse=True)

    def simular_precio_linea_receta(self, receta_id: str, raciones: int, linea_nombre: str, nuevo_precio: float, precio_venta_por_racion: float = 0.0) -> Dict[str, Any]:
        antes = self.calcular_coste_receta(receta_id, raciones, precio_venta_por_racion, registrar_historial=False)
        objetivo = (linea_nombre or "").strip().lower()
        lineas = []
        encontrado = False
        for linea in antes["lineas"]:
            nueva = dict(linea)
            if nueva.get("nombre", "").strip().lower() == objetivo or nueva.get("articulo_id", "").strip().lower() == objetivo:
                nueva["precio_unitario"] = float(nuevo_precio)
                nueva["coste_total"] = round(float(nueva.get("cantidad", 0.0)) * float(nuevo_precio), 4)
                encontrado = True
            lineas.append(nueva)
        if not encontrado:
            raise ValueError(f"No se encontró la línea {linea_nombre}.")
        coste_total = round(sum(float(l.get("coste_total", 0.0)) for l in lineas), 4)
        coste_por_racion = round(coste_total / int(raciones), 4) if int(raciones) else 0.0
        venta_total = float(precio_venta_por_racion or 0.0) * int(raciones)
        margen = round(venta_total - coste_total, 4) if venta_total else 0.0
        food_cost = round((coste_total / venta_total) * 100, 2) if venta_total else 0.0
        despues = {**antes, "lineas": lineas, "coste_total": coste_total, "coste_por_racion": coste_por_racion, "margen_bruto": margen, "food_cost_porcentaje": food_cost}
        return {"antes": antes, "despues": despues, "impacto": {"coste_total": round(coste_total-float(antes.get("coste_total",0)),4), "coste_por_racion": round(coste_por_racion-float(antes.get("coste_por_racion",0)),4), "margen": round(margen-float(antes.get("margen_bruto",0)),4)}}

    # ---------------------------------------------------------------------
    # PRECIOS
    # ---------------------------------------------------------------------
    def registrar_precio(
        self,
        nombre: str,
        precio_unitario: float,
        unidad: str,
        articulo_id: str = "",
        proveedor: str = "",
        familia: str = "",
        fecha: str = "",
    ) -> Dict[str, Any]:
        precio = PrecioArticulo(
            nombre=nombre,
            precio_unitario=float(precio_unitario),
            unidad=unidad,
            articulo_id=articulo_id,
            proveedor=proveedor,
            familia=familia,
            fecha=fecha,
        )
        clave = articulo_id or nombre.lower().strip()
        self.precios[clave] = precio
        return precio.to_dict()

    def listar_precios(self) -> Dict[str, Any]:
        return {
            "precios": [p.to_dict() for p in self.precios.values()],
            "total": len(self.precios),
            "lectura_host_ai": f"Precios registrados: {len(self.precios)}.",
        }

    def obtener_precio(self, nombre: str, articulo_id: str = "") -> float:
        clave = articulo_id or nombre.lower().strip()
        if clave in self.precios:
            return float(self.precios[clave].precio_unitario)
        # fallback: si no encuentra por id, busca por nombre
        nombre_l = nombre.lower().strip()
        for precio in self.precios.values():
            if precio.nombre.lower().strip() == nombre_l:
                return float(precio.precio_unitario)
        return 0.0

    def obtener_proveedor(self, nombre: str, articulo_id: str = "") -> str:
        clave = articulo_id or nombre.lower().strip()
        if clave in self.precios:
            return self.precios[clave].proveedor
        return ""

    # ---------------------------------------------------------------------
    # RECETAS
    # ---------------------------------------------------------------------
    def calcular_coste_receta(
        self,
        receta_id: str,
        raciones: int,
        precio_venta_por_racion: float = 0.0,
        registrar_historial: bool = True,
    ) -> Dict[str, Any]:
        if not hasattr(self.core, "escandallos_inteligente"):
            raise ValueError("No existe motor de escandallos en el core.")

        calculo = self.core.escandallos_inteligente.calcular_necesidades_receta(
            receta_id=receta_id,
            raciones=int(raciones),
        )

        lineas = []
        avisos = []
        for nec in calculo["necesidades"]:
            precio_unitario = float(nec.get("coste_estimado", 0.0) or 0.0) / float(nec.get("cantidad_bruta", 1) or 1)
            precio_registrado = self.obtener_precio(nec["nombre"], nec.get("articulo_id", ""))
            if precio_registrado > 0:
                precio_unitario = precio_registrado
            elif precio_unitario <= 0:
                avisos.append(f"Sin precio para {nec['nombre']}.")

            coste_total = round(float(nec["cantidad_bruta"]) * precio_unitario, 4)
            lineas.append(CosteLinea(
                nombre=nec["nombre"],
                cantidad=nec["cantidad_bruta"],
                unidad=nec["unidad"],
                precio_unitario=precio_unitario,
                coste_total=coste_total,
                tipo=nec.get("tipo", "articulo"),
                articulo_id=nec.get("articulo_id", ""),
                elaboracion_id=nec.get("elaboracion_id", ""),
                proveedor=self.obtener_proveedor(nec["nombre"], nec.get("articulo_id", "")) or nec.get("proveedor_preferente", ""),
                familia=nec.get("familia", ""),
                origen=f"Escandallo {calculo['receta']}",
            ))

        coste_total = round(sum(l.coste_total for l in lineas), 4)
        coste_por_racion = round(coste_total / int(raciones), 4) if int(raciones) else 0.0
        venta_total = float(precio_venta_por_racion or 0.0) * int(raciones)
        margen = round(venta_total - coste_total, 4) if venta_total else 0.0
        food_cost = round((coste_total / venta_total) * 100, 2) if venta_total else 0.0

        coste = CosteReceta(
            receta_id=receta_id,
            receta=calculo["receta"],
            raciones=int(raciones),
            lineas=lineas,
            coste_total=coste_total,
            coste_por_racion=coste_por_racion,
            precio_venta_por_racion=float(precio_venta_por_racion or 0.0),
            margen_bruto=margen,
            food_cost_porcentaje=food_cost,
            estado="revisar" if avisos else "ok",
            avisos=avisos,
        )
        self.costes_recetas[f"{receta_id}:{raciones}"] = coste
        resultado = {**coste.to_dict(), "lectura_host_ai": self._lectura_receta(coste)}
        if registrar_historial:
            self._registrar_historial_escandallo(resultado, "calculo")
        return resultado

    # ---------------------------------------------------------------------
    # EVENTOS
    # ---------------------------------------------------------------------
    def calcular_coste_evento(
        self,
        evento_id: str,
        precio_venta_por_pax: float = 0.0,
        extras: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        evento = self.core.eventos.obtener(evento_id).to_dict()
        pax = int(evento.get("pax", 0) or 0)
        recetas_coste = []
        avisos = []

        receta_ids = []
        for servicio in evento.get("servicios", []):
            for pase in servicio.get("pases", []):
                for receta_id in pase.get("recetas", []):
                    receta_ids.append(receta_id)

        for receta_id in receta_ids:
            try:
                coste = self.calcular_coste_receta(receta_id, pax, 0.0)
                recetas_coste.append(coste)
                avisos.extend(coste.get("avisos", []))
            except Exception as exc:
                avisos.append(f"No se pudo calcular {receta_id}: {exc}")

        extra_lineas = []
        for extra in extras or []:
            cantidad = float(extra.get("cantidad", 1))
            precio_unitario = float(extra.get("precio_unitario", 0.0))
            extra_lineas.append(CosteLinea(
                nombre=extra.get("nombre", "Extra"),
                cantidad=cantidad,
                unidad=extra.get("unidad", "ud"),
                precio_unitario=precio_unitario,
                coste_total=round(cantidad * precio_unitario, 4),
                tipo=extra.get("tipo", "extra"),
                familia=extra.get("familia", "extras"),
                origen="extra_evento",
                notas=extra.get("notas", ""),
            ))

        coste_materia = round(sum(float(r.get("coste_total", 0.0)) for r in recetas_coste), 4)
        coste_extras = round(sum(e.coste_total for e in extra_lineas), 4)
        coste_total = round(coste_materia + coste_extras, 4)
        coste_por_pax = round(coste_total / pax, 4) if pax else 0.0

        venta_total = round(float(precio_venta_por_pax or 0.0) * pax, 4)
        margen = round(venta_total - coste_total, 4) if venta_total else 0.0
        food_cost = round((coste_total / venta_total) * 100, 2) if venta_total else 0.0

        coste_evento = CosteEvento(
            evento_id=evento_id,
            evento=evento.get("nombre", ""),
            pax=pax,
            recetas=recetas_coste,
            extras=extra_lineas,
            coste_materia_prima=coste_materia,
            coste_extras=coste_extras,
            coste_total=coste_total,
            coste_por_pax=coste_por_pax,
            precio_venta_total=venta_total,
            precio_venta_por_pax=float(precio_venta_por_pax or 0.0),
            margen_bruto=margen,
            beneficio_estimado=margen,
            food_cost_porcentaje=food_cost,
            estado="revisar" if avisos else "ok",
            avisos=avisos,
        )
        self.costes_eventos[evento_id] = coste_evento

        return {**coste_evento.to_dict(), "lectura_host_ai": self._lectura_evento(coste_evento)}

    # ---------------------------------------------------------------------
    # SIMULACIÓN
    # ---------------------------------------------------------------------
    def simular_variacion_precio_receta(
        self,
        receta_id: str,
        raciones: int,
        variacion_porcentaje: float,
        precio_venta_por_racion: float = 0.0,
    ) -> Dict[str, Any]:
        antes = self.calcular_coste_receta(receta_id, raciones, precio_venta_por_racion)
        factor = 1 + (float(variacion_porcentaje) / 100.0)

        despues_lineas = []
        for linea in antes["lineas"]:
            nuevo_precio = round(float(linea["precio_unitario"]) * factor, 4)
            nuevo_total = round(float(linea["cantidad"]) * nuevo_precio, 4)
            nueva = dict(linea)
            nueva["precio_unitario"] = nuevo_precio
            nueva["coste_total"] = nuevo_total
            despues_lineas.append(nueva)

        coste_total_despues = round(sum(l["coste_total"] for l in despues_lineas), 4)
        venta_total = float(precio_venta_por_racion or 0.0) * int(raciones)
        margen_despues = round(venta_total - coste_total_despues, 4) if venta_total else 0.0
        food_cost_despues = round((coste_total_despues / venta_total) * 100, 2) if venta_total else 0.0

        despues = {
            **antes,
            "lineas": despues_lineas,
            "coste_total": coste_total_despues,
            "coste_por_racion": round(coste_total_despues / int(raciones), 4) if int(raciones) else 0.0,
            "margen_bruto": margen_despues,
            "food_cost_porcentaje": food_cost_despues,
        }

        impacto = {
            "diferencia_coste_total": round(coste_total_despues - float(antes["coste_total"]), 4),
            "diferencia_coste_por_racion": round(despues["coste_por_racion"] - float(antes["coste_por_racion"]), 4),
            "diferencia_margen": round(margen_despues - float(antes.get("margen_bruto", 0.0)), 4),
        }

        sim = SimulacionPrecio(
            objetivo=f"receta:{receta_id}",
            variacion_porcentaje=float(variacion_porcentaje),
            antes=antes,
            despues=despues,
            impacto=impacto,
        )
        return {**sim.to_dict(), "lectura_host_ai": f"Simulación de precios generada: {variacion_porcentaje}% sobre {antes['receta']}."}

    def diagnosticar_evento_costes(self, evento_id: str, food_cost_objetivo: float = 30.0) -> Dict[str, Any]:
        if evento_id not in self.costes_eventos:
            raise ValueError("Primero calcula el coste del evento.")
        coste = self.costes_eventos[evento_id]
        avisos = list(coste.avisos)

        if coste.precio_venta_total <= 0:
            avisos.append("El evento no tiene precio de venta asignado.")
        if coste.food_cost_porcentaje and coste.food_cost_porcentaje > float(food_cost_objetivo):
            avisos.append(f"Food cost alto: {coste.food_cost_porcentaje}% > objetivo {food_cost_objetivo}%.")

        return {
            "evento_id": evento_id,
            "evento": coste.evento,
            "food_cost_objetivo": float(food_cost_objetivo),
            "food_cost_actual": coste.food_cost_porcentaje,
            "margen_bruto": coste.margen_bruto,
            "beneficio_estimado": coste.beneficio_estimado,
            "avisos": avisos,
            "estado": "revisar" if avisos else "ok",
            "lectura_host_ai": "Costes del evento correctos." if not avisos else f"Costes del evento con {len(avisos)} avisos.",
        }


    def _cargar_historial_rentabilidad(self) -> None:
        db = getattr(self.core, "db", None)
        if not db:
            return
        try:
            self.historial_rentabilidad = list(db.cargar("historial_rentabilidad") or [])
        except Exception:
            self.historial_rentabilidad = []

    def _guardar_historial_rentabilidad(self) -> None:
        db = getattr(self.core, "db", None)
        if db:
            db.guardar("historial_rentabilidad", self.historial_rentabilidad)

    @staticmethod
    def _ultima_por_clave(datos: List[Dict[str, Any]], clave: str) -> List[Dict[str, Any]]:
        ultimos: Dict[str, Dict[str, Any]] = {}
        for item in sorted(datos, key=lambda x: x.get("fecha", "")):
            valor = str(item.get(clave, "") or "")
            if valor:
                ultimos[valor] = item
        return list(ultimos.values())

    def analizar_rentabilidad_evento(self, evento_id: str, food_cost_objetivo: float = 30.0, margen_minimo: float = 20.0, registrar: bool = True) -> Dict[str, Any]:
        datos = self.listar_historial_costes_eventos(evento_id)
        if not datos:
            raise ValueError("Primero calcula los costes operativos del evento.")
        ultimo = dict(datos[0])
        evento = self.core.eventos.obtener(evento_id).to_dict()
        venta = float(ultimo.get("precio_venta_total", 0.0) or 0.0)
        coste = float(ultimo.get("coste_total_real", 0.0) or 0.0)
        beneficio = round(venta - coste, 4) if venta else 0.0
        margen = round((beneficio / venta) * 100, 2) if venta else 0.0
        materia = float(ultimo.get("coste_materia_real", 0.0) or 0.0)
        food_cost = round((materia / venta) * 100, 2) if venta else 0.0
        pax = int(ultimo.get("pax", 0) or 0)
        alertas=[]
        if venta <= 0: alertas.append("El evento no tiene ingresos registrados.")
        if beneficio < 0: alertas.append("El evento presenta pérdida.")
        if margen < float(margen_minimo): alertas.append(f"Margen bajo: {margen}% < {float(margen_minimo)}%.")
        if food_cost > float(food_cost_objetivo): alertas.append(f"Food cost alto: {food_cost}% > {float(food_cost_objetivo)}%.")
        resultado={
            "evento_id": evento_id, "evento": ultimo.get("evento", evento.get("nombre", "")),
            "cliente": evento.get("cliente", ""), "pax": pax, "venta_total": venta,
            "coste_total_real": coste, "beneficio": beneficio, "margen_porcentaje": margen,
            "food_cost_porcentaje": food_cost, "beneficio_por_pax": round(beneficio/pax,4) if pax else 0.0,
            "coste_por_pax": round(coste/pax,4) if pax else 0.0,
            "estado": "revisar" if alertas else "rentable", "alertas": alertas,
        }
        if registrar:
            from datetime import datetime
            item={**resultado, "fecha": datetime.now().isoformat(timespec="seconds")}
            self.historial_rentabilidad.append(item)
            self.historial_rentabilidad=self.historial_rentabilidad[-1000:]
            self._guardar_historial_rentabilidad()
        return resultado

    def simular_rentabilidad_evento(self, evento_id: str, precio_venta_por_pax: float | None = None, pax: int | None = None, variacion_materia_pct: float = 0.0, variacion_mano_obra_pct: float = 0.0) -> Dict[str, Any]:
        datos=self.listar_historial_costes_eventos(evento_id)
        if not datos: raise ValueError("Primero calcula los costes operativos del evento.")
        base=dict(datos[0])
        pax_base=int(base.get("pax",0) or 0)
        pax_nuevo=int(pax if pax is not None else pax_base)
        venta_pax=float(precio_venta_por_pax) if precio_venta_por_pax is not None else (float(base.get("precio_venta_total",0) or 0)/(pax_base or 1))
        factor_pax=(pax_nuevo/(pax_base or 1)) if pax_base else 1.0
        materia=float(base.get("coste_materia_real",0) or 0)*factor_pax*(1+float(variacion_materia_pct)/100)
        mano=float(base.get("coste_mano_obra",0) or 0)*(1+float(variacion_mano_obra_pct)/100)
        indirectos=float(base.get("costes_indirectos",0) or 0)+float(base.get("otros_costes",0) or 0)
        coste=round(materia+mano+indirectos,4)
        venta=round(venta_pax*pax_nuevo,4)
        beneficio=round(venta-coste,4)
        margen=round((beneficio/venta)*100,2) if venta else 0.0
        food=round((materia/venta)*100,2) if venta else 0.0
        return {"evento_id":evento_id,"evento":base.get("evento", ""),"pax":pax_nuevo,"precio_venta_por_pax":venta_pax,"venta_total":venta,"coste_total":coste,"beneficio":beneficio,"margen_porcentaje":margen,"food_cost_porcentaje":food,"impacto_beneficio":round(beneficio-float(base.get("beneficio_real",0) or 0),4)}

    def rankings_rentabilidad(self) -> Dict[str, Any]:
        eventos=self._ultima_por_clave(self.historial_rentabilidad, "evento_id")
        recetas=self._ultima_por_clave(self.historial_escandallos, "receta_id")
        ranking_eventos=sorted(eventos,key=lambda x: float(x.get("beneficio",0)),reverse=True)
        ranking_recetas=sorted(recetas,key=lambda x: float(x.get("margen_bruto",0)),reverse=True)
        clientes: Dict[str, Dict[str, Any]]={}
        for e in eventos:
            cliente=(e.get("cliente") or "Sin cliente").strip()
            c=clientes.setdefault(cliente,{"cliente":cliente,"eventos":0,"venta_total":0.0,"coste_total":0.0,"beneficio":0.0})
            c["eventos"]+=1; c["venta_total"]+=float(e.get("venta_total",0)); c["coste_total"]+=float(e.get("coste_total_real",0)); c["beneficio"]+=float(e.get("beneficio",0))
        ranking_clientes=sorted(clientes.values(),key=lambda x:x["beneficio"],reverse=True)
        return {"eventos":ranking_eventos,"recetas":ranking_recetas,"clientes":ranking_clientes}

    def resumen_rentabilidad_global(self, food_cost_objetivo: float = 30.0, margen_minimo: float = 20.0) -> Dict[str, Any]:
        eventos=self._ultima_por_clave(self.historial_rentabilidad, "evento_id")
        venta=sum(float(x.get("venta_total",0)) for x in eventos)
        coste=sum(float(x.get("coste_total_real",0)) for x in eventos)
        beneficio=round(venta-coste,4)
        margen=round((beneficio/venta)*100,2) if venta else 0.0
        materia=sum(float(x.get("food_cost_porcentaje",0))*float(x.get("venta_total",0))/100 for x in eventos)
        food=round((materia/venta)*100,2) if venta else 0.0
        alertas=[]
        if any(float(x.get("beneficio",0))<0 for x in eventos): alertas.append("Hay eventos con pérdidas.")
        if margen < float(margen_minimo) and eventos: alertas.append(f"Margen global bajo: {margen}%.")
        if food > float(food_cost_objetivo): alertas.append(f"Food cost global alto: {food}%.")
        return {"eventos_analizados":len(eventos),"venta_total":round(venta,4),"coste_total":round(coste,4),"beneficio_total":beneficio,"margen_global_porcentaje":margen,"food_cost_global_porcentaje":food,"alertas":alertas,"estado":"revisar" if alertas else "correcto"}

    # ---------------------------------------------------------------------
    # LECTURAS
    # ---------------------------------------------------------------------
    def _lectura_receta(self, coste: CosteReceta) -> str:
        if coste.precio_venta_por_racion:
            return f"{coste.receta}: coste {coste.coste_por_racion} €/ración, food cost {coste.food_cost_porcentaje}%."
        return f"{coste.receta}: coste {coste.coste_por_racion} €/ración."

    def _lectura_evento(self, coste: CosteEvento) -> str:
        if coste.precio_venta_total:
            return f"{coste.evento}: coste total {coste.coste_total} €, coste/pax {coste.coste_por_pax} €, margen {coste.margen_bruto} €, food cost {coste.food_cost_porcentaje}%."
        return f"{coste.evento}: coste total {coste.coste_total} €, coste/pax {coste.coste_por_pax} €."
