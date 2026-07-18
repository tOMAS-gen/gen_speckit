---
name: "speckit-clis"
description: "Configura CLIs genéricos de IA en .specify/models.json: registra, edita, verifica y da de baja cualquier CLI del inventario."
argument-hint: "registrar | editar | verificar | dar-de-baja [nombre]"
metadata:
  author: "gen_speckit"
user-invocable: true
---

## Objetivo

Administrar entradas individuales de `.specify/models.json` sin regenerar el inventario
completo. Esta skill trabaja sobre un CLI a la vez y respeta las ediciones manuales del
usuario.

## REGISTRAR

1. **Pedir al usuario**:
   - `nombre`: kebab-case (`^[a-z][a-z0-9-]*$`).
   - `headless`: plantilla de invocación headless que contenga el placeholder `{prompt}`.
     Si se declaran más de un modelo, la plantilla debe contener `{modelo}` o aceptar el
     default `--model`.
   - `modelos`: array de al menos uno. Cada modelo necesita:
     - `id`: único dentro del CLI.
     - `capacidad`: entero 1–10.
     - `costo`: entero 1–3.
     - `contexto_k`: ventana de contexto en miles de tokens (entero) o `"desconocido"`.
   - Opcionalmente `patrones_cuota`: lista de expresiones regulares válidas.
   - Opcionalmente `version_cmd`: comando para consultar la versión.

2. **Mostrar resumen** con todos los valores antes de ejecutar.

3. **Ejecutar**:

   ```powershell
   .specify/scripts/powershell/clis-config.ps1 `
     -Operacion agregar `
     -ModelsPath ".specify/models.json" `
     -Nombre "<nombre>" `
     -Headless "<plantilla>" `
     -Modelos @(
       @{ id="<id>"; capacidad=<1-10>; costo=<1-3>; contexto_k=<entero en miles de tokens o "desconocido"> }
     ) `
     [-PatronesCuota @("<regex>"[, ...])] `
     [-VersionCmd "<comando>"]
   ```

4. Si el script rechaza la definición, **mostrar los mensajes de validación tal cual**
   aparecen en el error (lista de problemas V1–V6) y no modificar el inventario.

## EDITAR

1. **Pedir al usuario** el nombre del CLI existente.
2. **Pedir solo los campos que quiere cambiar**. No enviar los campos que no se tocan.
3. **Ejecutar** con `-Operacion editar` pasando únicamente los campos modificados:

   ```powershell
   .specify/scripts/powershell/clis-config.ps1 `
     -Operacion editar `
     -ModelsPath ".specify/models.json" `
     -Nombre "<nombre>" `
     [-Headless "<nueva plantilla>"] `
     [-Modelos @(@{ id="..."; capacidad=...; costo=...; contexto_k=... })] `
     [-PatronesCuota @("...")] `
     [-VersionCmd "..."]
   ```

4. El script valida el resultado final con las mismas reglas que el alta. Si falla,
   mostrar el error tal cual y dejar el inventario sin cambios.

## DAR DE BAJA

1. **Obtener las advertencias** de etiquetas `[M:<nombre>/...]` activas en
   `specs/*/tasks.md`. El script expone esta información mediante
   `Get-ActiveCliTaskLabels`; por ejemplo:

   ```powershell
   $models = (Resolve-Path ".specify/models.json").Path
   . .specify/scripts/powershell/clis-config.ps1
   Get-ActiveCliTaskLabels -ModelsPath $models -Nombre "<nombre>"
   ```

2. **Mostrar cada tarea activa** (archivo, línea y texto) al usuario. Si no hay
   advertencias, indicarlo.

3. **Pedir confirmación explícita**: el usuario debe responder afirmativamente; sin
   confirmación no se ejecuta la baja.

4. **Recién entonces ejecutar**:

   ```powershell
   .specify/scripts/powershell/clis-config.ps1 `
     -Operacion eliminar `
     -ModelsPath ".specify/models.json" `
     -Nombre "<nombre>" `
     -Confirmado
   ```

5. **Efecto**:
   - Si el CLI es de `origen: catalogo`, queda marcado como `deshabilitado: true`
     (el catálogo es inmutable; eliminarlo haría que el próximo escaneo lo recree).
   - Si el CLI es de `origen: registrado`, se elimina del inventario.

## VERIFICAR

1. **Pedir al usuario** el nombre del CLI a verificar (debe existir en
   `.specify/models.json`).

2. **Ejecutar primero sin prueba real** para mostrar el diagnóstico por niveles:

   ```powershell
   .specify/scripts/powershell/clis-config.ps1 `
     -Operacion verificar `
     -ModelsPath ".specify/models.json" `
     -Nombre "<nombre>"
   ```

   Interpretar el resultado:
   - **Nivel a**: resolución del ejecutable (`ok` / `fallo`).
   - **Nivel b**: autenticación detectable por hints del SO (`ok` / `fallo` /
     `ok` sin verificación).
   - **Nivel c**: invocación de prueba real. Por defecto queda **omitido**
     para no gastar cuota.

3. **Si el nivel c está omitido**, explicar al usuario que ese nivel **consume
   UNA llamada del CLI** y solo se ejecuta si lo aprueba explícitamente. Antes
   de ejecutarlo, **mostrar el comando exacto** que se usará: reemplazar en la
   plantilla `headless` del CLI el primer modelo disponible y el prompt
   `'responde solo: ok'`. Pedir confirmación explícita.

4. **Si el usuario aprueba**, repetir con `-AprobarPrueba`:

   ```powershell
   .specify/scripts/powershell/clis-config.ps1 `
     -Operacion verificar `
     -ModelsPath ".specify/models.json" `
     -Nombre "<nombre>" `
     -AprobarPrueba
   ```

   El diagnóstico del nivel c mostrará el comando renderizado, la clasificación
   (`exito` / `fallo` / `cuota`), el código de salida y la latencia en segundos.

5. **Efecto en el inventario**: el script actualiza **solo los campos
   detectables** (`instalado`, `autenticado`, `version`). Los campos del usuario
   (`headless`, `modelos`, `patrones_cuota`, `plan`, `cuota`, etc.) quedan
   intactos.

## Reglas

- Las ediciones manuales del usuario en `.specify/models.json` siempre prevalecen; no
  sobrescribir campos que no se estén modificando.
- La baja **jamás** borra o deshabilita sin confirmación explícita del usuario.
- Estas operaciones **no gastan cuota**: solo leen/escriben `.specify/models.json` y
  escanean `tasks.md`.
