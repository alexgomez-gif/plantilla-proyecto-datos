"""Generación de eventos de seguridad sintéticos (logs de red y autenticación)."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

INICIO = datetime(2026, 1, 15, 8, 0, 0)
IPS_INTERNAS = [f"10.0.0.{i}" for i in range(10, 40)]
USUARIOS = ["ana", "luis", "marta", "jorge", "sofia", "admin"]


@dataclass(frozen=True)
class Evento:
    """Un registro de log normalizado."""

    marca_tiempo: datetime
    tipo: str  # "login", "conexion" o "transferencia"
    ip_origen: str
    destino: str
    usuario: str | None = None
    exito: bool = True
    puerto: int | None = None
    bytes_enviados: int = 0

    def a_dict(self) -> dict:
        datos = asdict(self)
        datos["marca_tiempo"] = self.marca_tiempo.isoformat()
        return datos


def _trafico_normal(rng: random.Random, n: int) -> list[Evento]:
    eventos = []
    for _ in range(n):
        t = INICIO + timedelta(seconds=rng.randint(0, 3600))
        ip = rng.choice(IPS_INTERNAS)
        tipo = rng.choices(["login", "conexion", "transferencia"], [3, 5, 2])[0]
        if tipo == "login":
            eventos.append(
                Evento(t, "login", ip, "srv-auth", rng.choice(USUARIOS), rng.random() > 0.05)
            )
        elif tipo == "conexion":
            puerto = rng.choice([80, 443, 443, 443, 22, 53])
            eventos.append(Evento(t, "conexion", ip, "srv-web", puerto=puerto))
        else:
            eventos.append(
                Evento(
                    t,
                    "transferencia",
                    ip,
                    "cdn-externa",
                    bytes_enviados=rng.randint(1_000, 2_000_000),
                )
            )
    return eventos


def _fuerza_bruta(rng: random.Random, ip: str) -> list[Evento]:
    t0 = INICIO + timedelta(minutes=12)
    eventos = [
        Evento(t0 + timedelta(seconds=2 * i), "login", ip, "srv-auth", "admin", exito=False)
        for i in range(25)
    ]
    eventos.append(Evento(t0 + timedelta(seconds=52), "login", ip, "srv-auth", "admin", exito=True))
    return eventos


def _escaneo_puertos(rng: random.Random, ip: str) -> list[Evento]:
    t0 = INICIO + timedelta(minutes=30)
    puertos = rng.sample(range(1, 1024), 60)
    return [
        Evento(t0 + timedelta(milliseconds=300 * i), "conexion", ip, "srv-db", puerto=p)
        for i, p in enumerate(puertos)
    ]


def _exfiltracion(ip: str) -> list[Evento]:
    t0 = INICIO + timedelta(minutes=45)
    return [
        Evento(
            t0 + timedelta(seconds=20 * i),
            "transferencia",
            ip,
            "203.0.113.50",
            bytes_enviados=80_000_000,
        )
        for i in range(5)
    ]


def generar_eventos(semilla: int = 42, n_normales: int = 400) -> list[Evento]:
    """Genera tráfico normal mezclado con tres ataques conocidos, ordenado por tiempo."""
    rng = random.Random(semilla)
    eventos = _trafico_normal(rng, n_normales)
    eventos += _fuerza_bruta(rng, "198.51.100.23")
    eventos += _escaneo_puertos(rng, "198.51.100.77")
    eventos += _exfiltracion("10.0.0.21")
    return sorted(eventos, key=lambda e: e.marca_tiempo)
