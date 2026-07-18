# Reporte de Orquestación: [FEATURE]

**Feature**: `[###-nombre]` | **Creado**: [FECHA] | **Principal**: [cli/modelo que orquesta]

> Plantilla del reporte multi-CLI. Secciones PARSEABLES (tablas de columnas fijas,
> las lee la retomabilidad): "Modelos por fase" y "Asignaciones". Secciones
> INFORMATIVAS (prosa, solo para humanos): "Triage", "Eventos", "Métricas".
> Ninguna lógica debe depender de parsear las secciones informativas.

## Triage

- **Complejidad de la idea**: [simple | media | compleja]
- **Justificación (rúbrica)**: [componentes tocados, claridad de criterios, riesgo]
- **Flujo invocado**: [ECO | IDEAL] | **Flujo recomendado**: [ECO | IDEAL]
- **Resolución de discordancia**: [n/a | preguntado al usuario | cambiado por -bypass]
- **Punto de entrada**: [cli/modelo] → [sin cambio | escalado a X | degradado a X]

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | cli/modelo | pendiente |
| plan | cli/modelo | pendiente |
| tasks | cli/modelo | pendiente |
| implement | (por tarea, ver Asignaciones) | pendiente |

<!-- Estados válidos: pendiente | ejecutada | omitida. Filas según el flujo elegido. -->

## Asignaciones

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | baja | kimi/k2 | pendiente |

<!-- Estados válidos: pendiente | en_ejecucion | verificada | reasignada | rechazada | pendiente_bloqueada -->

## Eventos

<!-- Registro cronológico informativo: fallbacks, reintentos, cuotas agotadas,
     cambios de flujo, escaladas/degradaciones. Formato libre, una línea por evento:
     - [timestamp] tipo — detalle (causa) -->

## Métricas

<!-- Al cierre de la orquestación:
     - Tareas por modelo (tabla o lista)
     - % de tareas ejecutadas por modelos económicos (costo < 3)
     - Consumo estimado del modelo caro vs. baseline (SC-004), en la unidad que
       reporte cada CLI (tokens o % de cuota) -->
