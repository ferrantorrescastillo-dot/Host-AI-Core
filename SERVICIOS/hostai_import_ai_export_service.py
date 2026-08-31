from __future__ import annotations

import base64
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path, PurePath
from zipfile import ZIP_DEFLATED, ZipFile

from MODELOS.hostai_import_package import hostai_import_package_json_schema


class HostAIImportAIExportError(ValueError):
    pass


class HostAIImportAIExportService:
    """Exporta en memoria un documento y el contrato público para una IA externa."""

    MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)

    def prepare(self, *, filename: str, content_base64: str) -> tuple[str, bytes]:
        safe_name = self._safe_filename(filename)
        try:
            document = base64.b64decode(str(content_base64), validate=True)
        except Exception as exc:
            raise HostAIImportAIExportError("El documento no contiene base64 válido.") from exc
        if not document:
            raise HostAIImportAIExportError("El documento está vacío.")
        if len(document) > self.MAX_DOCUMENT_BYTES:
            raise HostAIImportAIExportError("El documento supera el máximo de 10 MB.")

        template_path = self.base_dir / "DEVKIT" / "HOSTAI_IMPORT_PACKAGE_AI_TEMPLATE.md"
        if not template_path.is_file():
            raise HostAIImportAIExportError("No está disponible la plantilla oficial para IA.")
        instructions = template_path.read_text(encoding="utf-8")
        readme = (
            "1. Sube este ZIP a tu herramienta de IA.\n"
            "2. Pídele que prepare el documento para Host AI.\n"
            "3. Descarga el JSON resultante.\n"
            "4. En Host AI pulsa ‘Importar resultado de IA’.\n"
            "5. Selecciona el JSON.\n"
        )

        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr(f"documento/{safe_name}", document)
            archive.writestr(
                "contrato/HOSTAI_IMPORT_PACKAGE_0.1.schema.json",
                json.dumps(hostai_import_package_json_schema(), ensure_ascii=False, indent=2),
            )
            archive.writestr("instrucciones/INSTRUCCIONES_PARA_IA.md", instructions)
            archive.writestr("LEEME.txt", readme)
        ascii_stem = unicodedata.normalize("NFKD", Path(safe_name).stem).encode("ascii", "ignore").decode("ascii")
        stem = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_stem).strip("._") or "documento"
        return f"HOSTAI_PARA_IA_{stem}.zip", output.getvalue()

    @staticmethod
    def _safe_filename(filename: str) -> str:
        value = PurePath(str(filename or "").replace("\\", "/")).name.strip()
        if not value or value in {".", ".."} or "\x00" in value:
            raise HostAIImportAIExportError("El nombre del documento no es válido.")
        return value
