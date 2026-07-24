# Playbook: Triage de la idea

> Lógica portable (cualquier CLI principal la ejecuta). Contrato de entrada: la idea
> del usuario, el flujo invocado (ECO/IDEAL), los flags (`-bypass`), y un
> `.specify/models.json` válido. Salida: decisión de flujo + modelos por fase,
> registrada en el reporte de orquestación. NO ejecuta ninguna fase: el despacho
> efectivo se resuelve en `.specify/orchestrator/dispatch-phase.md`.

## Quién ejecuta el triage

El **modelo más capaz disponible**: primer candidato de `asignacion.alta` con
`cuota != "agotada"` (empate → orden de lista). Si ese modelo no es el que está
leyendo esto, ver "Autoevaluación del punto de entrada".

## Paso 0 — Precondiciones

1. Leer `.specify/models.json`. Si no existe o no parsea: informar el problema
   concreto, ofrecer correr `/speckit-models`, y DETENERSE. Nunca inventar inventario.
2. Crear el reporte de la feature desde `.specify/orchestrator/report-template.md`
   como `specs/<feature>/orchestration-report.md` (si no existe aún; si la feature
   todavía no tiene directorio, crearlo tras la fase specify y volcar el triage ahí).

## Paso 1 — Clasificar la idea (rúbrica observable)

Evaluar los TRES indicadores; la clasificación es el máximo nivel alcanzado:

| Indicador | simple | media | compleja |
|---|---|---|---|
| **Alcance**: componentes/sistemas tocados | 1 componente, sin integraciones | 2–3 componentes o 1 integración | >3 componentes, integraciones múltiples o cambios transversales |
| **Ambigüedad**: claridad de criterios de éxito | Resultado obvio y verificable | Requiere definir algunos criterios | Objetivos difusos, requiere clarificación sustancial |
| **Riesgo**: datos, seguridad, irreversibilidad | Sin datos sensibles ni estado compartido | Toca datos persistentes o APIs externas | Migraciones, pagos, seguridad, o difícil de revertir |

Registrar la justificación (una línea por indicador) en la sección Triage del reporte.

## Paso 2 — Elegir flujo y modelos por fase

| Complejidad | Flujo | Asignación de fases |
|---|---|---|
| simple | ECO (specify → plan → tasks → gate → implement) | Todas las fases con candidatos de `asignacion.baja`/`media`; el modelo importante SOLO asigna en tasks |
| media | IDEAL (7 fases) | plan y analyze con el primer candidato de `alta`; el resto con `media` |
| compleja | IDEAL (7 fases) | specify, plan y analyze con el primer candidato de `alta`; el resto con `media` |

- La fase **tasks incluye siempre el paso de asignación** ejecutado por el primer
  candidato de `alta` (playbook `assign.md`) — equivocar el reparto es caro.
- Volcar la tabla resultante en la sección "Modelos por fase" del reporte (estado
  `pendiente`).
- **Ejecución del reparto**: con inventario válido, las fases asignadas a un modelo
  distinto del principal se ejecutan efectivamente vía el playbook
  `.specify/orchestrator/dispatch-phase.md`. El modo decisión-solo (registrar modelos
  y ejecutar todo en el principal) queda solo como fallback cuando no hay inventario
  válido, cuando el usuario pide modo clásico, o cuando `dispatch-phase.md` no está
  disponible en el proyecto; toda caída al fallback se registra en Eventos del reporte.

## Paso 3 — Discordancia flujo invocado vs. recomendado

- Coinciden → continuar.
- Difieren y **sin `-bypass`** → preguntar al usuario si cambia al flujo recomendado
  (mostrar por qué, con la rúbrica). Esperar respuesta.
- Difieren y **con `-bypass`** → cambiar al recomendado automáticamente y registrar
  el cambio en Triage y Eventos del reporte.

## Paso 4 — Autoevaluación del punto de entrada (FR-007)

Comparar el modelo que está ejecutando este triage con el que la tabla del Paso 2
exige para las fases clave:

- **Punto de entrada inferior** (ej.: idea compleja escrita en el CLI económico):
  ESCALAR — las fases clave se asignan al modelo superior del ranking; el CLI de
  entrada queda como secundario/despachador. Registrar en Triage y Eventos.
- **Punto de entrada superior** (ej.: idea simple escrita en el CLI caro): DEGRADAR —
  asignar las fases a los modelos económicos; el modelo caro no ejecuta fases que un
  económico resuelve. Registrar igual.
- Ningún punto de entrada es un error: el sistema se reacomoda solo, hacia arriba o
  hacia abajo.

## Paso 5 — Cierre

Resumen en consola (complejidad, flujo, modelos por fase, escalada/degradación si
hubo) y reporte actualizado. Devolver el control al pipeline para que ejecute la
primera fase.
