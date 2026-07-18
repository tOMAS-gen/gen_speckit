# Playbook: Orquestación de la implementación

> Lógica portable. Entrada: `specs/<feature>/tasks.md` etiquetado (`[C:]`/`[M:]`) +
> `.specify/models.json` válido. El CLI que ejecuta este playbook es el **principal**:
> despacha, verifica, integra y es el ÚNICO que marca `[X]`. Los secundarios ejecutan
> tareas vía headless y NUNCA tocan `tasks.md`.

## Paso 0 — Validación previa

1. Leer `.specify/feature.json` → directorio de la feature; leer `tasks.md` y
   `.specify/models.json`. Inventario faltante/inválido → informar, ofrecer
   `/speckit-models`, detenerse.
2. Validar cada etiqueta `[M:cli/modelo]` contra el inventario: CLI instalado y modelo
   existente. Etiqueta inválida → aplicar el primer candidato válido de
   `asignacion.<C de la tarea>` e informarlo; sin candidatos → tarea no despachable,
   pedir corrección.
3. Tareas sin `[M:]` → reportarlas como sin asignar y ofrecer correr el playbook
   `assign.md` antes de continuar.
4. **Retome**: si hay tareas ya `[X]`, esto es una reanudación — despachar solo las
   pendientes, reconstruyendo estado desde `tasks.md` + sección Asignaciones del
   reporte (FR-012).

## Paso 1 — Planificar las tandas

```powershell
.specify/scripts/powershell/get-parallel-groups.ps1 -TasksPath specs/<feature>/tasks.md
```

Devuelve los grupos ordenados: `[P]` sin conflictos de ruta en paralelo (límite 4 por
defecto), el resto serializado. Respetar además las dependencias de fase declaradas en
`tasks.md` (Setup → Foundational → historias): nunca despachar una tarea cuya fase
bloqueante no terminó.

## Paso 2 — Despachar cada grupo

Para cada tarea del grupo:

- **Si `[M:]` es el propio principal**: ejecutarla en sesión (el principal nunca se
  auto-invoca por headless).
- **Si es un secundario**: empaquetar el prompt según `contracts/headless-adapters.md`
  (identificación T### + descripción literal + rutas; referencias a spec/plan para
  leer del disco, no pegadas; restricciones: solo dentro del repo, no tocar
  `tasks.md`, reportar archivos tocados) y despachar:

  ```powershell
  .specify/scripts/powershell/invoke-secondary.ps1 -Cli <cli> -Model <modelo> `
      -Prompt "<prompt empaquetado>" -ModelsPath .specify/models.json `
      -LogDir specs/<feature>/orchestration-logs -LogBaseName <T###>
  ```

  Los grupos paralelos se lanzan como jobs concurrentes (`Start-Job` o procesos en
  background); esperar TODO el grupo antes de verificar y pasar al siguiente.

## Paso 3 — Interpretar resultados y fallback

Según la `clasificacion` que devuelve el script (contrato headless-adapters):

| Resultado | Acción |
|---|---|
| `exito` | Pasar a verificación (Paso 4) |
| `cuota_agotada` | `update-quota.ps1 -Cli <cli> -Estado agotada`; reasignar la tarea al SIGUIENTE candidato de `asignacion.<nivel>` (luego niveles superiores); actualizar la etiqueta `[M:]` en `tasks.md`; registrar el evento; re-despachar |
| `indisponible` | Igual que cuota (fallback + etiqueta + evento) pero SIN tocar el inventario |
| Sin candidatos restantes | La tarea queda `pendiente_bloqueada`: NO frenar las demás; al final, reportar qué quedó bloqueado y por qué |

Si el **principal** agota su propia cuota: pausa ordenada — esperar las tareas en
vuelo, verificar lo que se pueda, persistir estado (tasks.md + reporte) e indicar al
usuario cómo retomar desde otro CLI como principal.

## Paso 4 — Verificación estándar (FR-019) — solo el principal

Para cada tarea que terminó:

- (a) Revisar el diff producido contra lo que la tarea describe (leer los archivos
  tocados según el resumen del secundario y los logs).
- (b) Correr las validaciones existentes del proyecto (tests/build si los hay) sin
  que fallen.

Resultado:

- **Pasa** → marcar `[X]` en `tasks.md`, estado `verificada` en el reporte.
- **Falla** → ciclo acotado: 1 reintento al MISMO modelo incluyendo el motivo del
  rechazo → si vuelve a fallar, 1 escalada al siguiente candidato de mayor capacidad →
  si aún falla, `pendiente_bloqueada` + reporte. NUNCA marcar `[X]` sin verificar.

## Paso 5 — Cierre

1. Actualizar la sección Asignaciones (estados finales) y Eventos del reporte.
2. Completar Métricas: tareas por modelo, % ejecutado por modelos económicos
   (costo < 3), y consumo estimado del modelo caro vs. baseline (SC-004), en la
   unidad que reporte cada CLI.
3. Resumen en consola: completadas/bloqueadas, fallbacks aplicados, dónde están los
   logs (`orchestration-logs/`).
4. Si quedó algo bloqueado: instrucciones concretas (esperar reset de cuota, corregir
   etiqueta, correr de nuevo — el retome despacha solo lo pendiente).
