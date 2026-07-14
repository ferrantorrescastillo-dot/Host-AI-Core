from __future__ import annotations

import importlib
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class OpcionBootloader:
    codigo: str
    titulo: str
    descripcion: str
    tipo: str
    destino: str


class BootloaderHostAI502:
    """
    Punto de entrada seguro para Host AI 5.x.

    5.1 actualiza la opción 1 para abrir el Orquestador Inteligente.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.cwd()).resolve()
        self._asegurar_pythonpath()
        self.opciones = self._crear_opciones()

    def _asegurar_pythonpath(self) -> None:
        ruta = str(self.base_dir)
        if ruta not in sys.path:
            sys.path.insert(0, ruta)

    def validar_estructura(self) -> Dict[str, object]:
        carpetas = ["APP", "CORE", "SERVICIOS", "TESTS", "DOCS"]
        estado = {c: (self.base_dir / c).exists() for c in carpetas}
        estado["main_py"] = (self.base_dir / "main.py").exists()
        estado["base_dir"] = str(self.base_dir)
        estado["ok"] = all(estado[c] for c in carpetas)
        return estado

    def _crear_opciones(self) -> List[OpcionBootloader]:
        return [
            OpcionBootloader("1", "Hablar con Host AI", "Orquestador 5.2 con datos mínimos", "modulo", "APP.orquestador_inteligente_52"),
            OpcionBootloader("2", "Chat recepción 5.0.5", "Chat seguro con confirmación de recepción", "modulo", "APP.chat_host_ai_505"),
            OpcionBootloader("3", "Auditoria nucleo IA 5.0.1", "Revisa intenciones y motores del chat", "modulo", "APP.auditoria_nucleo_ia_501"),
            OpcionBootloader("4", "Test nucleo IA 5.0.1", "Ejecuta el test del nucleo IA", "modulo", "TESTS.test_501_auditoria_nucleo_ia"),
            OpcionBootloader("5", "Test bootloader 5.0.2", "Comprueba el punto de entrada", "modulo", "TESTS.test_502_bootloader_host_ai"),
            OpcionBootloader("6", "Test clasificador 5.0.3", "Comprueba clasificación de intenciones", "modulo", "TESTS.test_503_clasificador_intenciones"),
            OpcionBootloader("7", "Test recepción confirmada 5.0.5", "Comprueba confirmación y aplicación segura", "modulo", "TESTS.test_505_confirmacion_recepcion"),
            OpcionBootloader("8", "Beta conversacional QA 5.0.6", "Ejecuta 100 conversaciones reales de prueba", "modulo", "APP.beta_conversacional_qa_506"),
            OpcionBootloader("10", "Test Beta QA 5.0.6", "Comprueba el framework de beta conversacional", "modulo", "TESTS.test_506_beta_conversacional_qa"),
            OpcionBootloader("11", "Test Orquestador 5.1", "Comprueba flujos multi-motor", "modulo", "TESTS.test_51_orquestador_inteligente"),
            OpcionBootloader("12", "Test Orquestador 5.2", "Comprueba datos mínimos y preguntas inteligentes", "modulo", "TESTS.test_52_datos_minimos_evento"),
            OpcionBootloader("9", "Estado estructura", "Muestra carpetas clave detectadas", "interno", "estado"),
        ]

    def obtener_opciones(self) -> List[Dict[str, str]]:
        return [o.__dict__.copy() for o in self.opciones]

    def buscar_opcion(self, codigo: str) -> Optional[OpcionBootloader]:
        for opcion in self.opciones:
            if opcion.codigo == codigo:
                return opcion
        return None

    def ejecutar_opcion(self, codigo: str) -> Dict[str, object]:
        opcion = self.buscar_opcion(codigo)
        if not opcion:
            return {"ok": False, "mensaje": "Opcion no valida", "codigo": codigo}

        if opcion.tipo == "interno" and opcion.destino == "estado":
            return {"ok": True, "tipo": "estado", "datos": self.validar_estructura()}

        if opcion.tipo == "modulo":
            return self.ejecutar_modulo(opcion.destino)

        return {"ok": False, "mensaje": f"Tipo de opcion no soportado: {opcion.tipo}"}

    def ejecutar_modulo(self, nombre_modulo: str) -> Dict[str, object]:
        self._asegurar_pythonpath()
        try:
            runpy.run_module(nombre_modulo, run_name="__main__")
            return {"ok": True, "modulo": nombre_modulo}
        except SystemExit as exc:
            return {"ok": True, "modulo": nombre_modulo, "system_exit": str(exc)}
        except Exception as exc:
            return {"ok": False, "modulo": nombre_modulo, "error": repr(exc)}

    def comprobar_import(self, nombre_modulo: str) -> Dict[str, object]:
        self._asegurar_pythonpath()
        try:
            importlib.import_module(nombre_modulo)
            return {"ok": True, "modulo": nombre_modulo}
        except Exception as exc:
            return {"ok": False, "modulo": nombre_modulo, "error": repr(exc)}


def imprimir_estado(estado: Dict[str, object]) -> None:
    print("\nESTADO DEL PROYECTO")
    print(f"Raiz: {estado.get('base_dir')}")
    for clave in ["APP", "CORE", "SERVICIOS", "TESTS", "DOCS", "main_py"]:
        print(f"- {clave}: {'OK' if estado.get(clave) else 'NO'}")
    print(f"Estado general: {'OK' if estado.get('ok') else 'REVISAR'}")


def ejecutar_menu(base_dir: Optional[Path] = None) -> None:
    boot = BootloaderHostAI502(base_dir)
    print("=" * 70)
    print("HOST AI 5.2 - BOOTLOADER")
    print("Punto de entrada unico del proyecto")
    print("=" * 70)

    while True:
        print("\nMENU BOOTLOADER")
        for opcion in boot.opciones:
            print(f"{opcion.codigo}. {opcion.titulo} - {opcion.descripcion}")
        print("0. Salir")

        codigo = input("Elige una opcion: ").strip()
        if codigo == "0":
            print("Saliendo del bootloader.")
            break

        resultado = boot.ejecutar_opcion(codigo)
        if resultado.get("tipo") == "estado":
            imprimir_estado(resultado["datos"])
        elif resultado.get("ok"):
            print("OK", resultado.get("modulo", ""))
        else:
            print("ERROR:", resultado.get("mensaje") or resultado.get("error"))


__all__ = ["BootloaderHostAI502", "ejecutar_menu"]
