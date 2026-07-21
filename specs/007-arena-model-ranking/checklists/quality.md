# Requirements Quality Checklist: Clasificación de modelos por nivel y tarea

**Purpose**: Validar la **calidad de los requisitos escritos** (completitud, claridad,
consistencia, medibilidad, cobertura) antes de generar tareas. No valida implementación.
**Created**: 2026-07-19
**Feature**: [spec.md](../spec.md)

**Foco**: integración con fuente externa y degradación · contratos de datos y precedencia
global↔local. **Audiencia**: revisor. **Profundidad**: estándar.

## Requirement Completeness

- [x] CHK001 - ¿Están documentados los requisitos para el caso en que la fuente externa no responde, tarda de más o entrega contenido ininterpretable? [Completeness, Spec §FR-018]
- [x] CHK002 - ¿Está definido qué ocurre con una clasificación guardada corrupta o de formato no reconocido? [Completeness, Spec §FR-020]
- [x] CHK003 - ¿Se especifica qué datos tiene prohibido contener el almacén de la máquina? [Completeness, Spec §FR-016]
- [x] CHK004 - ¿Existe un requisito que garantice que el comportamiento actual se preserva cuando no hay clasificación alguna? [Completeness, Spec §FR-022]
- [x] CHK005 - ¿Están definidos los requisitos para que el usuario revierta la decisión global↔local y borre lo guardado? [Completeness, Spec §FR-015]
- [x] CHK006 - ¿Define el spec un requisito para el caso, listado en Edge Cases, de **falta de permisos de escritura** en el directorio de configuración del usuario? [Gap→resuelto, Spec §FR-020a]
- [x] CHK007 - ¿Define el spec qué pasa con los datos ya guardados cuando **cambia la versión de formato** del almacén (migración vs. descarte vs. pérdida de los planes declarados)? [Gap→resuelto, Spec §FR-020]
- [x] CHK008 - ¿Establece el spec un criterio de **muestra mínima** (cantidad de votos) para considerar confiable una entrada del leaderboard? [Gap→resuelto, Spec §FR-019a]

## Requirement Clarity

- [x] CHK009 - ¿Está definido de forma inequívoca el orden de precedencia entre las cuatro fuentes de un mismo dato? [Clarity, Spec §FR-012]
- [x] CHK010 - ¿Es explícito que "el nivel medido reemplaza la semilla" y que el inventario mantiene un único campo de nivel? [Clarity, Spec §FR-005]
- [x] CHK011 - ¿Está claro qué significa que un mapeo sea "inequívoco" frente a "dudoso" en términos de la acción que dispara cada uno? [Clarity, Spec §FR-004a]
- [x] CHK012 - ¿Se distingue con claridad el dato "fecha del snapshot publicado" del dato "fecha en que se consultó"? [Clarity, Spec §FR-002]
- [x] CHK013 - ¿Está **cuantificado dentro de un requisito** el umbral de frescura, o solo aparece como supuesto? [Clarity→resuelto, Spec §FR-019]
- [ ] CHK014 - ¿Enumera el spec **cuáles** son los tipos de fase que reciben un orden de candidatos propio, o queda abierto? [Clarity, Spec §FR-009]

## Requirement Consistency

- [x] CHK015 - ¿Son consistentes entre sí la regla de "preguntar una sola vez por máquina" y la de "poder cambiar la decisión después"? [Consistency, Spec §FR-013 vs §FR-015]
- [x] CHK016 - ¿Es consistente que el plan/suscripción se comparta en la máquina mientras el estado de cuota permanece en el proyecto? [Consistency, Spec §FR-016 vs §Assumptions]
- [x] CHK017 - ¿Coincide la afirmación de que la corrección manual siempre prevalece en todos los requisitos donde aparece? [Consistency, Spec §FR-006, §FR-012, §SC-007]
- [x] CHK018 - ¿Es consistente el requisito de no excluir modelos con el de derivar el nivel del puntaje externo? [Consistency, Spec §FR-010 vs §FR-005]
- [x] CHK019 - ¿La terminología es estable a lo largo del documento (nivel / puntaje / fortalezas / clasificación), sin sinónimos que compitan? [Consistency]

## Acceptance Criteria Quality

- [x] CHK020 - ¿El criterio de éxito sobre resiliencia es objetivamente verificable sin conocer la implementación? [Measurability, Spec §SC-003]
- [x] CHK021 - ¿Está acotado con un número el costo temporal que la feature puede agregar al comando? [Measurability, Spec §SC-004]
- [x] CHK022 - ¿Es verificable el criterio de reproducibilidad entre dos corridas? [Measurability, Spec §SC-006]
- [x] CHK023 - ¿Es medible el criterio del 80 % de asociación correcta, dado que varios modelos requieren **confirmación del usuario** para asociarse? ¿Cuenta un mapeo confirmado por el usuario dentro de ese 80 %? [Ambiguity→resuelto, Spec §SC-001]
- [x] CHK024 - ¿El criterio sobre no perder correcciones manuales está expresado como cantidad verificable (cero sobrescrituras)? [Measurability, Spec §SC-007]

