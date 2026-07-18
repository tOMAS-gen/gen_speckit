# Checklist: Calidad de Requisitos — Soporte Genérico de CLIs y Multiplataforma

**Purpose**: Validar requisitos antes de generar tareas
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: equivalencia multi-OS + compatibilidad hacia atrás | **Depth**: estándar | **Audience**: autor
**Status**: ✅ Revisado 2026-07-18 — 14/14 resueltos (12 ya cubiertos, 2 corregidos en spec)

## Configuración y Verificación de CLIs

- [x] CHK001 - ¿La validación de alta es exhaustiva y con criterios objetivos? [Measurability, contracts/cli-config-operations V1–V6]
- [x] CHK002 - ¿El comportamiento ante registro inválido evita estados parciales? [Coverage, Spec §FR-003 — rechazo completo, nunca persiste]
- [x] CHK003 - ¿La verificación distingue niveles con/sin gasto de cuota de forma verificable? [Measurability, Spec §FR-006 + SC-006]
- [x] CHK004 - ¿Está definido el riesgo de plantillas maliciosas registradas? [Edge Case, Spec §Edge Cases — comando mostrado + aprobación]
- [x] CHK005 - ¿La baja define qué pasa con los CLIs del catálogo (que un re-escaneo re-crearía)? [Gap → resuelto: nuevo edge case en spec — `deshabilitado: true`, respetado por escaneo y ranking]
- [x] CHK006 - ¿La baja contempla etiquetas [M:] activas? [Coverage, Spec §FR-005 + Edge Cases]

## Generalización y Compatibilidad

- [x] CHK007 - ¿"Cero hardcodeo" es objetivamente verificable? [Measurability, SC-003 — búsqueda automática, catálogo como única fuente]
- [x] CHK008 - ¿La resolución inventario>catálogo>genérico está definida sin ambigüedad? [Clarity, data-model §2 + contracts/clis-catalog inv. 2]
- [x] CHK009 - ¿El caso de catálogo ausente/corrupto está definido? [Gap → resuelto: nuevo edge case en spec — no fatal, defaults genéricos + aviso]
- [x] CHK010 - ¿La compatibilidad v1 preserva las ediciones manuales con mecanismo definido? [Consistency, Spec §FR-011 + garantías FR-004 del proyecto]
- [x] CHK011 - ¿Los nombres de CLI registrados son compatibles con las etiquetas [M:] existentes? [Consistency, research R7 — mismo patrón en alta y regex]

## Multiplataforma

- [x] CHK012 - ¿"Comportamiento equivalente" (FR-013) tiene forma de verificación concreta? [Measurability, SC-005 — suite en 3 OS vía CI + escenarios stub]
- [x] CHK013 - ¿Los supuestos Windows a eliminar están enumerados (no genéricos)? [Completeness, Spec §FR-014 — intérprete, utilidades, rutas, kill de árbol; aislados en helper único (plan)]
- [x] CHK014 - ¿El prerequisito pwsh es detectable con mensaje accionable? [Clarity, Spec §FR-015 + Edge Cases]

## Notes

- CHK005 y CHK009 generaron 2 casos borde nuevos en spec.md; el resto ya estaba
  cubierto por spec/clarificaciones/contratos/data-model.
