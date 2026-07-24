# Contract: `--prompt-file` en `invoke_secondary.py`

**Feature**: `008-multi-model-phase-dispatch`

## Interfaz

```
python .specify/scripts/python/invoke_secondary.py \
  --cli <cli> [--model <modelo>] \
  ( --prompt "<texto>" | --prompt-file <ruta> ) \
  --models-path <ruta> --log-dir <ruta> [--log-base-name <base>] \
  [--timeout <seg>] [--working-directory <ruta>]
```

- `--prompt` y `--prompt-file` son mutuamente excluyentes; exactamente uno es
  obligatorio. Ambos o ninguno ⇒ exit 2 con mensaje claro (sin invocar nada).

## Semántica de `--prompt-file`

1. La ruta debe existir, ser legible y estar DENTRO del repositorio (resuelta
   absoluta, comparada contra `--working-directory`/cwd). Fuera del repo ⇒ exit 2.
2. El archivo se lee como UTF-8; vacío ⇒ exit 2.
3. El comando headless se construye con un **prompt puntero** corto (< 500
   caracteres), generado por el script:

   ```text
   Lee el archivo <ruta-relativa-al-repo> y ejecuta COMPLETAS las instrucciones
   que contiene. Trabaja solo dentro de este repositorio. Al terminar, lista los
   archivos que escribiste.
   ```

   El contenido del archivo NUNCA se interpola en la línea de comandos (evita el
   límite de ~8191 chars de `cmd.exe` y el aplanado de whitespace del prompt
   inline).
4. El puntero pasa por el mismo escape/sustitución `{prompt}` existente.

## Salida

JSON existente + campo aditivo:

```jsonc
{
  "clasificacion": "exito | cuota_agotada | indisponible",
  "intentos": 1,
  "exitCode": 0,
  "stdoutPath": "...",
  "stderrPath": "...",
  "comando": "...",
  "promptFile": "specs/008-x/.phase-dispatch/plan.prompt.md"   // null con --prompt
}
```

## Compatibilidad

- Toda invocación existente con `--prompt` conserva comportamiento byte-idéntico
  (mismo escape, mismo aplanado, mismo JSON con `promptFile: null`).
- Los consumidores actuales (playbook orchestrate, tests) no requieren cambios para
  seguir funcionando; el playbook de fases y el de tareas PUEDEN migrar a
  `--prompt-file` para prompts largos.

## Casos de error

| Caso | Resultado |
|---|---|
| Ambos flags | exit 2, mensaje "usar --prompt O --prompt-file" |
| Ninguno | exit 2 (argparse required group) |
| Archivo inexistente / ilegible | exit 2, ruta en el mensaje |
| Archivo fuera del repo | exit 2, motivo "fuera del repositorio" |
| Archivo vacío | exit 2 |
| CLI/modelo/inventario inválidos | comportamiento existente sin cambios |
