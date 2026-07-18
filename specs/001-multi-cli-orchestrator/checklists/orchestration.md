# Checklist: Calidad de Requisitos — Orquestación y Contratos de Datos

**Purpose**: Validar que los requisitos de orquestación multi-CLI y sus contratos de datos estén completos, claros y sin ambigüedades antes de generar tareas e implementar
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: Confiabilidad de orquestación + contratos de datos | **Depth**: estándar | **Audience**: autor
**Status**: ✅ Revisado 2026-07-18 — 27/27 ítems resueltos (13 ya cubiertos, 14 corregidos en spec/artefactos)

## Confiabilidad de la Orquestación

- [x] CHK001 - ¿Está definido el orden exacto de fallback cuando se agotan todos los candidatos de un nivel de complejidad (baja → media → alta)? [Completeness, Spec §Edge Cases, FR-018]
- [x] CHK002 - ¿Está especificado qué pasa con las tareas ya en ejecución cuando el orquestador pausa por falta total de candidatos? [Gap → resuelto: nuevo edge case — se esperan y verifican; solo las no despachadas quedan bloqueadas]
- [x] CHK003 - ¿Se define cuántas tareas `[P]` pueden correr en paralelo a la vez (límite de concurrencia), o queda sin acotar? [Gap → resuelto: FR-017 — límite configurable, 4 por defecto]
- [x] CHK004 - ¿El criterio de "verificación estándar" (diff cumple la tarea + validaciones existentes) es objetivamente evaluable para tareas sin tests en el proyecto? [Measurability, Spec §FR-019 — el inciso (a) aplica siempre; (b) es condicional explícito]
- [x] CHK005 - ¿Está definido el comportamiento cuando la verificación falla repetidamente para la misma tarea? [Coverage → resuelto: FR-019 — 1 reintento con feedback, 1 escalada, luego pendiente-bloqueada]
- [x] CHK006 - ¿Se especifica cómo se detecta que un fallo es "por cuota" versus "otro fallo" de forma consistente entre los tres CLIs? [Consistency, Contracts headless-adapters — tabla de patrones por CLI]
- [x] CHK007 - ¿Está definido qué pasa si el orquestador mismo (CLI principal) agota su propia cuota a mitad de una corrida? [Gap → resuelto: nuevo edge case — pausa ordenada + retomable desde otro principal]
- [x] CHK008 - ¿Se define el estado resultante de una corrida interrumpida a mitad de la fase implement? [Coverage → resuelto: FR-012 — retomar = despachar solo tareas sin [X], estado desde tasks.md + reporte]
- [x] CHK009 - ¿El timeout por tarea está reflejado como requisito en la spec o solo vive en el contrato? [Consistency → resuelto: FR-016 — 15 min por defecto, configurable]
- [x] CHK010 - ¿Está especificado si el fallback respeta el nivel `[C:]` original o puede degradar la complejidad? [Ambiguity — cubierto: fallback dentro del nivel (contracts task-labels regla 1), escalada solo hacia arriba (Edge Cases)]
- [x] CHK011 - ¿Se definen requisitos para conflictos de archivos cuando la tarea no declara rutas explícitas? [Edge Case → resuelto: FR-017 — tarea [P] sin rutas se serializa]

## Contratos de Datos

- [x] CHK012 - ¿Está definido el comportamiento cuando `models.json` existe pero es inválido, distinto del caso "no existe"? [Coverage → resuelto: nuevo edge case — se trata como faltante, se informa el problema concreto]
- [x] CHK013 - ¿El mecanismo para distinguir "edición manual" de "valor detectado" está especificado de forma verificable? [Clarity, Contracts models-schema inv. 4 — comparación contra models.scan.json]
- [x] CHK014 - ¿Está definido qué pasa con las etiquetas al re-generar tasks.md después de asignar? [Gap → resuelto: nuevo edge case — se advierte la pérdida y se exige re-asignar antes de implementar]
- [x] CHK015 - ¿La regla de escritura automática cubre los campos derivados de cuota sin contradicción? [Consistency → resuelto: FR-018 reformulado — "campos de cuota" (estado, detección, reset)]
- [x] CHK016 - ¿Se especifica la codificación/formato de models.json para que tres CLIs lo editen sin corromperlo? [Gap → resuelto: contracts models-schema inv. 6 — UTF-8 sin BOM, indentación 2]
- [x] CHK017 - ¿Está definido cómo se estima `cuota_reset` cuando el plan es "desconocido"? [Edge Case → resuelto: FR-018 + contracts inv. 7 — reset desconocido, persiste hasta reset manual]
- [x] CHK018 - ¿El reporte define qué secciones son parseables versus informativas? [Clarity → resuelto: data-model §4 — Asignaciones y Modelos por fase parseables; el resto informativo]
- [x] CHK019 - ¿Son consistentes los estados de tarea entre data-model y la spec? [Consistency — el data-model es superconjunto compatible de lo que la spec exige reportar]

## Triage y Pipelines (cobertura mínima)

- [x] CHK020 - ¿Los criterios de clasificación simple/media/compleja son reproducibles? [Measurability → resuelto: FR-005 — rúbrica documentada con indicadores observables]
- [x] CHK021 - ¿Está definido qué constituye una "duda real"? [Clarity, Spec §FR-010 — enumeradas: clarificaciones, hallazgos críticos, gate pre-implement]
- [x] CHK022 - ¿Se especifica el comportamiento de `-bypass` cuando SÍ hay dudas pendientes? [Ambiguity → resuelto: FR-011 — frena igual; bypass solo salta el gate de confirmación]
- [x] CHK023 - ¿La retomabilidad define qué pasa con artefactos parciales o corruptos? [Edge Case → resuelto: nuevo edge case — se tratan como faltantes, se regeneran desde esa fase]

## Criterios de Éxito y Supuestos

- [x] CHK024 - ¿SC-004 define cómo y con qué unidad se mide el consumo? [Measurability → resuelto: SC-004 — unidad de uso reportada por cada CLI (tokens o % de cuota)]
- [x] CHK025 - ¿SC-003 contempla features sin tareas de algún nivel de complejidad? [Edge Case — cubierto: SC-003 acota a "tareas asignables de su nivel" + contracts task-labels regla 4 (justificación en reporte)]
- [x] CHK026 - ¿La detección reactiva de cuota está alineada con SC-005 ("sin intervención")? [Consistency — el fallback es automático; la intervención solo aparece sin candidatos restantes]
- [x] CHK027 - ¿Están documentadas las versiones mínimas de CLI para los flags headless asumidos? [Dependency → resuelto: nueva Assumption — versiones ≥ verificadas en diseño; el escaneo valida flags]

## Notes

- Revisión completada el 2026-07-18. Los 14 ítems marcados "→ resuelto" generaron
  ediciones en: `spec.md` (FR-005, FR-011, FR-012, FR-016, FR-017, FR-018, FR-019,
  SC-004, 6 edge cases nuevos, 1 assumption nueva), `contracts/models-schema.md`
  (invariantes 6 y 7) y `data-model.md` (§4 parseabilidad del reporte).
- Este checklist valida la REDACCIÓN de los requisitos, no el funcionamiento del
  sistema (eso es quickstart.md).
