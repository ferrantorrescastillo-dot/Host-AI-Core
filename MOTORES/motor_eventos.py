from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
import copy
import re
import unicodedata
import uuid


def nuevo_id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8].upper()}"


@dataclass
class Pase:
    nombre: str
    hora_inicio: str
    duracion_min: int
    recetas: List[str] = field(default_factory=list)
    notas: str = ""
    id: str = field(default_factory=lambda: nuevo_id("PASE"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "Pase":
        return cls(
            nombre=str(datos.get("nombre", "Pase")),
            hora_inicio=str(datos.get("hora_inicio", "21:00")),
            duracion_min=int(datos.get("duracion_min", 30) or 30),
            recetas=list(datos.get("recetas", []) or []),
            notas=str(datos.get("notas", "")),
            id=str(datos.get("id") or nuevo_id("PASE")),
        )


@dataclass
class Servicio:
    nombre: str
    tipo: str
    hora_inicio: str
    duracion_min: int
    pases: List[Pase] = field(default_factory=list)
    id: str = field(default_factory=lambda: nuevo_id("SERV"))

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "pases": [p.to_dict() for p in self.pases]}

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "Servicio":
        return cls(
            nombre=str(datos.get("nombre", "Servicio")),
            tipo=str(datos.get("tipo", "servicio")),
            hora_inicio=str(datos.get("hora_inicio", "20:00")),
            duracion_min=int(datos.get("duracion_min", 240) or 240),
            pases=[Pase.from_dict(p) for p in datos.get("pases", []) or []],
            id=str(datos.get("id") or nuevo_id("SERV")),
        )


@dataclass
class Evento:
    nombre: str
    fecha: str
    pax: int
    tipo: str = "evento"
    cliente: str = ""
    telefono: str = ""
    email: str = ""
    ubicacion: str = ""
    hora_inicio: str = ""
    observaciones: str = ""
    estado: str = "pendiente"
    servicios: List[Servicio] = field(default_factory=list)
    id: str = field(default_factory=lambda: nuevo_id("EVT"))

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "servicios": [s.to_dict() for s in self.servicios]}

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "Evento":
        return cls(
            nombre=str(datos.get("nombre", "Evento")),
            fecha=str(datos.get("fecha", "")),
            pax=int(datos.get("pax", datos.get("personas", 0)) or 0),
            tipo=str(datos.get("tipo", "evento")),
            cliente=str(datos.get("cliente", "")),
            telefono=str(datos.get("telefono", datos.get("teléfono", ""))),
            email=str(datos.get("email", "")),
            ubicacion=str(datos.get("ubicacion", datos.get("lugar", ""))),
            hora_inicio=str(datos.get("hora_inicio", datos.get("hora", ""))),
            observaciones=str(datos.get("observaciones", datos.get("notas", ""))),
            estado=str(datos.get("estado", "pendiente") or "pendiente"),
            servicios=[Servicio.from_dict(s) for s in datos.get("servicios", []) or []],
            id=str(datos.get("id") or nuevo_id("EVT")),
        )


