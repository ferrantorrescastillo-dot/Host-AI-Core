from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SERVICIOS.fichas_produccion_reales_556e31 import RepositorioFichasProduccion556E31


def plantilla(receta: str) -> dict:
    return {
        "receta": receta,
        "rendimiento_base": 10,
        "unidad_rendimiento": "personas",
        "validada_por": "jefe_cocina",
        "fases": [
            {"nombre": "Ejemplo: preparar", "duracion_base_min": 20, "tipo_tiempo": "activo", "requiere_presencia": True, "escalable_por_volumen": True, "recursos": ["mesa_trabajo"]},
            {"nombre": "Ejemplo: cocer", "duracion_base_min": 30, "tipo_tiempo": "pasivo", "requiere_presencia": False, "escalable_por_volumen": False, "recursos": ["fogones"]},
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("receta")
    p.add_argument("--plantilla")
    p.add_argument("--desde-json")
    p.add_argument("--mostrar", action="store_true")
    p.add_argument("--confirmar", action="store_true")
    args = p.parse_args()
    repo = RepositorioFichasProduccion556E31(ROOT)
    if args.plantilla:
        path = Path(args.plantilla)
        path.write_text(json.dumps(plantilla(args.receta), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Plantilla creada: {path}")
        print("Completa fases, tiempos, tipos y recursos. Después impórtala con --desde-json y --confirmar.")
        return 0
    if args.mostrar:
        ficha = repo.buscar(args.receta)
        print(json.dumps(ficha or {"estado": "NO_ENCONTRADA", "receta": args.receta}, ensure_ascii=False, indent=2))
        return 0
    if args.desde_json:
        ficha = json.loads(Path(args.desde_json).read_text(encoding="utf-8"))
        ficha["receta"] = ficha.get("receta") or args.receta
        resultado = repo.guardar(ficha, confirmar=args.confirmar)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0
    print("Indica --plantilla, --mostrar o --desde-json.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
