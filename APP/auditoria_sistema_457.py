from __future__ import annotations

from SERVICIOS.auditoria_sistema_457 import AuditoriaSistema457


def main() -> None:
    auditoria = AuditoriaSistema457()
    print("=== HOST AI 4.5.7 - AUDITORÍA DEL SISTEMA ===")
    print(auditoria.resumen_auditoria()["lectura_host_ai"])
    print("\nÚltimas acciones:")
    for accion in auditoria.listar_acciones(limite=10)["acciones"]:
        print(f"- {accion['creado_en']} | {accion['usuario']} | {accion['modulo']} | {accion['accion']}")


if __name__ == "__main__":
    main()
