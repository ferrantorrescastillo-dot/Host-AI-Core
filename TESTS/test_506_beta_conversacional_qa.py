
from __future__ import annotations

from SERVICIOS.beta_conversacional_qa_506 import BetaConversacionalQA506


def main():
    qa = BetaConversacionalQA506()
    casos = qa.cargar_casos()
    assert len(casos) == 100, f"Se esperaban 100 casos, hay {len(casos)}"
    informe = qa.ejecutar()
    assert informe["total"] == 100
    assert informe["ok"] + informe["parcial"] + informe["fail"] == 100
    assert "recepcion" in informe["por_categoria"]
    assert "compras" in informe["por_categoria"]
    assert "produccion" in informe["por_categoria"]
    assert "eventos" in informe["por_categoria"]
    assert "rentabilidad" in informe["por_categoria"]
    assert 0 <= informe["nota_global"] <= 100
    print("TEST OK 5.0.6 Beta Conversacional QA")


if __name__ == "__main__":
    main()
