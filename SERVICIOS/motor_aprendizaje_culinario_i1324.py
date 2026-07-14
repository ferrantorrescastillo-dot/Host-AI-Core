from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid

from SERVICIOS.vista_previa_resolucion_asistida_menus_i1323 import (
    DecisionResolucionI1323,
    VistaPreviaResolucionAsistidaMenusI1323,
    formatear_vista_previa_i1323,
)
from SERVICIOS.motor_reconocimiento_menus_i1321 import normalizar


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MotorAprendizajeCulinarioI1324(VistaPreviaResolucionAsistidaMenusI1323):
    """I1.3.2.4 — memoria culinaria auditable por restaurante.

    Aprende únicamente decisiones confirmadas por el usuario. No crea recetas,
    artículos ni menús. La única escritura permitida es su propio fichero de
    memoria, con historial y posibilidad de edición o borrado.
    """

    VERSION = "I1.3.2.4"
    ESQUEMA = 1

    def __init__(self, base_dir: str | Path, constructor=None):
        super().__init__(base_dir, constructor=constructor)
        self.ruta_memoria_anterior = self.base_dir / "DATOS" / "db" / "memoria_resoluciones_menu_i1323.json"
        self.ruta_memoria = self.base_dir / "DATOS" / "db" / "aprendizaje_culinario_i1324.json"
        self.registros = self._cargar_registros()
        self.memoria = self._memoria_compatible()

    def _documento_vacio(self) -> dict[str, Any]:
        return {"version": self.VERSION, "esquema": self.ESQUEMA, "decisiones": {}}

    def _cargar_registros(self) -> dict[str, Any]:
        documento = self._documento_vacio()
        if self.ruta_memoria.exists():
            try:
                data = json.loads(self.ruta_memoria.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("decisiones"), dict):
                    documento.update(data)
                    documento["decisiones"] = data["decisiones"]
                    return documento
            except (OSError, json.JSONDecodeError):
                pass
        # Migración no destructiva de la memoria simple de I1.3.2.3.
        if self.ruta_memoria_anterior.exists():
            try:
                anterior = json.loads(self.ruta_memoria_anterior.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                anterior = {}
            if isinstance(anterior, dict):
                for clave, decision in anterior.items():
                    if isinstance(decision, dict):
                        registro = self._crear_registro(decision, origen="migracion_i1323")
                        documento["decisiones"][normalizar(clave)] = registro
                if documento["decisiones"]:
                    self._guardar_documento(documento)
        return documento

    def _memoria_compatible(self) -> dict[str, dict[str, Any]]:
        memoria: dict[str, dict[str, Any]] = {}
        for clave, registro in self.registros.get("decisiones", {}).items():
            if registro.get("estado") != "ACTIVO":
                continue
            memoria[clave] = {
                "texto_origen": registro.get("texto_origen", clave),
                "rol": registro.get("rol", "COMPONENTE_PENDIENTE"),
                "accion": registro.get("accion", "MANTENER_PENDIENTE"),
                "nombre_destino": registro.get("nombre_destino", ""),
                "tipo_destino": registro.get("tipo_destino", ""),
                "entidad_id": registro.get("entidad_id", ""),
                "confianza": float(registro.get("confianza", 1.0)),
            }
        return memoria

    def _crear_registro(self, decision: dict[str, Any], origen: str = "usuario") -> dict[str, Any]:
        ahora = _ahora()
        return {
            "aprendizaje_id": f"CUL-{uuid.uuid4().hex[:12].upper()}",
            "texto_origen": str(decision.get("texto_origen") or "").strip(),
            "clave_normalizada": normalizar(decision.get("texto_origen")),
            "rol": str(decision.get("rol") or "COMPONENTE_PENDIENTE"),
            "accion": str(decision.get("accion") or "MANTENER_PENDIENTE"),
            "nombre_destino": str(decision.get("nombre_destino") or "").strip(),
            "tipo_destino": str(decision.get("tipo_destino") or "").strip(),
            "entidad_id": str(decision.get("entidad_id") or "").strip(),
            "confianza": float(decision.get("confianza") or 1.0),
            "estado": "ACTIVO",
            "origen": origen,
            "usos": 0,
            "creado_en": ahora,
            "actualizado_en": ahora,
            "ultimo_uso_en": None,
            "historial": [{"fecha": ahora, "evento": "CREADO", "origen": origen}],
        }

    def _guardar_documento(self, documento: dict[str, Any] | None = None) -> None:
        documento = documento or self.registros
        self.ruta_memoria.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta_memoria.with_suffix(".tmp")
        tmp.write_text(json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.ruta_memoria)

    def guardar_decision(self, decision: DecisionResolucionI1323) -> None:
        clave = normalizar(decision.texto_origen)
        existente = self.registros["decisiones"].get(clave)
        ahora = _ahora()
        if existente:
            anterior = {k: existente.get(k) for k in ("rol", "accion", "nombre_destino", "tipo_destino", "entidad_id", "confianza")}
            existente.update({
                "texto_origen": decision.texto_origen,
                "rol": decision.rol,
                "accion": decision.accion,
                "nombre_destino": decision.nombre_destino,
                "tipo_destino": decision.tipo_destino,
                "entidad_id": decision.entidad_id,
                "confianza": decision.confianza,
                "estado": "ACTIVO",
                "actualizado_en": ahora,
            })
            existente.setdefault("historial", []).append({"fecha": ahora, "evento": "ACTUALIZADO", "anterior": anterior, "origen": "usuario"})
        else:
            self.registros["decisiones"][clave] = self._crear_registro(decision.a_dict())
        self._guardar_documento()
        self.memoria = self._memoria_compatible()

    def preparar_desde_excel(self, ruta_excel: str | Path, hojas: list[str] | None = None) -> dict[str, Any]:
        # Captura qué decisiones pueden aplicarse antes de delegar en I1.3.2.3.
        base_sin_memoria = self.constructor.preparar_desde_excel(ruta_excel, hojas=hojas)
        claves_aplicables: set[str] = set()
        for menu in base_sin_memoria.get("menus", []):
            for plato in menu.get("platos", []):
                for _, _, _, item in self._iter_pendientes(plato["semantica"]["arbol"]):
                    clave = normalizar(item.get("nombre"))
                    if clave in self.memoria:
                        claves_aplicables.add(clave)
        resultado = super().preparar_desde_excel(ruta_excel, hojas=hojas)
        if claves_aplicables:
            ahora = _ahora()
            for clave in claves_aplicables:
                registro = self.registros["decisiones"].get(clave)
                if not registro:
                    continue
                registro["usos"] = int(registro.get("usos", 0)) + 1
                registro["ultimo_uso_en"] = ahora
                registro["actualizado_en"] = ahora
                registro.setdefault("historial", []).append({"fecha": ahora, "evento": "APLICADO_AUTOMATICAMENTE"})
            self._guardar_documento()
        resultado["version"] = self.VERSION
        resultado["resumen_aprendizaje"] = {
            "aprendizajes_activos": len([r for r in self.registros["decisiones"].values() if r.get("estado") == "ACTIVO"]),
            "aprendizajes_aplicados": len(claves_aplicables),
            "escritura_memoria": bool(claves_aplicables),
        }
        resultado["importacion_disponible"] = False
        return resultado

    def aplicar_decision(self, resultado: dict[str, Any], texto_origen: str, rol: str, accion: str,
                         destino: dict[str, Any] | None = None, recordar: bool = False) -> bool:
        aplicada = super().aplicar_decision(resultado, texto_origen, rol, accion, destino, recordar=recordar)
        if recordar and aplicada:
            resultado.setdefault("resumen_aprendizaje", {})["aprendizajes_activos"] = len(self.listar_aprendizajes())
            resultado["resumen_aprendizaje"]["nuevo_aprendizaje_guardado"] = True
        return aplicada

    def listar_aprendizajes(self, incluir_inactivos: bool = False) -> list[dict[str, Any]]:
        registros = [deepcopy(r) for r in self.registros.get("decisiones", {}).values()]
        if not incluir_inactivos:
            registros = [r for r in registros if r.get("estado") == "ACTIVO"]
        return sorted(registros, key=lambda r: (normalizar(r.get("texto_origen")), r.get("aprendizaje_id", "")))

    def editar_aprendizaje(self, aprendizaje_id: str, **cambios: Any) -> bool:
        permitidos = {"rol", "accion", "nombre_destino", "tipo_destino", "entidad_id", "confianza", "estado"}
        for registro in self.registros.get("decisiones", {}).values():
            if registro.get("aprendizaje_id") != aprendizaje_id:
                continue
            anterior = {k: registro.get(k) for k in permitidos}
            for campo, valor in cambios.items():
                if campo in permitidos and valor is not None:
                    registro[campo] = float(valor) if campo == "confianza" else valor
            ahora = _ahora()
            registro["actualizado_en"] = ahora
            registro.setdefault("historial", []).append({"fecha": ahora, "evento": "EDITADO", "anterior": anterior, "origen": "usuario"})
            self._guardar_documento()
            self.memoria = self._memoria_compatible()
            return True
        return False

    def eliminar_aprendizaje(self, aprendizaje_id: str) -> bool:
        return self.editar_aprendizaje(aprendizaje_id, estado="INACTIVO")


def formatear_vista_aprendizaje_i1324(resultado: dict[str, Any]) -> str:
    lineas = formatear_vista_previa_i1323(resultado).splitlines()
    if lineas:
        lineas[0] = "I1.3.2.4 — MOTOR DE APRENDIZAJE CULINARIO"
    ra = resultado.get("resumen_aprendizaje", {})
    # Sustituye el pie de I1.3.2.3 por el contrato del nuevo sprint.
    lineas = [l for l in lineas if l not in {
        "RESOLUCIÓN ASISTIDA: las decisiones solo afectan a la vista previa; únicamente se recuerdan con confirmación explícita.",
        "No se importó ningún menú ni se creó ninguna receta o artículo.",
    }]
    lineas.extend([
        f"Aprendizajes activos: {ra.get('aprendizajes_activos', 0)} | Aplicados automáticamente: {ra.get('aprendizajes_aplicados', 0)}",
        "APRENDIZAJE CULINARIO: solo guarda decisiones confirmadas, con historial, confianza y contador de usos.",
        "No se importó ningún menú ni se creó ninguna receta o artículo.",
    ])
    return "\n".join(lineas)
