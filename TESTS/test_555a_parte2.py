from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from CORE.entidades.escandallo import Escandallo
from SERVICIOS.repositorio_escandallos_555a import RepositorioEscandallos
from SERVICIOS.validador_escandallos_555a import validar_escandallo


def construir_escandallo() -> Escandallo:
    arroz = Ingrediente(
        codigo="ART-ARROZ",
        nombre="Arroz bomba",
        cantidad=1.0,
        unidad="kg",
        articulo_id="ART-ARROZ",
        precio_unitario=2.15,
    )
    receta = Receta(
        codigo="REC-PAELLA-001",
        nombre="Paella de prueba",
        rendimiento=10,
        unidad_rendimiento="raciones",
        ingredientes=[arroz],
    )
    return Escandallo(receta=receta, coste_total=2.15)


def main() -> None:
    escandallo = construir_escandallo()
    resultado = validar_escandallo(escandallo)
    assert resultado.valido, resultado.errores

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "escandallos.json"
        repo = RepositorioEscandallos(ruta)
        assert repo.listar() == []
        assert repo.upsert(escandallo) == "creado"
        assert repo.upsert(escandallo) == "actualizado"
        encontrados = repo.buscar_por_nombre("paella")
        assert len(encontrados) == 1
        assert len(repo.buscar_por_ingrediente("arroz")) == 1
        assert ruta.exists()

    print("TEST OK 5.5.5A PARTE 2 - Repositorio, schema y validación")


if __name__ == "__main__":
    main()
