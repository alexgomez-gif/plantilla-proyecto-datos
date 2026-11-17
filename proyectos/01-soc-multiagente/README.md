# SOC multiagente: detección y respuesta coordinada

Simulación de un centro de operaciones de seguridad (SOC) en el que cuatro agentes
autónomos colaboran para detectar ataques en logs de red y decidir una respuesta.
Escrito en Python, solo con la biblioteca estándar.

## Problema

Un analista humano no puede revisar miles de eventos por hora. La idea es repartir el
trabajo entre agentes especializados que no se conocen entre sí y solo se comunican
mediante mensajes, igual que los microservicios de un SOC real.

## Arquitectura

```
 eventos ──► Monitor ──alerta──► Analista ──incidente──► Coordinador ──orden──► Respondedor
             (reglas en          (correlación y         (prioriza y            (ejecuta en
              ventana de 5 min)   puntuación 1-10)        decide la acción)      modo simulado)
                         └──────────────── BusMensajes (publicar/suscribir) ────────────────┘
```

| Agente | Responsabilidad |
|---|---|
| **Monitor** | Ventanas deslizantes por IP: fallos de login, puertos distintos y bytes enviados al exterior. |
| **Analista** | Asigna riesgo según la regla, lo agrava si la misma IP acumula alertas y distingue origen interno o externo. |
| **Coordinador** | Ordena los incidentes por riesgo y elige: vigilar, bloquear IP, bloquear y revocar sesiones o aislar el equipo. |
| **Respondedor** | Registra la acción. No toca sistemas reales: es una simulación defensiva. |

## Datos

`eventos.py` genera unos 400 eventos de tráfico normal (semilla fija, reproducible) y
mezcla tres ataques: fuerza bruta SSH con acceso final exitoso, escaneo de puertos y
exfiltración desde un equipo interno. Las IPs externas usan rangos de documentación
(RFC 5737).

## Resultado

```
Riesgo  Regla                      IP              Acción
    10  acceso_tras_fuerza_bruta   198.51.100.23   bloquear_ip_y_revocar_sesiones
     9  exfiltracion               10.0.0.21       aislar_equipo
     5  fuerza_bruta               198.51.100.23   bloquear_ip
     3  escaneo_puertos            198.51.100.77   vigilar
```

Los tres ataques se detectan sin falsos positivos en el tráfico normal, y la correlación
eleva el acceso tras fuerza bruta al riesgo máximo.

## Cómo ejecutarlo

```bash
cd proyectos/01-soc-multiagente
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest
soc-agentes                       # imprime el informe
soc-agentes --json informe.json   # y lo guarda en JSON
pytest                            # pruebas
```

## Próximos pasos

- Sustituir las reglas fijas por un modelo de detección de anomalías (Isolation Forest).
- Usar logs reales públicos, por ejemplo el conjunto CIC-IDS2017.
- Añadir un agente con LLM que redacte el resumen del incidente para el analista.
