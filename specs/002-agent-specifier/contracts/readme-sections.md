# Contract: secciones gestionadas del README

**Feature**: 002-agent-specifier

Contrato entre `speckit-readme` (productor) y el `README.md` del proyecto.

## Delimitadores

```markdown
<!-- speckit:objetivo:inicio -->
## Objetivo
<contenido gestionado>
_Actualizado: 2026-07-18_
<!-- speckit:objetivo:fin -->
```

Secciones gestionadas: `objetivo` (obligatoria), `alcance` (qué es / qué no es),
`estado` (features y su fase, derivado de `specs/*/`). Cada una con su par
`inicio`/`fin` y su línea `_Actualizado: <fecha>_`.

## Reglas duras

1. **Todo lo externo a los delimitadores es intocable** — byte a byte (FR-008).
2. Re-ejecución: reemplazar SOLO el interior de cada par de delimitadores presente;
   secciones gestionadas ausentes se ofrecen, no se imponen.
3. README inexistente → se crea con las tres secciones gestionadas + espacio para
   contenido manual.
4. README preexistente sin delimitadores → proponer el punto de inserción (después
   del título principal) y MOSTRAR el diff propuesto antes de escribir (FR-009).
5. Un delimitador de `inicio` sin su `fin` (o viceversa) es un README corrupto para
   la skill: reportar y pedir corrección manual; nunca adivinar el cierre.
6. Fuente del contenido: constitución → README previo → specs → declaración del
   usuario (FR-001, mismo orden que el especificador).
