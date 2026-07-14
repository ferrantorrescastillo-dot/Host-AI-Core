from SERVICIOS.beta_conversacional_qa_506 import BetaConversacionalQA506


def main():
    qa = BetaConversacionalQA506()
    informe = qa.ejecutar()

    assert informe["nota_global"] >= 90, f"Nota global baja: {informe['nota_global']}"

    categorias_bajas = {
        categoria: datos["nota"]
        for categoria, datos in informe["por_categoria"].items()
        if datos["nota"] < 90
    }
    assert not categorias_bajas, f"Categorías por debajo del 90%: {categorias_bajas}"

    assert informe["fail"] == 0, f"Quedan fallos FAIL: {informe['fail']}"

    print("TEST OK 5.0.9 Optimización Beta 1: todas las categorías >= 90%")
    print(f"Nota global: {informe['nota_global']} / 100")
    for categoria, datos in sorted(informe["por_categoria"].items()):
        print(f"- {categoria}: {datos['nota']}%")


if __name__ == "__main__":
    main()
