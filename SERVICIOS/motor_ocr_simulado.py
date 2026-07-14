from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from MODELOS.resultado_ocr import ResultadoOCRDocumento


class MotorOCRSimulado:
    """
    Host AI 3.0.3.7.2

    Motor OCR preparado para el flujo.
    Importante:
    - No usa OCR real todavía.
    - Permite trabajar con texto manual asociado a una imagen/PDF escaneado.
    - Deja preparado el contrato para un OCR real posterior.
    """

    def __init__(self, core):
        self.core = core
        self.base_dir = core.base_dir
        self.facturas_dir = self.base_dir / "DATOS" / "facturas"
        self.facturas_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.facturas_dir / "ocr_cache_manual.json"
        self.cache = self._cargar_cache()

    def registrar_texto_manual(self, ruta_archivo: str, texto: str) -> Dict[str, Any]:
        ruta = self._resolver(ruta_archivo)
        clave = str(ruta)
        self.cache[clave] = {
            "archivo": clave,
            "nombre_archivo": ruta.name,
            "texto": texto,
        }
        self._guardar_cache()
        return {
            "registrado": True,
            "archivo": clave,
            "caracteres": len(texto or ""),
            "lectura_host_ai": f"Texto OCR manual registrado para {ruta.name}.",
        }

    def extraer_texto(self, ruta_archivo: str, texto_manual: str = "") -> Dict[str, Any]:
        ruta = self._resolver(ruta_archivo)
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")

        diagnostico = self.core.base_ocr_documentos.diagnosticar_archivo(str(ruta))

        texto = texto_manual or self.cache.get(str(ruta), {}).get("texto", "")
        avisos = []
        metodo = "manual_cache" if texto and not texto_manual else "manual_parametro" if texto_manual else "pendiente_ocr_real"
        confianza = 85.0 if texto else 0.0

        if not texto:
            avisos.append("No hay OCR real disponible ni texto manual registrado.")
            avisos.append("En 3.0.3.7.2 el motor simula OCR usando texto manual.")

        res = ResultadoOCRDocumento(
            archivo=str(ruta),
            nombre_archivo=ruta.name,
            texto_extraido=texto,
            metodo=metodo,
            confianza=confianza,
            paginas=int(diagnostico.get("paginas", 0) or 0),
            requiere_revision=not bool(texto),
            avisos=avisos,
            diagnostico=diagnostico,
        )
        datos = res.to_dict()
        datos["lectura_host_ai"] = (
            f"OCR simulado extraído: {len(texto)} caracteres."
            if texto else "OCR pendiente: falta texto manual u OCR real."
        )
        return datos

    def exportar_resultado(self, resultado: Dict[str, Any], nombre: str = "") -> Dict[str, Any]:
        nombre = nombre or "resultado_ocr_documento.json"
        destino = self.facturas_dir / nombre
        destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"archivo": str(destino), "lectura_host_ai": f"Resultado OCR exportado: {destino.name}."}

    def _resolver(self, ruta_archivo: str) -> Path:
        ruta = Path(ruta_archivo)
        return ruta if ruta.is_absolute() else self.base_dir / ruta

    def _cargar_cache(self):
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _guardar_cache(self):
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
