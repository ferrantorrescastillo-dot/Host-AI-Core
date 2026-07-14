from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.gestor_contexto_permanente_5410 import GestorContextoPermanente5410


def main() -> None:
    gestor = GestorContextoPermanente5410()
    gestor.activar_flujo({"evento": {"tipo": "boda"}, "estado_conversacion": "pendiente_confirmacion"})
    gestor.cambiar_estado("esperando_seleccion_accion")
    print("HOST AI 5.4.10 - GESTOR DE CONTEXTO PERMANENTE")
    print("Contexto activo:", "SI" if gestor.esta_activo() else "NO")
    print("Estado:", gestor.estado())
    print("Historial:", " -> ".join(gestor.obtener("historial_estados", [])))


if __name__ == "__main__":
    main()
