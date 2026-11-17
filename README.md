# Portafolio de datos · Alex Gómez

**Científico de datos.** Construyo sistemas que convierten datos en decisiones, con
especial interés en ciberseguridad y en sistemas de agentes autónomos.

## Proyectos

| # | Proyecto | Temas | Tecnologías |
|---|---|---|---|
| 01 | [SOC multiagente: detección y respuesta coordinada](proyectos/01-soc-multiagente) | Ciberseguridad, agentes autónomos, detección de anomalías | Python |
| 02 | Próximamente | | |
| 03 | Próximamente | | |

### 01 · SOC multiagente

Cuatro agentes (monitor, analista, coordinador y respondedor) se comunican por un bus de
mensajes para detectar fuerza bruta, escaneo de puertos y exfiltración en logs de red, y
deciden una respuesta según el riesgo. Detecta los tres ataques sin falsos positivos.
[Ver proyecto →](proyectos/01-soc-multiagente)

## Habilidades

- **Lenguajes:** Python, SQL
- **Ciencia de datos:** análisis exploratorio, detección de anomalías, modelado
- **Ingeniería:** pruebas con pytest, calidad con ruff, CI con GitHub Actions

## Estructura

```
proyectos/
└── 01-soc-multiagente/   # cada proyecto es independiente: su propio README, código y pruebas
```

Cada proyecto se instala y prueba por separado (ver su README). La CI ejecuta ruff y
pytest para todos en cada push.

## Contacto

<!-- Añade aquí tu LinkedIn, correo o web -->
