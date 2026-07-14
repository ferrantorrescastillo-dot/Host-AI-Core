from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from CORE.entidades.ingrediente import Ingrediente
from CORE.entidades.receta import Receta
from CORE.entidades.escandallo import Escandallo
from SERVICIOS.validador_escandallos_555a import validar_escandallo
from SERVICIOS.schema_escandallos_555a import SCHEMA_VERSION


class RepositorioEscandallos:
    """Repositorio JSON seguro para el modelo canónico 5.5.5A.

    No sobrescribe datos inválidos. La escritura es atómica: primero crea un
    temporal y después reemplaza el archivo destino.
    """

    def __init__(self, ruta: str | Path = "DATOS/db/escandallos_canonicos.json") -> None:
        self.ruta = Path(ruta)

    def listar(self) -> list[Escandallo]:
        if not self.ruta.exists():
            return []
        with self.ruta.open("r", encoding="utf-8") as fh:
            contenido = json.load(fh)
        registros = contenido.get("escandallos", contenido if isinstance(contenido, list) else [])
        return [self._desde_dict(item) for item in registros]

    def buscar_por_nombre(self, texto: str) -> list[Escandallo]:
        patron = (texto or "").strip().casefold()
        if not patron:
            return self.listar()
        return [e for e in self.listar() if patron in e.receta.nombre.casefold()]

    def buscar_por_ingrediente(self, texto: str) -> list[Escandallo]:
        patron = (texto or "").strip().casefold()
        if not patron:
            return []
        encontrados: list[Escandallo] = []
        for escandallo in self.listar():
            if any(patron in i.nombre.casefold() for i in escandallo.receta.ingredientes):
                encontrados.append(escandallo)
        return encontrados

    def guardar_todos(self, escandallos: Iterable[Escandallo]) -> int:
        lista = list(escandallos)
        errores: list[str] = []
        for escandallo in lista:
            resultado = validar_escandallo(escandallo)
            errores.extend(resultado.errores)
        if errores:
            raise ValueError("No se guardaron escandallos inválidos: " + " | ".join(errores))

        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "escandallos": [asdict(e) for e in lista],
        }
        temporal = self.ruta.with_suffix(self.ruta.suffix + ".tmp")
        with temporal.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        temporal.replace(self.ruta)
        return len(lista)

    def upsert(self, escandallo: Escandallo) -> str:
        resultado = validar_escandallo(escandallo)
        if not resultado.valido:
            raise ValueError("Escandallo inválido: " + " | ".join(resultado.errores))
        actuales = self.listar()
        codigo = escandallo.receta.codigo.strip().casefold()
        accion = "creado"
        for indice, actual in enumerate(actuales):
            if actual.receta.codigo.strip().casefold() == codigo:
                actuales[indice] = escandallo
                accion = "actualizado"
                break
        else:
            actuales.append(escandallo)
        self.guardar_todos(actuales)
        return accion

    @staticmethod
    def _desde_dict(datos: dict) -> Escandallo:
        receta_datos = datos.get("receta", {})
        ingredientes = [Ingrediente(**item) for item in receta_datos.get("ingredientes", [])]
        receta = Receta(
            codigo=receta_datos.get("codigo", ""),
            nombre=receta_datos.get("nombre", ""),
            rendimiento=float(receta_datos.get("rendimiento", 0)),
            unidad_rendimiento=receta_datos.get("unidad_rendimiento", ""),
            ingredientes=ingredientes,
        )
        return Escandallo(receta=receta, coste_total=float(datos.get("coste_total", 0)))
