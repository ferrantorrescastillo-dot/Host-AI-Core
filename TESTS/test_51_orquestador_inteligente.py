from pathlib import Path

from SERVICIOS.orquestador_inteligente_51 import OrquestadorInteligente51


def assert_contiene_paso(resp, texto):
    pasos = resp.get("pasos", [])
    assert pasos, f"sin pasos para {texto!r}"
    return " ".join(p.get("accion", "") + " " + p.get("modulo", "") for p in pasos).lower()


def main():
    base = Path(__file__).resolve().parents[1]
    o = OrquestadorInteligente51(base)

    r1 = o.procesar("Tengo una boda para 180 personas el sábado y dime qué tengo que comprar.")
    assert r1["ok"] is True
    assert r1["intencion"] in {"evento", "compras"}
    plan1 = assert_contiene_paso(r1, "evento+compras")
    assert "evento" in plan1
    assert "produccion" in plan1 or "planificar producción" in plan1
    assert "stock" in plan1
    assert "compra" in plan1
    assert "rentabilidad" in plan1

    r2 = o.procesar("Organízame la producción de mañana y revisa si falta stock.")
    plan2 = assert_contiene_paso(r2, "produccion+stock")
    assert "produccion" in plan2 or "planificar producción" in plan2
    assert "stock" in plan2

    r3 = o.procesar("Han llegado 25 kg de arroz bomba de Makro a 2,15 €/kg.")
    assert r3["intencion"] == "recepcion_mercancia"
    assert "recepción" in r3["mensaje"].lower() or "recepcion" in r3["mensaje"].lower()
    assert o.contexto.get("borrador_recepcion"), "debe quedar borrador pendiente"

    r4 = o.procesar("S")
    assert r4["intencion"] == "recepcion_mercancia"
    assert "recepción" in r4["mensaje"].lower() or "recepcion" in r4["mensaje"].lower()

    print("TEST OK 5.1 Orquestador Inteligente")


if __name__ == "__main__":
    main()
