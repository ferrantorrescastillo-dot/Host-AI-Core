from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
import json, re, unicodedata, difflib
from MODELOS.proveedores_pdf import ProveedorPDF, DeteccionProveedorPDF

class DetectorProveedoresPDF:
    PROVEEDORES_BASE = [
        {"proveedor_id":"PROV-MAKRO","nombre_normalizado":"Makro","nombres":["makro","makro españa","makro españa s.a.","makro autoservicio mayorista"],"cifs":["A28647451","A12345678"],"dominios":["makro.es"],"palabras_clave":["makro","mayorista","cash carry"],"categoria":"mayorista"},
        {"proveedor_id":"PROV-BIDFOOD","nombre_normalizado":"Bidfood","nombres":["bidfood","bidfood iberia","guzman gastronomia","guzman gastronomía"],"cifs":[],"dominios":["bidfoodiberia.com"],"palabras_clave":["bidfood","guzman gastronomia"],"categoria":"distribuidor"},
        {"proveedor_id":"PROV-TRANSGOURMET","nombre_normalizado":"Transgourmet","nombres":["transgourmet","transgourmet iberica","transgourmet ibérica"],"cifs":[],"dominios":["transgourmet.es"],"palabras_clave":["transgourmet","gm food"],"categoria":"distribuidor"},
        {"proveedor_id":"PROV-BONAREA","nombre_normalizado":"BonÀrea","nombres":["bonarea","bon àrea","bonarea agrupa"],"cifs":[],"dominios":["bonarea.com"],"palabras_clave":["bonarea","bon àrea","guissona"],"categoria":"alimentacion"},
        {"proveedor_id":"PROV-FRIMAN","nombre_normalizado":"Friman","nombres":["friman","frimancha","frigorificos manchegos"],"cifs":[],"dominios":[],"palabras_clave":["friman","frigorificos"],"categoria":"carnes"},
    ]

    def __init__(self, base_dir: Path, lector_pdf_facturas):
        self.base_dir = Path(base_dir)
        self.lector_pdf_facturas = lector_pdf_facturas
        self.diccionario_path = self.base_dir / "DATOS" / "diccionarios" / "diccionario_proveedores_pdf.json"
        self.diccionario_path.parent.mkdir(parents=True, exist_ok=True)
        self.proveedores = self._cargar_diccionario()

    def detectar_en_pdf(self, ruta_archivo: str) -> Dict[str, Any]:
        analisis = self.lector_pdf_facturas.analizar_pdf(ruta_archivo, exportar_json=True)
        det_fact = analisis.get("deteccion_factura", {})
        return self.detectar_desde_texto(
            texto=analisis.get("texto_completo", ""),
            proveedor_sugerido=det_fact.get("proveedor", ""),
            cif_sugerido=det_fact.get("cif", ""),
            contexto={"archivo": analisis.get("archivo"), "nombre_archivo": analisis.get("nombre_archivo")},
        )

    def detectar_desde_texto(self, texto: str, proveedor_sugerido: str = "", cif_sugerido: str = "", contexto: Dict[str, Any] | None = None) -> Dict[str, Any]:
        contexto = contexto or {}
        texto_norm = self._normalizar(texto)
        proveedor_norm = self._normalizar(proveedor_sugerido)
        cif = (cif_sugerido or self._extraer_cif(texto) or "").upper().strip()

        candidatos = []
        for prov in self.proveedores.values():
            score, metodo, coincidencias = self._puntuar(prov, texto_norm, proveedor_norm, cif)
            if score > 0:
                candidatos.append({"proveedor_id":prov.proveedor_id,"nombre":prov.nombre_normalizado,"confianza":round(score,2),"metodo":metodo,"coincidencias":coincidencias,"categoria":prov.categoria})
        candidatos.sort(key=lambda x: x["confianza"], reverse=True)

        if candidatos:
            mejor = candidatos[0]
            avisos = []
            if len(candidatos)>1 and mejor["confianza"]-candidatos[1]["confianza"]<10:
                avisos.append(f"Detección ambigua entre {mejor['nombre']} y {candidatos[1]['nombre']}.")
            det = DeteccionProveedorPDF(mejor["proveedor_id"], mejor["nombre"], mejor["confianza"], mejor["metodo"], mejor["coincidencias"], candidatos[:5], mejor["confianza"]<70, avisos)
        else:
            nombre = proveedor_sugerido or self._primera_linea(texto)
            det = DeteccionProveedorPDF("", nombre, 0.0, "sin_coincidencia", [], [], True, ["Proveedor no reconocido. Conviene aprenderlo."])
        datos = det.to_dict()
        datos["contexto"] = contexto
        datos["lectura_host_ai"] = f"Proveedor detectado: {datos['nombre']} ({datos['confianza']}%)." if datos.get("proveedor_id") else f"Proveedor pendiente de aprender: {datos.get('nombre') or 'desconocido'}."
        return datos

    def aprender_proveedor(self, nombre: str, proveedor_id: str = "", cif: str = "", dominio: str = "", palabras_clave: List[str] | None = None, categoria: str = "") -> Dict[str, Any]:
        palabras_clave = palabras_clave or []
        proveedor_id = proveedor_id or f"PROV-{self._slug(nombre)}"
        if proveedor_id in self.proveedores:
            prov = self.proveedores[proveedor_id]
            self._add(prov.nombres, nombre)
            if cif: self._add(prov.cifs, cif.upper().strip())
            if dominio: self._add(prov.dominios, dominio.lower().strip())
            for p in palabras_clave: self._add(prov.palabras_clave, p)
            if categoria: prov.categoria = categoria
        else:
            prov = ProveedorPDF(proveedor_id, nombre, [nombre], [cif.upper().strip()] if cif else [], [dominio.lower().strip()] if dominio else [], palabras_clave, categoria, "aprendido")
            self.proveedores[proveedor_id]=prov
        self._guardar()
        return {"proveedor":prov.to_dict(),"lectura_host_ai":f"Proveedor aprendido/actualizado: {prov.nombre_normalizado}."}

    def listar_proveedores(self) -> Dict[str, Any]:
        proveedores=[p.to_dict() for p in self.proveedores.values()]
        return {"proveedores":proveedores,"total":len(proveedores),"lectura_host_ai":f"Diccionario de proveedores PDF: {len(proveedores)} proveedores."}

    def exportar_diccionario(self) -> Dict[str, Any]:
        self._guardar()
        return {"archivo":str(self.diccionario_path),"lectura_host_ai":"Diccionario de proveedores PDF exportado."}

    def _puntuar(self, prov: ProveedorPDF, texto_norm: str, proveedor_norm: str, cif: str):
        score=0.0; metodo="sin_coincidencia"; coincidencias=[]
        if cif and cif in [c.upper() for c in prov.cifs]:
            score=100; metodo="cif"; coincidencias.append(f"CIF {cif}")
        for dominio in prov.dominios:
            d=self._normalizar(dominio)
            if d and d in texto_norm:
                score=max(score,90); metodo="dominio"; coincidencias.append(f"Dominio {dominio}")
        for nombre in prov.nombres:
            n=self._normalizar(nombre)
            if not n: continue
            if proveedor_norm and (n==proveedor_norm or n in proveedor_norm or proveedor_norm in n):
                score=max(score,95); metodo="nombre_sugerido"; coincidencias.append(f"Nombre {nombre}")
            elif n in texto_norm:
                score=max(score,85); metodo="nombre_en_texto"; coincidencias.append(f"Texto {nombre}")
            elif proveedor_norm:
                ratio=difflib.SequenceMatcher(None, proveedor_norm, n).ratio()
                if ratio>=0.78 and ratio*80>score:
                    score=ratio*80; metodo="parecido_nombre"; coincidencias.append(f"Parecido {nombre}: {round(ratio,2)}")
        claves=0
        for clave in prov.palabras_clave:
            c=self._normalizar(clave)
            if c and c in texto_norm:
                claves+=1; coincidencias.append(f"Clave {clave}")
        if claves:
            score=max(score, min(80, 35+claves*15))
            if metodo=="sin_coincidencia": metodo="palabras_clave"
        return min(100.0, score), metodo, coincidencias[:10]

    def _cargar_diccionario(self):
        if self.diccionario_path.exists():
            try:
                raw=json.loads(self.diccionario_path.read_text(encoding="utf-8"))
                proveedores={}
                for item in raw.get("proveedores",[]):
                    p=ProveedorPDF(**item); proveedores[p.proveedor_id]=p
                if proveedores: return proveedores
            except Exception:
                pass
        proveedores={}
        for item in self.PROVEEDORES_BASE:
            p=ProveedorPDF(**item); proveedores[p.proveedor_id]=p
        self._guardar_dict(proveedores)
        return proveedores

    def _guardar(self): self._guardar_dict(self.proveedores)
    def _guardar_dict(self, proveedores):
        self.diccionario_path.write_text(json.dumps({"version":"3.0.3.2","proveedores":[p.to_dict() for p in proveedores.values()]}, ensure_ascii=False, indent=2), encoding="utf-8")
    def _normalizar(self,texto):
        texto=str(texto or "").strip().lower()
        texto="".join(c for c in unicodedata.normalize("NFD",texto) if unicodedata.category(c)!="Mn")
        texto=texto.replace("_"," ").replace("-"," ").replace("."," ")
        return " ".join(texto.split())
    def _extraer_cif(self,texto):
        m=re.search(r"\b([A-Z][0-9]{8})\b", texto or "", re.I)
        return m.group(1).upper() if m else ""
    def _primera_linea(self,texto):
        for l in (texto or "").splitlines():
            if l.strip(): return l.strip()[:80]
        return ""
    def _slug(self,texto):
        t=self._normalizar(texto).upper()
        return re.sub(r"[^A-Z0-9]+","-",t).strip("-")[:40] or "SIN-NOMBRE"
    def _add(self,lista,valor):
        v=str(valor or "").strip()
        if v and v not in lista: lista.append(v)
