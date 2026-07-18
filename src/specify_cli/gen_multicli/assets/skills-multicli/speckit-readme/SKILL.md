---
name: "speckit-readme"
description: "Crea o actualiza el README.md del proyecto con secciones gestionadas delimitadas por comentarios HTML (objetivo, alcance, estado con fecha), preservando todo el contenido manual fuera de los delimitadores. Usar cuando el usuario invoca /speckit-readme o cuando un pipeline necesita mantener el README al día."
argument-hint: ""
compatibility: "Cualquier proyecto spec-kit con README.md raíz"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Objetivo

Crear o actualizar el `README.md` raíz del proyecto manteniendo visibles y al día las
secciones gestionadas: **objetivo**, **alcance** y **estado**. Todo el contenido manual
fuera de los delimitadores se preserva byte a byte. La skill nunca reescribe un README
ajeno sin aprobación ni adivina el cierre de un delimitador roto.

## Pasos

1. **Determinar el idioma y la fuente del objetivo** (FR-007, FR-001):

   Leer en este orden hasta obtener un objetivo claro:
   - Archivo de constitución del proyecto (si existe: `.specify/memory/constitution.md`).
   - Sección `objetivo` del `README.md` actual (si ya está delimitada por
     `<!-- speckit:objetivo:inicio -->` / `<!-- speckit:objetivo:fin -->`).
   - `specs/*/spec.md` y `specs/*/README.md` (resumen del propósito del proyecto).
   - Declaración del usuario.

   Si ninguna fuente es legible, preguntar al usuario el objetivo antes de continuar.
   El idioma de las secciones gestionadas debe coincidir con el del proyecto detectado.

2. **Revisar el estado actual de `README.md`**:

   - Si no existe → ir al paso 5 (crear README nuevo).
   - Si existe → detectar todos los delimitadores `<!-- speckit:<seccion>:inicio -->` y
     `<!-- speckit:<seccion>:fin -->` para las secciones `objetivo`, `alcance` y
     `estado`.

3. **Validar la integridad de los delimitadores** (regla dura 5):

   Para cada sección gestionada, verificar que:
   - Si existe un delimitador de `inicio`, existe su correspondiente `fin`.
   - Si existe un delimitador de `fin`, existe su correspondiente `inicio`.
   - Los pares están en el orden correcto (`inicio` antes que `fin`).

   Si se encuentra cualquier delimitador roto (falta par, orden invertido, etiqueta
   malformada), **no escribir nada**. Reportar la corrupción al usuario, indicar la
   línea aproximada del problema y pedir corrección manual antes de reintentar.

4. **Generar el contenido actualizado de cada sección gestionada**:

   A partir de la fuente determinada en el paso 1, producir:
   - **Objetivo**: qué se construye y para qué.
   - **Alcance**: qué incluye el proyecto y qué queda fuera.
   - **Estado**: features principales y su fase actual, derivadas de `specs/*/spec.md`.

   Al final de cada sección gestionada agregar la línea:
   ```markdown
   _Actualizado: <fecha-actual-ISO-8601>_
   ```
   (FR-010).

5. **Crear o actualizar el archivo**:

   - **README inexistente**: crear `README.md` con un título principal, las tres
     secciones gestionadas delimitadas y un bloque de contenido manual vacío. Ejemplo:
     ```markdown
     # Nombre del proyecto

     <!-- speckit:objetivo:inicio -->
     ## Objetivo
     ...
     _Actualizado: 2026-07-18_
     <!-- speckit:objetivo:fin -->

     <!-- speckit:alcance:inicio -->
     ## Alcance
     ...
     _Actualizado: 2026-07-18_
     <!-- speckit:alcance:fin -->

     <!-- speckit:estado:inicio -->
     ## Estado
     ...
     _Actualizado: 2026-07-18_
     <!-- speckit:estado:fin -->

     <!-- Contenido manual: todo lo escrito fuera de los delimitadores anteriores se
          preserva en futuras ejecuciones. -->
     ```

   - **README existente con delimitadores completos**: reemplazar únicamente el
     contenido entre cada par `inicio`/`fin` por las secciones generadas en el paso 4.
     No modificar absolutamente nada fuera de los delimitadores, incluyendo espacios,
     saltos de línea y orden de secciones manuales.

   - **README preexistente sin delimitadores** (FR-009): proponer el punto de inserción
     (después del título principal `# ...`), mostrar el diff completo que resultaría de
     insertar las tres secciones gestionadas, y pedir confirmación explícita antes de
     escribir. Si el usuario declina, terminar sin efectos secundarios.

6. **Verificar el resultado**:

   - Leer el archivo resultante y confirmar que:
     - Todos los delimitadores de inicio tienen su correspondiente fin.
     - El contenido fuera de los delimitadores es idéntico al original (para README
       existente con delimitadores) o contiene el título principal y espacio para
       contenido manual (para README nuevo).
     - Cada sección gestionada incluye su línea `_Actualizado: <fecha>_`.

   Si la verificación falla, corregir antes de terminar.

7. **Mostrar resumen**: indicar qué se hizo (creado / actualizado / propuesta pendiente /
   corrupción detectada) y listar las secciones gestionadas encontradas o insertadas.

## Reglas

- **Contenido manual intocable**: fuera de los delimitadores `<!-- speckit:*:inicio/fin -->`
  no se agrega, elimina ni modifica nada — ni siquiera espacios en blanco (FR-008).
- **Secciones ausentes no se imponen**: si un README existente no tiene una sección
  gestionada (p. ej. falta `estado`), se ofrece insertarla; no se agrega sin aviso.
- **Delimitador roto = stop**: ante cualquier corrupción en los delimitadores, reportar
  y pedir corrección manual; nunca adivinar dónde termina una sección.
- **README sin delimitadores requiere confirmación**: mostrar el diff propuesto y
  esperar aprobación antes del primer cambio (FR-009).
- **Fecha obligatoria**: cada sección gestionada debe terminar con
  `_Actualizado: <fecha-actual>_` (FR-010).
