from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from SERVICIOS.release_candidate_conversacional_5415 import ejecutar_release_candidate_5415


def main() -> None:
    resultado = ejecutar_release_candidate_5415(BASE_DIR)
    assert resultado["total"] == 5
    assert resultado["comprobaciones"]["integracion_solo_lectura"] is True
    assert resultado["comprobaciones"]["respuesta_estructurada"] is True
    assert resultado["comprobaciones"]["confirmacion_escritura_protegida"] is True
    assert resultado["ok"] is True, resultado
    print("TEST OK 5.4.15 Release Candidate Conversacional")
    print(f"Comprobaciones: {resultado['aprobadas']}/{resultado['total']} ({resultado['porcentaje']}%)")


if __name__ == "__main__":
    main()