## Scenario Coverage

- [x] CHK025 - ¿Hay requisitos para el flujo principal (primera clasificación en un proyecto)? [Coverage, Spec §US1]
- [x] CHK026 - ¿Hay requisitos para el flujo alternativo (segundo proyecto que hereda lo declarado)? [Coverage, Spec §US2]
- [x] CHK027 - ¿Hay requisitos para el flujo de excepción (fuente caída, con y sin dato previo)? [Coverage, Spec §US4]
- [x] CHK028 - ¿Hay requisitos para el flujo de recuperación (refrescar a demanda, olvidar lo global, corregir a mano)? [Coverage, Spec §FR-015]
- [x] CHK029 - ¿Se cubre el escenario de un modelo del inventario **ausente** del leaderboard, que el research confirmó como caso real y no hipotético? [Coverage, Spec §FR-010]

## Edge Case Coverage

- [x] CHK030 - ¿Están definidos los requisitos ante escritura concurrente del archivo compartido por dos proyectos? [Edge Case, Spec §FR-017]
- [x] CHK031 - ¿Está definido el desempate cuando dos candidatos tienen puntaje equivalente? [Edge Case, Spec §FR-011]
- [x] CHK032 - ¿Se aborda el caso de varias variantes de esfuerzo del mismo modelo en el leaderboard? [Edge Case, Spec §Assumptions, §Edge Cases]
- [x] CHK033 - ¿Se aborda el caso de modelos del inventario que no son de texto o no compiten en el leaderboard? [Edge Case, Spec §Edge Cases]

## Non-Functional Requirements

- [x] CHK034 - ¿Están especificados los requisitos de privacidad respecto de lo que se envía a la fuente externa? [NFR, Spec §FR-021]
- [x] CHK035 - ¿Se especifica que la obtención no puede depender de las capacidades particulares del CLI principal? [NFR/Portabilidad, Spec §FR-005a]
- [x] CHK036 - ¿Hay un requisito de comprensibilidad de la salida (que el usuario entienda el origen de cada nivel sin abrir archivos)? [NFR/UX, Spec §SC-005]

## Dependencies & Assumptions

- [x] CHK037 - ¿Está documentado el supuesto de que la fuente es pública y sin autenticación, junto con su plan de contingencia si cambia el formato? [Assumption, Spec §Assumptions, §FR-018]
- [x] CHK038 - ¿Está documentado por qué el costo NO se toma del leaderboard sino del plan declarado? [Assumption, Spec §Assumptions]
- [x] CHK039 - ¿Está declarada la dependencia con las features previas de inventario y descubrimiento de modelos? [Dependency, Spec §Assumptions]
- [x] CHK040 - ¿Está acotado el alcance a modelos de texto, excluyendo explícitamente otros leaderboards? [Scope, Spec §Assumptions]

## Notas de la evaluación (2026-07-19)

**Primera pasada: 35/40.** Los 5 fallos eran huecos reales de redacción (no de diseño).
Cuatro se corrigieron en el spec en el acto; queda uno abierto por bajo impacto.

**Segunda pasada: 39/40.**

Detalle de los hallazgos:

- **CHK007 (corregido)** — El hallazgo de más impacto. FR-020 decía que un formato no
  reconocido "se ignora con aviso", pero tras la ampliación de alcance el almacén guarda
  **planes declarados por el usuario**: ignorar el archivo entero por un cambio de versión
  le habría hecho perder en silencio justo lo que la feature promete no volver a
  preguntar. FR-020 ahora prohíbe descartar datos declarados por el usuario.
- **CHK008 (corregido)** — Ningún requisito fijaba muestra mínima de votos; el diseño
  guardaba `vote_count` "para descartar entradas con muestra insuficiente" sin umbral, así
  que el implementador lo habría inventado. Nuevo FR-019a: mínimo configurable, 500 por
  defecto.
- **CHK023 (corregido)** — SC-001 pedía 80 % de asociación correcta, pero el research
  mostró que `opus`, `sonnet` y `gpt-5.5` **requieren confirmación del usuario**: sin
  aclarar si un mapeo confirmado cuenta, el criterio no era verificable. SC-001 ahora lo
  dice y además jerarquiza: asociar mal es inaceptable, no asociar solo pierde precisión.
- **CHK006 (corregido)** — Edge case sin requisito (directorio de configuración no
  escribible). Nuevo FR-020a: avisar y degradar a guardado local.
- **CHK013 (corregido)** — El umbral de frescura pasó de Assumptions a FR-019.
- **CHK014 (abierto, bajo impacto)** — FR-009 no enumera qué fases reciben orden propio;
  la lista vive en el catálogo por diseño (R6), precisamente para poder cambiarla sin
  tocar el spec ni el código. Se deja así de forma deliberada.
