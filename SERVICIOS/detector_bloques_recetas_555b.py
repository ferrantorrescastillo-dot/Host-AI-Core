from __future__ import annotations

import re
import unicodedata
from typing import Any

from MODELOS.analisis_estructural_excel_555b import BloqueFichaDetectado555B


def _norm(valor: object) -> str:
    texto = str(valor or "").strip().lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"\s+", " ", texto).split())


class DetectorBloquesRecetas555B:
    MARCADORES = (
        "ficha tecnica plato",
        "ficha tecnica",
        "nombre plato",
        "elaboracion",
    )

    def detectar_en_filas(self, filas: list[tuple[Any, ...]]) -> list[BloqueFichaDetectado555B]:
        inicios: list[tuple[int, str]] = []
        for numero, fila in enumerate(filas, start=1):
            celdas = [str(v).strip() for v in fila if v not in (None, "")]
            normalizadas = [_norm(v) for v in celdas]
            if any(any(marcador in celda for marcador in self.MARCADORES) for celda in normalizadas):
                titulo = self._titulo_desde_fila(celdas) or "Ficha técnica"
                inicios.append((numero, titulo))

        # Muchos libros usan un único encabezado y separan recetas con filas en mayúsculas.
        if not inicios and filas:
            for numero, fila in enumerate(filas, start=1):
                celdas = [str(v).strip() for v in fila if v not in (None, "")]
                if len(celdas) == 1 and len(celdas[0]) >= 5 and celdas[0].upper() == celdas[0] and any(ch.isalpha() for ch in celdas[0]):
                    inicios.append((numero, celdas[0]))

        bloques: list[BloqueFichaDetectado555B] = []
        for indice, (inicio, titulo) in enumerate(inicios):
            fin = (inicios[indice + 1][0] - 1) if indice + 1 < len(inicios) else len(filas)
            datos = sum(1 for fila in filas[inicio:fin] if any(v not in (None, "") for v in fila))
            confianza = 90.0 if "ficha tecnica" in _norm(titulo) else 70.0
            bloques.append(BloqueFichaDetectado555B(inicio, fin, titulo, datos, confianza))
        return bloques

    @staticmethod
    def _titulo_desde_fila(celdas: list[str]) -> str:
        for valor in celdas:
            normal = _norm(valor)
            if normal not in {"ficha tecnica plato", "ficha tecnica", "nombre plato", "elaboracion"}:
                return valor
        return celdas[0] if celdas else ""
