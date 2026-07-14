from pathlib import Path
import json
from MODELOS.recomendaciones_compras import RecomendacionCompra

class MotorRecomendacionesCompras:
    """
    Host AI 3.0.4.2 - Motor Inteligente de Recomendaciones de Compras.
    """
    def __init__(self, core):
        self.core=core; self.base_dir=core.base_dir
        self.facturas_dir=self.base_dir/"DATOS"/"facturas"; self.facturas_dir.mkdir(parents=True, exist_ok=True)

    def generar_recomendaciones(self):
        analisis=self.core.analizador_inteligente_compras.analizar_compras()
        recomendaciones=[]
        if analisis.get("avisos"):
            for av in analisis["avisos"]:
                recomendaciones.append(RecomendacionCompra("datos_insuficientes","aviso",av,"Importar más facturas").to_dict())
        for art in analisis.get("articulos_mas_comprados", []):
            if art.get("cantidad_total",0) > 0:
                recomendaciones.append(RecomendacionCompra("articulo_relevante","info",f"{art['nombre_articulo']} es un artículo con compras registradas.","Revisar precio y proveedor",articulo_id=art["articulo_id"],datos=art).to_dict())
        for prov, gasto in analisis.get("compras_por_proveedor", {}).items():
            if gasto > 0:
                recomendaciones.append(RecomendacionCompra("proveedor_con_gasto","info",f"Hay gasto registrado con {prov}: {gasto}.","Comparar con otros proveedores",proveedor_id=prov,datos={"gasto":gasto}).to_dict())
        if not recomendaciones:
            recomendaciones.append(RecomendacionCompra("sin_accion","info","No hay recomendaciones suficientes todavía.","Importar más facturas").to_dict())
        return {"recomendaciones":recomendaciones,"total":len(recomendaciones),"analisis":analisis,"lectura_host_ai":f"Recomendaciones generadas: {len(recomendaciones)}."}

    def exportar_recomendaciones(self, datos, nombre=""):
        nombre=nombre or "recomendaciones_compras.json"
        destino=self.facturas_dir/nombre
        destino.write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding="utf-8")
        return {"archivo":str(destino),"lectura_host_ai":f"Recomendaciones exportadas: {destino.name}."}
