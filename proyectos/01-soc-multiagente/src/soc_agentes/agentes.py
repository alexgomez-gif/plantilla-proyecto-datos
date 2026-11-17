"""Agentes autónomos del SOC.

Flujo: Monitor -> "alerta" -> Analista -> "incidente" -> Coordinador -> "orden"
-> Respondedor -> "accion". Cada agente solo conoce el bus, no a los demás.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import timedelta

from soc_agentes.bus import BusMensajes, Mensaje
from soc_agentes.eventos import Evento

UMBRAL_FALLOS_LOGIN = 10  # fallos por IP en la ventana
UMBRAL_PUERTOS = 25  # puertos distintos por IP en la ventana
UMBRAL_BYTES = 100_000_000  # bytes enviados al exterior en la ventana
VENTANA = timedelta(minutes=5)


class Agente:
    def __init__(self, nombre: str, bus: BusMensajes) -> None:
        self.nombre = nombre
        self.bus = bus

    def publicar(self, tema: str, contenido: dict) -> None:
        self.bus.publicar(tema, self.nombre, contenido)


class AgenteMonitor(Agente):
    """Lee eventos en streaming y aplica reglas de ventana deslizante por IP."""

    def __init__(self, bus: BusMensajes) -> None:
        super().__init__("monitor", bus)
        self._ventanas: dict[tuple[str, str], deque[Evento]] = defaultdict(deque)
        self._alertadas: set[tuple[str, str]] = set()

    def _ventana(self, regla: str, evento: Evento) -> deque[Evento]:
        cola = self._ventanas[(regla, evento.ip_origen)]
        cola.append(evento)
        while cola and evento.marca_tiempo - cola[0].marca_tiempo > VENTANA:
            cola.popleft()
        return cola

    def _alertar(self, regla: str, evento: Evento, evidencia: dict) -> None:
        clave = (regla, evento.ip_origen)
        if clave in self._alertadas:
            return
        self._alertadas.add(clave)
        self.publicar(
            "alerta",
            {
                "regla": regla,
                "ip": evento.ip_origen,
                "momento": evento.marca_tiempo.isoformat(),
                "evidencia": evidencia,
            },
        )

    def procesar(self, evento: Evento) -> None:
        if evento.tipo == "login" and not evento.exito:
            cola = self._ventana("fuerza_bruta", evento)
            if len(cola) >= UMBRAL_FALLOS_LOGIN:
                usuarios = sorted({e.usuario for e in cola if e.usuario})
                self._alertar("fuerza_bruta", evento, {"fallos": len(cola), "usuarios": usuarios})
        elif evento.tipo == "login" and evento.exito:
            if ("fuerza_bruta", evento.ip_origen) in self._alertadas:
                self._alertar("acceso_tras_fuerza_bruta", evento, {"usuario": evento.usuario})
        elif evento.tipo == "conexion":
            cola = self._ventana("escaneo", evento)
            puertos = {e.puerto for e in cola}
            if len(puertos) >= UMBRAL_PUERTOS:
                self._alertar("escaneo_puertos", evento, {"puertos_distintos": len(puertos)})
        elif evento.tipo == "transferencia" and not evento.destino.startswith("cdn"):
            cola = self._ventana("exfiltracion", evento)
            total = sum(e.bytes_enviados for e in cola)
            if total >= UMBRAL_BYTES:
                self._alertar("exfiltracion", evento, {"bytes": total, "destino": evento.destino})


GRAVEDAD_BASE = {
    "escaneo_puertos": 3,
    "fuerza_bruta": 5,
    "exfiltracion": 8,
    "acceso_tras_fuerza_bruta": 9,
}


class AgenteAnalista(Agente):
    """Enriquece alertas, calcula una puntuación de riesgo y abre incidentes."""

    def __init__(self, bus: BusMensajes) -> None:
        super().__init__("analista", bus)
        self._alertas_por_ip: dict[str, list[str]] = defaultdict(list)
        bus.suscribir("alerta", self.recibir)

    @staticmethod
    def es_interna(ip: str) -> bool:
        return ip.startswith("10.")

    def recibir(self, mensaje: Mensaje) -> None:
        alerta = mensaje.contenido
        ip = alerta["ip"]
        self._alertas_por_ip[ip].append(alerta["regla"])
        puntuacion = GRAVEDAD_BASE[alerta["regla"]]
        # Correlación: varias alertas de la misma IP agravan el riesgo.
        puntuacion += 2 * (len(self._alertas_por_ip[ip]) - 1)
        # Un activo interno exfiltrando sugiere un equipo comprometido.
        if self.es_interna(ip) and alerta["regla"] == "exfiltracion":
            puntuacion += 1
        puntuacion = min(puntuacion, 10)
        self.publicar(
            "incidente",
            {
                **alerta,
                "riesgo": puntuacion,
                "origen": "interno" if self.es_interna(ip) else "externo",
                "alertas_relacionadas": list(self._alertas_por_ip[ip]),
            },
        )


class AgenteCoordinador(Agente):
    """Prioriza incidentes y decide qué acción ordenar al respondedor."""

    def __init__(self, bus: BusMensajes) -> None:
        super().__init__("coordinador", bus)
        self.incidentes: list[dict] = []
        bus.suscribir("incidente", self.recibir)

    @staticmethod
    def decidir(incidente: dict) -> str:
        if incidente["riesgo"] >= 9 and incidente["origen"] == "externo":
            return "bloquear_ip_y_revocar_sesiones"
        if incidente["origen"] == "interno" and incidente["riesgo"] >= 8:
            return "aislar_equipo"
        if incidente["riesgo"] >= 5:
            return "bloquear_ip"
        return "vigilar"

    def recibir(self, mensaje: Mensaje) -> None:
        incidente = {**mensaje.contenido, "accion": self.decidir(mensaje.contenido)}
        self.incidentes.append(incidente)
        self.publicar("orden", incidente)

    def priorizados(self) -> list[dict]:
        return sorted(self.incidentes, key=lambda i: i["riesgo"], reverse=True)


class AgenteRespondedor(Agente):
    """Ejecuta las órdenes en modo simulado: registra la acción, no toca sistemas reales."""

    def __init__(self, bus: BusMensajes) -> None:
        super().__init__("respondedor", bus)
        self.ips_bloqueadas: set[str] = set()
        self.equipos_aislados: set[str] = set()
        bus.suscribir("orden", self.recibir)

    def recibir(self, mensaje: Mensaje) -> None:
        orden = mensaje.contenido
        accion, ip = orden["accion"], orden["ip"]
        if accion.startswith("bloquear_ip"):
            self.ips_bloqueadas.add(ip)
        elif accion == "aislar_equipo":
            self.equipos_aislados.add(ip)
        self.publicar("accion", {"accion": accion, "ip": ip, "simulada": True})