class MotorEventos:
    """Motor canónico de eventos de Host AI Base.

    E1 añadió gestión completa y persistencia automática.
    E2 incorpora una ficha profesional, estados y fechas flexibles.
    E3 completa servicios, pases, línea temporal y resumen operativo.
    """

    ESTADOS = (
        "presupuesto", "pendiente", "confirmado", "produccion",
        "finalizado", "facturado", "cancelado",
    )
    CAMPOS_EDITABLES = {
        "nombre", "fecha", "pax", "tipo", "cliente", "telefono", "email",
        "ubicacion", "hora_inicio", "observaciones", "estado",
    }
    MESES = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
        "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9,
        "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    DIAS_SEMANA = {
        "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
        "viernes": 4, "sabado": 5, "domingo": 6,
    }

    @staticmethod
    def _sin_acentos(texto: str) -> str:
        return "".join(
            c for c in unicodedata.normalize("NFD", texto or "")
            if unicodedata.category(c) != "Mn"
        ).lower().strip()

    @classmethod
    def normalizar_fecha(cls, valor: str, referencia: Optional[date] = None) -> str:
        """Convierte fechas habituales en cocina a ISO YYYY-MM-DD."""
        referencia = referencia or date.today()
        texto_original = (valor or "").strip().strip('"').strip("'")
        texto = cls._sin_acentos(texto_original)
        if not texto:
            return referencia.isoformat()
        if texto in {"hoy"}:
            return referencia.isoformat()
        if texto in {"manana"}:
            return (referencia + timedelta(days=1)).isoformat()
        if texto in {"pasado manana"}:
            return (referencia + timedelta(days=2)).isoformat()
        if texto in cls.DIAS_SEMANA:
            objetivo = cls.DIAS_SEMANA[texto]
            dias = (objetivo - referencia.weekday()) % 7
            return (referencia + timedelta(days=dias)).isoformat()

        # ISO y variantes numéricas habituales.
        for formato in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"):
            try:
                return datetime.strptime(texto_original, formato).date().isoformat()
            except ValueError:
                pass

        limpio = re.sub(r"\bde\b", " ", texto)
        limpio = re.sub(r"\s+", " ", limpio).strip()
        patron = re.fullmatch(r"(\d{1,2})\s+([a-z]+)(?:\s+(\d{2,4}))?", limpio)
        if patron and patron.group(2) in cls.MESES:
            dia = int(patron.group(1))
            mes = cls.MESES[patron.group(2)]
            anio_txt = patron.group(3)
            anio = int(anio_txt) if anio_txt else referencia.year
            if anio < 100:
                anio += 2000
            resultado = date(anio, mes, dia)
            if not anio_txt and resultado < referencia:
                resultado = date(anio + 1, mes, dia)
            return resultado.isoformat()
        raise ValueError(f"Fecha no reconocida: {valor}")

    @classmethod
    def normalizar_estado(cls, valor: str) -> str:
        texto = cls._sin_acentos(valor).replace(" ", "_")
        alias = {
            "en_produccion": "produccion", "producción": "produccion",
            "confirmada": "confirmado", "finalizada": "finalizado",
            "facturada": "facturado", "cancelada": "cancelado",
        }
        texto = alias.get(texto, texto)
        if texto not in cls.ESTADOS:
            raise ValueError(f"Estado no válido: {valor}")
        return texto

    @staticmethod
    def normalizar_hora(valor: str) -> str:
        texto = (valor or "").strip()
        if not texto:
            return ""
        try:
            return datetime.strptime(texto, "%H:%M").strftime("%H:%M")
        except ValueError as exc:
            raise ValueError("La hora debe tener formato HH:MM.") from exc

    def __init__(self, db=None):
        self.db = db
        self.eventos: Dict[str, Evento] = {}
        self._cargar_desde_db()

    def _cargar_desde_db(self) -> None:
        if self.db is None:
            return
        for datos in self.db.cargar("eventos"):
            try:
                evento = Evento.from_dict(datos)
                self.eventos[evento.id] = evento
            except (TypeError, ValueError):
                # Un registro antiguo o dañado no impide arrancar Host AI.
                continue

    def _persistir(self) -> None:
        if self.db is not None:
            self.db.guardar("eventos", [e.to_dict() for e in self.eventos.values()])

    def crear_evento(
        self, nombre, fecha, pax, tipo="evento", cliente="", telefono="",
        email="", ubicacion="", hora_inicio="", observaciones="",
        estado="pendiente",
    ):
        pax = int(pax)
        if pax < 0:
            raise ValueError("Los pax no pueden ser negativos.")
        evento = Evento(
            nombre=str(nombre).strip() or "Evento",
            fecha=self.normalizar_fecha(fecha),
            pax=pax,
            tipo=str(tipo).strip() or "evento",
            cliente=str(cliente).strip(),
            telefono=str(telefono).strip(),
            email=str(email).strip(),
            ubicacion=str(ubicacion).strip(),
            hora_inicio=self.normalizar_hora(hora_inicio),
            observaciones=str(observaciones).strip(),
            estado=self.normalizar_estado(estado or "pendiente"),
        )
        self.eventos[evento.id] = evento
        self._persistir()
        return evento

    def obtener(self, evento_id):
        if evento_id not in self.eventos:
            raise ValueError(f"No existe evento: {evento_id}")
        return self.eventos[evento_id]

    def listar_eventos(self) -> List[Evento]:
        return sorted(
            self.eventos.values(),
            key=lambda evento: (evento.fecha or "9999-99-99", evento.nombre.lower()),
        )

    def buscar_eventos(self, texto: str) -> List[Evento]:
        consulta = (texto or "").strip().lower()
        if not consulta:
            return self.listar_eventos()
        return [
            evento
            for evento in self.listar_eventos()
            if consulta in " ".join(
                [
                    evento.id,
                    evento.nombre,
                    evento.fecha,
                    evento.tipo,
                    evento.cliente,
                    evento.telefono,
                    evento.email,
                    evento.ubicacion,
                    evento.observaciones,
                    evento.estado,
                ]
            ).lower()
        ]

    def editar_evento(self, evento_id: str, cambios: Dict[str, Any]) -> Evento:
        evento = self.obtener(evento_id)
        for campo, valor in (cambios or {}).items():
            if campo not in self.CAMPOS_EDITABLES or valor is None:
                continue
            if campo == "pax":
                valor = int(valor)
                if valor < 0:
                    raise ValueError("Los pax no pueden ser negativos.")
            elif campo == "fecha":
                valor = self.normalizar_fecha(str(valor))
            elif campo == "estado":
                valor = self.normalizar_estado(str(valor))
            elif campo == "hora_inicio":
                valor = self.normalizar_hora(str(valor))
            elif isinstance(valor, str):
                valor = valor.strip()
            setattr(evento, campo, valor)
        self._persistir()
        return evento

    def eliminar_evento(self, evento_id: str) -> Evento:
        evento = self.obtener(evento_id)
        del self.eventos[evento_id]
        self._persistir()
        return evento

    def duplicar_evento(self, evento_id: str, nombre: Optional[str] = None, fecha: Optional[str] = None) -> Evento:
        original = self.obtener(evento_id)
        datos = copy.deepcopy(original.to_dict())
        datos["id"] = nuevo_id("EVT")
        datos["nombre"] = nombre or f"{original.nombre} (copia)"
        if fecha:
            datos["fecha"] = self.normalizar_fecha(fecha)
        for servicio in datos.get("servicios", []):
            servicio["id"] = nuevo_id("SERV")
            for pase in servicio.get("pases", []):
                pase["id"] = nuevo_id("PASE")
        duplicado = Evento.from_dict(datos)
        self.eventos[duplicado.id] = duplicado
        self._persistir()
        return duplicado

    def agregar_servicio(self, evento_id, nombre, tipo="servicio", hora_inicio="20:00", duracion_min=240):
        evento = self.obtener(evento_id)
        hora = self.normalizar_hora(hora_inicio) or "20:00"
        duracion = int(duracion_min)
        if duracion <= 0:
            raise ValueError("La duración del servicio debe ser mayor que cero.")
        evento.servicios.append(Servicio(str(nombre).strip() or "Servicio", str(tipo).strip() or "servicio", hora, duracion))
        self._persistir()
        return evento

    def obtener_servicio(self, evento_id: str, servicio_id: str) -> Servicio:
        evento = self.obtener(evento_id)
        for servicio in evento.servicios:
            if servicio.id == servicio_id:
                return servicio
        raise ValueError(f"No existe servicio: {servicio_id}")

    def editar_servicio(self, evento_id: str, servicio_id: str, cambios: Dict[str, Any]) -> Evento:
        servicio = self.obtener_servicio(evento_id, servicio_id)
        if cambios.get("nombre") is not None:
            servicio.nombre = str(cambios["nombre"]).strip() or servicio.nombre
        if cambios.get("tipo") is not None:
            servicio.tipo = str(cambios["tipo"]).strip() or servicio.tipo
        if cambios.get("hora_inicio") is not None:
            servicio.hora_inicio = self.normalizar_hora(str(cambios["hora_inicio"]))
        if cambios.get("duracion_min") is not None:
            duracion = int(cambios["duracion_min"])
            if duracion <= 0:
                raise ValueError("La duración del servicio debe ser mayor que cero.")
            servicio.duracion_min = duracion
        self._persistir()
        return self.obtener(evento_id)

    def eliminar_servicio(self, evento_id: str, servicio_id: str) -> Evento:
        evento = self.obtener(evento_id)
        servicio = self.obtener_servicio(evento_id, servicio_id)
        evento.servicios.remove(servicio)
        self._persistir()
        return evento

    def duplicar_servicio(self, evento_id: str, servicio_id: str, nombre: Optional[str] = None) -> Evento:
        evento = self.obtener(evento_id)
        original = self.obtener_servicio(evento_id, servicio_id)
        datos = copy.deepcopy(original.to_dict())
        datos["id"] = nuevo_id("SERV")
        datos["nombre"] = nombre or f"{original.nombre} (copia)"
        for pase in datos.get("pases", []):
            pase["id"] = nuevo_id("PASE")
        evento.servicios.append(Servicio.from_dict(datos))
        self._persistir()
        return evento

    def agregar_pase(self, evento_id, servicio_id, nombre, hora_inicio, duracion_min, recetas=None, notas=""):
        servicio = self.obtener_servicio(evento_id, servicio_id)
        hora = self.normalizar_hora(hora_inicio) or "21:00"
        duracion = int(duracion_min)
        if duracion <= 0:
            raise ValueError("La duración del pase debe ser mayor que cero.")
        recetas_limpias = []
        for receta in recetas or []:
            receta_id = str(receta).strip()
            if receta_id and receta_id not in recetas_limpias:
                recetas_limpias.append(receta_id)
        servicio.pases.append(Pase(str(nombre).strip() or "Pase", hora, duracion, recetas_limpias, str(notas).strip()))
        self._persistir()
        return self.obtener(evento_id)

    def obtener_pase(self, evento_id: str, servicio_id: str, pase_id: str) -> Pase:
        servicio = self.obtener_servicio(evento_id, servicio_id)
        for pase in servicio.pases:
            if pase.id == pase_id:
                return pase
        raise ValueError(f"No existe pase: {pase_id}")

    def editar_pase(self, evento_id: str, servicio_id: str, pase_id: str, cambios: Dict[str, Any]) -> Evento:
        pase = self.obtener_pase(evento_id, servicio_id, pase_id)
        if cambios.get("nombre") is not None:
            pase.nombre = str(cambios["nombre"]).strip() or pase.nombre
        if cambios.get("hora_inicio") is not None:
            pase.hora_inicio = self.normalizar_hora(str(cambios["hora_inicio"]))
        if cambios.get("duracion_min") is not None:
            duracion = int(cambios["duracion_min"])
            if duracion <= 0:
                raise ValueError("La duración del pase debe ser mayor que cero.")
            pase.duracion_min = duracion
        if cambios.get("recetas") is not None:
            pase.recetas = list(dict.fromkeys(str(r).strip() for r in cambios["recetas"] if str(r).strip()))
        if cambios.get("notas") is not None:
            pase.notas = str(cambios["notas"]).strip()
        self._persistir()
        return self.obtener(evento_id)

    def eliminar_pase(self, evento_id: str, servicio_id: str, pase_id: str) -> Evento:
        servicio = self.obtener_servicio(evento_id, servicio_id)
        pase = self.obtener_pase(evento_id, servicio_id, pase_id)
        servicio.pases.remove(pase)
        self._persistir()
        return self.obtener(evento_id)

    def duplicar_pase(self, evento_id: str, servicio_id: str, pase_id: str, nombre: Optional[str] = None) -> Evento:
        servicio = self.obtener_servicio(evento_id, servicio_id)
        original = self.obtener_pase(evento_id, servicio_id, pase_id)
        datos = copy.deepcopy(original.to_dict())
        datos["id"] = nuevo_id("PASE")
        datos["nombre"] = nombre or f"{original.nombre} (copia)"
        servicio.pases.append(Pase.from_dict(datos))
        self._persistir()
        return self.obtener(evento_id)

    @staticmethod
    def _minutos(hora: str) -> int:
        try:
            horas, minutos = str(hora).split(":", 1)
            return int(horas) * 60 + int(minutos)
        except (TypeError, ValueError):
            return 24 * 60

    def construir_linea_temporal(self, evento_id):
        evento = self.obtener(evento_id)
        linea = []
        for servicio in evento.servicios:
            linea.append({
                "tipo": "servicio", "hora": servicio.hora_inicio,
                "nombre": servicio.nombre, "servicio_id": servicio.id,
                "duracion_min": servicio.duracion_min,
            })
            for pase in servicio.pases:
                linea.append({
                    "tipo": "pase", "hora": pase.hora_inicio,
                    "nombre": pase.nombre, "servicio": servicio.nombre,
                    "servicio_id": servicio.id, "pase_id": pase.id,
                    "duracion_min": pase.duracion_min,
                    "recetas": list(pase.recetas), "notas": pase.notas,
                })
        linea.sort(key=lambda item: (self._minutos(item.get("hora", "")), 0 if item["tipo"] == "servicio" else 1))
        totales = {
            "servicios": len(evento.servicios),
            "pases": sum(len(s.pases) for s in evento.servicios),
            "recetas_en_pases": sum(len(p.recetas) for s in evento.servicios for p in s.pases),
        }
        return {
            "evento": evento.to_dict(),
            "linea_temporal": linea,
            "totales": totales,
            "lectura_host_ai": f"Línea temporal de '{evento.nombre}': {totales['servicios']} servicios y {totales['pases']} pases.",
        }

    def resumen_ejecutivo(self, evento_id: str) -> Dict[str, Any]:
        evento = self.obtener(evento_id)
        recetas = [r for s in evento.servicios for p in s.pases for r in p.recetas]
        avisos = []
        if not evento.servicios:
            avisos.append("Faltan servicios.")
        if any(not s.pases for s in evento.servicios):
            avisos.append("Hay servicios sin pases.")
        if any(not p.recetas for s in evento.servicios for p in s.pases):
            avisos.append("Hay pases sin recetas.")
        return {
            "evento": evento.to_dict(),
            "totales": {
                "servicios": len(evento.servicios),
                "pases": sum(len(s.pases) for s in evento.servicios),
                "recetas": len(recetas),
                "recetas_unicas": len(set(recetas)),
            },
            "avisos": avisos,
            "estado_operativo": "listo" if not avisos else "revisar",
        }

    def diagnosticar_evento(self, evento_id):
        evento = self.obtener(evento_id)
        avisos = []
        if not evento.servicios:
            avisos.append("El evento no tiene servicios.")
        for servicio in evento.servicios:
            if not servicio.pases:
                avisos.append(f"El servicio {servicio.nombre} no tiene pases.")
        return {
            "estado_diagnostico": "revisar" if avisos else "ok",
            "avisos": avisos,
            "lectura_host_ai": "Evento listo." if not avisos else f"Evento con {len(avisos)} avisos.",
        }
