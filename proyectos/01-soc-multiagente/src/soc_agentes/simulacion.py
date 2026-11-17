"""Orquesta la simulación completa y genera un informe."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from soc_agentes.agentes import (
    AgenteAnalista,
    AgenteCoordinador,
    AgenteMonitor,
    AgenteRespondedor,
)
from soc_agentes.bus import BusMensajes
from soc_agentes.eventos import generar_eventos


@dataclass
class Resultado:
    eventos_procesados: int
    incidentes: list[dict]
    ips_bloqueadas: list[str]
    equipos_aislados: list[str]
    mensajes_por_tema: dict[str, int]

    def a_dict(self) -> dict:
        return self.__dict__


def ejecutar_simulacion(semilla: int = 42, n_normales: int = 400) -> Resultado:
    bus = BusMensajes()
    monitor = AgenteMonitor(bus)
    AgenteAnalista(bus)
    coordinador = AgenteCoordinador(bus)
    respondedor = AgenteRespondedor(bus)

    eventos = generar_eventos(semilla, n_normales)
    for evento in eventos:
        monitor.procesar(evento)

    temas = ["alerta", "incidente", "orden", "accion"]
    return Resultado(
        eventos_procesados=len(eventos),
        incidentes=coordinador.priorizados(),
        ips_bloqueadas=sorted(respondedor.ips_bloqueadas),
        equipos_aislados=sorted(respondedor.equipos_aislados),
        mensajes_por_tema={t: bus.contar(t) for t in temas},
    )


def imprimir_informe(r: Resultado) -> None:
    print(f"Eventos procesados: {r.eventos_procesados}")
    print(f"Mensajes en el bus: {r.mensajes_por_tema}\n")
    print(f"{'Riesgo':>6}  {'Regla':<26} {'IP':<15} Acción")
    for i in r.incidentes:
        print(f"{i['riesgo']:>6}  {i['regla']:<26} {i['ip']:<15} {i['accion']}")
    print(f"\nIPs bloqueadas: {', '.join(r.ips_bloqueadas) or '-'}")
    print(f"Equipos aislados: {', '.join(r.equipos_aislados) or '-'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulación de un SOC multiagente")
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--eventos", type=int, default=400, help="eventos normales")
    parser.add_argument("--json", type=Path, help="guardar el informe en JSON")
    args = parser.parse_args()

    resultado = ejecutar_simulacion(args.semilla, args.eventos)
    imprimir_informe(resultado)
    if args.json:
        args.json.write_text(json.dumps(resultado.a_dict(), indent=2, ensure_ascii=False))
        print(f"\nInforme guardado en {args.json}")


if __name__ == "__main__":
    main()
