from __future__ import annotations

from typing import Dict, List, Any
from MODELOS.ia_culinaria import IngredienteIdea, IdeaCulinaria, AnalisisCulinario


class MotorIACulinaria:
    """
    Motor IA Culinaria v2.0.8.

    Primera versión determinista:
    - lee stock disponible
    - propone platos usando productos disponibles
    - detecta faltantes básicos
    - convierte una idea en escandallo inicial
    - conecta con costes y producción si existen

    No usa LLM externo todavía: razona con reglas gastronómicas simples.
    """

    def __init__(self, core):
        self.core = core
        self.ideas: Dict[str, IdeaCulinaria] = {}
        self.analisis: Dict[str, AnalisisCulinario] = {}

    # ------------------------------------------------------------------
    # IDEAS DESDE STOCK / SOBRAS
    # ------------------------------------------------------------------
    def proponer_platos_con_stock(
        self,
        objetivo: str = "comida_personal",
        raciones: int = 4,
        estilo: str = "",
        limitar: int = 3,
    ) -> Dict[str, Any]:
        stock_items = self._stock_items()
        ingredientes_disponibles = self._ingredientes_desde_stock(stock_items)

        ideas: List[IdeaCulinaria] = []

        nombres = [i.nombre.lower() for i in ingredientes_disponibles]
        tiene_carne = any("carrillera" in n or "ternera" in n or "pollo" in n or "cerdo" in n for n in nombres)
        tiene_salsa = any("demi" in n or "salsa" in n or "fondo" in n for n in nombres)
        tiene_verdura = any("cebolla" in n or "zanahoria" in n or "patata" in n or "pimiento" in n for n in nombres)

        if tiene_carne:
            ideas.append(self._idea(
                nombre="Meloso de carne con salsa reducida",
                objetivo=objetivo,
                raciones=raciones,
                estilo=estilo or "cocina de aprovechamiento gastronómica",
                tecnica="regenerar / guisar / reducir",
                ingredientes=self._seleccionar(ingredientes_disponibles, ["carrillera", "ternera", "demi", "salsa", "fondo", "cebolla", "zanahoria", "patata"]),
                fases=[
                    "Revisar stock disponible y caducidades.",
                    "Regenerar la carne con humedad controlada.",
                    "Reducir salsa o fondo hasta textura napante.",
                    "Preparar guarnición sencilla con verduras o patata.",
                    "Emplatar o envasar según objetivo.",
                ],
            ))

        if tiene_verdura:
            ideas.append(self._idea(
                nombre="Salteado de verduras y proteína disponible",
                objetivo=objetivo,
                raciones=raciones,
                estilo=estilo or "comida personal",
                tecnica="saltear",
                ingredientes=self._seleccionar(ingredientes_disponibles, ["cebolla", "zanahoria", "patata", "pimiento", "pollo", "ternera", "cerdo"]),
                fases=[
                    "Cortar verduras de forma homogénea.",
                    "Saltear por orden de dureza.",
                    "Añadir proteína disponible.",
                    "Ajustar sal, acidez y grasa.",
                ],
            ))

        if tiene_salsa:
            ideas.append(self._idea(
                nombre="Pasta o arroz con salsa de cocina",
                objetivo=objetivo,
                raciones=raciones,
                estilo=estilo or "aprovechamiento rápido",
                tecnica="ligar salsa",
                ingredientes=self._seleccionar(ingredientes_disponibles, ["demi", "salsa", "fondo", "cebolla", "queso", "nata"]),
                fases=[
                    "Calentar la salsa suavemente.",
                    "Ajustar textura con agua de cocción o fondo.",
                    "Mezclar con pasta, arroz o guarnición disponible.",
                    "Terminar con grasa, hierbas o queso si hay.",
                ],
            ))

        if not ideas:
            ideas.append(self._idea(
                nombre="Plato base de aprovechamiento",
                objetivo=objetivo,
                raciones=raciones,
                estilo=estilo or "aprovechamiento",
                tecnica="organizar stock",
                ingredientes=ingredientes_disponibles[:6],
                fases=[
                    "Agrupar productos por familia.",
                    "Elegir una base, una proteína y una salsa.",
                    "Cocinar con técnica sencilla.",
                    "Guardar como comida personal o propuesta de servicio.",
                ],
                avisos=["No se ha detectado una combinación gastronómica clara; revisar stock real."],
            ))

        ideas = ideas[:limitar]
        for idea in ideas:
            self.ideas[idea.id] = idea

        analisis = AnalisisCulinario(
            consulta=f"Proponer platos con stock para {objetivo}",
            ideas=ideas,
            necesidades_compra=[],
            posibles_acciones=[
                "Aceptar una idea y convertirla en escandallo.",
                "Calcular coste estimado.",
                "Pasar la idea a producción real.",
            ],
            avisos=[],
        )
        self.analisis[analisis.id] = analisis

        return {
            **analisis.to_dict(),
            "lectura_host_ai": f"IA culinaria propone {len(ideas)} ideas usando el stock disponible.",
        }

    # ------------------------------------------------------------------
    # CREAR IDEA MANUAL
    # ------------------------------------------------------------------
    def crear_idea(
        self,
        nombre: str,
        ingredientes: List[Dict[str, Any]],
        raciones: int = 4,
        objetivo: str = "plato",
        tecnica_principal: str = "",
        estilo: str = "",
        fases: List[str] | None = None,
    ) -> Dict[str, Any]:
        idea = IdeaCulinaria(
            nombre=nombre,
            objetivo=objetivo,
            raciones=int(raciones),
            tecnica_principal=tecnica_principal,
            estilo=estilo,
            ingredientes=[IngredienteIdea(**i) for i in ingredientes],
            fases=fases or [
                "Preparar mise en place.",
                "Aplicar técnica principal.",
                "Ajustar punto de sal, textura y temperatura.",
                "Emplatar o envasar.",
            ],
        )
        self.ideas[idea.id] = idea
        return {**idea.to_dict(), "lectura_host_ai": f"Idea culinaria creada: {idea.nombre}."}

    # ------------------------------------------------------------------
    # CONVERTIR IDEA EN ESCANDALLO
    # ------------------------------------------------------------------
    def convertir_idea_en_escandallo(
        self,
        idea_id: str,
        receta_id: str = "",
        raciones_base: int | None = None,
    ) -> Dict[str, Any]:
        if idea_id not in self.ideas:
            raise ValueError(f"No existe idea culinaria: {idea_id}")
        idea = self.ideas[idea_id]

        receta_id = receta_id or f"REC-{idea.nombre.upper().replace(' ', '-')[:30]}"
        raciones_base = int(raciones_base or idea.raciones or 1)

        lineas = []
        for ing in idea.ingredientes:
            cantidad = float(ing.cantidad or 0.0)
            if cantidad <= 0:
                cantidad = self._cantidad_estimada_por_racion(ing.nombre) * raciones_base
            lineas.append({
                "nombre": ing.nombre,
                "cantidad": round(cantidad, 4),
                "unidad": ing.unidad or self._unidad_estimada(ing.nombre),
                "tipo": "articulo",
                "articulo_id": ing.articulo_id,
                "merma_porcentaje": self._merma_estimada(ing.nombre),
                "familia": ing.familia,
                "proveedor_preferente": "",
                "coste_unitario": 0.0,
                "notas": ing.notas,
            })

        esc = self.core.escandallos_inteligente.registrar_escandallo(
            receta_id=receta_id,
            nombre=idea.nombre,
            raciones_base=raciones_base,
            lineas=lineas,
            grupo="IA Culinaria",
            subgrupo=idea.objetivo,
        )

        return {
            "idea": idea.to_dict(),
            "escandallo": esc,
            "lectura_host_ai": f"Idea '{idea.nombre}' convertida en escandallo {receta_id}.",
        }

    # ------------------------------------------------------------------
    # ANALIZAR IDEA COMPLETA
    # ------------------------------------------------------------------
    def analizar_idea(
        self,
        idea_id: str,
        precio_venta_por_racion: float = 0.0,
    ) -> Dict[str, Any]:
        if idea_id not in self.ideas:
            raise ValueError(f"No existe idea culinaria: {idea_id}")
        idea = self.ideas[idea_id]

        faltantes = []
        for ing in idea.ingredientes:
            if not ing.disponible:
                faltantes.append({
                    "nombre": ing.nombre,
                    "cantidad": ing.cantidad,
                    "unidad": ing.unidad,
                    "motivo": "Ingrediente marcado como no disponible.",
                })
                continue
            if hasattr(self.core, "stock") and ing.cantidad and ing.unidad:
                pred = self.core.stock.predecir_necesidad(
                    nombre=ing.nombre,
                    cantidad_necesaria=ing.cantidad,
                    unidad=ing.unidad,
                    articulo_id=ing.articulo_id,
                )
                if pred.get("estado") != "ok":
                    faltantes.append(pred)

        acciones = [
            "Convertir idea en escandallo.",
            "Registrar precios si se quiere calcular coste real.",
            "Planificar producción si se acepta la propuesta.",
        ]
        if faltantes:
            acciones.insert(0, "Registrar necesidades de compra para ingredientes faltantes.")

        return {
            "idea": idea.to_dict(),
            "faltantes": faltantes,
            "acciones_recomendadas": acciones,
            "estado": "revisar" if faltantes else "ok",
            "lectura_host_ai": "Idea culinaria viable con stock actual." if not faltantes else f"Idea culinaria con {len(faltantes)} faltantes.",
        }

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _stock_items(self) -> List[Dict[str, Any]]:
        if not hasattr(self.core, "stock"):
            return []
        try:
            return self.core.stock.stock_actual().get("items", [])
        except Exception:
            return []

    def _ingredientes_desde_stock(self, stock_items: List[Dict[str, Any]]) -> List[IngredienteIdea]:
        salida = []
        for item in stock_items:
            cantidad = float(item.get("cantidad", 0.0) or 0.0)
            if cantidad <= 0:
                continue
            salida.append(IngredienteIdea(
                nombre=item.get("nombre", ""),
                cantidad=cantidad,
                unidad=item.get("unidad", ""),
                disponible=True,
                origen="stock",
                articulo_id=item.get("articulo_id", ""),
                familia=item.get("familia", ""),
            ))
        return salida

    def _idea(self, nombre, objetivo, raciones, estilo, tecnica, ingredientes, fases, avisos=None):
        return IdeaCulinaria(
            nombre=nombre,
            objetivo=objetivo,
            raciones=int(raciones),
            estilo=estilo,
            tecnica_principal=tecnica,
            ingredientes=ingredientes,
            fases=fases,
            avisos=avisos or [],
        )

    def _seleccionar(self, ingredientes: List[IngredienteIdea], claves: List[str]) -> List[IngredienteIdea]:
        seleccion = []
        for clave in claves:
            for ing in ingredientes:
                if clave in ing.nombre.lower() and ing not in seleccion:
                    seleccion.append(ing)
        return seleccion or ingredientes[:5]

    def _unidad_estimada(self, nombre: str) -> str:
        n = nombre.lower()
        if "salsa" in n or "fondo" in n or "demi" in n:
            return "L"
        return "kg"

    def _cantidad_estimada_por_racion(self, nombre: str) -> float:
        n = nombre.lower()
        if "salsa" in n or "demi" in n or "fondo" in n:
            return 0.08
        if "carne" in n or "carrillera" in n or "ternera" in n:
            return 0.18
        if "patata" in n or "verdura" in n:
            return 0.12
        return 0.05

    def _merma_estimada(self, nombre: str) -> float:
        n = nombre.lower()
        if "carrillera" in n or "carne" in n:
            return 10.0
        if "verdura" in n or "cebolla" in n or "zanahoria" in n:
            return 15.0
        return 0.0
