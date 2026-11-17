from datetime import timedelta

from soc_agentes.agentes import AgenteCoordinador, AgenteMonitor
from soc_agentes.bus import BusMensajes
from soc_agentes.eventos import INICIO, Evento
from soc_agentes.simulacion import ejecutar_simulacion


def test_detecta_los_tres_ataques_y_el_acceso():
    r = ejecutar_simulacion()
    reglas = {(i["regla"], i["ip"]) for i in r.incidentes}
    assert ("fuerza_bruta", "198.51.100.23") in reglas
    assert ("acceso_tras_fuerza_bruta", "198.51.100.23") in reglas
    assert ("escaneo_puertos", "198.51.100.77") in reglas
    assert ("exfiltracion", "10.0.0.21") in reglas


def test_sin_falsos_positivos_en_trafico_normal():
    r = ejecutar_simulacion()
    ips_atacantes = {"198.51.100.23", "198.51.100.77", "10.0.0.21"}
    assert {i["ip"] for i in r.incidentes} <= ips_atacantes


def test_respuesta_coordinada():
    r = ejecutar_simulacion()
    assert "198.51.100.23" in r.ips_bloqueadas
    assert r.equipos_aislados == ["10.0.0.21"]
    assert r.incidentes[0]["riesgo"] == max(i["riesgo"] for i in r.incidentes)
    # Cada alerta recorre toda la cadena de agentes.
    conteo = r.mensajes_por_tema
    assert conteo["alerta"] == conteo["incidente"] == conteo["orden"] == conteo["accion"]


def test_monitor_no_alerta_bajo_umbral():
    bus = BusMensajes()
    monitor = AgenteMonitor(bus)
    for i in range(5):
        t = INICIO + timedelta(seconds=i)
        monitor.procesar(Evento(t, "login", "1.2.3.4", "srv", "x", exito=False))
    assert bus.contar("alerta") == 0


def test_decisiones_del_coordinador():
    decidir = AgenteCoordinador.decidir
    assert decidir({"riesgo": 10, "origen": "externo"}) == "bloquear_ip_y_revocar_sesiones"
    assert decidir({"riesgo": 9, "origen": "interno"}) == "aislar_equipo"
    assert decidir({"riesgo": 5, "origen": "externo"}) == "bloquear_ip"
    assert decidir({"riesgo": 3, "origen": "externo"}) == "vigilar"
